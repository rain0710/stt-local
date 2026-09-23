"""云端 STT 后端（OpenAI 兼容的 /v1/audio/transcriptions 接口）。

设计目标：接口与本地 `stt.transcriber.Transcriber` 完全一致，
因此 `main.py` 的录音 / 注入 / 托盘逻辑无需任何改动。

同时附带：
  - 平台预设（硅基流动 / OpenAI / Groq / 自定义）
  - 静态参考价表
  - 尽力而为的账户余额查询（硅基流动支持）
"""

import io
import wave
import logging
import threading
from typing import Optional

import numpy as np
import requests

logger = logging.getLogger(__name__)


# ── 平台预设 ──────────────────────────────────────────────────────
# 所有平台都走 OpenAI 兼容的 /audio/transcriptions，
# 差别只在 base_url / model。
PROVIDER_PRESETS = {
    "siliconflow": {
        "label": "硅基流动 SiliconFlow",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": [
            "XingChenAGI/XingChenASR-V3.2",
            "XingChenAGI/XingChenASR-V3.2-Ultra",
            "Qwen/Qwen3-ASR-1.7B",
            "FunAudioLLM/SenseVoiceSmall",
            "XingChenAGI/XingChenASR-Diarize-V3.0",
        ],
        "console": "https://cloud.siliconflow.cn/",
    },
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": [
            "whisper-1",
            "gpt-4o-transcribe",
            "gpt-4o-mini-transcribe",
        ],
        "console": "https://platform.openai.com/usage",
    },
    "groq": {
        "label": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            "whisper-large-v3",
            "whisper-large-v3-turbo",
            "distil-whisper-large-v3-en",
        ],
        "console": "https://console.groq.com/settings/usage",
    },
    "custom": {
        "label": "自定义（OpenAI 兼容）",
        "base_url": "",
        "models": [],
        "console": "",
    },
}

DEFAULT_PROVIDER = "siliconflow"
DEFAULT_MODEL = "XingChenAGI/XingChenASR-V3.2"


# ── 静态参考价（价格会变动，请以平台官网为准）────────────────────
MODEL_PRICING = {
    # 硅基流动当前免费的语音识别模型（以官网为准）
    "XingChenAGI/XingChenASR-V3.2-Ultra":  "免费（限时）— 以官网为准",
    "XingChenAGI/XingChenASR-V3.2":        "免费（限时）— 以官网为准",
    "XingChenAGI/XingChenASR-Diarize-V3.0": "免费（限时）— 说话人分离",
    "XingChenAGI/XingChenGSR-V1.0":        "免费（限时）",
    "Qwen/Qwen3-ASR-1.7B":                "免费（限时）— 以官网为准",
    "FunAudioLLM/SenseVoiceSmall":        "免费（限时）— 以官网为准",
    "FunAudioLLM/SenseVoice":             "免费（限时）— 以官网为准",
    # 其他平台
    "whisper-large-v3-turbo":      "约 $0.04/小时 — 以官网为准",
    "distil-whisper-large-v3-en":  "约 $0.02/小时 — 以官网为准",
    "whisper-large-v3":            "约 $0.111/小时（≈¥0.8/小时）— 以官网为准",
    "whisper-1":                   "约 $0.006/分钟（≈¥0.043/分钟）",
    "gpt-4o-transcribe":           "约 $0.006/分钟",
    "gpt-4o-mini-transcribe":      "约 $0.003/分钟",
}


def pricing_for(model: str) -> str:
    """返回给定模型的参考价文案（未知模型返回提示）。"""
    if not model:
        return "未知（请查阅平台官网）"
    key = model.strip().lower()
    # 长 key 优先，避免 "whisper-large-v3" 误匹配 "distil-whisper-large-v3-en"
    for m in sorted(MODEL_PRICING, key=len, reverse=True):
        if m.lower() in key:
            return MODEL_PRICING[m]
    return "未知（请查阅平台官网）"


