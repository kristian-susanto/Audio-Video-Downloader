from flask import Flask, render_template, request, send_file, after_this_request, jsonify
import yt_dlp
import os
import re

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

            # Bersihkan teks (ambil 50 karakter pertama agar tidak terlalu panjang)
            # dan hapus karakter terlarang
            clean_title = sanitize_filename(raw_title[:50].strip()) if raw_title else "audio_download"

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

if __name__ == '__main__':
    # Jalankan aplikasi
    app.run(debug=True, port=5000)