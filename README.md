# STT Local

**中文** | [English](#english)

---

## 中文

Push-to-Talk 语音转文字工具。按住快捷键说话，松开后文字自动粘贴到当前输入框。支持两种后端：基于 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 的**本地离线模式**（可选 GPU 加速），以及 **OpenAI 兼容的云端 API 模式**（无需下载模型、无需显卡）。

### 功能特性

- **Push-to-Talk**：按住快捷键开始录音，松开后自动转写并粘贴文字
- **系统托盘图标**：三种状态实时显示——待命（绿）、录音中（红）、转录中（蓝）
- **GPU 加速**：支持 NVIDIA CUDA，RTX 系列显卡可将转写速度提升 6 倍以上
- **云端 API 模式**：可切换 OpenAI 兼容的云端 STT（如硅基流动），无需下载模型与显卡；界面实时显示模型**参考价**，并可**查询账户余额**
- **高精度转写**：使用 Whisper 模型（tiny / base / small / medium / large-v3 可选），支持中文、英文、日文及自动语言检测
- **自动断句**：在合适位置添加逗号、句号、问号等标点符号
- **图形设置界面**：右键托盘图标打开设置，支持中英文界面切换
- **热重载配置**：修改快捷键后无需重启，立即生效
- **自动发送**：可选粘贴文字后自动按 Enter 发送

### 安装

1. 从 [Releases](../../releases) 页面下载最新的 `stt_local_setup.exe`
2. 双击运行安装程序
3. 可选勾选"**启用 GPU 加速**"——安装程序会自动检测 CUDA；若未检测到，会给出下载指引
4. 安装完成后可选择立即启动

> **首次启动**：程序会自动从 HuggingFace 下载 Whisper 模型（base 约 150 MB，medium 约 1.5 GB），请保持网络畅通。

### GPU 加速配置（可选）

如需 GPU 加速，需提前安装：

1. [CUDA Toolkit 12.x](https://developer.nvidia.com/cuda-downloads)（NVIDIA 官网）
2. [cuDNN 8.x for CUDA 12](https://developer.nvidia.com/cudnn)（需要注册 NVIDIA Developer 账号）

安装后，在软件"设置 → 语音识别"中将推理设备改为 `cuda`，计算精度改为 `float16`。

无 GPU 或未安装 CUDA 时，程序默认使用 CPU 模式，`int8` 精度运行。

### 使用方法

1. 程序启动后最小化至系统托盘（右下角通知区域）
2. 将光标定位到任意文本输入框（聊天框、文档编辑器等）
3. **按住** `左 Ctrl + Space`（默认快捷键）开始说话
4. **松开**快捷键，文字自动转写并粘贴到输入框
5. 右键托盘图标 → **设置** 可修改所有配置

### 设置说明

| 选项 | 说明 |
|------|------|
| 触发键 / 组合键 | 自定义快捷键组合，修改后立即生效 |
| 粘贴后自动发送 Enter | 粘贴文字后自动按回车，适用于聊天软件 |
| 模型大小 | tiny（最快）→ large-v3（最准）|
| 识别语言 | zh / en / ja / auto（自动检测）|
| 推理设备 | cpu / cuda |
| 计算精度 | int8（CPU 推荐）/ float16（GPU 推荐）|
| 麦克风 | 选择录音设备，默认使用系统麦克风 |
| 界面语言 | 中文 / English |

### 云端 API 模式（可选）

除了本地 faster-whisper，还可以切换到**云端 STT API**——无需下载模型、无需显卡：

1. 右键托盘图标 → **设置** → **云端 API**
2. **识别后端** 选择「云端 API」
3. **平台预设** 选择「硅基流动 SiliconFlow」（已预填 Base URL 和模型）
4. 粘贴你的 **API Key**
5. 点 **保存**，然后重启程序

界面会实时显示当前模型的**参考价**，并可点「查询余额」查看账户额度（目前硅基流动支持，其他平台会自动降级提示）。

任何 **OpenAI 兼容** 的平台都可以用：把「平台预设」切到「自定义」，填入该平台的 Base URL、API Key 和模型名即可。

| 平台 | Base URL | 推荐模型 |
|------|----------|---------|
| 硅基流动 | `https://api.siliconflow.cn/v1` | `FunAudioLLM/SenseVoiceSmall` |
| OpenAI | `https://api.openai.com/v1` | `whisper-1` / `gpt-4o-mini-transcribe` |
| Groq | `https://api.groq.com/openai/v1` | `whisper-large-v3-turbo` |

> ⚠️ API Key 以**明文**保存在 `config.yaml` 中，请注意不要泄露或提交到仓库。

### 配置文件位置

安装版：`%APPDATA%\stt_local\config.yaml`  
开发版：项目根目录 `config.yaml`

### 从源码运行

```bash
# 仅使用云端 API（轻量，不含 faster-whisper）
pip install -r requirements-api.txt

# 或安装包含本地 faster-whisper 的完整依赖
pip install -r requirements.txt

# 运行
python main.py
```

> Windows 用户也可直接双击 `start_stt.bat`（静默启动，无控制台）或 `debug_stt.bat`（带控制台，便于排查）。

> Windows 中文环境下若 `pip` 读 requirements 报编码错误，请用 ASCII 版依赖文件（仓库内已是纯英文注释）。

### 重新打包

```powershell
# 需要已安装 Inno Setup 6（安装至 %LOCALAPPDATA%\InnoSetup6\）
.\build.ps1
```

---

## English

<a name="english"></a>

A push-to-talk speech-to-text tool. Hold a hotkey to record, release to transcribe — text is automatically pasted into the active input field. Two backends: **local offline** via [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (optional GPU acceleration), or a **cloud OpenAI-compatible API** (no model download, no GPU).

### Features

- **Push-to-Talk**: Hold hotkey to record, release to transcribe and paste
- **System Tray Icon**: Three real-time states — idle (green), recording (red), processing (blue)
- **GPU Acceleration**: NVIDIA CUDA support, 6× faster transcription on RTX GPUs
- **Cloud API Mode**: Optional OpenAI-compatible cloud STT (e.g. SiliconFlow) — no model download or GPU; shows live model **reference pricing** and can **query account balance**
- **High-accuracy Transcription**: Whisper models (tiny / base / small / medium / large-v3), supports Chinese, English, Japanese, and auto language detection
- **Auto Punctuation**: Inserts commas, periods, question marks at appropriate positions
- **Settings GUI**: Right-click tray icon to open settings, with Chinese/English UI toggle
- **Hot-reload Hotkeys**: Hotkey changes take effect immediately without restart
- **Auto-send**: Optionally press Enter automatically after pasting

### Installation

1. Download the latest `stt_local_setup.exe` from the [Releases](../../releases) page
2. Run the installer
3. Optionally check "**Enable GPU Acceleration**" — the installer auto-detects CUDA and provides download links if not found
4. Optionally launch the app immediately after installation

> **First launch**: The app automatically downloads the Whisper model from HuggingFace (base ~150 MB, medium ~1.5 GB). Ensure you have an internet connection.

### GPU Acceleration (Optional)

To enable GPU acceleration, install:

1. [CUDA Toolkit 12.x](https://developer.nvidia.com/cuda-downloads)
2. [cuDNN 8.x for CUDA 12](https://developer.nvidia.com/cudnn) (requires NVIDIA Developer account)

Then open Settings → Whisper → set Device to `cuda` and Compute Type to `float16`.

Without a GPU or CUDA, the app runs in CPU mode with `int8` precision by default.

### Usage

1. The app minimizes to the system tray (bottom-right notification area) on startup
2. Place the cursor in any text input field (chat box, document editor, etc.)
3. **Hold** `Left Ctrl + Space` (default hotkey) and speak
4. **Release** the hotkey — text is transcribed and pasted automatically
5. Right-click the tray icon → **Settings** to configure all options

### Settings Reference

| Option | Description |
|--------|-------------|
| Trigger Key / Modifier | Customize hotkey combo, effective immediately |
| Auto-send Enter | Press Enter after paste — useful for chat apps |
| Model Size | tiny (fastest) → large-v3 (most accurate) |
| Language | zh / en / ja / auto |
| Device | cpu / cuda |
| Compute Type | int8 (CPU) / float16 (GPU) |
| Microphone | Select recording device |
| UI Language | 中文 / English |

### Cloud API Mode (Optional)

Besides the local faster-whisper backend, you can switch to a **cloud STT API** — no model download, no GPU required:

1. Right-click the tray icon → **Settings** → **Cloud API**
2. Set **Backend** to **Cloud API**
3. Pick **Provider** = `SiliconFlow` (Base URL and model are prefilled)
4. Paste your **API Key**
5. **Save**, then restart the app

The UI shows the model's **reference pricing** live, and a **Refresh** button queries your account balance (supported by SiliconFlow; other providers degrade gracefully).

Any **OpenAI-compatible** provider works: choose `Custom` and fill in the provider's Base URL, API Key and model name.

| Provider | Base URL | Recommended model |
|----------|----------|-------------------|
| SiliconFlow | `https://api.siliconflow.cn/v1` | `FunAudioLLM/SenseVoiceSmall` |
| OpenAI | `https://api.openai.com/v1` | `whisper-1` / `gpt-4o-mini-transcribe` |
| Groq | `https://api.groq.com/openai/v1` | `whisper-large-v3-turbo` |

> ⚠️ The API Key is stored in **plain text** in `config.yaml` — keep this file private.

### Config File Location

Installed: `%APPDATA%\stt_local\config.yaml`  
Development: `config.yaml` in project root

### Run from Source

```bash
# Cloud-API-only (lightweight, no faster-whisper)
pip install -r requirements-api.txt

# Or the full set including the local faster-whisper backend
pip install -r requirements.txt

# Run
python main.py
```

> On Windows you can also double-click `start_stt.bat` (silent) or `debug_stt.bat` (with console for troubleshooting).

### Rebuild Installer

```powershell
# Requires Inno Setup 6 installed to %LOCALAPPDATA%\InnoSetup6\
.\build.ps1
```

### Architecture

```
main.py              Entry point, wires all modules together
stt/
  hotkey.py          Global keyboard hook (pynput WH_KEYBOARD_LL)
  recorder.py        Microphone input streaming (sounddevice)
  transcriber.py     faster-whisper wrapper with VAD filter (lazy import)
  api_transcriber.py Cloud (OpenAI-compatible) backend + presets + pricing/balance
  injector.py        Clipboard-based text injection (Ctrl+V)
  tray.py            System tray icon with state-based icons (pystray + Pillow)
  settings.py        tkinter settings GUI, 5-tab layout
```

### Dependencies

| Package | Purpose |
|---------|---------|
| faster-whisper | Local speech-to-text transcription (optional in API mode) |
| requests | Cloud API calls + balance query |
| numpy | Audio buffer handling |
| sounddevice | Microphone audio capture |
| pynput | Global keyboard hook |
| pystray | Windows system tray |
| Pillow | Tray icon rendering |
| PyYAML | Config file read/write |
| pywin32 | Clipboard injection |

### License

MIT
