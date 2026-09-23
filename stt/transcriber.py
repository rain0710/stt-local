import numpy as np
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(
        self,
        model: str = "base",
        language: str = "zh",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        self._model_size = model
        self._language = language if language != "auto" else None
        self._device = device
        self._compute_type = compute_type
        self._model = None
        self._ready = threading.Event()

    def load_async(self):
        def _load():
            try:
                # 惰性导入：纯云端 API 模式无需安装 faster-whisper
                from faster_whisper import WhisperModel
                logger.info(f"Loading Whisper model '{self._model_size}'...")
                self._model = WhisperModel(
                    self._model_size,
                    device=self._device,
                    compute_type=self._compute_type,
                )
                self._ready.set()
                logger.info("Model ready")
            except Exception:
                logger.exception("Failed to load model")
        threading.Thread(target=_load, daemon=True).start()

    def transcribe(self, audio: np.ndarray, timeout: float = 30.0) -> str:
        if not self._ready.wait(timeout=timeout):
            logger.error("Model not ready (timeout)")
            return ""
        if len(audio) < 1600:
            logger.info("Audio too short, skipped")
            return ""
        prompt = "以下是普通话语音，请在适当位置加上标点符号，例如逗号、句号、问号。" if self._language == "zh" else None
        try:
            segments, info = self._model.transcribe(
                audio,
                language=self._language,
                beam_size=1,
                without_timestamps=True,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
                initial_prompt=prompt,
            )
            text = "".join(seg.text for seg in segments).strip()
            logger.info(f"Transcribed ({info.language}): {text!r}")
            return text
        except Exception:
            logger.exception("Transcription failed")
            return ""
