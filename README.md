# AudioCenter - AI制作

Windows 音频控制面板，基于 Python + customtkinter 构建。

<p align="center">
  <img src="https://img.shields.io/badge/Windows-10%2F11-blue?style=flat-square&logo=windows" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-yellow?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
  <img src="https://github.com/1756490981/audiocenter/actions/workflows/ci.yml/badge.svg" />
</p>

---

## ⚠️ 后端源码状态

本项目分两层：

| 层 | 语言 | 是否在本仓库 |
|---|---|---|
| 界面层 | Python + customtkinter | ✅ 在 |
| 后端 | C# (.NET 8) → `AudioHelper.exe` | ⚠️ **在，但是反编译恢复的** |

所有真正的音频操作 —— 设备枚举、设为默认设备、修改设备格式、per-app 设备路由、
配置存档 —— 都由这个 C# 进程完成。Python 侧只负责画界面，通过 stdin/stdout 的
JSON 协议向它发 25 个命令（见 `audio.py`）。

**后端源码曾经不在本仓库**：它从未被提交过，原作者重装系统后本地也丢了，只存在于
编译产物里。现已从 `AudioCenter.exe` 内嵌的 `AudioHelper.exe` 反编译恢复，放在
[`AudioHelper/`](AudioHelper/) 目录，**可以正常构建和发布**，已验证与原版行为一致
（5 个核心命令输出逐字节相同）。

代价是这份代码**不好读**：没有注释、变量名是反编译器生成的、部分控制流被改写成
等价形式。改后端之前请先读 [`AudioHelper/README.md`](AudioHelper/README.md) ——
它详细说明了来源、验证情况和局限。

> 顺带说明：原作者 README 里那句「文件太大上传不了，从成品中手动提取
> `AudioHelper.exe` 补齐」是个误会。编译产物（67MB）确实不该进 git，但它本来就该
> 放 Release；而源码只有几十 KB，直接提交即可 —— 缺的从来不是 exe，是源码。

---

## 功能

- **音量混合器** — 主音量控制 + 每个应用独立音量/静音/输出设备
- **播放设备** — 查看、设为默认、调节音量、调整格式（采样率/位深度/通道）、启用/禁用
- **录制设备** — 同上，管理录音设备
- **高级功能** — 音频配置备份/恢复（含 per-app 设备路由）、一键最大音量、导入/导出
- **Studio One 一键修复** — ASIO 驱动选择、音频引擎设置自动写入、一键重启

完整操作说明见 [使用教程.md](使用教程.md)。

## 项目结构

```
audiocenter/
├── main.py                      # 主窗口、标题栏、Tab 切换、系统托盘
├── audio.py                     # AudioHelper 子进程管理（JSON stdin/stdout 协议）
├── themecolors.py               # 主题颜色定义
├── iconutil.py                  # 应用图标提取工具
├── icon.ico                     # 应用图标
├── build.py                     # 打包脚本（唯一入口，PyInstaller 参数都在这里）
├── build.bat                    # Windows 下调用 build.py 的包装脚本
├── requirements.txt             # Python 依赖
├── manual_check_device_routing.py  # 手动冒烟脚本（非 pytest 测试，见文件头注释）
├── sfx_config.txt               # 7-Zip SFX 打包模板（当前流程未使用）
├── 使用教程.md                   # 用户手册
├── tabs/
│   ├── mixer.py                 # 音量混合器
│   ├── playback.py              # 播放设备
│   ├── recording.py             # 录制设备
│   ├── profiles.py              # 配置管理（备份/恢复）
│   └── studio.py                # Studio One ASIO 修复
├── AudioHelper/                  # C# 后端源码（⚠️ 反编译恢复，见其中 README）
│   ├── AudioHelper.csproj
│   ├── app.manifest              # asInvoker —— 原作者未申请提权
│   ├── README.md                 # 来源、验证情况、反编译局限
│   └── src/
│       ├── Program.cs            # 25 个命令的分发与实现（2300 行）
│       ├── IPolicyConfig.cs      # per-app 设备路由（undocumented WinRT API）
│       └── *.cs                  # COM 接口定义 / PROPVARIANT / 数据模型
├── tools/
│   ├── check_imports.py         # CI：校验所有模块可导入
│   ├── fetch_audiohelper.py     # 兜底：源码缺失时从成品取得 AudioHelper.exe
│   └── extract_audiohelper.py   # 从 PyInstaller 成品中取出 AudioHelper.exe
└── .github/workflows/
    ├── ci.yml                   # 每次 push / PR
    └── release.yml              # 打 tag 时打包并发布
```

