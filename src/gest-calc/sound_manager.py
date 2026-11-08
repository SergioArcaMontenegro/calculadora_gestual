import sys
import threading

class SoundManager:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._is_windows = sys.platform.startswith("win")
        self._winsound = None
        if self._is_windows:
            try:
                import winsound
                self._winsound = winsound
            except ImportError:
                pass

    def play_click(self) -> None:
        if not self.enabled or not self._winsound:
            return
        threading.Thread(target=self._beep, args=(1200, 40), daemon=True).start()

    def play_delete(self) -> None:
        if not self.enabled or not self._winsound:
            return
        threading.Thread(target=self._beep, args=(600, 60), daemon=True).start()

    def play_calculate(self) -> None:
        if not self.enabled or not self._winsound:
            return
        threading.Thread(target=self._beep, args=(1800, 80), daemon=True).start()

    def _beep(self, freq: int, duration: int) -> None:
        try:
            self._winsound.Beep(freq, duration)
        except Exception:
            pass

