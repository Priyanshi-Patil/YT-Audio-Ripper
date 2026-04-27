# ◈ YT Audio Ripper

A simple desktop app to download YouTube videos as **MP3 files** with embedded cover art — either a custom image you choose, or the video's own YouTube thumbnail automatically.

---

## Features

- Download any YouTube video as a 192kbps MP3
- Auto-embeds the YouTube thumbnail as cover art
- Option to use your own custom cover image (JPG, PNG, WEBP, BMP)
- Editable filename — pre-filled with the video title, change it before downloading
- Choose any output folder
- Live download progress bar
- Dark minimal UI, no browser needed

---

## Requirements

### 1. Python 3.8+
Download from https://www.python.org/downloads/
Make sure to check **"Add Python to PATH"** during installation.

### 2. Python packages (auto-installed on first run)
The app installs these automatically if missing:
- `yt-dlp`
- `mutagen`
- `Pillow`
- `requests`

You can also install them manually:
```
pip install yt-dlp mutagen Pillow requests
```

### 3. FFmpeg (required for MP3 conversion)
FFmpeg must be installed and available in your system PATH.

**Windows:**
1. Go to https://github.com/BtbN/FFmpeg-Builds/releases
2. Download `ffmpeg-master-latest-win64-gpl.zip`
3. Extract it — open the `bin` folder inside
4. Copy the path to the `bin` folder (e.g. `C:\ffmpeg\bin`)
5. Add it to PATH:
   - Search "Environment Variables" in Start
   - System Variables → Path → Edit → New → paste the path
   - Click OK everywhere
6. Open a new Command Prompt and run `ffmpeg -version` to confirm

**macOS:**
```
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```
sudo apt install ffmpeg
```

---

## How to Run

```
python main.py
```

Or double-click the `.vbs` launcher if you created one (see below).

---

## How to Use

1. **Paste** a YouTube URL into the URL field
2. Click **FETCH** — the app loads the title, channel, duration and thumbnail
3. **Edit the filename** if you want to rename it (optional)
4. **Choose a custom cover image** on the right panel (optional — skipping this uses the YouTube thumbnail automatically)
5. **Choose output folder** if you don't want it saved to Downloads
6. Click **▶ DOWNLOAD MP3** in the top-right — done!

---

## Create a Shortcut (Windows)

So you don't have to open a terminal every time:

1. Open Notepad and paste:
   ```
   CreateObject("WScript.Shell").Run "python ""C:\path\to\main.py""", 0, False
   ```
   Replace the path with wherever your `main.py` lives.

2. Save the file as `YT Audio Ripper.vbs`

3. Double-click it anytime to launch the app with no terminal window.

4. Right-click → **Send to → Desktop** to make a desktop shortcut.

---

## File Structure

```
your-folder/
├── main.py          ← the app
├── README.md        ← this file
└── YT Audio Ripper.vbs  ← optional launcher shortcut
```

---

## Notes

- Downloaded files are saved as `.mp3`
- Cover art is embedded directly into the MP3 ID3 tags — visible in Windows Explorer, iTunes, VLC, Spotify etc.
- The app strips illegal characters from filenames automatically
- Only one video can be downloaded at a time

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ffmpeg not found` | Make sure ffmpeg is installed and its `bin` folder is in PATH. Restart terminal after adding to PATH. |
| `No module named yt_dlp` | Run `pip install yt-dlp` manually |
| App window doesn't open | Make sure you're running Python 3.8+ with tkinter (`python --version`) |
| Download fails | The video may be age-restricted, private, or region-locked |
| Cover not showing | Some players cache metadata — try re-opening the file in your music player |
