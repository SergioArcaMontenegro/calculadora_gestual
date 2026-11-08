import math
import cv2
import mediapipe as mp

class HandDetector:
    def __init__(self, max_hands: int = 1, detection_con: float = 0.7, track_con: float = 0.7, smooth_factor: float = 0.5):
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con
        self.smooth_factor = smooth_factor

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_draw_styles = mp.solutions.drawing_styles

        self.smoothed_index_tip = None
        self.tip_ids = [4, 8, 12, 16, 20]

    def find_hands(self, img, draw: bool = True):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks and draw:
            for hand_lms in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    img,
                    hand_lms,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_draw_styles.get_default_hand_landmarks_style(),
                    self.mp_draw_styles.get_default_hand_connections_style()
                )
        return img

    def get_hand_landmarks(self, img, hand_index: int = 0):
        landmarks = []
        if not self.results.multi_hand_landmarks or len(self.results.multi_hand_landmarks) <= hand_index:
            self.smoothed_index_tip = None
            return landmarks

        h, w, _ = img.shape
        target_hand = self.results.multi_hand_landmarks[hand_index]
        for idx, lm in enumerate(target_hand.landmark):
            cx, cy = int(lm.x * w), int(lm.y * h)
            landmarks.append([idx, cx, cy, lm.z])

        raw_index_tip = (landmarks[8][1], landmarks[8][2])
        if self.smoothed_index_tip is None:
            self.smoothed_index_tip = raw_index_tip
        else:
            sx = int(self.smooth_factor * raw_index_tip[0] + (1 - self.smooth_factor) * self.smoothed_index_tip[0])
            sy = int(self.smooth_factor * raw_index_tip[1] + (1 - self.smooth_factor) * self.smoothed_index_tip[1])
            self.smoothed_index_tip = (sx, sy)

        landmarks[8][1], landmarks[8][2] = self.smoothed_index_tip
        return landmarks

    def fingers_up(self, landmarks) -> list[int]:
        if len(landmarks) < 21:
            return [0, 0, 0, 0, 0]

        fingers = []

        # Pulgar (comprobación horizontal segun orientacion de la mano)
        if landmarks[self.tip_ids[0]][1] > landmarks[self.tip_ids[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # Resto de dedos (comprobacion vertical de punta vs nudillo PIP)
        for idx in range(1, 5):
            tip_y = landmarks[self.tip_ids[idx]][2]
            pip_y = landmarks[self.tip_ids[idx] - 2][2]
            fingers.append(1 if tip_y < pip_y else 0)

        return fingers

    def get_pinch_metrics(self, landmarks) -> tuple[float, float, tuple[int, int]]:
        if len(landmarks) < 21:
            return 0.0, 0.0, (0, 0)

        x1, y1 = landmarks[4][1], landmarks[4][2]
        x2, y2 = landmarks[8][1], landmarks[8][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        pinch_px = math.hypot(x2 - x1, y2 - y1)

        # Escala de la palma (muneca landmark 0 al nudillo del medio landmark 9)
        wx, wy = landmarks[0][1], landmarks[0][2]
        mx, my = landmarks[9][1], landmarks[9][2]
        hand_scale = math.hypot(mx - wx, my - wy)

        normalized_dist = pinch_px / max(hand_scale, 1.0)
        return pinch_px, normalized_dist, (cx, cy)

