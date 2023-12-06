require('dotenv').config();
require('dotenv').config({ path: '.env.base' });
const{  app, BrowserWindow } = require('electron');

require('electron-reload')(__dirname);

function createWindow () {
    const win = new BrowserWindow({
        width: 768, 
        height: 560,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false // Be cautious with this setting for security reasons
        }
    });

    win.loadFile('src/index.html');
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if(process.platform !== 'darwin') app.quit();
})
