from flask import Flask, send_from_directory

app = Flask(__name__)

# http://localhost:5000/stream/stream.m3u8
@app.route('/stream/<path:filename>')
def stream_video(filename):
    return send_from_directory('videos/', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
