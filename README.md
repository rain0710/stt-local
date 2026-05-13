# STT Local

**中文** | [English](#english)

---

## 中文

本地运行的 Push-to-Talk 语音转文字工具。按住快捷键说话，松开后文字自动粘贴到当前输入框。基于 [faster-whisper](https://github.com/SYSTRAN/faster-whisper)，支持 GPU 加速，完全离线运行。

### 功能特性

- **Push-to-Talk**：按住快捷键开始录音，松开后自动转写并粘贴文字
- **系统托盘图标**：三种状态实时显示——待命（绿）、录音中（红）、转录中（蓝）
- **GPU 加速**：支持 NVIDIA CUDA，RTX 系列显卡可将转写速度提升 6 倍以上
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

### 配置文件位置

安装版：`%APPDATA%\stt_local\config.yaml`  
开发版：项目根目录 `config.yaml`

### 从源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

### 重新打包

```powershell
# 需要已安装 Inno Setup 6（安装至 %LOCALAPPDATA%\InnoSetup6\）
.\build.ps1
```

---

## English

<a name="english"></a>

A local push-to-talk speech-to-text tool. Hold a hotkey to record, release to transcribe — text is automatically pasted into the active input field. Powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper), supports GPU acceleration, runs fully offline.

### Features

- **Push-to-Talk**: Hold hotkey to record, release to transcribe and paste
- **System Tray Icon**: Three real-time states — idle (green), recording (red), processing (blue)
- **GPU Acceleration**: NVIDIA CUDA support, 6× faster transcription on RTX GPUs
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

### Config File Location

Installed: `%APPDATA%\stt_local\config.yaml`  
Development: `config.yaml` in project root

### Run from Source

```bash
pip install -r requirements.txt
python main.py
```

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
  transcriber.py     faster-whisper wrapper with VAD filter
  injector.py        Clipboard-based text injection (Ctrl+V)
  tray.py            System tray icon with state-based icons (pystray + Pillow)
  settings.py        tkinter settings GUI, 4-tab layout
```

### Dependencies

| Package | Purpose |
|---------|---------|
| faster-whisper | Speech-to-text transcription |
| sounddevice | Microphone audio capture |
| pynput | Global keyboard hook |
| pystray | Windows system tray |
| Pillow | Tray icon rendering |
| PyYAML | Config file read/write |

### License

MIT
