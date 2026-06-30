# Plano de Testes para `record_rtsp_yoosee.py`

## Objetivo
Validar a estabilidade, robustez de rede e fechamento correto de recursos do script de gravação RTSP.

## Pré-requisitos
- Python 3.8+ instalado
- OpenCV instalado (`pip install opencv-python`)
- Acesso ao stream RTSP da câmera Yoosee/NVR
- Diretório de gravação acessível e com permissões de escrita

## Testes Básicos

### 1. Teste de conexão inicial
1. Configure os parâmetros em `record_rtsp_yoosee.py`:
   - `NVR_IP`, `NVR_USER`, `NVR_PASSWORD`, `CAMERA_ID`
2. Execute:
   ```bash
   python record_rtsp_yoosee.py
   ```
3. Verifique se o script conecta e cria o primeiro arquivo no diretório `gravacoes_yoose`.
4. Verifique que o arquivo `.mp4` gerado contém vídeo reproduzível.

### 2. Teste de gravação em segmentos de 5 minutos
1. Mantenha o script rodando por mais de 5 minutos.
2. Confirme que o arquivo é rotulado corretamente com timestamp e que ele encerra após 5 minutos.
3. Verifique se um novo arquivo é criado ao iniciar o próximo segmento.

### 3. Teste de detecção de FPS e fallback
1. Verifique no log se o FPS detectado é exibido corretamente.
2. Em câmeras que retornam `0` de FPS, confirme que o script usa `FPS_FALLBACK = 20.0`.

## Testes de Resiliência de Rede

### 4. Simulação de queda de conexão RTSP
1. Execute o script normalmente.
2. No NVR ou roteador, desative temporariamente a câmera ou bloqueie o acesso ao IP.
3. Observe o log; o script deve relatar "conexão perdida" e tentar reconectar.
4. Restaure a câmera/rota e confirme que o script reconecta e continua gerando segmentos.

### 5. Simulação de queda de rede local
1. Desative a interface de rede ou desconecte o cabo/Wi-Fi temporariamente.
2. Observe o log; o script deve falhar na leitura do stream e reiniciar a conexão sem travar.
3. Reconecte a rede e confirme a retomada do processo.

### 6. Simulação de problemas na fonte RTSP usando `ffmpeg`
Se você não puder desligar fisicamente a câmera, execute um servidor RTSP local ou use uma fonte de stream instável.

#### a) Usando `ffmpeg` para criar um RTSP fake:
```bash
ffmpeg -re -stream_loop -1 -i sample.mp4 -c copy -f rtsp rtsp://localhost:8554/live.stream
```
1. Aponte `NVR_IP` para `localhost` e ajuste o caminho RTSP.
2. Interrompa o `ffmpeg` com `Ctrl+C` durante a gravação para simular queda de stream.
3. Verifique se o script reconecta após a queda.

## Verificação de Recursos e Logs

### 7. Verificação de vazamento de arquivo / handles
1. Enquanto o script roda, use `lsof` para listar handles abertos no processo:
   ```bash
   lsof -p <PID> | grep mp4
   ```
2. Confirme que `VideoCapture` e `VideoWriter` são liberados após cada segmento ou erro.

### 8. Verificação de tratamento de interrupção
1. Execute o script e pressione `Ctrl+C`.
2. Confirme que o script termina com a mensagem de encerramento e sem traceback de erro.

## Observações e recomendações
- Se o NVR suportar caminhos RTSP diferentes, ajuste `build_rtsp_url()` conforme a documentação do fabricante.
- Para ambientes de produção, considere usar `systemd` ou `supervisord` para reiniciar o script automaticamente.