## 环境要求

- Windows 10 / 11
- Python 3.10+
- .NET 8 SDK（只在需要构建 C# 后端时；CI 里由 workflow 自动装，用成品
  `AudioCenter.exe` 则完全不需要）
- **管理员权限**：启用/禁用设备、修改设备格式等操作需要提权。打包出的
  `AudioCenter.exe` 会通过 UAC 自动请求提权；直接运行 `python main.py` 时
  请用管理员身份启动终端，否则音频服务会启动失败。

## 安装

```bash
git clone https://github.com/1756490981/audiocenter.git
cd audiocenter

pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

> 注意：仓库里**没有** `AudioHelper.exe`（它是构建产物，不应提交），所以直接
> `python main.py` 会停在「音频服务启动失败」。本地跑起来需要先构建它：
>
> ```bash
> dotnet publish AudioHelper/AudioHelper.csproj -c Release \
>   --self-contained true -r win-x64 -p:PublishSingleFile=true \
>   -o AudioHelper/bin/publish
> cp AudioHelper/bin/publish/AudioHelper.exe .
> python main.py
> ```

## 打包为 EXE

```bash
python build.py
```

或双击 `build.bat`（只是 `build.py` 的包装）。

输出文件：`dist/AudioCenter.exe`（约 47MB，已内嵌 AudioHelper 与图标）。

打包前需要项目根目录存在 `AudioHelper.exe`，构建方式见上一节。

## 发布流程

发布由 GitHub Actions 自动完成，不需要手动打包上传：

1. 打一个 `v` 开头的 tag 并推送：

   ```bash
   git tag v1.1
   git push origin v1.1
   ```

2. `.github/workflows/release.yml` 会自动：
   - 从 `AudioHelper/` 的 C# 源码 `dotnet publish` 构建 `AudioHelper.exe`
   - 用 `build.py` 打包出 `dist/AudioCenter.exe`
   - 创建 Release 并把 `AudioCenter.exe` 作为附件上传

也可以在 Actions 页面手动触发（`workflow_dispatch`），填入要发布的 tag。

> 构建后端需要 .NET 8 SDK。workflow 用的是 `actions/setup-dotnet@v4`
> （`dotnet-version: '8.0.x'`），不需要在本机装。
>
> 如果哪天又拿不到源码了，可以设置仓库变量 `AUDIOHELPER_URL`
> （Settings → Secrets and variables → Actions → Variables）指向一个直链，
> 或者在既有的 `audio` Release 里留一份成品 —— workflow 会退而从成品中取出
> `AudioHelper.exe`，源码构建的选择优先级更高。

## 核心功能说明

### Per-App 设备路由备份

Windows 的 per-app 音频路由（设置 → 声音 → 应用音量和设备首选项）在软件更新后可能被重置。

本工具通过 `IPolicyConfig` COM 接口的 `SetPersistedDefaultAudioEndpoint` API 实现：

1. **保存**：记录所有正在运行的音频应用及其输出设备（按进程名匹配）
2. **恢复**：自动查找当前运行中的应用 PID，按进程名匹配后恢复路由

保存时应用必须正在播放音频，恢复时应用也必须在运行中。

### Studio One ASIO 修复

自动检测 Studio One 安装位置和 ASIO 驱动，一键修改 `AudioEngine.settings` 配置文件，并优雅重启 Studio One（先发送 WM_CLOSE，避免强制关闭导致"上次没有正常关闭"提示）。

保存配置时，Studio One 的 ASIO 设置会作为 `<配置名>.asio` companion 文件一起存到
`%LOCALAPPDATA%\AudioCenter\profiles\`，恢复配置时一并写回。

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端 GUI | Python + customtkinter |
| 后端服务 | C# (.NET 8 self-contained) ← **反编译恢复，见 `AudioHelper/README.md`** |
| 音频 API | Windows Core Audio (pycaw / COM) |
| 设备路由 | IPolicyConfig (undocumented WinRT API) |
| ASIO 管理 | Windows Registry + XML 配置 |
| 打包 | PyInstaller --onefile |
| CI/CD | GitHub Actions |

## 许可证

MIT License

## 作者

纯 AI 生成
