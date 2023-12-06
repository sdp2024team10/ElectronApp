const DEBUG = true

require('dotenv').config()
require('dotenv').config({ path: '.env-base' })
if (DEBUG) { require('electron-reload')(__dirname) }
const{  app, BrowserWindow } = require('electron')
const WebSocket = require('ws')
const { exec } = require('child_process')

function createWindow () {
    const win = new BrowserWindow({
        width: 768, 
        height: 560,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false // Be cautious with this setting for security reasons
        }
    })
    win.loadFile('src/index.html')
    if (DEBUG) { win.webContents.openDevTools() }
}

function handleIncomingWebSockMessage(encodedMessage, ws){
    // TODO juggle electron websocket and machine learning websocket
    const message = JSON.parse(encodedMessage)
    console.log(message)
    if (message.type === 'run-verif') {
        ws.send(JSON.stringify({ "type": "verif-output", "data": "verification running..." }))
        const verificationExePath = process.env.VERIFICATION_EXE_PATH
        console.log(`executing \"${verificationExePath}\" ...`)
        const verifProcess = exec(verificationExePath)
        verifProcess.stdin.write(JSON.stringify(message.data))
        verifProcess.stdin.end()
        verifProcess.stdout.on('data', (data) => {
            console.log(data)
            ws.send(JSON.stringify({ "type": "verif-output", "data": data }))
        })
        verifProcess.stderr.on('data', (data) => {
            console.log(data)
        })
        verifProcess.on('close', (code) => {
            if (code != 0){ // return code 2 means expressions not equal
                ws.send(JSON.stringify({ "type": "verif-output", "data": "ERROR" }))
            }
            console.log(`verification process exited with code ${code}`)
        })
    } else {
        console.log(`ERROR: unrecognized message of type \"${message.type}\"\n${message.data}`)
    }
}

function main(){
    const wss = new WebSocket.Server({ port: 8080 })
    wss.on('connection', function connection(ws) {
        ws.on('message', function incoming(message) {
            handleIncomingWebSockMessage(message, ws)
        })
    })
    console.log('WebSocket server started on ws://localhost:8080')
    createWindow()
}

app.whenReady().then(main)

app.on('window-all-closed', () => {
    if(process.platform !== 'darwin') app.quit()
})
