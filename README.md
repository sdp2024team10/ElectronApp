getting started:
- make sure you have npm: https://nodejs.org/en
- clone the repo to your local: git clone https://github.com/sdp2024team10/ElectronApp
- npm install

to run the app:
npm start

plan (need to implement branches currently everything is in origin):
- push to develop branch for any non-complete changes
- prod branch is going to be the current running state of the app

build the electron app (only will do at the very end of our project eg. MDR and final):
- npm install --save-dev electron-packager
- npm electron-packager . <app name>
this will create the exe

Process for committs and pushes currently (will be more robust soon):
- git pull origin master (good practice to make sure you have the updated version)
- git add <file>
- git commit -m "commit message"
- git push origin master

