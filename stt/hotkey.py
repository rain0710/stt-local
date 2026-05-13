from pynput import keyboard as kb
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)

KEY_MAP = {
    "F1": kb.Key.f1, "F2": kb.Key.f2, "F3": kb.Key.f3, "F4": kb.Key.f4,
    "F5": kb.Key.f5, "F6": kb.Key.f6, "F7": kb.Key.f7, "F8": kb.Key.f8,
    "F9": kb.Key.f9, "F10": kb.Key.f10, "F11": kb.Key.f11, "F12": kb.Key.f12,
    "CapsLock": kb.Key.caps_lock,
    "right_ctrl": kb.Key.ctrl_r, "left_ctrl": kb.Key.ctrl_l,
    "right_alt": kb.Key.alt_r, "left_alt": kb.Key.alt_l,
    "right_shift": kb.Key.shift_r, "left_shift": kb.Key.shift_l,
    "ctrl": kb.Key.ctrl_l, "alt": kb.Key.alt_l, "shift": kb.Key.shift_l,
}


class HotkeyListener:
    def __init__(
        self,
        key_name: str,
        modifier_name: Optional[str],
        on_press: Callable,
        on_release: Callable,
    ):
        self._target = self._resolve(key_name)
        self._modifier = self._resolve(modifier_name) if modifier_name else None
        self._on_press_cb = on_press
        self._on_release_cb = on_release
        self._pressed = False
        self._modifier_held = False
        self._listener: Optional[kb.Listener] = None

    def _resolve(self, name: str):
        if name in KEY_MAP:
            return KEY_MAP[name]
        if len(name) == 1:
            return kb.KeyCode.from_char(name.lower())
        try:
            return kb.Key[name.lower()]
        except KeyError:
            return kb.KeyCode.from_char(name.lower())

    def _on_press(self, key):
        if self._modifier and key == self._modifier:
            self._modifier_held = True
            return
        if key == self._target:
            modifier_ok = (self._modifier is None) or self._modifier_held
            if modifier_ok and not self._pressed:
                self._pressed = True
                try:
                    self._on_press_cb()
                except Exception:
                    logger.exception("on_press callback error")

    def _on_release(self, key):
        if self._modifier and key == self._modifier:
            self._modifier_held = False
        if key == self._target and self._pressed:
            self._pressed = False
            try:
                self._on_release_cb()
            except Exception:
                logger.exception("on_release callback error")

    def start(self):
        self._listener = kb.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False,
        )
        self._listener.start()
        logger.info(f"Hotkey listener started: {self._modifier}+{self._target}" if self._modifier else f"Hotkey: {self._target}")

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener.join(timeout=2.0)
