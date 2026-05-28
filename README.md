# AudioCenter - 阿云音频制作

Windows 音频控制面板，基于 Python + customtkinter 构建。

## 功能

- **音量混合器** — 主音量控制 + 每个应用独立音量/静音/输出设备
- **播放设备** — 查看、设为默认、调节音量、调整格式（采样率/位深度/通道）、启用/禁用
- **录制设备** — 同上，管理录音设备
- **高级功能** — 音频配置备份/恢复（含 per-app 设备路由）、一键最大音量、导入/导出
- **Studio One 一键修复** — ASIO 驱动选择、音频引擎设置自动写入、一键重启

## 截图

<p align="center">
  <img src="https://img.shields.io/badge/Windows-10%2F11-blue?style=flat-square&logo=windows" />
  <img src="https://img.shields.io/badge/Python-3.14-yellow?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
</p>

## 项目结构

```
python_audiocenter/
├── main.py              # 主窗口、标题栏、Tab 切换
├── audio.py             # AudioHelper 子进程管理（JSON stdin/stdout 协议）
├── themecolors.py       # 主题颜色定义
├── iconutil.py          # 应用图标加载工具
├── icon.ico             # 应用图标
├── AudioHelper.exe      # C# 后端（需自行编译）
├── build.bat            # PyInstaller 打包脚本
├── requirements.txt     # Python 依赖
└── tabs/
    ├── mixer.py         # 音量混合器 Tab
    ├── playback.py      # 播放设备 Tab
    ├── recording.py     # 录制设备 Tab
    ├── profiles.py      # 高级功能 Tab（备份/恢复）
    └── studio.py        # Studio One ASIO 修复 Tab
```

## 环境要求

- Windows 10 / 11
- Python 3.10+
- 需要**管理员权限**运行（用于访问 Windows 音频策略 API）

## 安装

```bash
# 克隆仓库
git clone https://github.com/1756490981/python_audiocenter.git
cd python_audiocenter

# 安装依赖
pip install -r requirements.txt
```

## 编译 AudioHelper

AudioHelper 是 C# 编写的后端程序，通过 JSON 协议与 Python 前端通信。

```bash
cd audiocenter/AudioHelper
dotnet publish -c Release --self-contained true -r win-x64 -p:PublishSingleFile=true
```

编译产物在 `bin/Release/net8.0-windows/win-x64/publish/AudioHelper.exe`，复制到项目根目录即可。

## 运行

```bash
python main.py
```

## 打包为 EXE

```bash
build.bat
```

输出文件：`dist/AudioCenter.exe`（约 47MB，包含 AudioHelper）

## 核心功能说明

### Per-App 设备路由备份

Windows 的 per-app 音频路由（设置 → 声音 → 应用音量和设备首选项）在软件更新后可能被重置。

本工具通过 `IPolicyConfig` COM 接口的 `SetPersistedDefaultAudioEndpoint` API 实现：

1. **保存**：记录所有正在运行的音频应用及其输出设备（按进程名匹配）
2. **恢复**：自动查找当前运行中的应用 PID，按进程名匹配后恢复路由

保存时应用必须正在播放音频，恢复时应用也必须在运行中。

### Studio One ASIO 修复

自动检测 Studio One 安装位置和 ASIO 驱动，一键修改 `AudioEngine.settings` 配置文件，并优雅重启 Studio One（先发送 WM_CLOSE，避免强制关闭导致"上次没有正常关闭"提示）。

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端 GUI | Python + customtkinter |
| 后端服务 | C# (.NET 8 self-contained) |
| 音频 API | Windows Core Audio (pycaw / COM) |
| 设备路由 | IPolicyConfig (undocumented WinRT API) |
| ASIO 管理 | Windows Registry + XML 配置 |
| 打包 | PyInstaller --onefile |

## 许可证

MIT License

## 作者
纯  AI生成 
