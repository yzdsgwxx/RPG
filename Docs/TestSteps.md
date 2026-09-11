# PIE 测试步骤（第三人称角色）

> 本文档只描述**测试步骤**。按约定，PIE 由开发者执行，AI 不运行 PIE。

## 0. 前置状态（AI 已完成，供核对）

| 项目 | 状态 |
|---|---|
| UnrealSharp 插件 | 已部署在 `Plugins/UnrealSharp` |
| 项目 C++ 模块 | `Source/RPG`（含 `RPGCharacterBase` 包装类） |
| RPGEditor 目标 | 已编译成功 |
| C# 程序集 | `Script/ManagedRPG/`，已编译（0 错误 0 警告）并部署到 `Binaries/Managed/net10.0/` |
| 默认地图 | `Config/DefaultEngine.ini` 中 `GameDefaultMap` / `EditorStartupMap` = `/Game/NewMap` |
| 输入 | 传统 Action/Axis Mapping，`Config/DefaultInput.ini`；**未使用 EnhancedInput** |
| Lumen / Nanite | 已关闭 |

## 1. 打开工程

1. 双击 `D:\UnrealProjects\RPG\RPG.uproject`。
   - 若提示模块需要重新编译，选择「是」。
2. 编辑器打开后应停在 `NewMap`。
   - 若未停在 NewMap：**编辑 → 项目设置 → 地图和模式 → 默认地图**，确认
     `Editor Startup Map` 与 `Game Default Map` 均为 `NewMap`。

> ⚠️ 启动编辑器请从 Windows 环境（资源管理器 / VS / 快捷键）启动，
> **不要从 Git Bash 等 MSYS 环境启动**：UnrealSharp 依赖 PATH 中出现
> `C:\Program Files\dotnet\` 字面量来检测 .NET SDK，MSYS 会改写 PATH 导致
> 报“UnrealSharp can't be initialized. An installation of .NET 10.0.0 SDK can't be found.”

## 2. 确认角色已放入 NewMap

`ARPGCharacter` 是 C# 类，UnrealSharp 的命名为 **C# 类名去掉首字符**，
因此它在编辑器里显示为 **`RPGCharacter`**（可加载的类路径为
`/Script/UnrealSharp.RPGCharacter_C`，即 Blueprint 生成类）。

预期：`NewMap` 的**大纲（Outliner）**中存在一个名为 `RPGCharacter_C_0` 的 Actor，
细节面板中 `Auto Possess Player` = `Player 0`。

> 该放置已由 AI 通过 `Tools/place_character.py` 完成并保存（NewMap 已落盘）。
> 若事后丢失，在编辑器控制台（`~`）执行一次即可自动放置：

```
py "D:/UnrealProjects/RPG/Tools/place_character.py"
```

脚本会自动等待 UnrealSharp 加载完成后生成角色、设置 `Auto Possess Player = Player 0` 并保存地图。

## 3. 确认游戏模式

**项目设置 → 地图和模式 → 默认模式（Default GameMode）** 应指向
`ARPGGameMode`（编辑器显示为 `RPGGameMode`）。

该 GameMode 的 `DefaultPawnClass` 刻意留空（`default`），避免与关卡中已放置的
角色重复生成；`PlayerControllerClass` = `ARPGPlayerController`（显示为 `RPGPlayerController`）。

## 4. 运行 PIE

点击工具栏 **播放（Play）**，或按 `Alt+P`。

### 4.1 走路
- 不按任何修饰键，按 `W` / `A` / `S` / `D`。
- **预期**：角色以走路速度（默认 300 uu/s）在水平面移动；角色**转向移动方向**。

### 4.2 跑步
- 按住 `Left Shift` 的同时按 `W` / `A` / `S` / `D`。
- **预期**：移动速度提升到跑步速度（默认 600 uu/s）；松开 `Shift` 回到走路速度。

### 4.3 跳跃
- 按 `Space`。
- **预期**：角色起跳（跳跃初速默认 600）；松开 `Space` 提前结束上升。

### 4.4 鼠标控制视角
- 移动鼠标。
- **预期**：镜头绕角色旋转（左右偏航 + 上下俯仰）；
  **角色本体不随镜头转动**，仅当有移动输入时才朝移动方向转身。
- 鼠标应被锁定/隐藏在视口内（`DefaultViewportMouseCaptureMode` / `LockMode`）。

### 4.5 手柄（可选）
- 左摇杆移动、右摇杆转视角、A 键跳跃、按下左摇杆跑步。

## 5. 需要观察的日志

打开 **窗口 → 输出日志**，过滤 `LogUnrealSharp` 与 `RPGSetup`：

- 预期能看到类似
  `Compiling Blueprint '/Script/UnrealSharp.RPGCharacter'`
  等三条（Character / PlayerController / GameMode）。
- `[RPGSetup]` 行会说明角色是「已生成」还是「复用」。
- **不应出现** `Failed to find type`（出现则说明 C# 类型名与注册名不匹配）。

## 6. 常见问题排查

| 现象 | 排查方向 |
|---|---|
| 启动即报找不到 .NET SDK | 确认系统 PATH 含 `C:\Program Files\dotnet\`；从 Windows 环境启动编辑器 |
| 大纲里找不到 `RPGCharacter_0` | 在控制台运行 `Tools/place_character.py`；确认 `Binaries/Managed/net10.0/ManagedRPG.dll` 存在 |
| PIE 后角色不能动 | 确认关卡的 `RPGCharacter_0` 上 `Auto Possess Player = Player 0`；确认 GameMode 的 `DefaultPawnClass` 为空 |
| 视角不动 | 确认使用的是 legacy 输入映射（`Config/DefaultInput.ini` 中的 `Turn`/`LookUp`），且 `DefaultPlayerInputClass` 是 `/Script/Engine.PlayerInput` |
| 改了 C# 后不生效 | 重新运行 `BuildUserSolution`（见 `AGENTS.md` 4.0.1），或在编辑器内用 UnrealSharp 的构建/热重载 |
| `inherits from 'X' which does not inherit from 'UObject'` | `Script/ManagedRPG/ManagedRPG.csproj` 缺少对 `Binaries/Managed/net10.0/RPG.dll` 的引用 |
