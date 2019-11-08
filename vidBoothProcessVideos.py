#!/usr/bin/python3
from argparse import ArgumentParser
from multiprocessing import Pool, cpu_count, Value
from time import sleep
from moviepy.editor import ImageClip, VideoFileClip, concatenate_videoclips, AudioFileClip, afx, CompositeAudioClip
from os import listdir, makedirs
from os.path import isfile, join, exists
import sys
import tarfile
from datetime import date
import subprocess

verbose = False
school = ""
#home = "S:\\Interdepartmental Share\\IT\\Scripts\\VID MERGE\\VidBooth" #Where are the Video Booth Clips?
home = sys.path[0]

audioFiles = [["bensound-funday.mp3", 6]] #pairs, file -> start time/beat drop
introCards = ["introCard.png"]
outroCards = ["outroCard.png"]

filecount = 0
currentfile = 0

dir = ""

#mainLog = open("log.txt" ,"w+") # Where do we store the output meta file

def main():
    ## SETUP ARGPARSE ##
    global school
    global verbose
    global mainLog
    global filecount
    global currentfile
    global home
    parser = ArgumentParser(
        description='MWS Video Booth : Utility : Render Videos'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        dest='verbose',
        default=False,
        required=False,
        action="store_true",
        help='Display progress'
    )
    parser.add_argument(
        '-s',
        '--school',
        dest='school',
        default=False,
        required=True,
        action='store',
        help='The School + City'
    )
    args = parser.parse_args()
    verbose = args.verbose
    school = args.school

    #######################
    # MAIN                #
    #######################
    #mainLog.write("Number of cpu : " + str(cpu_count()) + '\n')
    if (verbose):
        print("Number of cpu : ", cpu_count())
    dir = join(home, 'Captures', school)
    files = listdir(dir)
    filecount = len(files)
    for i in range(len(files)):
        files[i] = [school, files[i]]

    dispatcher(files)

def init(_currentfile, _filecount):
    global currentfile
    global filecount
    currentfile = _currentfile
    filecount = _filecount

def dispatcher(files):
    global currentfile
    global filecount
    global verbose
    global home
    global school
    dir = join(home, 'Finals', school)
    currentfile = Value('i', 0)
    filecount = Value('i', filecount)
    p = Pool(cpu_count(), initializer=init, initargs=(currentfile,filecount))
    p.map(dispatcher_process, files)
    p.close()
    p.join()
    if (verbose):
        print ("Archiving... ", dir)
    # Archive the finals
    arc = archive(dir)
    if (verbose):
        print (arc, " has been archived in: ", dir)

def dispatcher_process(file):
    global filecount
    global currentfile
    #global mainLog
    school = file[0]
    name = file[1]
    currentfile.value += 1
    _currentfile = currentfile.value

    #invoke = "python mergeClips.py"
    #args = '-v -school "' + school + '" -student "' + name + '"'

    #mainLog.write("[Starting]: School: " + school + ' | Student: ' + name + '\n')
    print("[Starting " + str(_currentfile) + "/" + str(filecount.value) + "]\nSchool: " + school + ' | Student: ' + name)
    mergeClips(school, name)
    #mainLog.write("[Done]: School: " + school + ' | Student: ' + name + '\n')
    print("[Done " + str(_currentfile) + "/" + str(filecount.value) + "]\nSchool: " + school + ' | Student: ' + name)

def get_volume(file):
    file = file.replace(" ", "\\ ")
    cmd = "ffmpeg -i {0} -filter:a volumedetect -f null /dev/null".format(file)
    out = subprocess.run(cmd, shell=True, stderr=subprocess.PIPE).stderr.decode('utf-8')
    spool = [o for o in out.split('\n') if "[Parsed_volumedetect" in o]
    mean = max = 0.0
    #print ("FILE: {0} \nOUT: {1} \nSPOOL: {2}".format(file, out, spool))
    for item in spool:
        if "mean_volume" in item:
            mean = float(item.split(":")[-1].replace("dB", "").strip())
            #print("FILE: {0} | MEAN: {1}".format(file, mean))
        elif "max_volume" in item:
            max = float(item.split(":")[-1].replace("dB", "").strip())
            #print("FILE: {0} | MAX: {1}".format(file, max))

    return mean, max

