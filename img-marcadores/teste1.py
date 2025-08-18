import cv2
import numpy as np
from djitellopy import Tello
import time

def detectar_simbolo(frame):
    """
    Função para detectar o símbolo de círculo amarelo com uma cruz.
    Retorna o frame com as detecções e um booleano indicando se o símbolo foi encontrado.
    """
    simbolo_encontrado = False
    
    # Converte o frame para o espaço de cores HSV, que é melhor para detecção de cores
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define a faixa de cor amarela em HSV
    # Estes valores podem precisar de ajuste dependendo da iluminação
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([30, 255, 255])

    # Cria uma máscara para a cor amarela
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # Melhora a máscara para remover ruídos
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # Encontra os contornos na máscara
    contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Se algum contorno for encontrado
    if len(contornos) > 0:
        # Pega o maior contorno (assumindo que seja o nosso círculo)
        c = max(contornos, key=cv2.contourArea)
        
        # Encontra o círculo que envolve o contorno
        ((x, y), raio) = cv2.minEnclosingCircle(c)
        
        # Verifica se o contorno é suficientemente grande e circular
        area = cv2.contourArea(c)
        area_circulo = np.pi * raio**2
        
        if raio > 20 and area > 1000 and (area / area_circulo) > 0.7:
            # Desenha o círculo no frame original
            cv2.circle(frame, (int(x), int(y)), int(raio), (0, 255, 0), 2)
            
            # Recorta a região de interesse (ROI) - a área do círculo
            x_int, y_int, r_int = int(x), int(y), int(raio)
            roi = mask[y_int - r_int:y_int + r_int, x_int - r_int:x_int + r_int]

            if roi.size > 0:
                # Dentro da ROI, vamos procurar por linhas (a cruz)
                linhas = cv2.HoughLinesP(roi, 1, np.pi / 180, threshold=20, minLineLength=r_int*0.5, maxLineGap=10)
                
                if linhas is not None and len(linhas) >= 2:
                    # Uma verificação simples: se encontrarmos pelo menos 2 linhas, consideramos uma cruz
                    # Para uma detecção mais robusta, seria necessário analisar a orientação das linhas
                    simbolo_encontrado = True
                    cv2.putText(frame, "SIMBOLO DETECTADO", (int(x) - 100, int(y) - 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    return frame, simbolo_encontrado

# --- Controle do Drone ---

# Inicializa o drone
tello = Tello()

# Conecta ao drone
tello.connect()
print(f"Bateria: {tello.get_battery()}%")

# Liga a câmera
tello.streamon()
frame_read = tello.get_frame_read()

# Decola
tello.takeoff()
time.sleep(1) # Aguarda um pouco após decolar
tello.move_up(30) # Sobe um pouco mais para ter um bom campo de visão
time.sleep(1)

simbolo_foi_detectado = False

try:
    while True:
        # Pega o frame da câmera
        frame = frame_read.frame

        # Redimensiona o frame para processamento mais rápido
        frame = cv2.resize(frame, (640, 480))

        # Chama a função de detecção
        frame_processado, encontrado = detectar_simbolo(frame)

        # Exibe a imagem da câmera
        cv2.imshow("Tello Stream", frame_processado)

        # Se o símbolo for encontrado e ainda não tivermos reagido
        if encontrado and not simbolo_foi_detectado:
            print("Símbolo detectado! Executando comando...")
            
            # TELLO VAI POUSAR 
            tello.land()  # Pousa o drone
            # -------------------------------

            simbolo_foi_detectado = True # Marca que já reagimos
            # Aguarda um pouco para não detectar o mesmo símbolo várias vezes seguidas
            time.sleep(5) 
            simbolo_foi_detectado = False # Permite nova detecção


        # Verifica se a tecla 'q' foi pressionada para sair e pousar
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Interrompido pelo usuário.")
