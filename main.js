//const path = require('path');
require('dotenv').config()
require('dotenv').config({ path: '.env-base' })
const { app, BrowserWindow } = require('electron')
const WebSocket = require('ws')
const fs = require('fs')
const readline = require('readline');
const { exec } = require('child_process')
const { spawn } = require('child_process')
const Ajv = require('ajv')

const WEBSOCK_PORT = 8080

const ajv = new Ajv()
const verifResultsSchema = JSON.parse(fs.readFileSync("src/verif-results-schema.json"))
validateVerifResults = ajv.compile(verifResultsSchema)

const wss = new WebSocket.Server({ port: WEBSOCK_PORT })
console.log(`WebSocket server started on ws://localhost:${WEBSOCK_PORT}`)

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

function handleIncomingWebSockMessage(encodedMessage, ws) {
    const message = JSON.parse(encodedMessage)
    console.log(message)
    if (message.type === 'run-verif') {
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

function sendWebSockMessageToFrontend(message) {
    // and also any other websocket listeners on this port
    wss.clients.forEach(function each(client) {
      if (client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  }

function spawnAndHandleLines(binary, args, options, stdout_handler, stderr_handler, exit_handler) {
    console.log(`starting binary ${binary} with args ${JSON.stringify(args)} and options ${JSON.stringify(options)}`)
    const thisProcess = spawn(binary, args, options);
    const rlStdout = readline.createInterface({
        input: thisProcess.stdout,
        crlfDelay: Infinity
    });
    rlStdout.on('line', (line) => {
        stdout_handler(line)
    });
    const rlStderr = readline.createInterface({
        input: thisProcess.stderr,
        crlfDelay: Infinity
    });
    rlStderr.on('line', (line) => {
        stderr_handler(line)
    });
    thisProcess.on('close', (code) => {
        exit_handler(code)
    });
}

function handlePredictionStdoutLine(predictionStdoutLine) {
    // TODO validate schema
    console.log(`predict.py stdout: ${predictionStdoutLine}`)
    sendWebSockMessageToFrontend(predictionStdoutLine)
}

function runPrediction(image_path) {
    spawnAndHandleLines(
        process.env.PREDICT_PYTHON_PATH,
        [process.env.PREDICT_PATH, image_path],
        { cwd: process.env.PREDICT_CWD },
        line => handlePredictionStdoutLine(line),
        line => console.log(`predict.py stderr : ${line}`),
        (code) => console.log(`predict.py exited with code ${code}`)
    );
}

function handleImagesFromSerialStdoutLine(imagesFromSerialStdoutLine) {
    // if the line is an image path, then run a prediction
    var image_path = null
    try {
        image_path = JSON.parse(imagesFromSerialStdoutLine)["image_path"]
    } catch (error) {
        console.log(`images-from-serial.py stdout: ${imagesFromSerialStdoutLine}`)
        return
    }
    runPrediction(image_path)
}


function main() {
    wss.on('connection', function connection(ws) {
        ws.on('message', function incoming(message) {
            handleIncomingWebSockMessage(message, ws)
        })
    })
    console.log("websocket message handlers initialized")
    spawnAndHandleLines(
        process.env.IMAGE_FROM_SERIAL_PYTHON_PATH,
        [process.env.IMAGE_FROM_SERIAL_PATH, process.env.COM_PORT, process.env.BAUD_RATE],
        {}, // Options
        line => handleImagesFromSerialStdoutLine(line),
        line => console.log(`images-from-serial.py stderr : ${line}`),
        (code) => {
            console.log(`images-from-serial.py exited with code ${code}`)
            if (process.platform !== 'darwin') app.quit()
        }
    );
    createWindow()
}

app.whenReady().then(main)

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit()
})
