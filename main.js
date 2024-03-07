const DEBUG = true
//const path = require('path');
require('dotenv').config()
require('dotenv').config({ path: '.env-base' })
if (DEBUG) { require('electron-reload')(__dirname) }
const { app, BrowserWindow } = require('electron')
const WebSocket = require('ws')
const fs = require('fs')
const { exec } = require('child_process')
const { spawn } = require('child_process')
const Ajv = require('ajv')

const WEBSOCK_PORT=8080

const ajv = new Ajv()
var validateVerifResults = null // defined by initJsonSchemaValidators()

function createWindow() {
    const win = new BrowserWindow({
        width: 768,
        height: 560,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false // Be cautious with this setting for security reasons
        }
    })
    win.loadFile('src/index.html')
}

function initJsonSchemaValidators() {
    const verifResultsSchema = JSON.parse(fs.readFileSync("src/verif-results-schema.json"))
    validateVerifResults = ajv.compile(verifResultsSchema)
}

function handleIncomingWebSockMessage(encodedMessage, ws) {
    const message = JSON.parse(encodedMessage)
    console.log(message)

    if (message.type == "new-camera-jpeg-path") {
        console.log("image path received!")
        console.log(message.data)
    }
    else if (message.type === 'run-prediction') { // if run predicition button is clicked
        const pythonExecutablePath = '/Users/jordanandrade/opt/anaconda3/envs/bttr/bin/python'
        const scriptPath = '/Users/jordanandrade/electronapp/BTTR/example/prediction.py'
        const ckptPath = '/Users/jordanandrade/Desktop/BTTR/lightning_logs/version_13270759/checkpoints/epoch=245-step=92495-val_ExpRate=0.5536.ckpt';
        const imgPath = '/Users/jordanandrade/electronapp/BTTR/example/18_em_1.bmp';
        const command = `${pythonExecutablePath} ${scriptPath} --ckpt "${ckptPath}" --img "${imgPath}"`;

        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.error(`Prediction script error: ${error}`);
                ws.send(JSON.stringify({ "type": "prediction-status", "data": "ERROR" }))
                return;
            }
            if (stderr) {
                console.error(`Prediction script stderr: ${stderr}`)
            }

            const lines = stdout.trim().split('\n');
            const predictionOutput = lines[lines.length - 1].trim(); // takes the last line of prediction output
            console.log(`Prediction script output: ${predictionOutput}`)

            ws.send(JSON.stringify({
                "type": "expressions", "data": [ //TODO figure out why ten expression must be sent
                    predictionOutput,
                    "x^3",
                    "x^2",
                    "x^2",
                    "x^2",
                    "x^2",
                    "x^2",
                    "x^2",
                    "x^2",
                    "x^2",
                ]
            }))
        })

    }
    else if (message.type === 'run-verif') {
        ws.send(JSON.stringify({ "type": "verif-status", "data": "verification running..." }))
        const verif_cmd = `${process.env.VERIF_PYTHON_PATH} ${process.env.VERIF_PATH}`
        console.log(`executing \"${verif_cmd}\" ...`)
        const verifProcess = exec(verif_cmd, { cwd: process.env.VERIF_CWD })
        verifProcess.stdin.write(JSON.stringify(message.data))
        verifProcess.stdin.end()
        verifProcess.stdout.on('data', (data) => {
            console.log("verification stdout received:")
            console.log(JSON.stringify(data))
            if (validateVerifResults(JSON.parse(data))) {
                ws.send(JSON.stringify({ "type": "verif-output", "data": data }))
            } else {
                console.log("verification output does not comply to schema!")
                ws.send(JSON.stringify({ "type": "verif-status", "data": "ERROR" }))
            }
        })
        verifProcess.stderr.on('data', (data) => {
            console.log(data)
        })
        verifProcess.on('close', (code) => {
            if (code != 0) { // return code 2 means expressions not equal
                ws.send(JSON.stringify({ "type": "verif-status", "data": "ERROR" }))
            }
            console.log(`verification process exited with code ${code}`)
        })
    } else {
        console.log(`ERROR: unrecognized message of type \"${message.type}\"\n${message.data}`)
    }
}

function main() {
    initJsonSchemaValidators()
    const wss = new WebSocket.Server({ port: WEBSOCK_PORT })
    wss.on('connection', function connection(ws) {
        ws.on('message', function incoming(message) {
            handleIncomingWebSockMessage(message, ws)
        })
    })
    console.log('WebSocket server started on ws://localhost:8080')

    const image_from_serial_process = spawn(
        process.env.IMAGE_FROM_SERIAL_PYTHON_PATH,
        [process.env.IMAGE_FROM_SERIAL_PATH, process.env.COM_PORT, process.env.BAUD_RATE, WEBSOCK_PORT]
    );

    image_from_serial_process.stdout.on('data', (data) => {
        console.log(`images-from-serial.py stdout: ${data}`);
    });

    image_from_serial_process.stderr.on('data', (data) => {
        console.error(`images-from-serial.py stderr: ${data}`);
    });

    image_from_serial_process.on('close', (code) => {
        console.log(`images-from-serial.py exited with code ${code}. quitting...`);
        if (process.platform !== 'darwin') app.quit()
    });
    createWindow()
}

app.whenReady().then(main)

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit()
})
