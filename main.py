import copy
import ctypes
import os
import threading
import logging
import sys
from pathlib import Path


def _find_cuda_dir() -> str | None:
    """搜索 CUDA 12 DLL 目录，返回路径字符串；已在 PATH 中或未找到则返回 None。"""
    # 若 cublas 已在 PATH / System32 中，无需额外处理
    try:
        lib = ctypes.WinDLL("cublas64_12.dll")
        ctypes.windll.kernel32.FreeLibrary(lib._handle)
        return None
    except OSError:
        pass

    candidates: list[Path] = []

    # 1. NVIDIA CUDA Toolkit（读取 CUDA_PATH 环境变量，再手动枚举 v12.x）
    cuda_path_env = os.environ.get("CUDA_PATH", "")
    if cuda_path_env:
        candidates.append(Path(cuda_path_env) / "bin")
    toolkit_root = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / \
                   "NVIDIA GPU Computing Toolkit" / "CUDA"
    if toolkit_root.exists():
        for v in sorted(toolkit_root.iterdir(), reverse=True):
            candidates.append(v / "bin")

    # 2. 常见应用附带的 CUDA 运行时
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    candidates += [
        local / "JianyingPro" / "User Data" / "ComponentStore" / "onnxruntime_gpu" / "1.0.2",
        Path(r"C:\Program Files\Blackmagic Design\DaVinci Resolve"),
    ]

    # 3. PyTorch（如已安装）
    try:
        import site
        for sp in site.getsitepackages():
            candidates.append(Path(sp) / "torch" / "lib")
    except Exception:
        pass

    for d in candidates:
        if (Path(d) / "cublas64_12.dll").exists():
            return str(d)
    return None


# 启动时激活 CUDA（在 import yaml/stt 之前完成，确保 ctranslate2 能找到 DLL）
_cuda_dir = _find_cuda_dir()
if _cuda_dir:
    os.environ["PATH"] = _cuda_dir + os.pathsep + os.environ.get("PATH", "")

import yaml

from stt.hotkey import HotkeyListener
from stt.recorder import AudioRecorder
from stt.transcriber import Transcriber
from stt.api_transcriber import ApiTranscriber, DEFAULT_MODEL, DEFAULT_PROVIDER
from stt.injector import Injector
from stt.tray import TrayIcon
from stt.settings import open_settings_in_thread

_FROZEN = getattr(sys, "frozen", False)


def _appdata_dir() -> Path:
    return Path(os.environ.get("APPDATA", Path.home())) / "stt_local"


