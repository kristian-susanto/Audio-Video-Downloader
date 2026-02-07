from flask import Flask, render_template, request, send_file, after_this_request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import yt_dlp
import re
import time
import os

app = Flask(__name__)

# Folder tempat menyimpan hasil download sementara
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def sanitize_filename(filename):
    """Menghapus karakter yang tidak diperbolehkan dalam nama file."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL kosong'}), 400
    try:
        ydl_opts = {
            'quiet': True, 
            'noplaylist': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'title': info.get('title', 'Video'),
                'thumbnail': info.get('thumbnail'),
                'description': info.get('description', ''),
                'platform': info.get('extractor_key').lower(),
                'video_id': info.get('id')
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    
    if not url:
        return "URL tidak boleh kosong!", 400

    try:
        # 1. Ambil info terlebih dahulu untuk menentukan nama file dari caption
        ydl_info_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            platform = info.get('extractor_key', '').lower()
            video_id = info.get('id')
            
            # LOGIKA PENAMAAN FILE:
            # Jika Instagram, prioritaskan 'description' (caption) daripada 'title'
            if 'instagram' in platform:
                raw_title = info.get('description') or info.get('title')
            else:
                raw_title = info.get('title')

            # Ganti logika pembersihan judul dengan ini:
            if raw_title:
                # 1. Hapus newline (\n) dan carriage return (\r) lalu ganti dengan spasi
                raw_title = raw_title.replace('\n', ' ').replace('\r', ' ')
                # 2. Hapus karakter terlarang lainnya
                clean_title = sanitize_filename(raw_title[:200].strip())
            else:
                clean_title = "audio_download"

        # 2. Proses Download
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, f'{video_id}.%(ext)s'),
            'quiet': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
            actual_filename = f"{video_id}.mp3"
            temp_file_path = os.path.join(DOWNLOAD_FOLDER, actual_filename)

        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception as e:
                app.logger.error(f"Error removing file: {e}")
            return response

        return send_file(
            temp_file_path, 
            as_attachment=True, 
            download_name=f"{clean_title}.mp3",
            mimetype="audio/mpeg"
        )

    except Exception as e:
        return f"Terjadi kesalahan: {str(e)}", 500

@app.route('/download_video', methods=['POST'])
def download_video():
    url = request.form.get('url')
    if not url:
        return "URL tidak boleh kosong!", 400

    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info.get('id')
            platform = info.get('extractor_key', '').lower()
            
            # Perbaikan Logika: Ambil caption untuk Instagram
            if 'instagram' in platform:
                raw_title = info.get('description') or info.get('title')
            else:
                raw_title = info.get('title')

            # Ganti logika pembersihan judul dengan ini:
            if raw_title:
                # 1. Hapus newline (\n) dan carriage return (\r) lalu ganti dengan spasi
                raw_title = raw_title.replace('\n', ' ').replace('\r', ' ')
                # 2. Hapus karakter terlarang lainnya
                clean_title = sanitize_filename(raw_title[:200].strip())
            else:
                clean_title = "video_download"

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, f'{video_id}_video.%(ext)s'),
            'quiet': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.startswith(video_id + "_video")]
            actual_filename = files[0]
            temp_file_path = os.path.join(DOWNLOAD_FOLDER, actual_filename)
            extension = os.path.splitext(actual_filename)[1]

        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception as e:
                app.logger.error(f"Error removing file: {e}")
            return response

        # Bagian yang diperbaiki (tidak ada double argument)
        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name=f"{clean_title}{extension}",
            mimetype="video/mp4"
        )

    except Exception as e:
        return f"Terjadi kesalahan: {str(e)}", 500
        
def cleanup_downloads():
    """Fungsi untuk menghapus semua file di folder downloads"""
    print("Menjalankan pembersihan rutin folder downloads...")
    folder = DOWNLOAD_FOLDER
    now = time.time()
    
    try:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            # Opsional: Hanya hapus file yang sudah berumur lebih dari 30 menit
            # agar tidak menghapus file yang sedang didownload user lain
            if os.path.isfile(file_path):
                if os.stat(file_path).st_mtime < now - 1800: # 1800 detik = 30 menit
                    os.remove(file_path)
                    print(f"File dihapus: {filename}")
    except Exception as e:
        print(f"Error saat pembersihan: {e}")

# Inisialisasi Scheduler
scheduler = BackgroundScheduler()
# Jalankan cleanup_downloads setiap 30 menit
scheduler.add_job(func=cleanup_downloads, trigger="interval", minutes=30)
scheduler.start()

if __name__ == '__main__':
    try:
        # use_reloader=False mencegah Flask restart sendiri saat file berubah
        app.run(debug=True, port=5000, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()