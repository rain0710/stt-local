import time
import logging
import win32clipboard
import win32con
from pynput.keyboard import Controller, Key

logger = logging.getLogger(__name__)
_ctrl = Controller()


class Injector:
    def __init__(self, auto_send: bool = False, paste_delay_ms: int = 50):
        self._auto_send = auto_send
        self._paste_delay = paste_delay_ms / 1000.0

    def inject(self, text: str):
        if not text:
            return
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
        finally:
            win32clipboard.CloseClipboard()

        time.sleep(self._paste_delay)

        with _ctrl.pressed(Key.ctrl):
            _ctrl.press("v")
            _ctrl.release("v")

        if self._auto_send:
            time.sleep(0.05)
            _ctrl.press(Key.enter)
            _ctrl.release(Key.enter)

        logger.info(f"Injected {len(text)} chars")