def _setup_logging():
    handlers = []
    if _FROZEN:
        d = _appdata_dir()
        d.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(d / "stt_local.log", encoding="utf-8"))
    else:
        # 控制台可能没有（pythonw）或编码为 GBK，尽量切到 UTF-8
        stream = sys.stdout or sys.stderr
        if stream is not None:
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
            handlers.append(logging.StreamHandler(stream))
        handlers.append(logging.FileHandler("stt_local.log", encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )


def _default_config() -> dict:
    has_cuda = _find_cuda_dir() is not None
    return {
        "hotkey": "space",
        "modifier": "left_ctrl",
        "auto_send": False,
        "ui_language": "zh",
        "backend": "local",
        "whisper": {
            "model": "base",
            "language": "zh",
            "device": "cuda" if has_cuda else "cpu",
            "compute_type": "float16" if has_cuda else "int8",
        },
        "api": {
            "provider": DEFAULT_PROVIDER,
            "base_url": "https://api.siliconflow.cn/v1",
            "api_key": "",
            "model": DEFAULT_MODEL,
            "language": "zh",
        },
        "audio": {
            "sample_rate": 16000,
            "device": None,
        },
    }


def _build_transcriber(cfg: dict, logger):
    """根据配置选择本地或云端后端，两者接口一致。"""
    backend = cfg.get("backend", "local")
    if backend == "api":
        api = cfg.get("api", {}) or {}
        logger.info("使用云端 API 后端：%s / %s",
                    api.get("base_url", ""), api.get("model", ""))
        return ApiTranscriber(
            base_url=api.get("base_url", ""),
            api_key=api.get("api_key", ""),
            model=api.get("model", DEFAULT_MODEL),
            language=api.get("language", "zh"),
        )
    w = cfg.get("whisper", {}) or {}
    logger.info("使用本地 faster-whisper 后端：%s", w.get("model", "base"))
    return Transcriber(
        model=w.get("model", "base"),
        language=w.get("language", "zh"),
        device=w.get("device", "cpu"),
        compute_type=w.get("compute_type", "int8"),
    )


def _get_config_path() -> Path:
    if _FROZEN:
        d = _appdata_dir()
        d.mkdir(parents=True, exist_ok=True)
        config_path = d / "config.yaml"
        if not config_path.exists():
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(_default_config(), f, allow_unicode=True,
                          default_flow_style=False, sort_keys=False)
        return config_path
    else:
        return Path("config.yaml")


def load_config(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _write_config(path: Path, cfg: dict):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def main():
    _setup_logging()
    logger = logging.getLogger(__name__)

    try:
        _main(logger)
    except Exception:
        logger.exception("STT 程序异常退出")
        raise


def _main(logger):
    config_path = _get_config_path()
    if not config_path.exists():
        logger.error("找不到 %s，请先创建配置文件。", config_path)
        sys.exit(1)

    cfg = load_config(config_path)
    a = cfg.get("audio", {})

    transcriber = _build_transcriber(cfg, logger)
    transcriber.load_async()

    recorder = AudioRecorder(
        sample_rate=a.get("sample_rate", 16000),
        device=a.get("device", None),
    )
    injector = Injector(
        auto_send=cfg.get("auto_send", False),
    )

    hotkey_ref: list[HotkeyListener] = []
    _settings_open = threading.Event()

    def on_press():
        logger.info("● 录音开始")
        tray.set_state("recording")
        try:
            recorder.start()
        except Exception:
            logger.exception("麦克风启动失败")
            tray.set_state("idle")

    def on_release():
        audio = recorder.stop()
        tray.set_state("processing")
        logger.info("■ 录音结束，转写中...")

        def _run():
            text = transcriber.transcribe(audio)
            if text:
                injector.inject(text)
                logger.info(">> %s", text)
            else:
                logger.info("未识别到内容")
            tray.set_state("idle")

        threading.Thread(target=_run, daemon=True).start()

    def on_save(new_cfg: dict):
        nonlocal cfg
        old_cfg = cfg
        cfg = new_cfg
        _write_config(config_path, new_cfg)

        if old_cfg.get("hotkey") != new_cfg.get("hotkey") or \
                old_cfg.get("modifier") != new_cfg.get("modifier"):
            hotkey_ref[0].stop()
            new_hl = HotkeyListener(
                key_name=new_cfg.get("hotkey", "F9"),
                modifier_name=new_cfg.get("modifier"),
                on_press=on_press,
                on_release=on_release,
            )
            hotkey_ref[0] = new_hl
            new_hl.start()

        injector._auto_send = new_cfg.get("auto_send", False)

        if old_cfg.get("ui_language") != new_cfg.get("ui_language"):
            tray.update_language(new_cfg.get("ui_language", "zh"))

        if (old_cfg.get("backend") != new_cfg.get("backend")
                or old_cfg.get("api") != new_cfg.get("api")
                or old_cfg.get("whisper") != new_cfg.get("whisper")):
            try:
                tray._icon.notify("STT", "识别参数已保存，重启后生效。")
            except Exception:
                pass

    def on_open_settings():
        if _settings_open.is_set():
            return
        _settings_open.set()
        open_settings_in_thread(
            copy.deepcopy(cfg),
            cfg.get("ui_language", "zh"),
            on_save=on_save,
            on_close=lambda: _settings_open.clear(),
        )

    tray = TrayIcon(
        on_quit=lambda: hotkey_ref and hotkey_ref[0].stop(),
        language=cfg.get("ui_language", "zh"),
        on_open_settings=on_open_settings,
    )

    hotkey = HotkeyListener(
        key_name=cfg.get("hotkey", "F9"),
        modifier_name=cfg.get("modifier", None),
        on_press=on_press,
        on_release=on_release,
    )
    hotkey_ref.append(hotkey)
    hotkey.start()

    key_desc = cfg.get("hotkey", "F9")
    if cfg.get("modifier"):
        key_desc = f"{cfg['modifier']}+{key_desc}"
    logger.info("STT 已启动，按住 [%s] 说话，松开转写。右键托盘图标退出。", key_desc)

    tray.run()  # 阻塞主线程，pystray 需要在主线程运行


if __name__ == "__main__":
    main()
