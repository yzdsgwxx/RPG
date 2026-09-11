# RPG

基于 **Unreal Engine 5.8** + **UnrealSharp（C#/.NET 10）** 的第三人称 RPG 项目。

- 逻辑全部用 **C#**（`Script/ManagedRPG/`），C++ 仅保留最小宿主模块并提供少量工具函数
- 蓝图只放**视觉与资源引用**，不写逻辑
- 输入使用 **EnhancedInput**，不使用 GAS

> 项目的详细技术约定、目录规范、踩坑记录都在 **[AGENTS.md](AGENTS.md)**（AI 助手指令文件，
> 同时也是最完整的技术文档）。换机器后建议先通读一遍，尤其是第 4 章「环境与工具链」。

---

## 换机器后的起步步骤

### 0. 前置软件

| 软件 | 版本要求 | 说明 |
|---|---|---|
| Unreal Engine | **5.8** | 路径按 `D:\UE_5.8` 假定，装到别处需同步改脚本 |
| Visual Studio | **2022**（17.14） | 需 `.NET 桌面开发` + `使用 C++ 的游戏开发` 工作负载 |
| .NET SDK | **10.0.1xx**（如 10.0.103） | ⚠️ 波段有硬性要求，见下 |
| Git + Git LFS | 任意较新版本 | 二进制资产走 LFS，**必须装 Git LFS** |

**为什么只能用 .NET 10 的 1xx 波段**：每个 .NET SDK 会声明自己的最低 MSBuild 版本，
而 VS2022 的 MSBuild 是 17.14。`10.0.2xx` 及以上要求 MSBuild 18.0（只有 VS2026 满足），
在 VS2022 里会报 `找不到指定的 SDK "Microsoft.NET.Sdk"`。
`10.0.1xx` 波段最低只要 MSBuild 17.14，所以是唯一可用的选择。

**推荐的免管理员配法**（装到 D 盘，不污染 C 盘）：

1. 从 <https://dotnetcli.blob.core.windows.net/dotnet/Sdk/10.0.103/dotnet-sdk-10.0.103-win-x64.zip>
   下载 SDK zip，解压到 `D:\dotnet`
2. 设用户级环境变量，让 VS 的 SDK 解析器改从 `D:\dotnet` 取：
   ```powershell
   [Environment]::SetEnvironmentVariable(
       'DOTNET_MSBUILD_SDK_RESOLVER_CLI_DIR', 'D:\dotnet', 'User')
   ```
   改完**重启 VS** 才生效。
3. `Script/global.json` 已请求 `10.0.100` + `rollForward: latestFeature`，无需修改。

配好后两者各司其职（这是刻意设计）：
- **VS** 从 `D:\dotnet` 拿 10.0.103（MSBuild 17.14 能满足）
- **dotnet CLI / UnrealSharp 的 UAT 构建** 从 `C:\Program Files\dotnet` 拿 10.0.401

### 1. 克隆

**前置：必须安装 Git LFS**

```bash
git lfs install          # 只需一次
git clone <仓库地址> RPG
cd RPG
```

克隆约 400MB，其中 73 个二进制资产走 LFS。
**没装 LFS 的话，`.uasset` / `.umap` 会变成 130 字节的指针文件，工程打不开。**

> 若目标平台是 GitHub，需要走代理（国内直连会被重置）。注意 LFS 的实际
> 文件存在 `github-cloud.s3.amazonaws.com`，该域名**直连可用但走代理会断流**，
> 所以要分开配：
> ```bash
> git config --global http.proxy http://127.0.0.1:7899
> git config --global http.https://github-cloud.s3.amazonaws.com/.proxy ""
> ```
> 工蜂等国内平台通常无需代理。

**凭据**：GitHub 不接受账号密码做 git 认证，克隆/推送的密码栏要填
**Personal Access Token**（<https://github.com/settings/tokens>，权限勾
Contents: Read and write），否则会报 `Bad credentials` 或
`Password authentication is not supported`。

**LFS 拉取中断**时可单独重试（不会重下已完成的）：

```bash
git lfs pull
```

**验证克隆完整**（应输出 73）：

```bash
git lfs ls-files | wc -l
```

### 2. 启动编辑器（PATH 有讲究）

UnrealSharp 通过读取进程的 **`PATH` 环境变量**、查找含 `Program Files\dotnet\` 的条目
来判断 .NET SDK 是否可用。从 Git Bash / MSYS 直接启动会把 PATH 改写成
`/c/Program Files/dotnet` 形式，导致匹配失败并弹
"UnrealSharp can't be initialized"。

**用 PowerShell 启动**：

```powershell
$env:PATH = 'C:\Program Files\dotnet\;' +
            [Environment]::GetEnvironmentVariable('PATH','Machine') + ';' +
            [Environment]::GetEnvironmentVariable('PATH','User')
