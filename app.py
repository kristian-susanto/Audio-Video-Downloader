from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO
import yt_dlp
import os

app = Flask(__name__)
# Tambahkan async_mode agar lebih stabil
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def progress_hook(d):
    if d['status'] == 'downloading':
        # Membersihkan string persentase
        p = d.get('_percent_str', '0%').replace('%','')
        # Kirim data secara real-time
        socketio.emit('progress', {'percentage': p, 'status': 'downloading'})
    elif d['status'] == 'finished':
        socketio.emit('progress', {'percentage': 100, 'status': 'finished'})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    video_url = data.get('url')
    quality = data.get('quality')

    ydl_opts = {
        'format': quality,
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'progress_hooks': [progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = os.path.basename(ydl.prepare_filename(info))
            return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)