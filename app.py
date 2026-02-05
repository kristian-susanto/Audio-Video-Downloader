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
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # Gunakan penamaan yang lebih aman untuk platform non-youtube
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(id)s.%(ext)s'),
            'quiet': True,
            'noplaylist': True, # Pastikan tidak download satu playlist jika linknya playlist
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'audio_download')
            video_id = info.get('id')
            
            # Cari file yang dihasilkan (yt-dlp mungkin mengubah ekstensi ke mp3)
            # Kita cari file di folder downloads yang mengandung video_id dan berakhiran .mp3
            actual_filename = f"{video_id}.mp3"
            temp_file_path = os.path.join(DOWNLOAD_FOLDER, actual_filename)
            
            safe_title = sanitize_filename(video_title)

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
            download_name=f"{safe_title}.mp3",
            mimetype="audio/mpeg"
        )

    except Exception as e:
        return f"Terjadi kesalahan: {str(e)}", 500

if __name__ == '__main__':
    # Jalankan aplikasi
    app.run(debug=True, port=5000)