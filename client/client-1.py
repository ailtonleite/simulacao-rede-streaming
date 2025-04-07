import cv2
import time
import os
import numpy as np
import requests
import vlc
import tempfile
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import matplotlib.pyplot as plt
from collections import defaultdict

HLS_URL = "http://localhost:5000/hls/video_longo.mp4"
VIDEO_URL = "http://localhost:5000/stream/stream.m3u8"
DASH_URL = "http://localhost:5000/dash/video_longo.mp4"
DASH_MANIFEST_URL = "http://localhost:5000/dash_stream/stream.mpd"


def segment_hls():
    try:
        response = requests.get(HLS_URL)
        response.raise_for_status()
        print("Video segmentado com sucesso!")

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar ou segmentar o vídeo: {e}")

def segment_dash():
    try:
        response = requests.get(DASH_URL)
        response.raise_for_status()
        print("Video segmentado em DASH com sucesso!")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao segmentar o vídeo com DASH: {e}")

def stream_video_hls():
    try:
        cap = cv2.VideoCapture(VIDEO_URL)

        frame_count = 0
        start_time = time.time()
        consecutive_failures = 0
        latency_total = 0.0
        buffering_time_total = 0.0
        stall_events = 0
        first_frame_time = None
        buffering_start = None
        bitrate_dict = defaultdict(int)

        while cap.isOpened():
            t1 = time.time()
            ret, frame = cap.read()
            t2 = time.time()

            if not ret:
                consecutive_failures += 1
                if buffering_start is None:
                    buffering_start = time.time()
                    stall_events += 1

                if consecutive_failures > 50:
                    print("Fim do vídeo detectado. Encerrando...")
                    break
                continue
            else:
                if buffering_start is not None:
                    buffering_time_total += time.time() - buffering_start
                    buffering_start = None

            consecutive_failures = 0
            frame_count += 1

            if first_frame_time is None:
                first_frame_time = t2 - start_time
                print(f"Latência de inicialização: {first_frame_time:.3f} segundos")

            frame_latency = t2 - t1
            latency_total += frame_latency

            # Bitrate (por segundo)
            elapsed_sec = int(t2 - start_time)
            frame_bits = frame.nbytes * 8
            bitrate_dict[elapsed_sec] += frame_bits

            cv2.imshow('Streaming', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Usuário encerrou o streaming.")
                break

        cap.release()
        cv2.destroyAllWindows()

        total_time = time.time() - start_time
        fps = frame_count / total_time if total_time > 0 else 0
        avg_latency = latency_total / frame_count if frame_count > 0 else 0
        avg_latency *= 1000

        print("")
        print(f"Frames renderizados: {frame_count}")
        print(f"Tempo de redenrização: {total_time:.2f}")
        print(f"Média de FPS: {fps:.2f}")
        print(f"Latência média por frame: {avg_latency:.2f} ms")
        print(f"Eventos de buffering: {stall_events}")
        print(f"Tempo total em buffering: {buffering_time_total:.2f} segundos")

        # Plot do gráfico de bitrate
        segundos = sorted(bitrate_dict.keys())
        bitrates = [bitrate_dict[s] / 1_000 for s in segundos]  # kbps

        plt.figure(figsize=(10, 5))
        plt.plot(segundos, bitrates, marker='o', linestyle='-')
        plt.title('Taxa de Bits por Segundo (HLS)')
        plt.xlabel('Tempo (s)')
        plt.ylabel('Bitrate (kbps)')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Erro ao processar o vídeo: {e}")



def gerar_segmentos_do_template(mpd_url):
    response = requests.get(mpd_url)
    base_url = mpd_url.rsplit('/', 1)[0] + '/'
    segmentos = []

    tree = ET.fromstring(response.content)
    ns = {'mpd': 'urn:mpeg:dash:schema:mpd:2011'}

    # Seleciona o vídeo (você pode mudar isso para áudio se quiser)
    representation = tree.find(".//mpd:AdaptationSet[@contentType='video']/mpd:Representation", ns)
    if representation is None:
        raise ValueError("Representation de vídeo não encontrada.")

    rep_id = representation.attrib['id']
    seg_template = representation.find("mpd:SegmentTemplate", ns)
    if seg_template is None:
        raise ValueError("SegmentTemplate não encontrado.")

    init_template = seg_template.attrib['initialization']  # ex: init-$RepresentationID$.mp4
    media_template = seg_template.attrib['media']          # ex: chunk-$RepresentationID$-$Number$.m4s
    start_number = int(seg_template.attrib.get('startNumber', 1))

    # Adiciona segmento de inicialização
    init_url = init_template.replace("$RepresentationID$", rep_id)
    segmentos.append(urljoin(base_url, init_url))

    # Parse da linha do tempo
    timeline = seg_template.find("mpd:SegmentTimeline", ns)
    if timeline is None:
        raise ValueError("SegmentTimeline não encontrado.")

    segment_number = start_number
    for s in timeline.findall("mpd:S", ns):
        repeat = int(s.attrib.get("r", 0))
        for _ in range(repeat + 1):
            seg_url = media_template.replace("$RepresentationID$", rep_id).replace("$Number$", str(segment_number))
            segmentos.append(urljoin(base_url, seg_url))
            segment_number += 1

    return segmentos

def concatenar_segmentos_em_arquivo(segmentos):
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    with open(tmp_file.name, 'wb') as f:
        for url in segmentos:
            print(f"Baixando: {url}")
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            else:
                print(f"Erro ao baixar segmento: {url} - Código {r.status_code}")
    return tmp_file.name

import matplotlib.pyplot as plt
from collections import defaultdict

def stream_video_dash():
    try:
        segmentos = gerar_segmentos_do_template(DASH_MANIFEST_URL)
        arquivo_video = concatenar_segmentos_em_arquivo(segmentos)

        cap = cv2.VideoCapture(arquivo_video)

        frame_count = 0
        start_time = time.time()
        consecutive_failures = 0
        latency_total = 0.0
        buffering_time_total = 0.0
        stall_events = 0
        first_frame_time = None
        buffering_start = None
        bitrate_dict = defaultdict(int)

        while cap.isOpened():
            t1 = time.time()
            ret, frame = cap.read()
            t2 = time.time()

            if not ret:
                consecutive_failures += 1
                if buffering_start is None:
                    buffering_start = time.time()
                    stall_events += 1

                if consecutive_failures > 50:
                    print("Fim do vídeo (DASH) detectado. Encerrando...")
                    break
                continue
            else:
                if buffering_start is not None:
                    buffering_time_total += time.time() - buffering_start
                    buffering_start = None

            consecutive_failures = 0
            frame_count += 1

            if first_frame_time is None:
                first_frame_time = t2 - start_time
                print(f"Latência de inicialização (DASH): {first_frame_time:.3f} segundos")

            frame_latency = t2 - t1
            latency_total += frame_latency

            # Bitrate (por segundo)
            elapsed_sec = int(t2 - start_time)
            frame_bits = frame.nbytes * 8
            bitrate_dict[elapsed_sec] += frame_bits

            cv2.imshow('Streaming DASH', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Usuário encerrou o streaming DASH.")
                break

        cap.release()
        cv2.destroyAllWindows()
        os.remove(arquivo_video)

        total_time = time.time() - start_time
        fps = frame_count / total_time if total_time > 0 else 0
        avg_latency = latency_total / frame_count if frame_count > 0 else 0
        avg_latency *= 1000

        print("")
        print(f"Frames renderizados: {frame_count}")
        print(f"Tempo de redenrização: {total_time:.2f}")
        print(f"Média de FPS (DASH): {fps:.2f}")
        print(f"Latência média por frame: {avg_latency:.2f} ms")
        print(f"Eventos de buffering: {stall_events}")
        print(f"Tempo total em buffering: {buffering_time_total:.2f} segundos")

        # Plot do gráfico de bitrate
        segundos = sorted(bitrate_dict.keys())
        bitrates = [bitrate_dict[s] / 1_000 for s in segundos]  # kbps

        plt.figure(figsize=(10, 5))
        plt.plot(segundos, bitrates, marker='o', linestyle='-')
        plt.title('Taxa de Bits por Segundo (DASH)')
        plt.xlabel('Tempo (s)')
        plt.ylabel('Bitrate (kbps)')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Erro no streaming DASH: {e}")



def clean_cache():
    try:
        response = requests.get("http://localhost:5000/clean_cache")
        response.raise_for_status()
        print("Cache do servidor limpa com sucesso!")

    except requests.exceptions.RequestException as e:
        print(f"Erro inesperado ao limpar a cahce: {e}")


def run():

    while True:
        print("\nMenu:")
        print("1. Stream video - HLS")
        print("2. Stream video - DASH")
        print("3. ...")   
        print("0. Sair")
        escolha = input("Escolha uma opção: ")

        if escolha == "1":
            print("Segmentando video...")
            segment_hls()
            print("Download do video...")
            stream_video_hls()
        elif escolha == "2":
            print("Segmentando video para DASH...")
            segment_dash()
            print("Download do video DASH...")
            stream_video_dash()
        elif escolha == "3":
            return
        elif escolha == "0":
            print("Limpando cache e encerrando...")
            clean_cache()
            break
        else:
            print("Opção inválida!")

if __name__ == '__main__':
    run()