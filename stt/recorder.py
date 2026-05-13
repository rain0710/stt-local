import sounddevice as sd
import numpy as np
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AudioRecorder:
    def __init__(self, sample_rate: int = 16000, device: Optional[int] = None):
        self._sr = sample_rate
        self._device = device
        self._buffer: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._stream: Optional[sd.InputStream] = None
        self._recording = False

    def start(self):
        with self._lock:
            self._buffer.clear()
            self._recording = True
        self._stream = sd.InputStream(
            samplerate=self._sr,
            channels=1,
            dtype="float32",
            device=self._device,
            callback=self._callback,
            blocksize=1024,
        )
        self._stream.start()
        logger.info("Recording started")

    def _callback(self, indata: np.ndarray, frames: int, time, status):
        if status:
            logger.warning(f"Audio status: {status}")
        if self._recording:
            with self._lock:
                self._buffer.append(indata[:, 0].copy())

    def stop(self) -> np.ndarray:
        self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        with self._lock:
            if not self._buffer:
                return np.zeros(0, dtype=np.float32)
            audio = np.concatenate(self._buffer).astype(np.float32)
        logger.info(f"Recording stopped: {len(audio) / self._sr:.2f}s")
        return audio