# ── 音频编码 ──────────────────────────────────────────────────────
def _to_wav_bytes(audio: np.ndarray, sample_rate: int = 16000) -> bytes:
    """float32 [-1,1] 单声道 → 16-bit PCM WAV 字节。"""
    clipped = np.clip(audio, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


# ── 转写器 ────────────────────────────────────────────────────────
class ApiTranscriber:
    """OpenAI 兼容的云端转写器，接口与本地 Transcriber 对齐。"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        language: str = "zh",
        timeout: float = 60.0,
    ):
        self._base_url = (base_url or "").rstrip("/")
        self._api_key = (api_key or "").strip()
        self._model = model or DEFAULT_MODEL
        self._language = None if language in (None, "", "auto") else language
        self._timeout = timeout
        self._ready = threading.Event()
        self._ready.set()  # 云端后端无需预加载模型

    # 保持与本地 Transcriber 相同的接口
    def load_async(self):
        self._ready.set()

    def _endpoint(self) -> str:
        return f"{self._base_url}/audio/transcriptions"

    def _post(self, wav: bytes, use_language: bool):
        data = {"model": self._model}
        if use_language and self._language:
            data["language"] = self._language
        return requests.post(
            self._endpoint(),
            headers={"Authorization": f"Bearer {self._api_key}"},
            files={"file": ("audio.wav", wav, "audio/wav")},
            data=data,
            timeout=self._timeout,
        )

    def transcribe(self, audio: np.ndarray, timeout: float = 30.0) -> str:
        if len(audio) < 1600:
            logger.info("Audio too short, skipped")
            return ""
        if not self._base_url or not self._api_key:
            logger.error("云端 API 未配置（base_url / api_key 为空）")
            return ""

        wav = _to_wav_bytes(audio)
        try:
            resp = self._post(wav, use_language=True)
            # 部分平台不接受 language 参数 → 去掉后重试一次
            if resp.status_code == 400 and self._language and \
                    "language" in resp.text.lower():
                resp = self._post(wav, use_language=False)

            if resp.status_code >= 400:
                logger.error("API 转写失败 HTTP %s: %s",
                             resp.status_code, resp.text[:300])
                return ""

            payload = resp.json()
            text = (payload.get("text") or "").strip()
            logger.info("Transcribed (api/%s): %r", self._model, text)
            return text
        except Exception:
            logger.exception("API 转写异常")
            return ""


# ── 余额查询（尽力而为）───────────────────────────────────────────
def _extract_balance_fields(obj) -> dict:
    """递归提取所有 key 含 'balance' 的标量字段。"""
    out: dict = {}

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    walk(v)
                elif isinstance(v, (int, float, str)) and "balance" in k.lower():
                    out.setdefault(k, str(v))
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(obj)
    return out


def _format_balance(fields: dict) -> str:
    order = ["totalBalance", "balance", "chargeBalance"]
    parts = []
    for k in order:
        if k in fields:
            parts.append(f"{k}: {fields.pop(k)}")
    parts += [f"{k}: {v}" for k, v in fields.items()]
    return "  ".join(parts)


def query_balance(base_url: str, api_key: str, timeout: float = 10.0):
    """查询账户余额。

    返回 (success: bool, message: str)。
    平台不提供余额接口时优雅降级。
    """
    base_url = (base_url or "").rstrip("/")
    api_key = (api_key or "").strip()
    if not base_url or not api_key:
        return False, "请先填写 Base URL 和 API Key"

    # 硅基流动：GET {base_url}/user/info
    try:
        resp = requests.get(
            f"{base_url}/user/info",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
    except requests.exceptions.RequestException as e:
        logger.debug("余额查询失败: %s", e)
        return False, "网络错误，无法查询余额"

    # 硅基流动已下线该接口（HTTP 410 / code 20092）
    body = resp.text or ""
    if resp.status_code == 410 or "deprecated" in body.lower() or "20092" in body:
        return False, "该平台已下线余额查询接口，请到官网后台查看"
    if resp.status_code in (401, 403):
        return False, "API Key 无效或无权限"
    if resp.status_code == 404:
        return False, "该平台不支持余额查询，请到官网后台查看"
    if resp.status_code != 200:
        return False, f"查询失败（HTTP {resp.status_code}）"

    try:
        fields = _extract_balance_fields(resp.json())
    except Exception:
        return False, "接口返回无法解析"

    if not fields:
        return False, "接口可用，但未返回余额字段（请到官网后台查看）"
    return True, "余额：" + _format_balance(fields)
