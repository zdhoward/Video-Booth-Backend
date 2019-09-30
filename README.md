Video Booth Backend

Requirements:
- gphoto2
- pydub
- ffmpeg
- python3

Process:
- Setup
  - Physically set up the unit
  - Load video questions via CSV
  - Load event branding for splash screen and intro/outro cards
  - Load selectable music
- Capture Photos and/or Videos
  - Allow users to select photo or video mode
  - Give users a login to the website and say they will be online next day to order
  - If in video mode present skippable and redoable questions
- Process videos and photos in the backend and upload to the ordering site
  - Uses the backend to merge video (may want to await orders for this to happen)
  - May want to do some batch video editing for colour correction and etc. (could also be done after an order is placed)
- Upload link to ordering website for digital distrobution

Gear:
- PA Stand
- Camera Mount
- Raspberry Pi with attached SSD
- Camera of choice (that is compatible with gphoto2)
- Server + Ordering Website