& 'D:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' 'D:\UnrealProjects\RPG\RPG.uproject'
```

首次打开时 UnrealSharp 会自动编译 C# 程序集（需要一两分钟）。

### 3. 验证工程正常

打开后确认：

- 能进入 `/Game/Maps/NewMap`
- World Outliner 里有 `RPGCharacter_0`（**不要删**，删了就没有 Pawn，输入会全无响应）
- 按 Play 后 WASD 能移动、鼠标能转视角、空格跳跃、Shift 加速

---

## 目录结构

```
RPG/
├── Source/RPG/              # C++ 宿主模块 + 工具函数（RPGCharacterBase、RPGTableRows）
├── Script/
│   ├── ManagedRPG/          # ★ 游戏逻辑 C# 代码（ARPGCharacter、ARPGGameMode…）
│   ├── RPG.RuntimeGlue/     # UnrealSharp 生成的胶水工程（一般不用手改）
│   └── global.json          # .NET SDK 版本约束（勿随意改，见上）
├── Config/                  # 引擎/输入/打包配置
├── Content/
│   ├── BP_RPG*.uasset       # 框架类蓝图（刻意放 /Game/ 根目录）
│   ├── Maps/NewMap.umap
│   ├── ControlRig/          # 第三人称模板的 Mannequin 资源
│   └── Data/ Blueprint/ …   # 按类型分类
├── Plugins/
│   ├── UnrealSharp/         # C# 脚本方案（已含源码）
│   └── UEEditorMCP/         # 编辑器自动化 MCP（含 FSharedString 兼容修复）
├── Tools/                   # 编辑器辅助 Python 脚本
└── Docs/TestSteps.md        # 各功能的测试步骤
```

**框架类蓝图刻意直接放 `/Game/` 根目录**（仿照 SBFC 工程的扁平管理），
其余资产按类型进子目录。详见 AGENTS.md 3.1 / 3.2。

---

## 打包

⚠️ **UnrealSharp 工程必须分两步打包** —— 引擎默认的 `Package Project`
**不会**打包 C# 程序集，漏掉第二步打出来的包会因为找不到托管程序集而启动失败。

1. **标准打包**：编辑器 `File → Package Project → Windows`，
   选一个**项目外**的输出目录（如 `D:\Builds\RPG`）
2. **发布 C# 程序集**：编辑器顶部 **UnrealSharp 工具栏 → Package Project**，
   在弹出的目录选择器里选**上一步输出目录的父目录**（如上一步输出到
   `D:\Builds\RPG\RPG.exe`，这里就选 `D:\Builds`）

第二步依赖第一步产出的 `RPG.exe`，选错目录会弹框提示找不到可执行文件。

命令行等价做法（便于脚本化）：

```bash
# 第一步
"D:/UE_5.8/Engine/Build/BatchFiles/RunUAT.bat" BuildCookRun \
  -project="D:/UnrealProjects/RPG/RPG.uproject" \
  -noP4 -platform=Win64 -clientconfig=Development \
  -cook -build -stage -pak -archive -archivedirectory="D:/Builds/RPG"

# 第二步
"D:/UE_5.8/Engine/Build/BatchFiles/RunUAT.bat" PackageProject \
  -ScriptDir="D:/UnrealProjects/RPG/Plugins/UnrealSharp/Build/Scripts" \
  -Project="D:/UnrealProjects/RPG/RPG.uproject" \
  -ArchiveDirectory="D:/Builds/RPG" \
  -UETargetType="Game" -UEBuildConfig="Development"
```

注意两版的 `ArchiveDirectory` 语义不同：编辑器版要给**父目录**，
命令行版直接给**含 exe 的目录**（源码里就是这么设计的）。

---

## 常见问题

**VS 里两个 C# 项目报"找不到指定的 SDK"**
→ .NET SDK 波段不对，见上面「0. 前置软件」。

**双击 .sln 用旧版 VS 打开**
→ `.sln` 的版本头被改写过。`RPG.sln` 应为 `# Visual Studio Version 17`。
若被改回 16，VSLauncher 会去找已不存在的 VS2019。

**按 Play 后键盘鼠标全无响应**
→ 多半是关卡里的 `BP_RPGCharacter` 实例被删了。
没有 Pawn 就没有 `SetupPlayerInput`，输入自然全无反应。
另一个可能是 `BP_RPGGameMode` 的「默认pawn类」没设为 `None`，
导致 GameMode 生成的占位 Pawn 抢走了控制权。

**鼠标上下视角反了**
→ `MouseY` 需要 Negate 修改器（鼠标上移是正值，而 `AddControllerPitchInput`
约定负值=抬头）。已在 `ARPGCharacter.BuildInputAssets` 里处理，勿去掉。

**外网访问 GitHub 慢**
→ 配置代理。本机开发时曾用 `127.0.0.1:7899`。

---

## 开发约定（摘要）

- 类名以 **RPG** 为标识（`ARPGCharacter`、`ARPGGameMode`）；
  C# 类的首字母 `A` 是刻意的 —— UnrealSharp 会去掉首字符作为 UE 侧类名
- 输入回调**必须**标 `[UFunction]` 且签名为 4 参数，否则按方法名找不到会崩溃
- DataTable 行结构**必须定义在 C++ 侧**（需继承 `FTableRowBase`）
- 资源路径用**软引用**（`TSoftObjectPtr`/`TSoftClassPtr`）+ 运行时动态加载
- 不要在 C# 构造函数里用 `typeof()` 引用其他 C# 类（时序问题会固化 null）

完整约定与踩坑记录见 **[AGENTS.md](AGENTS.md)**。
