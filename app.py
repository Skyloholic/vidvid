from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import tempfile
import threading
import time
from threading import Semaphore

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# =========================
# CONFIG
# =========================
BASE_TEMP_DIR = os.path.join(tempfile.gettempdir(), "video_downloader_temp")
os.makedirs(BASE_TEMP_DIR, exist_ok=True)

MAX_CONCURRENT_DOWNLOADS = 2          # queue limit
MAX_FILE_SIZE_MB = 200                # max file size
MAX_DURATION_SECONDS = 15 * 60        # 15 minutes

download_semaphore = Semaphore(MAX_CONCURRENT_DOWNLOADS)

# Rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["20 per hour"]
)

# =========================
# HELPERS
# =========================
def cleanup_file(path, delay=20):
    def delete_later():
        time.sleep(delay)
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
    threading.Thread(target=delete_later, daemon=True).start()


# =========================
# ROUTES
# =========================
@app.route('/')
def index():
    return render_template('index.html')


# Route to generate .bat file for yt-dlp
@app.route('/bat')
def bat_file():
    url = request.args.get('url', '').strip()
    bat_content = (
        '@echo off\n'
        'yt-dlp -f bestvideo+bestaudio --merge-output-format mp4 "{url}"\n'
        'pause\n'
    ).format(url=url)
    # Write to temp file and send, or send as attachment
    from io import BytesIO
    bat_bytes = BytesIO(bat_content.encode('utf-8'))
    return send_file(
        bat_bytes,
        as_attachment=True,
        download_name='download.bat',
        mimetype='application/octet-stream'
    )


@app.route('/download', methods=['POST'])
@limiter.limit("5 per minute")
def download():
    if not download_semaphore.acquire(blocking=False):
        return jsonify({
            "message": "Server busy. Please try again shortly."
        }), 429

    try:
        data = request.json or {}
        url = data.get('url', '').strip()
        quality = data.get('quality', 'best')

        if not url:
            return jsonify({"message": "Video URL is required"}), 400

        # Quality → yt-dlp format
        if quality == 'best':
            format_selector = 'bv*+ba/best'
        else:
            format_selector = f'bv*[height<={quality}]+ba/best'

        ydl_opts = {
            'format': format_selector,
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(BASE_TEMP_DIR, '%(id)s.%(ext)s'),
            'noplaylist': True,
            'quiet': True,

            # SAFETY LIMITS
            'max_filesize': MAX_FILE_SIZE_MB * 1024 * 1024,
            'match_filter': yt_dlp.utils.match_filter_func(
                f'duration < {MAX_DURATION_SECONDS}'
            ),

            'http_headers': {
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://www.pinterest.com/'
            },

            # YouTube anti-bot fix
            'extractor_args': {'youtube': {'player_client': ['tv', 'web']}},
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Correct file path (Pinterest / HLS fix)
        if 'requested_downloads' in info:
            filepath = info['requested_downloads'][0]['filepath']
        else:
            filepath = ydl.prepare_filename(info)

        if not os.path.exists(filepath):
            raise Exception("Downloaded file not found")

        filename = os.path.basename(filepath)

        cleanup_file(filepath)

        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='video/mp4'
        )

    except yt_dlp.utils.DownloadError:
        return jsonify({
            "message": "Video too large, too long, or not accessible"
        }), 400

    except Exception as e:
        return jsonify({
            "message": f"Error: {str(e)}"
        }), 500

    finally:
        download_semaphore.release()


# =========================
# ENTRY POINT
# =========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
