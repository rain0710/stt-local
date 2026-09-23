; STT Local — Inno Setup 安装脚本

[Setup]
AppName=STT Local
AppVersion=1.0.0
AppPublisher=Local Build
AppId={{B8E4A7F3-2C1D-4E8B-9F5A-6D3E7C8B1A2F}
DefaultDirName={localappdata}\stt_local
DisableDirPage=yes
DefaultGroupName=STT Local
OutputDir=dist
OutputBaseFilename=stt_local_setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\stt_local.exe
UninstallDisplayName=STT Local
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
DisableWelcomePage=no
ShowLanguageDialog=no
AppComments=Push-to-talk 语音转文字工具（faster-whisper）

[Tasks]
Name: desktopicon; Description: "创建桌面快捷方式"; GroupDescription: "附加图标："
Name: startup;     Description: "开机自动启动";   GroupDescription: "启动选项："; Flags: unchecked
Name: enable_gpu;  Description: "启用 GPU 加速（需要 NVIDIA 显卡 + CUDA 12 + cuDNN 8）"; GroupDescription: "性能选项："; Flags: unchecked

[Files]
Source: "dist\stt_local\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\STT Local";       Filename: "{app}\stt_local.exe"; IconFilename: "{app}\stt_local.exe"
Name: "{userdesktop}\STT Local"; Filename: "{app}\stt_local.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "stt_local"; \
  ValueData: """{app}\stt_local.exe"""; \
  Tasks: startup; Flags: uninsdeletevalue

[Run]
Filename: "{app}\stt_local.exe"; \
  Description: "立即启动 STT Local"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill.exe"; Parameters: "/IM stt_local.exe /F"; RunOnceId: "KillProcess"; \
  Flags: skipifdoesntexist runhidden

[Code]

{ ── CUDA 检测 ──────────────────────────────────────────────── }

function FindCudaDir: String;
{ 返回含有 cublas64_12.dll 的目录路径，未找到返回空字符串 }
var
  v: Integer;
  TestPath: String;
  CudaEnv: String;
begin
  Result := '';

  { 1. CUDA_PATH 环境变量（NVIDIA Toolkit 安装后自动设置） }
  CudaEnv := GetEnv('CUDA_PATH');
  if (CudaEnv <> '') and FileExists(CudaEnv + '\bin\cublas64_12.dll') then
  begin
    Result := CudaEnv + '\bin';
    Exit;
  end;

  { 2. NVIDIA CUDA Toolkit 标准安装路径（v12.0 – v12.9，从新到旧） }
  for v := 9 downto 0 do
  begin
    TestPath := 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.' +
                IntToStr(v) + '\bin';
    if FileExists(TestPath + '\cublas64_12.dll') then
    begin
      Result := TestPath;
      Exit;
    end;
  end;

  { 3. JianyingPro（剪映）内置 CUDA 运行时 }
  TestPath := ExpandConstant('{localappdata}') +
              '\JianyingPro\User Data\ComponentStore\onnxruntime_gpu\1.0.2';
  if FileExists(TestPath + '\cublas64_12.dll') then
  begin
    Result := TestPath;
    Exit;
  end;

  { 4. DaVinci Resolve }
  TestPath := 'C:\Program Files\Blackmagic Design\DaVinci Resolve';
  if FileExists(TestPath + '\cublas64_12.dll') then
  begin
    Result := TestPath;
    Exit;
  end;
end;

{ ── 写入初始配置 ─────────────────────────────────────────────── }

procedure WriteInitialConfig(UseCuda: Boolean);
var
  ConfigDir, ConfigPath: String;
  Device, ComputeType, Content: String;
begin
  ConfigDir := ExpandConstant('{userappdata}\stt_local');
  ForceDirectories(ConfigDir);
  ConfigPath := ConfigDir + '\config.yaml';
  if FileExists(ConfigPath) then Exit;  { 重装时不覆盖用户已有配置 }

  if UseCuda then
  begin
    Device := 'cuda';
    ComputeType := 'float16';
  end else
  begin
    Device := 'cpu';
    ComputeType := 'int8';
  end;

  Content :=
    'hotkey: space'                      + #10 +
    'modifier: left_ctrl'               + #10 +
    'auto_send: false'                  + #10 +
    'ui_language: zh'                   + #10 +
    'backend: api'                      + #10 +
    'whisper:'                          + #10 +
    '  model: base'                     + #10 +
    '  language: zh'                    + #10 +
    '  device: '      + Device          + #10 +
    '  compute_type: ' + ComputeType    + #10 +
    'api:'                              + #10 +
    '  provider: siliconflow'           + #10 +
    '  base_url: https://api.siliconflow.cn/v1' + #10 +
    '  api_key: ""'                    + #10 +
    '  model: XingChenAGI/XingChenASR-V3.2' + #10 +
    '  language: zh'                    + #10 +
    'audio:'                            + #10 +
    '  sample_rate: 16000'              + #10 +
    '  device: null'                    + #10;

  SaveStringToFile(ConfigPath, Content, False);
end;

{ ── 安装后逻辑 ────────────────────────────────────────────────── }

procedure CurStepChanged(CurStep: TSetupStep);
var
  CudaDir: String;
  UseCuda: Boolean;
begin
  if CurStep <> ssPostInstall then Exit;

  UseCuda := WizardIsTaskSelected('enable_gpu');

  if UseCuda then
  begin
    CudaDir := FindCudaDir;
    if CudaDir <> '' then
    begin
      MsgBox(
        '已检测到 CUDA 运行库：' + #13#10 + CudaDir + #13#10 + #13#10 +
        'GPU 加速已启用，初始配置将使用 cuda 模式。',
        mbInformation, MB_OK
      );
    end else
    begin
      UseCuda := False;
      MsgBox(
        '未检测到 CUDA 12 运行库，程序将以 CPU 模式运行。' + #13#10 + #13#10 +
        '如需 GPU 加速，请手动安装以下两个组件，然后在软件"设置→语音识别"中将设备改为 cuda：' + #13#10 + #13#10 +
        '  1. CUDA Toolkit 12.x（必需）' + #13#10 +
        '     https://developer.nvidia.com/cuda-downloads' + #13#10 + #13#10 +
        '  2. cuDNN 8.x for CUDA 12（必需）' + #13#10 +
        '     https://developer.nvidia.com/cudnn' + #13#10 + #13#10 +
        '安装完成后，重新启动 STT Local 即可使用 GPU 加速。',
        mbInformation, MB_OK
      );
    end;
  end;

  WriteInitialConfig(UseCuda);
end;

{ ── 卸载时询问是否删除配置 ──────────────────────────────────── }

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if MsgBox(
      '是否同时删除用户配置和日志文件？' + #13#10 +
      ExpandConstant('({userappdata}\stt_local\)'),
      mbConfirmation, MB_YESNO
    ) = IDYES then
      DelTree(ExpandConstant('{userappdata}\stt_local'), True, True, True);
  end;
end;
