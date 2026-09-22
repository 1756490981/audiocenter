# AudioHelper 源码说明

> **这批代码是反编译恢复的，不是原作者写的那一份。**

## 来源

`AudioHelper` 最初的 C# 源码从未提交到本仓库。它只以编译产物形式存在：
`AudioCenter.exe`（PyInstaller 单文件）内嵌的 `AudioHelper.exe`，以及 Release `audio`
里附带的成品。

原作者重装系统后本地源码也丢了，所以本目录下的代码是从那个编译产物反编译得来的：

```
AudioCenter.exe (PyInstaller 单文件)
  └─ AudioHelper.exe (67.6MB，.NET 自包含单文件)
       └─ AudioHelper.dll (97KB，业务代码本体)
            └─ ILSpy 反编译 → 本目录（src/）
```

## 与原版的关系

已验证行为一致，不是"猜的"：

| 验证项 | 结果 |
|---|---|
| `dotnet build -c Release` | 0 警告 0 错误 |
| `dotnet publish -c Release --self-contained true -r win-x64 -p:PublishSingleFile=true` | 产出 67.58MB（原版 67.57MB） |
| `list-devices` (render) | 输出逐字节一致 |
| `list-devices` (capture) | 输出逐字节一致 |
| `list-sessions` | 输出逐字节一致 |
| `get-master-volume` | 输出逐字节一致 |
| `list-profiles` | 输出逐字节一致 |

即：**功能等价，可以放心构建和发布。**

## 反编译带来的局限

改这份代码前需要知道它缺什么：

- **没有注释** —— 原作者写的一切说明、TODO、设计意图全部丢失
- **局部变量名是反编译器生成的**（`num`、`flag`、`array`、`text` 之类），可读性差
- **部分控制流被改写成等价但不同的形式**（`switch` 可能变成 `if` 链，`using` 被展开成
  try/finally，LINQ 查询被还原成方法调用）
- **`<>c`、`<>f__AnonymousType*`、`<PrivateImplementationDetails>` 是编译器生成物**
  的反编译残留，不是人写的代码，看着乱但编译需要，不要手动删
- **`app.manifest` 是 `level="asInvoker"`** —— 原作者从未申请过管理员权限。
  这也解释了为什么旧版文档里"双击会弹 UAC"从来是假的：整个程序不曾提权。
  提权现在由打包层 (`build.py` 的 `--uac-admin`) 负责。

## 建议

如果要长期维护，值得做一轮**人工重写**而不是在反编译代码上打补丁：

1. 把 `Program.cs`（2300 行）按 25 个命令拆开
2. 重新命名变量、补注释
3. `IPolicyConfig` / `IMMDeviceEnumerator` 等 COM 接口定义是标准 Win32 声明，
   可以直接对照 Windows SDK / [dotnet/runtime](https://github.com/dotnet/runtime)
   里的 `*.cs` 平台声明核对一遍

在那之前，这份代码是正确的、可用的，只是不好读。

## 构建

```bash
cd AudioHelper
dotnet publish -c Release --self-contained true -r win-x64 -p:PublishSingleFile=true
```

产物在 `bin/Release/net8.0-windows/win-x64/publish/AudioHelper.exe`，
仓库根目录的 `build.py` 会自动找到并使用它。
