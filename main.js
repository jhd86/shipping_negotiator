const { app, BrowserWindow } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fetch = require("electron-fetch").default; // Use electron-fetch for making network requests
const FLASK_SERVER_URL = "http://127.0.0.1:5001";

let pythonProcess = null;
let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
    },
  });

  startPythonBackend();

  // Start checking for the server to be ready
  checkServerReady();
}

function startPythonBackend() {
  const scriptPath = path.join(__dirname, "run_app.sh"); // Or 'run_app.bat' on Windows
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
  const maxAttempts = 10;

  const interval = setInterval(() => {
    attempt++;
    console.log(`Pinging Flask server, attempt ${attempt}...`);

    fetch(url)
      .then((res) => {
        if (res.ok) {
          console.log("✅ Flask server is ready.");
          clearInterval(interval);
          // Once the server is ready, load the main URL
          mainWindow.loadURL(FLASK_SERVER_URL);
        }
      })
      .catch(() => {
        // This catch block will be hit if the connection is refused
        if (attempt >= maxAttempts) {
          clearInterval(interval);
          console.error("❌ Flask server failed to start in time.");
          // You could show an error message to the user here
        }
      });
  }, 1000); // Check every 1 second
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
