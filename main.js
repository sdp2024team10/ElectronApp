//const path = require('path');
require("dotenv").config();
require("dotenv").config({ path: ".env-base" });
const { app, BrowserWindow } = require("electron");
const WebSocket = require("ws");
const fs = require("fs");
const readline = require("readline");
const { spawn } = require("child_process");
const Ajv = require("ajv");

const WEBSOCK_PORT = process.env.PORT || 8080;

const ajv = new Ajv();
const verifResultsSchema = JSON.parse(
  fs.readFileSync("app/verif-results-schema.json")
);
const validateVerifResults = ajv.compile(verifResultsSchema);

const wss = new WebSocket.Server({ port: WEBSOCK_PORT });
console.log(`WebSocket server started on ws://localhost:${WEBSOCK_PORT}`);

var activeWebsockConnections = new Set();

var runningProcesses = {};

var predictionStartTime = null;

var calibration = {};
var image_path = "";
var stepsCompleted = {
  "take-picture": false,
  calibration: false,
  prediction: false,
  verification: false,
};

function resetImageAndProgress() {
  image_path = "";
  stepsCompleted = {
    "take-picture": false,
    calibration: false,
    prediction: false,
    verification: false,
  };
}

function log(...args) {
  const now = new Date();
  console.log(now.toISOString(), ...args);
}

function spawnAndHandleLines(
  name,
  binary,
  args,
  options,
  stdout_handler,
  stderr_handler,
  exit_handler,
  stdin_str = ""
) {
  log(
    `Starting binary "${binary}" with args ${JSON.stringify(
      args
    )} and options ${JSON.stringify(options)}`
  );
  if (stdin_str != "") {
    log(`and stdin string "${stdin_str}"`);
  }
  const thisProcess = spawn(binary, args, options);
  log(`Spawned process PID: ${thisProcess.pid}`);
  if (!runningProcesses[name]) {
    runningProcesses[name] = [];
  }
  runningProcesses[name].push(thisProcess.pid);
  if (stdin_str != "") {
    thisProcess.stdin.write(stdin_str);
    thisProcess.stdin.end();
  }
  const rlStdout = readline.createInterface({
    input: thisProcess.stdout,
    crlfDelay: Infinity,
  });
  rlStdout.on("line", (line) => {
    stdout_handler(line);
  });
  const rlStderr = readline.createInterface({
    input: thisProcess.stderr,
    crlfDelay: Infinity,
  });
  rlStderr.on("line", (line) => {
    stderr_handler(line);
  });
  thisProcess.on("close", (code) => {
    console.log(`PID ${thisProcess.pid} exited with code ${code}`);
    runningProcesses[name] = runningProcesses[name].filter(
      (x) => x !== thisProcess.pid
    );
    exit_handler(code, thisProcess.pid);
  });
}

function handleExitCode(exit_code, pid, name, progressElementId) {
  log(`${name} (PID ${pid}) exited with code ${exit_code}`);
  if (exit_code == 0) {
    stepsCompleted[name] = true;
    broadcastProgress(progressElementId, "completed");
  } else {
    broadcastProgress(progressElementId, "failed");
  }
}

function broadcastWebSockMessage(message) {
  activeWebsockConnections.forEach(function each(ws) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(message);
    }
  });
}

function broadcastStatus(message) {
  broadcastWebSockMessage(JSON.stringify({ type: "status", data: message }));
}

function broadcastProgress(elementId, newProgress) {
  broadcastWebSockMessage(
    JSON.stringify({
      type: "progress",
      elementId: elementId,
      newProgress: newProgress,
    })
  );
}

function handleImageFromSerialStdoutLine(imageFromSerialStdoutLine) {
  log(`image-from-serial.py stdout: ${imageFromSerialStdoutLine}`);
  try {
    image_path = JSON.parse(imageFromSerialStdoutLine)["image_path"];
    log(`image path received from image-from-serial.py: ${image_path}`);
  } catch (error) {
    log(`image-from-serial.py stdout line is not json.`);
    return;
  }
}

function handleCalibrateStdoutLine(calibrateStdoutLine) {
  log(`calibrate.py stdout: ${calibrateStdoutLine}`);
  try {
    found_calibration = JSON.parse(calibrateStdoutLine)["calibration"];
  } catch (error) {
    log(`calibrate.py stdout line is not json.`);
    return;
  }
  if (!found_calibration) {
    log("JSON.parse(calibration stdout line) returned falsey!");
    return;
  }
  calibration = found_calibration;
  log("calibration received from calibrate.py");
}

function handlePredictionStdoutLine(predictionStdoutLine) {
  // TODO validate schema
  log(`predict.py stdout: ${predictionStdoutLine}`);
  broadcastWebSockMessage(predictionStdoutLine);
}

function handleVerifStdoutLine(data) {
  log(`verification stdout: ${JSON.stringify(data)}`);
  data_object = null;
  try {
    data_object = JSON.parse(data);
  } catch {
    log("verification returned malformed input!");
    broadcastProgress("verification-progress", "failed");
    return;
  }
  if (validateVerifResults(data_object)) {
    broadcastWebSockMessage(
      JSON.stringify({ type: "verif-output", data: data })
    );
  } else {
    log("verification output failed to validate schema!");
    broadcastProgress("verification-progress", "failed");
  }
}

