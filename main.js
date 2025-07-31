const { app, BrowserWindow } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

let pythonProcess = null;

function createWindow() {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
    },
  });

  // Start the Python backend
  startPythonBackend();

  // Load the index.html from your Flask server.
  // We add a small delay to give the Flask server time to start up.
  setTimeout(() => {
    mainWindow.loadURL("http://127.0.0.1:5001");
  }, 5000); // 5-second delay
}

function startPythonBackend() {
  // Use 'spawn' to run your Python script.
  // This is the equivalent of running 'python worker.py' and 'flask run...'
  // We use honcho via the shell script for simplicity.
  const scriptPath = path.join(__dirname, "run_app.sh"); // Or 'run_app.bat' on Windows
  pythonProcess = spawn("sh", [scriptPath]);

  pythonProcess.stdout.on("data", (data) => {
    console.log(`Python stdout: ${data}`);
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`Python stderr: ${data}`);
  });
}

app.whenReady().then(createWindow);

// Quit when all windows are closed, except on macOS.
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

// On quit, kill the python process
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
