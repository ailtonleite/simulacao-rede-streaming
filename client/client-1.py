import cv2
import time
import numpy as np
import requests

MP4_URL = "http://localhost:5000/hls/video.mp4"
VIDEO_URL = "http://localhost:5000/stream/stream.m3u8"


# Em construção...
def segment_hls():
    try:
        response = requests.get(MP4_URL)
        response.raise_for_status()
        print("Video segmentado com sucesso!")

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar ou segmentar o vídeo: {e}")

def stream_video_hls():
    try:
        cap = cv2.VideoCapture(VIDEO_URL)
       
        frame_count = 0
        start_time = time.time()
        consecutive_failures = 0
        latency_total = 0.0
        first_frame_time = None

        while cap.isOpened():
            t1 = time.time()  # início da leitura
            ret, frame = cap.read()
            t2 = time.time()  # fim da leitura

            if not ret:
                consecutive_failures += 1
                if consecutive_failures > 50:
                    print("Fim do vídeo detectado. Encerrando...")
                    break
                continue

            consecutive_failures = 0  # Reseta falhas se o frame for válido
            frame_count += 1

            # Marcar latência do primeiro frame
            if first_frame_time is None:
                first_frame_time = t2 - start_time
                print(f"Latência de inicialização: {first_frame_time:.3f} segundos")

            # Acumula a latência de leitura
            frame_latency = t2 - t1
            latency_total += frame_latency

            cv2.imshow('Streaming', frame)

            # Aguarda a tecla 'q' para sair
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Usuário encerrou o streaming.")
                break

        cap.release()
        cv2.destroyAllWindows()

        # Evitar erro de divisão por zero se o vídeo for muito curto
        total_time = time.time() - start_time
        fps = frame_count / total_time if total_time > 0 else 0
        avg_latency = latency_total / frame_count if frame_count > 0 else 0
        avg_latency *= 1000

        print("")
        print(f"Frames renderizados: {frame_count}")
        print(f"Tempo de redenrização: {total_time:.2f}")
        print(f"Média de Frames por segundo renderizados: {fps:.2f}")
        print(f"Latência média por frame: {avg_latency:.2f} ms")

    except Exception as e:
        print(f"Erro ao processar o vídeo: {e}")


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
        print("2. ...")
        print("3. ...")
        print("4. ...")
        print("5. ...")      
        print("0. Sair")
        escolha = input("Escolha uma opção: ")

        if escolha == "1":
            print("Segmentando video...")
            segment_hls()
            print("Download do video...")
            stream_video_hls()
        elif escolha == "2":
            return
        elif escolha == "3":
            return
        elif escolha == "4":
            return
        elif escolha == "5":
            return
        elif escolha == "0":
            print("Limpando cache e encerrando...")
            clean_cache()
            break
        else:
            print("Opção inválida!")

if __name__ == '__main__':
    run()