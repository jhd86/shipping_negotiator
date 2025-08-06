const { app, BrowserWindow } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fetch = require("electron-fetch").default;

let pythonProcess = null;
let mainWindow;

// Determine the path to the backend script based on whether the app is packaged
const isDev = process.env.NODE_ENV !== "production";
const scriptPath = isDev
  ? path.join(__dirname, "run_app.sh")
  : path.join(process.resourcesPath, "run_app.sh");

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
    },
  });

  startPythonBackend();
  checkServerReady();
}

function startPythonBackend() {
  pythonProcess = spawn("sh", [scriptPath]);
  pythonProcess.stdout.on("data", (data) =>
    console.log(`Python stdout: ${data}`),
  );
  pythonProcess.stderr.on("data", (data) =>
    console.error(`Python stderr: ${data}`),
  );
}

function checkServerReady() {
  const url = "http://127.0.0.1:5001/health";
  let attempt = 0;
  const maxAttempts = 15; // Try for 15 seconds

  const interval = setInterval(() => {
    attempt++;
    if (attempt > maxAttempts) {
      clearInterval(interval);
      console.error("❌ Flask server failed to start in time.");
      return;
    }
    console.log(`Pinging Flask server, attempt ${attempt}...`);
    fetch(url)
      .then((res) => {
        if (res.ok) {
          console.log("✅ Flask server is ready.");
          clearInterval(interval);
          mainWindow.loadURL("http://127.0.0.1:5001");
        }
      })
      .catch(() => {}); // Ignore connection refused errors and retry
  }, 1000);
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("will-quit", () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
