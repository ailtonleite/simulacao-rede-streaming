from flask import Flask, send_from_directory
import os
import ffmpeg
import shutil

app = Flask(__name__)

# http://localhost:5000/hls/video.mp4
@app.route('/hls/<path:filename>')
def segment_hls(filename):
    #Receber um video mp4 e segmentar usando HLS
    filename = "server/"+filename
    output_folder = "server/cache_videos/"
    
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


# http://localhost:5000/stream/stream.m3u8
@app.route('/stream/<path:filename>')
def stream_video(filename):
    return send_from_directory('cache_videos/', filename)


# http://localhost:5000/clean_cache
@app.route('/clean_cache')
def clean_cache():
    for item in os.listdir("server/cache_videos/"):
        item_path = os.path.join("server/cache_videos/", item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        except Exception as e:
            print(f"Erro ao remover {item_path}: {e}")
    return "Processo de limpeza de cache finalizado"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
