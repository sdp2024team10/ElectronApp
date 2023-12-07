const DEBUG = true

require('dotenv').config()
require('dotenv').config({ path: '.env-base' })
if (DEBUG) { require('electron-reload')(__dirname) }
const{  app, BrowserWindow } = require('electron')
const WebSocket = require('ws')
const fs = require('fs')
const { exec } = require('child_process')
const Ajv = require('ajv')

const ajv = new Ajv()
var validateVerifResults = null // defined by initJsonSchemaValidators()

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
    // win.loadFile('src/chart-test.html')
}

function initJsonSchemaValidators(){
    const verifResultsSchema = JSON.parse(fs.readFileSync("src/verif-results-schema.json"))
    validateVerifResults = ajv.compile(verifResultsSchema)
}

function handleIncomingWebSockMessage(encodedMessage, ws){
    // TODO juggle electron websocket and machine learning websocket
    const message = JSON.parse(encodedMessage)
    console.log(message)
    if (message.type === 'run-verif') {
        ws.send(JSON.stringify({ "type": "verif-status", "data": "verification running..." }))
        const verificationExePath = process.env.VERIFICATION_EXE_PATH
        console.log(`executing \"${verificationExePath}\" ...`)
        const verifProcess = exec(verificationExePath)
        verifProcess.stdin.write(JSON.stringify(message.data))
        verifProcess.stdin.end()
        verifProcess.stdout.on('data', (data) => {
            console.log("verification stdout received:")
            console.log(JSON.stringify(data))
            if(validateVerifResults(JSON.parse(data))){
                ws.send(JSON.stringify({ "type": "verif-output", "data": data }))
            }else{
                console.log("verification output does not comply to schema!")
                ws.send(JSON.stringify({ "type": "verif-status", "data": "ERROR" }))
            }
        })
        verifProcess.stderr.on('data', (data) => {
            console.log(data)
        })
        verifProcess.on('close', (code) => {
            if (code != 0){ // return code 2 means expressions not equal
                ws.send(JSON.stringify({ "type": "verif-status", "data": "ERROR" }))
            }
            console.log(`verification process exited with code ${code}`)
        })
    } else {
        console.log(`ERROR: unrecognized message of type \"${message.type}\"\n${message.data}`)
    }
}

function main(){
    initJsonSchemaValidators()
    const wss = new WebSocket.Server({ port: 8080 })
    wss.on('connection', function connection(ws) {
        ws.send(JSON.stringify({ "type": "expressions", "data": [
            "x^2",
            "x^2",
            "x^2",
            "x^2",
            "x^2",
            "x^2",
            "x^2",
            "x^2",
            "x^2",
            "x^2",
        ]}))
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
