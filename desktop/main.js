// Electron main process for the desktop wrapper.
//
// Goal: hard to exit — or fiddle with the window — by accident (this runs
// on a toddler's machine), easy to exit on purpose. So: always fullscreen
// (no title bar, no window management a toddler could stumble into), no
// menu bar (no stray Ctrl/Cmd+Q accelerator), and quitting always goes
// through a confirm dialog — whether triggered by Alt+F4, the window
// manager's own close action, or the Ctrl+Escape shortcut below (Alt+Tab
// is untouched; it's handled entirely by the window manager). A few keys a
// mashing toddler could hit by chance (reload, devtools, un-fullscreening)
// are swallowed.
const { app, BrowserWindow, Menu, dialog } = require("electron");
const path = require("path");

Menu.setApplicationMenu(null);

// The flatpak sandbox's GPU access is unreliable across host driver/Mesa
// combinations (seen: GPU process failing to init, leaving a blank window).
// This UI is flat-colored divs and text — software rendering costs nothing
// visible — so trade hardware acceleration for reliability everywhere.
app.disableHardwareAcceleration();

let win;
let allowClose = false;

function createWindow() {
    win = new BrowserWindow({
        fullscreen: true,
        show: false,
        autoHideMenuBar: true,
        backgroundColor: "#FFE7B3",
        icon: path.join(__dirname, "icon.png"),
        webPreferences: {
            devTools: false,
        },
    });

    win.once("ready-to-show", () => {
        win.show();
    });

    // Nothing should be able to knock the app out of fullscreen short of
    // actually quitting.
    win.on("leave-full-screen", () => {
        if (!allowClose) win.setFullScreen(true);
    });

    win.on("close", (event) => {
        if (allowClose) return;
        event.preventDefault();
        const choice = dialog.showMessageBoxSync(win, {
            type: "question",
            buttons: ["Cancel", "Quit"],
            defaultId: 0,
            cancelId: 0,
            title: "Quit ABC App?",
            message: "Quit ABC App?",
        });
        if (choice === 1) {
            allowClose = true;
            win.close();
        }
    });

    win.webContents.on("before-input-event", (event, input) => {
        if (input.type !== "keyDown") return;

        // KeyboardEvent.repeat is unreliable in the renderer on this
        // Electron/Linux build (always undefined, even mid-repeat) — but
        // input.isAutoRepeat here in the main process is correct, so swallow
        // OS auto-repeat before it ever reaches the page. Without this, a
        // held key would replay the letter sound ~30 times/sec.
        if (input.isAutoRepeat) {
            event.preventDefault();
            return;
        }

        const key = input.key.toLowerCase();
        const mod = input.control || input.meta;

        // Deliberately awkward chord, unlikely for a toddler to hit by
        // mashing keys — an experienced user's quit shortcut. Goes through
        // the same close handler (and its confirm dialog) as Alt+F4 / the
        // window manager's own close action, not a bypass around it.
        if (mod && key === "escape") {
            win.close();
            return;
        }

        const blocked =
            (mod && ["r", "w"].includes(key)) ||
            (mod && input.shift && key === "i") ||
            key === "f5" ||
            key === "f11" ||
            key === "f12";
        if (blocked) event.preventDefault();
    });

    win.loadFile(path.join(__dirname, "app", "index.html"));
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => app.quit());
