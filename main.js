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

const WEBSOCK_PORT = process.env.PORT || 8080;

const ajv = new Ajv()
const verifResultsSchema = JSON.parse(fs.readFileSync("src/verif-results-schema.json"))
const validateVerifResults = ajv.compile(verifResultsSchema)

const wss = new WebSocket.Server({ port: WEBSOCK_PORT })
console.log(`WebSocket server started on ws://localhost:${WEBSOCK_PORT}`)

var calibration = {}
var image_path = ""

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

function spawnAndHandleLines(binary, args, options, stdout_handler, stderr_handler, exit_handler) {
    console.log(`Starting binary ${binary} with args ${JSON.stringify(args)} and options ${JSON.stringify(options)}`);
    const thisProcess = spawn(binary, args, options);
    console.log(`Spawned process PID: ${thisProcess.pid}`);  // Log the PID of the subprocess
    const rlStdout = readline.createInterface({
        input: thisProcess.stdout,
        crlfDelay: Infinity
    });
    rlStdout.on('line', (line) => {
        stdout_handler(line);
    });
    const rlStderr = readline.createInterface({
        input: thisProcess.stderr,
        crlfDelay: Infinity
    });
    rlStderr.on('line', (line) => {
        stderr_handler(line);
    });
    thisProcess.on('close', (code) => {
        console.log(`Process with PID ${thisProcess.pid} exited with code ${code}`);  // Log when the process exits and its exit code
        exit_handler(code);
    });
}

function sendWebSockMessageToFrontend(message, client = null) {
    if (client && client.readyState === WebSocket.OPEN) {
        client.send(message); // Send to a specific client
    } else {
        wss.clients.forEach(function each(client) {
            if (client.readyState === WebSocket.OPEN) {
                client.send(message); // Broadcast to all clients
            }
        });
    }
}


function handleImageFromSerialStdoutLine(imageFromSerialStdoutLine) {
    try {
        image_path = JSON.parse(imageFromSerialStdoutLine)["image_path"]
        console.log(`image path received from image-from-serial.py: ${image_path}`)
    } catch (error) {
        console.log(`image-from-serial.py stdout: ${imageFromSerialStdoutLine}`)
        return
    }
}

function handlePredictionStdoutLine(predictionStdoutLine) {
    // TODO validate schema
    console.log(`predict.py stdout: ${predictionStdoutLine}`)
    sendWebSockMessageToFrontend(predictionStdoutLine)
}

function handleCalibrateStdoutLine(calibrateStdoutLine) {
    try {
        calibration = JSON.parse(calibrateStdoutLine)["calibration"]
        console.log("calibration received from calibrate.py")
    } catch (error) {
        console.log(`calibrate.py stdout: ${imageFromSerialStdoutLine}`)
        return
    }
}

function runPrediction() {
    spawnAndHandleLines(
        process.env.PREDICT_PYTHON_PATH,
        [process.env.PREDICT_PATH, image_path, JSON.stringify(calibration)],
        { cwd: process.env.PREDICT_CWD },
        line => handlePredictionStdoutLine(line),
        line => console.log(`predict.py stderr : ${line}`),
        (code) => console.log(`predict.py exited with code ${code}`)
    );
}

function handleIncomingWebSockMessage(encodedMessage, ws) {
    const message = JSON.parse(encodedMessage)
    console.log(message)
    if (message.type === 'run-verif') {
        sendWebSockMessageToFrontend(JSON.stringify({ "type": "status", "data": "verification running..." }), ws);
        const verif_cmd = `${process.env.VERIF_PYTHON_PATH} ${process.env.VERIF_PATH}`
        console.log(`executing \"${verif_cmd}\" ...`)
        const verifProcess = exec(verif_cmd, { cwd: process.env.VERIF_CWD })
        verifProcess.stdin.write(JSON.stringify(message.data))
        verifProcess.stdin.end()
        verifProcess.stdout.on('data', (data) => {
            console.log("verification stdout received:")
            console.log(JSON.stringify(data))
            if (validateVerifResults(JSON.parse(data))) {
                sendWebSockMessageToFrontend(JSON.stringify({ "type": "verif-output", "data": data }), ws);
            } else {
                sendWebSockMessageToFrontend(JSON.stringify({ "type": "status", "data": "ERROR" }), ws);
            }            
        })
        verifProcess.stderr.on('data', (data) => {
            console.log(data)
        })
        verifProcess.on('close', (code) => {
            if (code != 0) { // return code 2 means expressions not equal
                sendWebSockMessageToFrontend(JSON.stringify({ "type": "status", "data": "ERROR" }), ws);
            }
            console.log(`verification process exited with code ${code}`)
        })
    } else if (message.type == 'run-prediction') {
        if (calibration == {}){
            sendWebSockMessageToFrontend(JSON.stringify({ "type": "status", "data": "ERROR: you must calibrate before you can predict!" }), ws);
        }
        runPrediction()
    } else if (message.type == 'take-picture') {
        // spawnAndHandleLines(
        //     process.env.IMAGE_FROM_SERIAL_PYTHON_PATH,
        //     [process.env.IMAGE_FROM_SERIAL_PATH, process.env.COM_PORT, process.env.BAUD_RATE],
        //     {}, // Options
        //     line => handleImageFromSerialStdoutLine(line),
        //     line => console.log(`image-from-serial.py stderr : ${line}`),
        //     (code) => console.log(`image-from-serial.py exited with code ${code}`)
        // );
        const testImagePath = '../testimg.jpeg';
        handleImageFromSerialStdoutLine(JSON.stringify({ "image_path": testImagePath }));
    } else if (message.type == 'calibrate') {
        if (image_path == {}){
            sendWebSockMessageToFrontend(JSON.stringify({ "type": "status", "data": "ERROR: you must take a picture before you can calibrate!" }), ws);
        }
        spawnAndHandleLines(
            process.env.CALIBRATE_PYTHON_PATH,
            [process.env.CALIBRATE_PATH, image_path],
            { cwd: process.env.CALIBRATE_CWD },
            line => handleCalibrateStdoutLine(line),
            line => console.log(`calibrate.py stderr : ${line}`),
            (code) => console.log(`calibrate.py exited with code ${code}`)
        );
    }else {
        console.log(`ERROR: unrecognized message of type \"${message.type}\"\n${message.data}`)
    }
}


function main() {
    wss.on('connection', function connection(ws) {
        ws.on('message', function incoming(message) {
            handleIncomingWebSockMessage(message, ws)
        })
    })
    createWindow()
}

app.whenReady().then(main)

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit()
})
