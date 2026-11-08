import cv2
import numpy as np

class Button:
    def __init__(self, pos: tuple[int, int], width: int, height: int, value: str):
        self.pos = pos
        self.width = width
        self.height = height
        self.value = value
        self.is_hovered = False
        self.is_pressed = False
        self.dwell_progress = 0.0

        if self.value in {"C", "<"}:
            self.base_color = (45, 52, 71)
            self.accent_color = (60, 76, 230)
        elif self.value in {"+", "-", "*", "/", "="}:
            self.base_color = (60, 60, 75)
            self.accent_color = (235, 145, 52)
        else:
            self.base_color = (38, 38, 43)
            self.accent_color = (80, 80, 95)

    def is_inside(self, point: tuple[int, int]) -> bool:
        px, py = point
        x, y = self.pos
        return x <= px <= x + self.width and y <= py <= y + self.height

    def draw(self, img: np.ndarray) -> None:
        x, y = self.pos
        w, h = self.width, self.height

        color = self.base_color
        border_color = (90, 90, 105)
        text_color = (245, 245, 245)

        if self.is_pressed:
            color = self.accent_color
            border_color = (255, 255, 255)
        elif self.is_hovered:
            color = (int(self.base_color[0] * 1.3), int(self.base_color[1] * 1.3), int(self.base_color[2] * 1.3))
            border_color = self.accent_color

        sub_img = img[y:y + h, x:x + w]
        overlay = np.full_like(sub_img, color, dtype=np.uint8)
        alpha = 0.88
        cv2.addWeighted(overlay, alpha, sub_img, 1 - alpha, 0, sub_img)

        # Barra de progreso en modo permanencia (dwell time)
        if self.dwell_progress > 0.0:
            fill_w = int(w * min(max(self.dwell_progress, 0.0), 1.0))
            if fill_w > 0:
                cv2.rectangle(img, (x, y + h - 6), (x + fill_w, y + h), (0, 220, 100), cv2.FILLED)

        # Borde exterior
        cv2.rectangle(img, (x, y), (x + w, y + h), border_color, 2)

        # Centrado del texto
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.6, h / 110.0)
        thickness = 2
        text_size, _ = cv2.getTextSize(self.value, font, font_scale, thickness)
        tx = x + (w - text_size[0]) // 2
        ty = y + (h + text_size[1]) // 2
        cv2.putText(img, self.value, (tx, ty), font, font_scale, text_color, thickness, cv2.LINE_AA)


class CalculatorGUI:
    def __init__(self, frame_width: int, frame_height: int):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.buttons: list[Button] = []
        self._build_layout()

    def _build_layout(self) -> None:
        # Escala adaptativa segun resolucion
        btn_size = int(min(self.frame_width, self.frame_height) * 0.11)
        btn_size = max(55, min(btn_size, 90))
        margin = 10

        panel_w = 4 * btn_size + 3 * margin
        start_x = self.frame_width - panel_w - 30
        start_y = int(self.frame_height * 0.22)

        layout = [
            ["C", "<"],
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "-"],
            ["0", ".", "=", "+"]
        ]

        self.panel_rect = (
            start_x - 15,
            int(self.frame_height * 0.05),
            panel_w + 30,
            start_y + 5 * (btn_size + margin) - int(self.frame_height * 0.05) + 10
        )
        self.display_rect = (
            start_x,
            int(self.frame_height * 0.07),
            panel_w,
            int(btn_size * 1.1)
        )

        for row_idx, row in enumerate(layout):
            y = start_y + row_idx * (btn_size + margin)
            if row_idx == 0:
                w2 = (panel_w - margin) // 2
                self.buttons.append(Button((start_x, y), w2, btn_size, row[0]))
                self.buttons.append(Button((start_x + w2 + margin, y), w2, btn_size, row[1]))
            else:
                for col_idx, val in enumerate(row):
                    x = start_x + col_idx * (btn_size + margin)
                    self.buttons.append(Button((x, y), btn_size, btn_size, val))

    def draw_panel(self, img: np.ndarray, expression: str, last_result: str, mode_name: str, paused: bool) -> None:
        px, py, pw, ph = self.panel_rect
        if py + ph <= img.shape[0] and px + pw <= img.shape[1]:
            panel_sub = img[py:py + ph, px:px + pw]
            panel_bg = np.full_like(panel_sub, (22, 22, 26), dtype=np.uint8)
            cv2.addWeighted(panel_bg, 0.75, panel_sub, 0.25, 0, panel_sub)
            cv2.rectangle(img, (px, py), (px + pw, py + ph), (70, 70, 85), 2)

        # Pantalla display
        dx, dy, dw, dh = self.display_rect
        disp_sub = img[dy:dy + dh, dx:dx + dw]
        disp_bg = np.full_like(disp_sub, (32, 36, 42), dtype=np.uint8)
        cv2.addWeighted(disp_bg, 0.9, disp_sub, 0.1, 0, disp_sub)
        cv2.rectangle(img, (dx, dy), (dx + dw, dy + dh), (100, 110, 130), 2)

        # Texto de resultado previo e instruccion
        if last_result:
            cv2.putText(img, last_result, (dx + 12, dy + int(dh * 0.35)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 175, 190), 1, cv2.LINE_AA)

        # Expresion activa
        display_text = expression if expression else "0"
        font_scale = 1.0 if len(display_text) < 10 else 0.7
        cv2.putText(img, display_text, (dx + 12, dy + int(dh * 0.82)),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 2, cv2.LINE_AA)

        # Botones
        for btn in self.buttons:
            btn.draw(img)

        # Barra de estado inferior izquierda
        status_bg_x, status_bg_y = 20, self.frame_height - 60
        status_text = f"Modo: {mode_name} | {'PAUSADO' if paused else 'ACTIVO'}"
        hint_text = "[M]: Cambiar Modo  |  [ESPACIO]: Pausar  |  [Q/ESC]: Salir"
        
        cv2.putText(img, status_text, (status_bg_x, status_bg_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 200) if not paused else (80, 100, 255), 2, cv2.LINE_AA)
        cv2.putText(img, hint_text, (status_bg_x, status_bg_y + 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (200, 200, 200), 1, cv2.LINE_AA)
