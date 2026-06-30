import cv2
import os
import time
from datetime import datetime
from pathlib import Path

# Configurações
NVR_IP = "192.168.1.100"      # Substitua pelo IP do seu NVR
NVR_USER = "seu_usuario"      # Substitua pelo usuário do NVR
NVR_PASSWORD = "sua_senha"    # Substitua pela senha do NVR
CAMERA_ID = 1                 # Substitua pelo ID da câmera
OUTPUT_DIR = "gravacoes_yoose"  # Diretório onde as gravações serão salvas
DURACAO_SEGMENTO = 300        # Duração de cada vídeo em segundos (ex: 5 minutos)
FPS_FALLBACK = 20.0           # Fallback caso a câmera não informe FPS válido
RECONNECT_INITIAL_DELAY = 5   # Delay inicial entre tentativas de reconexão
RECONNECT_MAX_DELAY = 60      # Tempo máximo de backoff entre tentativas
READ_FAILURE_LIMIT = 10       # Número de tentativas de leitura antes de reiniciar a conexão
READ_RETRY_INTERVAL = 1.0     # Intervalo entre tentativas de leitura em segundos


def log(message: str) -> None:
    """Imprime mensagens com timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def build_rtsp_url() -> str:
    """Monta a URL RTSP com credenciais."""
    return f"rtsp://{NVR_USER}:{NVR_PASSWORD}@{NVR_IP}:554/live/{CAMERA_ID}"


def prepare_output_directory() -> None:
    """Cria o diretório de saída caso não exista."""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def open_rtsp_capture(url: str) -> cv2.VideoCapture:
    """Abre o stream RTSP e retorna o objeto VideoCapture se for válido."""
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        cap.release()
        return None

    # Reduz o buffer para evitar frames defasados em streams RTSP.
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass

    return cap


def get_video_properties(cap: cv2.VideoCapture, first_frame) -> tuple[int, int, float]:
    """Obtém largura, altura e FPS do stream, com fallback quando necessário."""
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    if width <= 0 or height <= 0:
        height, width = first_frame.shape[:2]
        log(f"Propriedades de vídeo não disponíveis. Usando frame inicial: {width}x{height}.")

    if not fps or fps <= 0 or fps != fps:
        log(f"FPS inválido retornado ({fps}). Usando fallback {FPS_FALLBACK}.")
        fps = FPS_FALLBACK

    return width, height, fps


def create_video_writer(filename: str, width: int, height: int, fps: float) -> cv2.VideoWriter:
    """Cria o VideoWriter para gravação em MP4."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    if not out.isOpened():
        raise RuntimeError(f"Não foi possível inicializar VideoWriter para {filename}")
    return out


def get_segment_filename() -> str:
    """Gera um nome de arquivo baseado em timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(OUTPUT_DIR, f"camera_{timestamp}.mp4")


def connect_and_record() -> None:
    """Loop principal que conecta ao RTSP e grava segmentos contínuos."""
    url = build_rtsp_url()
    prepare_output_directory()
    reconnect_delay = RECONNECT_INITIAL_DELAY

    while True:
        cap = open_rtsp_capture(url)
        if cap is None:
            log(f"Falha ao abrir stream RTSP. Tentando novamente em {reconnect_delay} segundos...")
            time.sleep(reconnect_delay)
            reconnect_delay = min(RECONNECT_MAX_DELAY, reconnect_delay * 2)
            continue

        reconnect_delay = RECONNECT_INITIAL_DELAY
        out = None

        try:
            log("Conexão estabelecida. Aguardando primeiro frame válido...")

            first_frame = None
            for attempt in range(READ_FAILURE_LIMIT):
                ret, first_frame = cap.read()
                if ret and first_frame is not None:
                    break
                log(f"Primeiro frame não disponível. Tentativa {attempt + 1}/{READ_FAILURE_LIMIT}...")
                time.sleep(READ_RETRY_INTERVAL)

            if first_frame is None or not ret:
                log("Não foi possível ler o primeiro frame. Reiniciando captura.")
                continue

            width, height, fps = get_video_properties(cap, first_frame)
            filename = get_segment_filename()
            out = create_video_writer(filename, width, height, fps)
            log(f"Iniciando gravação: {filename} | {width}x{height} @ {fps:.2f} FPS")

            segment_start = time.time()
            out.write(first_frame)

            while time.time() - segment_start < DURACAO_SEGMENTO:
                ret, frame = cap.read()
                if not ret or frame is None:
                    log("Leitura de frame falhou ou conexão perdida. Reiniciando segmento...")
                    break

                out.write(frame)

            log("Segmento concluído. Liberando recursos do segmento atual.")

        except Exception as exc:
            log(f"Erro de gravação: {exc}")

        finally:
            if out is not None:
                out.release()
            if cap is not None:
                cap.release()

        time.sleep(1)


if __name__ == "__main__":
    try:
        connect_and_record()
    except KeyboardInterrupt:
        log("Interrupção do usuário recebida. Encerrando o script.")
    except Exception as exc:
        log(f"Erro inesperado: {exc}")