function handleTakePictureRequest() {
  name = "take-picture";
  alreadyRunningPids = runningProcesses[name];
  if (alreadyRunningPids && alreadyRunningPids.length > 0) {
    log(`"${name}" (PID ${alreadyRunningPids}) is already running!`);
    broadcastStatus(`${name} is already running!`);
    return;
  }
  broadcastProgress("take-picture-progress", "started");
  spawnAndHandleLines(
    name,
    process.env.IMAGE_FROM_SERIAL_PYTHON_PATH,
    [
      process.env.IMAGE_FROM_SERIAL_PATH,
      process.env.COM_PORT,
      process.env.BAUD_RATE,
    ],
    {}, // Options
    (line) => handleImageFromSerialStdoutLine(line),
    (line) => log(`image-from-serial.py stderr : ${line}`),
    (code, pid) =>
      handleExitCode(
        code,
        pid,
        name,
        (progressElementId = "take-picture-progress")
      )
  );
  // const testImagePath = "../testimg.jpeg";
  // handleImageFromSerialStdoutLine(
  //   JSON.stringify({ image_path: testImagePath })
  // );
  // broadcastProgress("take-picture-progress", "completed");
  // stepsCompleted["take-picture"] = true;
}

function handlePredictionExitCode(code, pid) {
  const predictionTimeS = (performance.now() - predictionStartTime) / 1000;
  log(`predict.py time elapsed: ${predictionTimeS} seconds`);
  handleExitCode(
    code,
    pid,
    "prediction",
    (progressElementId = "prediction-progress")
  );
}

function handleCalibrationRequest() {
  if (!stepsCompleted["take-picture"]) {
    log("ERROR: you must take a picture before you can calibrate!");
    broadcastStatus("ERROR: you must take a picture before you can calibrate!");
    return;
  }
  name = "calibration";
  alreadyRunningPids = runningProcesses[name];
  if (alreadyRunningPids && alreadyRunningPids.length > 0) {
    log(`"${name}" (PID ${alreadyRunningPids}) is already running!`);
    broadcastStatus(`${name} is already running!`);
    return;
  }
  broadcastProgress("calibration-progress", "started");
  spawnAndHandleLines(
    name,
    process.env.CALIBRATE_PYTHON_PATH,
    [process.env.CALIBRATE_PATH, image_path, JSON.stringify(calibration)],
    { cwd: process.env.CALIBRATE_CWD },
    (line) => handleCalibrateStdoutLine(line),
    (line) => log(`calibrate.py stderr: ${line}`),
    (code, pid) =>
      handleExitCode(
        code,
        pid,
        name,
        (progressElementId = "calibration-progress")
      )
  );
}

function handlePredictionRequest() {
  if (!stepsCompleted["calibration"]) {
    log("ERROR: you must calibrate before you can run prediction!");
    broadcastStatus("ERROR: you must calibrate before you can run prediction!");
    return;
  }
  name = "prediction";
  alreadyRunningPids = runningProcesses[name];
  if (alreadyRunningPids && alreadyRunningPids.length > 0) {
    log(`"${name}" (PID ${alreadyRunningPids}) is already running!`);
    broadcastStatus(`${name} is already running!`);
    return;
  }
  predictionStartTime = performance.now();
  broadcastProgress("prediction-progress", "started");
  spawnAndHandleLines(
    name,
    process.env.PREDICT_PYTHON_PATH,
    [process.env.PREDICT_PATH, image_path, JSON.stringify(calibration)],
    { cwd: process.env.PREDICT_CWD },
    (line) => handlePredictionStdoutLine(line),
    (line) => log(`predict.py stderr : ${line}`),
    (code, pid) => handlePredictionExitCode(code, pid)
  );
}

function handleVerificationRequest(message) {
  name = "verification";
  alreadyRunningPids = runningProcesses[name];
  if (alreadyRunningPids && alreadyRunningPids.length > 0) {
    log(`"${name}" (PID ${alreadyRunningPids}) is already running!`);
    broadcastStatus(`${name} is already running!`);
    return;
  }
  broadcastProgress("verficiation-progress", "started");
  spawnAndHandleLines(
    name,
    process.env.VERIF_PYTHON_PATH,
    [process.env.VERIF_PATH],
    { cwd: process.env.VERIF_CWD },
    (line) => handleVerifStdoutLine(line),
    (line) => log(`verification stderr : ${line}`),
    (code, pid) =>
      handleExitCode(
        code,
        pid,
        name,
        (progressElementId = "verification-progress")
      ),
    (stdin_str = JSON.stringify(message))
  );
}

function createWindow() {
  const win = new BrowserWindow({
    width: 768,
    height: 560,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false, // Be cautious with this setting for security reasons
    },
  });
  win.loadFile("app/index.html");
}

function main() {
  wss.on("connection", function connection(ws) {
    activeWebsockConnections.add(ws);
    ws.on("message", function incoming(message) {
      log(message);
      try {
        const messageObject = JSON.parse(message);
        try {
          type = messageObject.type;
        } catch {
          log(
            `received json websock message with to "type" attribute: ${message}`
          );
          return;
        }
        switch (type) {
          case "run-verif":
            handleVerificationRequest(messageObject.data);
            break;
          case "run-prediction":
            handlePredictionRequest();
            break;
          case "take-picture":
            handleTakePictureRequest();
            break;
          case "calibrate":
            handleCalibrationRequest();
            break;
          case "reload":
            resetImageAndProgress();
            break;
          default:
            log(
              `received json websock message unknown "type" attribute: ${message}`
            );
        }
      } catch (e) {
        if (e instanceof SyntaxError) {
          log(`received non-json websock message: ${message}`);
          return;
        } else {
          throw e;
        }
      }
    });
    ws.on("close", () => {
      activeWebsockConnections.delete(ws);
    });
  });
  createWindow();
}

app.whenReady().then(main);

app.on("window-all-closed", () => {
  app.quit();
});
