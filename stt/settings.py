import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import sounddevice as sd

from stt.api_transcriber import PROVIDER_PRESETS, pricing_for, query_balance

STRINGS = {
    "zh": {
        "title":          "STT 设置",
        "tab_hotkey":     "快捷键",
        "tab_whisper":    "语音识别",
        "tab_api":        "云端 API",
        "tab_audio":      "音频",
        "tab_ui":         "界面",
        "hotkey_key":     "触发键",
        "hotkey_mod":     "组合键",
        "mod_none":       "无",
        "auto_send":      "粘贴后自动发送 Enter",
        "whisper_model":  "模型大小",
        "whisper_lang":   "识别语言",
        "whisper_device": "推理设备",
        "compute_type":   "计算精度",
        "backend":        "识别后端",
        "backend_local":  "本地 faster-whisper",
        "backend_api":    "云端 API",
        "provider":       "平台预设",
        "base_url":       "Base URL",
        "api_key":        "API Key",
        "api_model":      "模型",
        "api_lang":       "识别语言",
        "pricing":        "参考价",
        "balance":        "账户余额",
        "query_balance":  "查询余额",
        "querying":       "查询中...",
        "audio_device":   "麦克风",
        "audio_default":  "系统默认",
        "ui_language":    "界面语言",
        "btn_save":       "保存",
        "btn_cancel":     "取消",
        "restart_needed": "以下设置需重启后生效：\n{fields}\n是否保存并继续？",
        "restart_title":  "需要重启",
    },
    "en": {
        "title":          "STT Settings",
        "tab_hotkey":     "Hotkey",
        "tab_whisper":    "Whisper",
        "tab_api":        "Cloud API",
        "tab_audio":      "Audio",
        "tab_ui":         "Interface",
        "hotkey_key":     "Trigger Key",
        "hotkey_mod":     "Modifier",
        "mod_none":       "None",
        "auto_send":      "Auto-send Enter after paste",
        "whisper_model":  "Model size",
        "whisper_lang":   "Language",
        "whisper_device": "Device",
        "compute_type":   "Compute type",
        "backend":        "Backend",
        "backend_local":  "Local faster-whisper",
        "backend_api":    "Cloud API",
        "provider":       "Provider",
        "base_url":       "Base URL",
        "api_key":        "API Key",
        "api_model":      "Model",
        "api_lang":       "Language",
        "pricing":        "Pricing",
        "balance":        "Balance",
        "query_balance":  "Refresh",
        "querying":       "Querying...",
        "audio_device":   "Microphone",
        "audio_default":  "System default",
        "ui_language":    "UI Language",
        "btn_save":       "Save",
        "btn_cancel":     "Cancel",
        "restart_needed": "These settings require restart:\n{fields}\nSave and continue?",
        "restart_title":  "Restart required",
    },
}

HOTKEY_KEYS   = ["F9", "F10", "F11", "F12", "CapsLock", "space",
                 "right_ctrl", "left_ctrl", "right_alt", "left_alt"]
HOTKEY_MODS   = [None, "left_ctrl", "right_ctrl", "left_alt", "right_alt",
                 "left_shift", "right_shift"]
WHISPER_MODELS  = ["tiny", "base", "small", "medium", "large-v3"]
WHISPER_LANGS   = ["zh", "en", "ja", "auto"]
WHISPER_DEVICES = ["cpu", "cuda"]
COMPUTE_TYPES   = ["int8", "float16", "float32"]
RESTART_FIELDS  = {"whisper.model", "whisper.language", "whisper.device", "whisper.compute_type"}