def mergeClips(school, student, verbose=False):
    #global mainLog
    global home
    #global verbose

    # SET VARIABLES
    dir = join(home, 'Finals', school, student) #The base of the video booth clips including school and student subfolders
    capturesHome = join(home, 'Captures', school, student)

    introHome = join(home, "Assets", "IntroCards")  #The folder intro cards can be found
    outroHome = join(home, "Assets", "OutroCards") #The folder outro cards can be found
    audioHome = join(home, "Assets", "Audio") #The folder the audio can be found

    introCard = introCards[0] #The selected intro card name
    outroCard = outroCards[0] #The selected outro card name

    audioFile = audioFiles[0][0] #The selected audio file name

    #replace this with FFMPEG-NORMALIZE
    clipVolumeMult = 1 #How much to boost/reduce the Video Booth audio, 1.0 remains the same
    musicVolumeMult = 0.05 #0.05 #How much to boost/reduce the music, 1.0 remains the same

    fade_duration = 0.5 #in seconds

    introCardDuration = audioFiles[0][1] #in seconds
    outroCardDuration = audioFiles[0][1] #in seconds

    # create folders if they do not already exist
    if (not exists(dir)):
        makedirs(dir)

    meta = open(join(dir, student.replace(" ", "_") + "_meta.txt") ,"w+") # Where do we store the output meta file
    log = open(join(dir, student.replace(" ", "_") + "_log.txt") ,"w+") # Where do we store the output meta file
    outFile = join(dir, student.replace(" ", "_") + "_Video_Booth_final.mp4") # Where to store the output video

    clips = [] #an empty container for clips to be added

    # Find Video Booth Clips
    log.write("Gathering Files\n")
    if (verbose):
        print ("Gathering files\n")
    files = [f for f in listdir(capturesHome) if isfile(join(capturesHome, f)) and ".mp4" in f]

    for f in range(len(files)):
        #print(join(capturesHome, files[f]))
        mean, max = get_volume(join(capturesHome, files[f]))
        #clipVolumeMult.append(max/3) #divide by 3db
        ratio = 4.65
        db = (max * -1) / ratio
        clipVolumeMult = db
        #print ("\nFile: {0} \nMax: {1} \nclipVolumeMult: {2}".format(join(capturesHome, files[f]), max, clipVolumeMult))

    ### BEFORE ANYTHING ELSE, NORMALIZE THE CLIPS AND UPDATE FILE LOCATIONS/NAMES

    # INTRO CARD
    log.write("Checking Intro Card: " + join(introHome, introCard) + '\n')
    if (verbose):
        print ("Checking Intro Card: " + join(introHome, introCard) + '\n')
    clips.append(ImageClip(join(introHome, introCard)).set_duration(introCardDuration))
    meta.write(join(introHome, introCard) + '\n')

    # VIDEO BOOTH CLIPS
    for file in files:
        log.write("Checking Clips: " + join(capturesHome, file) + '\n')
        if (verbose):
            print ("Checking Clips: " + join(capturesHome, file) + '\n')
        if file.endswith(".mp4"):
            meta.write(join(capturesHome, file) + '\n')
            clips.append(VideoFileClip(join(capturesHome, file)))

    # OUTRO CARD
    log.write("Checking Outro Card: " + join(outroHome, outroCard) + '\n')
    if (verbose):
        print ("Checking: " + join(outroHome, outroCard))
    clips.append(ImageClip(join(outroHome, outroCard)).set_duration(outroCardDuration))
    meta.write(join(outroHome, outroCard) + '\n')

    # IMPLEMENT CROSSFADE BETWEEN CLIPS
    for i in range(len(clips)):
        if (i != 0):
            clips[i] = clips[i].volumex(clipVolumeMult)
            clips[i] = clips[i].crossfadein(fade_duration)

    # Piece all clips together into one clip
    final_clip = concatenate_videoclips(clips, padding = -fade_duration, method="compose")

    # Check Audio
    log.write("Checking Audio: " + join(audioHome, audioFile) + '\n')
    if (verbose):
        print ("Checking Audio: " + join(audioHome, audioFile))
    audioclip = AudioFileClip(join(audioHome, audioFile)).set_duration(final_clip.duration)
    audioclip = afx.audio_loop(audioclip, duration=final_clip.duration)
    meta.write(join(audioHome, audioFile) + '\n')

    # mix audio with clip audio
    new_audioclip = CompositeAudioClip([final_clip.audio, audioclip.fx(afx.volumex, musicVolumeMult).fx(afx.audio_fadeout, fade_duration)])
    final_clip.audio = new_audioclip.set_duration(final_clip.duration)

    log.write("Writing Video File...\n")
    log.write("School: " + school + " | Student: " + student + '\n')

    if (verbose):
        final_clip.write_videofile(outFile, bitrate="5000k", verbose=verbose)
    else:
        final_clip.write_videofile(outFile, bitrate="5000k", verbose=verbose, logger=None)

    log.write("Done Writing Video File!\n")

    #close meta file and begin writing
    meta.close()
    log.close()
    #mainLog.close()

def archive(dir):
    global school
    files = listdir(dir)
    formatted_date = date.today().strftime("%Y-%m-%d")
    name = school + "-" + formatted_date + ".tar.bz2"
    tf = tarfile.open("Archive/" + name, mode="w:bz2")
    for filename in files:
        file = join(dir, filename)
        tf.add(file, arcname=join(school, filename))
    tf.close()
    return name

if __name__ == "__main__":
    main()
