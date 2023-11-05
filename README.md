getting started:
- make sure you have npm: https://nodejs.org/en
- clone the repo to your local: git clone https://github.com/sdp2024team10/ElectronApp
- npm install

to run the app:
npm start

plan:
- push to develop branch for any non-complete changes
- prod brannch is the current running state of the app

build the electron app (only will do at the very end):
- npm install --save-dev electron-packager
- npm electron-packager . <app name>
this will create the exe