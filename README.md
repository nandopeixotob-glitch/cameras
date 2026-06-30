# Cameras

Este repositório contém um script Python para capturar streams RTSP de câmeras Yoosee/NVR e gravar em arquivos segmentados de vídeo.

## O que o sistema faz

O script `record_rtsp_yoosee.py`:

- conecta a um stream RTSP de uma câmera Yoosee através de um NVR;
- grava os frames recebidos em arquivos MP4 contínuos de 5 minutos;
- detecta automaticamente o FPS do stream com fallback para 20 FPS;
- tenta reconectar automaticamente quando o stream falha ou perde conexão;
- libera corretamente recursos de vídeo para evitar vazamentos de memória e arquivos corrompidos.

## Como usar

1. Atualize as configurações no arquivo `record_rtsp_yoosee.py`:
   - `NVR_IP`
   - `NVR_USER`
   - `NVR_PASSWORD`
   - `CAMERA_ID`

2. Instale a dependência:

```bash
python3 -m pip install opencv-python
```

3. Execute o script:

```bash
python3 record_rtsp_yoosee.py
```

4. Os arquivos de gravação serão salvos no diretório `gravacoes_yoose`.

## Arquivos adicionados

- `record_rtsp_yoosee.py`: script principal de gravação RTSP.
- `TEST_PLAN.md`: plano de testes práticos para validar o sistema em ambiente local.

## Observações

- Se a câmera retornar FPS inválido, o script usa um valor de fallback para manter a gravação.
- Para ambientes de produção, é recomendável executar o script com um gerenciador de processos como `systemd` ou `supervisord`.
