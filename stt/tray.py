from PIL import Image, ImageDraw
import pystray
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

STATES = {
    "idle":       {"bg": (40,  40,  40,  255), "fg": (80,  200, 80,  255),
                   "title": {"zh": "STT · 待命",    "en": "STT · Idle"}},
    "recording":  {"bg": (198, 40,  40,  255), "fg": (255, 255, 255, 255),
                   "title": {"zh": "STT · 录音中...", "en": "STT · Recording..."}},
    "processing": {"bg": (21,  101, 192, 255), "fg": (255, 193, 7,   255),
                   "title": {"zh": "STT · 转录中...", "en": "STT · Processing..."}},
}

MENU_STRINGS = {
    "zh": {"settings": "设置", "quit": "退出"},
    "en": {"settings": "Settings", "quit": "Quit"},
}


def _make_icon(state: str) -> Image.Image:
    theme = STATES[state]
    bg, fg = theme["bg"], theme["fg"]

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 圆形背景
    draw.ellipse([2, 2, 61, 61], fill=bg)

    # 麦克风胶囊体
    draw.rounded_rectangle([26, 10, 38, 36], radius=6, fill=fg)

    # 拾音弧线
    draw.arc([20, 26, 44, 46], start=0, end=180, fill=fg, width=2)

    # 支架
    draw.line([32, 46, 32, 52], fill=fg, width=2)

    # 底座
    draw.line([24, 52, 40, 52], fill=fg, width=2)

    # 录音状态：右上角加白色小圆点
    if state == "recording":
        draw.ellipse([46, 6, 58, 18], fill=(255, 255, 255, 220))

    # 转录状态：右下角加三个小点
    if state == "processing":
        for i, x in enumerate([44, 50, 56]):
            draw.ellipse([x, 50, x + 4, 54], fill=fg)

    return img


_ICONS = {s: _make_icon(s) for s in STATES}


class TrayIcon:
    def __init__(
        self,
        on_quit: Callable,
        language: str = "zh",
        on_open_settings: Optional[Callable] = None,
    ):
        self._on_quit = on_quit
        self._language = language
        self._on_open_settings = on_open_settings
        self._icon: Optional[pystray.Icon] = None
        self._current_state = "idle"

    def set_state(self, state: str):
        self._current_state = state
        if self._icon and state in _ICONS:
            self._icon.icon = _ICONS[state]
            self._icon.title = STATES[state]["title"][self._language]

    def update_language(self, lang: str):
        self._language = lang
        if self._icon:
            self._icon.menu = self._build_menu()
            self._icon.title = STATES[self._current_state]["title"][lang]

    def run(self):
        self._icon = pystray.Icon(
            "stt_local",
            _ICONS["idle"],
            STATES["idle"]["title"][self._language],
            menu=self._build_menu(),
        )
        self._icon.run()

    def _build_menu(self) -> pystray.Menu:
        s = MENU_STRINGS[self._language]
        items = []
        if self._on_open_settings:
            items.append(pystray.MenuItem(s["settings"], self._open_settings))
        items.append(pystray.MenuItem(s["quit"], self._quit))
        return pystray.Menu(*items)

    def _open_settings(self, icon, item):
        if self._on_open_settings:
            self._on_open_settings()

    def _quit(self, icon, item):
        icon.stop()
        self._on_quit()

    def stop(self):
        if self._icon:
            self._icon.stop()
