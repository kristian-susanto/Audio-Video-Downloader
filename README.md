# 📥 Multi Downloader (YouTube, Instagram, & More)

An efficient and responsive Flask-based web application that allows users to download audio (MP3) and video (MP4) from various social media platforms. Powered by `yt-dlp`, this tool features a clean UI with dark mode support and automated file cleanup.

## ✨ Key Features

- **Platform Support:** Download content from YouTube, Instagram, and other major platforms supported by yt-dlp.
- **High-Quality Downloads**: Support for **MP3 (192kbps)** audio extraction and **MP4** video downloads with the best available quality merged automatically.
- **Smart Metadata:** Automatically extracts video titles or Instagram captions to use as filenames.
- **Live Preview:** Fetches thumbnails and titles/descriptions before you start the download.
- **Dark Mode Support:** Toggle between light and dark themes with persistent settings.
- **Auto-Cleanup:** A background scheduler automatically deletes temporary files every 30 minutes to save server space.
- **Responsive Design:** Fully optimized for Desktop, Tablet, and Mobile devices.

## 📁 Folder Structure

```
Audio-Video-Downloader/
│
├── app.py              # Flask backend and downloader logic
├── downloads/          # Temporary storage for processed files
├── templates/
│ └── index.html        # Frontend (HTML/CSS/JS)
└── requirements.txt    # Python dependencies
```

## 🚀 How to Run

### 1. Prerequisites

Ensure you have **FFmpeg** installed on your system, as it is required for audio conversion and video merging.

- **Windows**: Install via [FFmpeg](https://www.ffmpeg.org/), [Gyan Doshi](https://www.gyan.dev/ffmpeg/builds/), [Chocolatey](https://chocolatey.org/), or download the builds.
- **Mac**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

### 2. Clone Repository

```bash
git clone https://github.com/kristian-susanto/Audio-Video-Downloader.git
cd Audio-Video-Downloader
```

### 3. Dependency Installation

It is recommended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate    # Mac/Linux
venv\Scripts\activate       # Windows
```

Once the virtual environment is active, install all dependencies in one of the following ways:
Using the requirements.txt file:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install flask yt-dlp apscheduler
```

### 4. Run the Application

```bash
python app.py
```

The application will start in debug mode at `http://127.0.0.1:5000`.

## 🛠️ Configuration Note

- **Background Cleanup**: The `BackgroundScheduler` is set to run `cleanup_downloads` every 30 minutes.
- **File Naming**: Filenames are sanitized to remove special characters that are not allowed by operating systems.
- **Instagram Preview**: Uses `images.weserv.nl` as a proxy to display Instagram thumbnails, bypassing common hotlinking restrictions.