class SettingsWindow:
    def __init__(
        self,
        cfg: dict,
        lang: str,
        on_save: Callable[[dict], None],
        on_close: Callable[[], None],
    ):
        self._cfg = cfg
        self._lang = lang
        self._on_save_cb = on_save
        self._on_close_cb = on_close
        self._s = STRINGS[lang]
        self._balance_result = None

    def run(self):
        root = tk.Tk()
        self._root = root
        root.title(self._s["title"])
        root.resizable(False, False)
        root.attributes("-toolwindow", True)
        root.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self._build_ui(root)
        self._populate()

        root.update_idletasks()
        w, h = root.winfo_reqwidth(), root.winfo_reqheight()
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        root.mainloop()
        self._on_close_cb()

    # ── UI 构建 ─────────────────────────────────────────────────────

    def _build_ui(self, root: tk.Tk):
        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_tab_hotkey(nb)
        self._build_tab_whisper(nb)
        self._build_tab_api(nb)
        self._build_tab_audio(nb)
        self._build_tab_ui(nb)

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        tk.Button(btn_frame, text=self._s["btn_cancel"], command=self._on_cancel, width=10).pack(side="right", padx=(4, 0))
        tk.Button(btn_frame, text=self._s["btn_save"],   command=self._on_save_clicked, width=10).pack(side="right")

    def _build_tab_hotkey(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text=self._s["tab_hotkey"])
        f.columnconfigure(1, weight=1)

        tk.Label(f, text=self._s["hotkey_key"]).grid(row=0, column=0, sticky="w", padx=12, pady=8)
        self._var_key = tk.StringVar()
        ttk.Combobox(f, textvariable=self._var_key, values=HOTKEY_KEYS, state="readonly", width=20).grid(row=0, column=1, padx=12, sticky="w")

        tk.Label(f, text=self._s["hotkey_mod"]).grid(row=1, column=0, sticky="w", padx=12, pady=8)
        self._var_mod = tk.StringVar()
        mod_display = [self._s["mod_none"]] + [m for m in HOTKEY_MODS if m is not None]
        ttk.Combobox(f, textvariable=self._var_mod, values=mod_display, state="readonly", width=20).grid(row=1, column=1, padx=12, sticky="w")

        self._var_auto_send = tk.BooleanVar()
        tk.Checkbutton(f, text=self._s["auto_send"], variable=self._var_auto_send).grid(
            row=2, column=0, columnspan=2, sticky="w", padx=10, pady=8)

    def _build_tab_whisper(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text=self._s["tab_whisper"])
        f.columnconfigure(1, weight=1)

        rows = [
            (self._s["whisper_model"],  WHISPER_MODELS,  "_var_w_model"),
            (self._s["whisper_lang"],   WHISPER_LANGS,   "_var_w_lang"),
            (self._s["whisper_device"], WHISPER_DEVICES, "_var_w_device"),
            (self._s["compute_type"],   COMPUTE_TYPES,   "_var_w_compute"),
        ]
        for i, (label, values, attr) in enumerate(rows):
            tk.Label(f, text=label).grid(row=i, column=0, sticky="w", padx=12, pady=8)
            var = tk.StringVar()
            setattr(self, attr, var)
            ttk.Combobox(f, textvariable=var, values=values, state="readonly", width=20).grid(row=i, column=1, padx=12, sticky="w")

    def _build_tab_api(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text=self._s["tab_api"])
        f.columnconfigure(1, weight=1)

        tk.Label(f, text=self._s["backend"]).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4))
        self._var_backend = tk.StringVar()
        bf = tk.Frame(f)
        bf.grid(row=0, column=1, sticky="w", padx=12, pady=(10, 4))
        tk.Radiobutton(bf, text=self._s["backend_local"],
                       variable=self._var_backend, value="local").pack(side="left")
        tk.Radiobutton(bf, text=self._s["backend_api"],
                       variable=self._var_backend, value="api").pack(side="left", padx=12)

        tk.Label(f, text=self._s["provider"]).grid(
            row=1, column=0, sticky="w", padx=12, pady=6)
        self._provider_labels = {p["label"]: k for k, p in PROVIDER_PRESETS.items()}
        self._var_provider = tk.StringVar()
        self._cbo_provider = ttk.Combobox(
            f, textvariable=self._var_provider,
            values=list(self._provider_labels.keys()), state="readonly", width=28)
        self._cbo_provider.grid(row=1, column=1, padx=12, sticky="w")
        self._cbo_provider.bind("<<ComboboxSelected>>", self._on_provider_change)

        tk.Label(f, text=self._s["base_url"]).grid(
            row=2, column=0, sticky="w", padx=12, pady=6)
        self._var_base_url = tk.StringVar()
        tk.Entry(f, textvariable=self._var_base_url, width=46).grid(
            row=2, column=1, columnspan=2, padx=12, sticky="we")

        tk.Label(f, text=self._s["api_key"]).grid(
            row=3, column=0, sticky="w", padx=12, pady=6)
        self._var_api_key = tk.StringVar()
        tk.Entry(f, textvariable=self._var_api_key, width=46, show="\u2022").grid(
            row=3, column=1, columnspan=2, padx=12, sticky="we")

        tk.Label(f, text=self._s["api_model"]).grid(
            row=4, column=0, sticky="w", padx=12, pady=6)
        self._var_api_model = tk.StringVar()
        self._cbo_api_model = ttk.Combobox(
            f, textvariable=self._var_api_model, values=[], width=36)
        self._cbo_api_model.grid(row=4, column=1, padx=12, sticky="w")
        self._cbo_api_model.bind("<<ComboboxSelected>>",
                                 lambda e: self._update_pricing())
        self._cbo_api_model.bind("<KeyRelease>",
                                 lambda e: self._update_pricing())

        tk.Label(f, text=self._s["api_lang"]).grid(
            row=5, column=0, sticky="w", padx=12, pady=6)
        self._var_api_lang = tk.StringVar()
        ttk.Combobox(f, textvariable=self._var_api_lang, values=WHISPER_LANGS,
                     state="readonly", width=12).grid(
            row=5, column=1, padx=12, sticky="w")

        ttk.Separator(f, orient="horizontal").grid(
            row=6, column=0, columnspan=3, sticky="we", padx=12, pady=10)

        tk.Label(f, text=self._s["pricing"]).grid(
            row=7, column=0, sticky="nw", padx=12, pady=6)
        self._lbl_pricing = tk.Label(f, text="\u2014", fg="#0a7a3c",
                                     justify="left", wraplength=330)
        self._lbl_pricing.grid(row=7, column=1, columnspan=2, sticky="w",
                               padx=12, pady=6)

        tk.Label(f, text=self._s["balance"]).grid(
            row=8, column=0, sticky="nw", padx=12, pady=6)
        bf2 = tk.Frame(f)
        bf2.grid(row=8, column=1, columnspan=2, sticky="w", padx=12, pady=6)
        tk.Button(bf2, text=self._s["query_balance"],
                  command=self._on_query_balance).pack(side="left")
        self._lbl_balance = tk.Label(bf2, text="\u2014", fg="#666",
                                     justify="left", wraplength=300)
        self._lbl_balance.pack(side="left", padx=10)

    def _on_provider_change(self, _event=None):
        key = self._provider_labels.get(self._var_provider.get())
        preset = PROVIDER_PRESETS.get(key, {})
        self._var_base_url.set(preset.get("base_url", ""))
        models = preset.get("models", [])
        self._cbo_api_model.config(values=models)
        if models:
            self._var_api_model.set(models[0])
        self._update_pricing()

    def _update_pricing(self, _event=None):
        if hasattr(self, "_lbl_pricing"):
            self._lbl_pricing.config(text=pricing_for(self._var_api_model.get()))

    def _on_query_balance(self):
        self._balance_result = None
        self._lbl_balance.config(text=self._s["querying"], fg="#666")
        base_url = self._var_base_url.get().strip()
        api_key = self._var_api_key.get().strip()

        def work():
            self._balance_result = query_balance(base_url, api_key)

        threading.Thread(target=work, daemon=True, name="balance-query").start()
        self._root.after(150, self._poll_balance)

    def _poll_balance(self):
        if self._balance_result is None:
            self._root.after(150, self._poll_balance)
            return
        ok, msg = self._balance_result
        self._balance_result = None
        self._lbl_balance.config(text=msg, fg=("#0a7a3c" if ok else "#c0392b"))

    def _build_tab_audio(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text=self._s["tab_audio"])
        f.columnconfigure(1, weight=1)

        self._audio_devices = self._query_input_devices()
        device_names = [d[0] for d in self._audio_devices]

        tk.Label(f, text=self._s["audio_device"]).grid(row=0, column=0, sticky="w", padx=12, pady=8)
        self._var_audio_dev = tk.StringVar()
        ttk.Combobox(f, textvariable=self._var_audio_dev, values=device_names, state="readonly", width=32).grid(row=0, column=1, padx=12, sticky="w")

    def _build_tab_ui(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text=self._s["tab_ui"])

        tk.Label(f, text=self._s["ui_language"]).grid(row=0, column=0, sticky="w", padx=12, pady=8)
        self._var_ui_lang = tk.StringVar()
        tk.Radiobutton(f, text="中文",    variable=self._var_ui_lang, value="zh").grid(row=0, column=1, padx=6)
        tk.Radiobutton(f, text="English", variable=self._var_ui_lang, value="en").grid(row=0, column=2, padx=6)

    # ── 数据填充 ────────────────────────────────────────────────────

    def _populate(self):
        self._var_key.set(self._cfg.get("hotkey", "F9"))
        mod = self._cfg.get("modifier")
        self._var_mod.set(mod if mod else self._s["mod_none"])
        self._var_auto_send.set(self._cfg.get("auto_send", False))

        w = self._cfg.get("whisper", {})
        self._var_w_model.set(w.get("model", "base"))
        self._var_w_lang.set(w.get("language", "zh"))
        self._var_w_device.set(w.get("device", "cpu"))
        self._var_w_compute.set(w.get("compute_type", "int8"))

        saved_dev = self._cfg.get("audio", {}).get("device")
        matched = next((d[0] for d in self._audio_devices if d[1] == saved_dev),
                       self._audio_devices[0][0])
        self._var_audio_dev.set(matched)

        api = self._cfg.get("api", {}) or {}
        provider = api.get("provider")
        if provider not in PROVIDER_PRESETS:
            provider = "custom"
        preset = PROVIDER_PRESETS[provider]
        self._var_backend.set(self._cfg.get("backend", "local"))
        self._var_provider.set(preset["label"])
        self._var_base_url.set(api.get("base_url") or preset.get("base_url", ""))
        self._var_api_key.set(api.get("api_key", ""))
        self._cbo_api_model.config(values=preset.get("models", []))
        self._var_api_model.set(api.get("model", ""))
        self._var_api_lang.set(api.get("language", "zh"))
        self._update_pricing()

        self._var_ui_lang.set(self._cfg.get("ui_language", "zh"))

    # ── 事件处理 ────────────────────────────────────────────────────

    def _collect(self) -> dict:
        mod_val = self._var_mod.get()
        mod = None if mod_val == self._s["mod_none"] else mod_val

        audio_dev_idx = next(
            (d[1] for d in self._audio_devices if d[0] == self._var_audio_dev.get()),
            None,
        )
        provider = self._provider_labels.get(self._var_provider.get(), "custom")
        return {
            "hotkey":      self._var_key.get(),
            "modifier":    mod,
            "auto_send":   self._var_auto_send.get(),
            "ui_language": self._var_ui_lang.get(),
            "backend":     self._var_backend.get(),
            "whisper": {
                "model":        self._var_w_model.get(),
                "language":     self._var_w_lang.get(),
                "device":       self._var_w_device.get(),
                "compute_type": self._var_w_compute.get(),
            },
            "api": {
                "provider": provider,
                "base_url": self._var_base_url.get().strip(),
                "api_key":  self._var_api_key.get().strip(),
                "model":    self._var_api_model.get().strip(),
                "language": self._var_api_lang.get(),
            },
            "audio": {
                "sample_rate": self._cfg.get("audio", {}).get("sample_rate", 16000),
                "device":      audio_dev_idx,
            },
        }

    def _diff_restart_fields(self, new_cfg: dict) -> list:
        changed = []
        if self._cfg.get("backend") != new_cfg.get("backend"):
            changed.append("backend")
        if self._cfg.get("api", {}) != new_cfg.get("api", {}):
            changed.append("api")
        old_w = self._cfg.get("whisper", {})
        new_w = new_cfg.get("whisper", {})
        for key in ("model", "language", "device", "compute_type"):
            if old_w.get(key) != new_w.get(key):
                changed.append(f"whisper.{key}")
        return changed

    def _on_save_clicked(self):
        new_cfg = self._collect()
        restart_fields = self._diff_restart_fields(new_cfg)

        if restart_fields:
            fields_str = "\n".join(f"  · {f}" for f in restart_fields)
            msg = self._s["restart_needed"].format(fields=fields_str)
            if not messagebox.askyesno(self._s["restart_title"], msg, parent=self._root):
                return

        self._on_save_cb(new_cfg)
        self._root.destroy()

    def _on_cancel(self):
        self._root.destroy()

    # ── 辅助 ────────────────────────────────────────────────────────

    def _query_input_devices(self) -> list:
        result = [(self._s["audio_default"], None)]
        try:
            for i, d in enumerate(sd.query_devices()):
                if d["max_input_channels"] > 0:
                    result.append((f"{i}: {d['name']}", i))
        except Exception:
            pass
        return result


def open_settings_in_thread(
    cfg: dict,
    lang: str,
    on_save: Callable[[dict], None],
    on_close: Callable[[], None],
):
    win = SettingsWindow(cfg, lang, on_save, on_close)
    threading.Thread(target=win.run, daemon=True, name="settings-tk").start()
