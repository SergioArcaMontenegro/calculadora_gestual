import argparse
import sys
import time
from pathlib import Path

# Permite ejecutar tanto desde la raiz del repositorio como desde src/gest-calc
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import cv2
from calculator import CalculatorLogic
from gui import CalculatorGUI
from hand_detector import HandDetector
from sound_manager import SoundManager


def parse_args():
    parser = argparse.ArgumentParser(description="Calculadora interactiva basada en gestos")
    parser.add_argument("--cam", type=int, default=0, help="Indice de la camara a utilizar (defecto: 0)")
    parser.add_argument("--width", type=int, default=1280, help="Ancho de captura")
    parser.add_argument("--height", type=int, default=720, help="Alto de captura")
    return parser.parse_args()


def main():
    args = parse_args()
    cap = cv2.VideoCapture(args.cam)

    if not cap.isOpened():
        print(f"Error: no se pudo abrir la camara con indice {args.cam}")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    ret, sample_frame = cap.read()
    if not ret:
        print("Error: no se pudo leer ningun fotograma de la camara.")
        sys.exit(1)

    frame_h, frame_w = sample_frame.shape[:2]

    detector = HandDetector(max_hands=1, detection_con=0.75, track_con=0.75, smooth_factor=0.45)
    calc = CalculatorLogic()
    gui = CalculatorGUI(frame_w, frame_h)
    sound = SoundManager(enabled=True)

    # Modos: "PINZA" y "DWELL"
    modes = ["PINZA", "DWELL"]
    current_mode_idx = 0
    paused = False

    # Parametros del modo pinza
    pinch_threshold = 0.28
    release_threshold = 0.40
    is_pinching = False
    last_click_time = 0.0
    click_cooldown = 0.35

    # Parametros del modo dwell (permanencia)
    dwell_duration = 0.8
    dwell_button = None
    dwell_start_time = 0.0

    # Medicion de FPS
    prev_time = time.time()
    fps = 0.0

    window_name = "Calculadora Gestual - UIE"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Espejo horizontal para mapeo espacial natural
        frame = cv2.flip(frame, 1)

        now = time.time()
        dt = now - prev_time
        prev_time = now
        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt)

        frame = detector.find_hands(frame, draw=False)
        landmarks = detector.get_hand_landmarks(frame)

        hovered_button = None
        cursor_pos = None
        action_triggered = False
        selected_value = ""

        if landmarks and not paused:
            # Cursor en punta de indice
            cursor_pos = (landmarks[8][1], landmarks[8][2])

            for btn in gui.buttons:
                if btn.is_inside(cursor_pos):
                    hovered_button = btn
                    break

            mode = modes[current_mode_idx]

            if mode == "PINZA":
                _, norm_dist, pinch_mid = detector.get_pinch_metrics(landmarks)

                if norm_dist < pinch_threshold:
                    if not is_pinching and (now - last_click_time > click_cooldown):
                        is_pinching = True
                        last_click_time = now
                        if hovered_button:
                            action_triggered = True
                            selected_value = hovered_button.value
                            hovered_button.is_pressed = True
                elif norm_dist > release_threshold:
                    is_pinching = False

            elif mode == "DWELL":
                if hovered_button:
                    if dwell_button == hovered_button:
                        elapsed = now - dwell_start_time
                        progress = min(elapsed / dwell_duration, 1.0)
                        hovered_button.dwell_progress = progress

                        if elapsed >= dwell_duration and (now - last_click_time > click_cooldown):
                            action_triggered = True
                            selected_value = hovered_button.value
                            hovered_button.is_pressed = True
                            last_click_time = now
                            dwell_button = None
                    else:
                        if dwell_button:
                            dwell_button.dwell_progress = 0.0
                        dwell_button = hovered_button
                        dwell_start_time = now
                        hovered_button.dwell_progress = 0.0
                else:
                    if dwell_button:
                        dwell_button.dwell_progress = 0.0
                        dwell_button = None

        else:
            if dwell_button:
                dwell_button.dwell_progress = 0.0
                dwell_button = None

        # Procesar accion si se disparo
        if action_triggered and selected_value:
            calc.input(selected_value)
            if selected_value == "=":
                sound.play_calculate()
            elif selected_value in {"C", "<"}:
                sound.play_delete()
            else:
                sound.play_click()

        # Actualizar estado visual de los botones
        for btn in gui.buttons:
            btn.is_hovered = (btn == hovered_button) and not paused
            if btn != hovered_button or not action_triggered:
                if now - last_click_time > 0.15:
                    btn.is_pressed = False
            if btn != hovered_button and modes[current_mode_idx] == "DWELL":
                btn.dwell_progress = 0.0

        # Dibujar interfaz
        gui.draw_panel(
            img=frame,
            expression=calc.expression,
            last_result=calc.last_result,
            mode_name=modes[current_mode_idx],
            paused=paused
        )

        # Dibujar cursor interactivo
        if cursor_pos and not paused:
            cx, cy = cursor_pos
            cursor_color = (0, 255, 120)
            if is_pinching:
                cursor_color = (0, 140, 255)
            elif dwell_button and modes[current_mode_idx] == "DWELL":
                cursor_color = (255, 200, 0)

            cv2.circle(frame, (cx, cy), 10, cursor_color, cv2.FILLED)
            cv2.circle(frame, (cx, cy), 14, (255, 255, 255), 2)

        # Contador de FPS en esquina superior izquierda
        cv2.putText(frame, f"FPS: {int(fps)}", (25, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 180), 2, cv2.LINE_AA)

        cv2.imshow(window_name, frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q'), ord('Q')):
            break
        elif key in (ord('m'), ord('M')):
            current_mode_idx = (current_mode_idx + 1) % len(modes)
            if dwell_button:
                dwell_button.dwell_progress = 0.0
                dwell_button = None
        elif key == 32:  # Barra espaciadora
            paused = not paused
            if paused and dwell_button:
                dwell_button.dwell_progress = 0.0
                dwell_button = None
        elif key in (ord('c'), ord('C')):
            sound.enabled = not sound.enabled

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
