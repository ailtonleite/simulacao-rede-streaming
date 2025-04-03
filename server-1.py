from flask import Flask, send_from_directory
import os
import ffmpeg

app = Flask(__name__)

@app.route('/hls/<output_folder>/<path:filename>')
def stream_video(filename, output_folder):
    #Receber um video mp4 e segmentar usando HLS
    os.makedirs(output_folder, exist_ok=True)
    output_playlist = os.path.join(output_folder, "stream.m3u8")
    
    ffmpeg.input(filename).output(
        output_playlist,
        codec='copy',
        start_number=0,
        hls_time=5,
        hls_list_size=0,
        format='hls'
    ).run()
    return f"Playlist gerada em: {output_playlist}"

@app.route('/rtsp/<path:filename>')
def stream_video(filename):
    #Receber um video mp4 e segmentar usando RTSP
    return

# http://localhost:5000/stream/stream.m3u8
@app.route('/stream/<path:filename>')
def stream_video(filename):
    return send_from_directory('videos/', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
