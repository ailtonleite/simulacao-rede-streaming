import cv2
import time
import numpy as np

VIDEO_URL = "http://localhost:5000/stream/stream.m3u8"

cap = cv2.VideoCapture(VIDEO_URL)
buffer_times = []
frame_count = 0
start_time = time.time()
consecutive_failures = 0  # Contador de falhas consecutivas

while cap.isOpened():
    ret, frame = cap.read()

    if not ret:
        consecutive_failures += 1
        if consecutive_failures > 50:  # Sai após muitas falhas consecutivas
            print("Fim do vídeo detectado. Encerrando...")
            break
        buffer_start = time.time()
        time.sleep(0.05)  # Pequeno atraso para evitar loop excessivo
        buffer_end = time.time()
        buffer_times.append(buffer_end - buffer_start)
        continue

    consecutive_failures = 0  # Reseta falhas se o frame for válido
    frame_count += 1
    cv2.imshow('Streaming', frame)

    # Aguarda a tecla 'q' para sair
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Usuário encerrou o streaming.")
        break

cap.release()
cv2.destroyAllWindows()

# Evita erro de divisão por zero se o vídeo for muito curto
total_time = time.time() - start_time
fps = frame_count / total_time if total_time > 0 else 0
avg_buffer_time = np.mean(buffer_times) if buffer_times else 0

print(f"FPS Médio: {fps:.2f}")
print(f"Tempo Médio de Buffer: {avg_buffer_time:.2f} segundos")
