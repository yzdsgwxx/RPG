# AGENTS.md — RPG 项目偏好设置

本文件是 `D:\UnrealProjects\RPG` 项目的 AI 助手指令文件，用于约定技术栈、目录结构、
编码规范与工程偏好。**每次在本项目对话都应遵循本文件**。

> 本文件是 ZCode 的工作区指令文件，会被自动加载。项目偏好只维护这一份。

---

## 0. 沟通与工作方式

- 默认使用**中文**回复，思考过程也用中文。
- **界面文案一律用中文**：任务清单（todo）条目、后台运行命令的描述文字，都用中文书写，
  不要出现英文条目。
- 修改代码前先读相关文件和调用链；不确定 API 时先搜索项目内已有用法，不要凭空造接口。
- 保持最小改动，不做无关重构；涉及多模块时先给计划再实现。
- 修改后需总结变更点、风险点和测试建议。

### 0.1 Git 操作全部由开发者执行（重要）

**AI 不执行任何 Git 命令的写操作/网络操作**，包括但不限于
`git add` / `git commit` / `git push` / `git pull` / `git clone` /
`git reset` / `git checkout` / `git rm` / `git lfs push` / `git remote` 等。

原因：Git 操作涉及账号凭据、远端仓库状态与不可逆的历史改写，
出错代价高（本次就曾因重建历史导致提交哈希变化、因 `.gitignore` 误配置
导致推送缺失插件源码）。这些由开发者自己掌控。

- **AI 可以做的**：只读地查看仓库状态以协助排查 ——
  `git status` / `git log` / `git diff` / `git ls-files` / `git ls-remote` /
  `git check-ignore` / `git lfs ls-files` 等**不改变任何状态**的命令。
- **AI 需要交付的**：把要执行的 Git 命令**写清楚给开发者**，
  注明每条命令的作用、预期输出与注意事项，由开发者自行执行。
- 涉及 `.gitignore` / `.gitattributes` 等**配置文件**的修改，AI 可以直接改文件
  （这属于脚本/配置编写），但改完后要说明影响，并由开发者决定何时提交。

### 0.2 访问 GitHub 一律走代理（重要）

**国内直连 GitHub 会被重置连接**（`Connection was reset` / `HTTP 000`），
所以访问 GitHub（含 `git clone` / `git push` / `curl` / `WebFetch` / API）
**必须固定走本机代理**：

```
http://127.0.0.1:7899
```

代理由**追云加速**（ZhuiYun）客户端提供。

- **操作前先探测端口**：若 `127.0.0.1:7899` 未监听，说明追云没开 ——
  **停下来提醒开发者“请先开启追云加速”**，不要硬重试、也不要改用直连（直连必定失败）。
- ⚠️ **git 全局配置里的代理端口可能是旧的**：本机曾出现
  `http.proxy = http://127.0.0.1:7890`（Clash 系默认端口），而追云实际监听 **7899**，
  导致 git 报 `Failed to connect to 127.0.0.1 port 7890`。
  已修正为 7899；若日后再遇端口类报错，先核对这三处是否一致：
  ```bash
  git config --global --get http.proxy     # 应为 http://127.0.0.1:7899
  (echo > /dev/tcp/127.0.0.1/7899) 2>/dev/null && echo "追云在 7899"
  ```
- **端口在监听也要验证代理真的能到 GitHub**：追云的节点/分流会失效，
  出现「端口通、Google 能开、但 github.com 返回 HTTP 000」的情况。
  此时**同样停下来提醒开发者切换节点**。探测方法：
  ```bash
  curl -sI -m 25 -x http://127.0.0.1:7899 -o /dev/null -w "%{http_code}\n" https://github.com/
  # 200/302 = 正常；000 = 当前节点不通，请开发者换节点
  # 排查时一并测 https://www.google.com/（判断是代理整体挂了还是仅 GitHub 分流坏了）
  # 以及直连 https://www.baidu.com/（判断本机网络本身是否正常）
  ```
- 命令行用法（Git 与 curl 都认这两个环境变量）：
  ```bash
  export https_proxy=http://127.0.0.1:7899 http_proxy=http://127.0.0.1:7899
  # 或只对单次 git 命令生效
  git -c http.proxy=http://127.0.0.1:7899 push
  ```
- 端口探测方法：
  ```bash
  (echo > /dev/tcp/127.0.0.1/7899) 2>/dev/null && echo "代理在" || echo "代理未开"
  ```
- ⚠️ **本项目使用 Git LFS** 存储二进制资产（`.uasset`/`.umap`/贴图/音频/模型等）。
  **LFS 追踪规则写在仓库根的 `.gitattributes` 里，必须随仓库提交** ——
  一旦该文件丢失，其他机器克隆后拿到的是 130 字节指针文件，工程直接打不开
  （本仓库踩过这个坑：曾有工具把 `.gitignore` 替换成通用模板，需警惕同类工具
  是否也会动 `.gitattributes`）。

  **LFS 的已知坑**（推送/克隆前先看这段）：
  1. **单次 batch 上限 100 个对象** —— 首次提交有 133 个 LFS 文件，
     `git push` 会报 `batch response: More than 100 objects specified.`。
     绕法是按每批 ~35 个 `git lfs push origin --object-id ...` 分批上传，
     最后 `git push --no-verify` 跳过多余校验。
  2. **LFS 上传走 `github-cloud.s3.amazonaws.com`，经代理频繁断流**
     （`LFS: Put "...": EOF`），需配成「GitHub 走代理、S3 域名直连」：
     ```bash
     git config --global http.proxy http://127.0.0.1:7899
     git config --global http.https://github-cloud.s3.amazonaws.com/.proxy ""
     ```
  3. **LFS 对象不随仓库分发**：`.gitattributes` 一旦丢失（本仓库就发生过），
     其他机器克隆后拿到的是 130 字节指针文件，工程直接打不开。
  4. 最终压垮的一根稻草：历史引用的 151 个 LFS 对象中**丢失了 17 个**，
     历史已不完整，无法用 `git lfs migrate export` 完整转换。

  当前 LFS 用量约 400MB。注意 GitHub 免费账号 LFS 配额是
  **1GB 存储 + 1GB/月下载流量**，每次完整克隆都会消耗流量。
  第 3 点已通过「把 `.gitattributes` 提交进仓库」缓解。
  另注：本仓库当前只有**单个提交、73 个 LFS 对象**（低于 100），
  所以普通 `git push` 即可；将来若一次加入大量资产导致对象数超 100，
  才需要上面第 1 点的分批上传。
- **例外**：`dotnetcli.blob.core.windows.net`（.NET SDK 下载源）直连可用但很慢
  （约 65KB/s），走代理可到约 1MB/s；下载大文件时优先走代理。
  其余微软域名（`dotnet.microsoft.com`、`builds.dotnet.microsoft.com`）直连与代理均不通，
  改用 `dotnetcli.blob.core.windows.net` 下的等价路径。

> ⚠️ **诊断命令的坑（本机踩过，浪费了很多轮）**：
> 在 Git Bash 下 `curl -o /dev/null` 与 `curl -o /tmp/x` **会写入失败并返回 HTTP 000**，
> 从而把"网络正常"误判成"代理节点不通"。
> **判定连通性时不要用 `-o` 重定向**，直接看输出或用 `-s` + 管道：
> ```bash
> curl -s -m 25 -x http://127.0.0.1:7899 "https://github.com/" | head -c 80
> # 能打出 HTML 就说明通
> ```
> 另外 `curl -I`（HEAD）也可能被节点拦成 000，测连通性一律用 GET。

### 0.3 职责边界：AI 只写 C++ / C#，编辑器操作全部由开发者执行（重要）

**AI 对编辑器只读，唯一的写权限是 C++ / C# 脚本。**

- **AI 负责**：编写与修改 `Source/RPG/`（C++）、`Script/ManagedRPG/`（C#）下的脚本代码。
  为了让代码写得准确，允许**只读**地查询编辑器 —— 读关卡 Actor、读资产清单、
  读蓝图属性、读日志、编译（UBT / `dotnet build` / UnrealSharp 的 `BuildUserSolution`）。

  AI 可用的只读探查手段：

  | 手段 | 典型用途 |
  |---|---|
  | MCP `editor.get_actors` / `editor.find_actors` | 关卡里有哪些 Actor、位置与类 |
  | MCP `editor.list_assets` | 资产存不存在、路径与类 |
  | MCP `blueprint.get_summary` / `blueprint.describe_full` | 蓝图父类、变量、组件、默认值 |
  | MCP `editor.get_logs` / `ue-editor-mcp-logs` | 运行时日志、报错 |
  | 读 `Saved/Logs/*.log` | 历史 PIE 记录、UnrealSharp 加载情况 |
  | 读 `Intermediate/UnrealSharp/UHT/**/*.generated.cs` | C# 侧到底有哪些 API 可用 |
  | 读 `D:\UE_5.8\Engine\Source\...\*.h` | 引擎类是否 `UFUNCTION`、属性是否 `config` |
  | `dotnet build` / UAT `BuildUserSolution` | 编译校验（不碰编辑器状态） |
- **开发者负责**：其余一切编辑器操作。包括但不限于
  放置/删除 Actor、保存关卡、创建与修改蓝图资产、配置蓝图 Class Defaults 与组件、
  建 DataTable / DataAsset / 结构体资产、改项目设置与编辑器偏好、运行 PIE。

**因此 AI 不得调用任何会修改编辑器状态的操作**，例如
`blueprint.spawn_actor`、`editor.save_all`、`editor.delete_actor`、
`blueprint.*` 的写操作、`editor.start_pie` 等 MCP 写动作，以及
`UnrealEditor-Cmd.exe -ExecCmds="py ..."` 这类会落盘的脚本。

**交付方式**：AI 完成代码后，必须明确列出**开发者需要在编辑器里执行的操作清单**
（操作路径 + 具体值 + 预期结果）以及**测试步骤**（见第 6 节），
由开发者照着做。不要自己动手改编辑器状态。

> 例：需要"把角色放进关卡"时，AI 不自己生成实例，而是写明
> "打开 `/Game/Maps/NewMap` → 从 `/Game/` 拖入 `BP_RPGCharacter` → 放到 PlayerStart 上方
> → 设置 `AutoPossessPlayer = Player0` → 保存关卡"。

## 1. 项目概况

- 项目名：`RPG`，路径 `D:\UnrealProjects\RPG`
- 引擎：**Unreal Engine 5.8**（`D:\UE_5.8`，Installed Engine Build）
- 脚本方案：**UnrealSharp**（C# / .NET 10），插件位于 `Plugins\UnrealSharp`
- 语言分工：**逻辑一律用 C#**；C++ 仅保留最小项目模块（`Source\RPG`）作为 UnrealSharp 宿主
- 地图：`NewMap`（`/Game/NewMap`），同时作为编辑器启动地图与游戏默认地图

## 2. 硬性技术约定

### 2.1 不使用 GAS
- **不使用** GameplayAbilitySystem（`GameplayAbilities` 等插件）。
- 原因：该插件被 SmartObjects、MLAdapter、GameplayBehaviors、TargetingSystem 等多个引擎插件依赖，
  强行禁用会引发插件依赖链报错，因此**保持插件启用但在项目中不引用**。
- 技能/Buff/属性系统自行实现（C# 组件或数据驱动），不要引入 GAS 概念与类。

### 2.2 输入使用 EnhancedInput

**项目统一使用 EnhancedInput，不再使用传统 Action/Axis Mapping。**

原因：编辑器会把 `UInputSettings::DefaultPlayerInputClass` 强制改回
`/Script/EnhancedInput.EnhancedPlayerInput`。在 `Config/DefaultInput.ini` 里改成
`Engine.PlayerInput` 会在编辑器保存设置时被覆盖，所以顺着引擎走更省事。

实现分工（见 `Source/RPG/RPGCharacterBase.h/.cpp` 与 `Script/ManagedRPG/ARPGCharacter.cs`）：

- **C++ 侧**（`ARPGCharacterBase`）：只提供**原子工具**，不碰按键表 ——
  `CreateInputAction` / `CreateMappingContext` / `MapKey` / `AddMappingContext`。
  之所以需要这几个包装：
  - `UInputAction::ValueType` 是 `BlueprintReadOnly`，C# 侧不便赋值；
  - `UInputMappingContext::MapKey` 返回 `FEnhancedActionKeyMapping&`，C# 侧不好接；
  - `ULocalPlayer::GetSubsystem<T>()` 是 C++ 模板、未反射，C# 拿不到子系统。
- **C# 侧**（`ARPGCharacter`）：**按键表与绑定逻辑全在这里**（`BuildInputAssets`），
  用 `UEnhancedInputComponent.BindAction(...)` 绑定回调。

> ⚠️ C++ 的 `BP_` 前缀函数在 C# 里会**去掉前 3 个字符**：
> `BP_CreateInputAction` → C# 的 `CreateInputAction`。写代码时别照抄带前缀的名字。

按键映射（写在 C# 的 `BuildInputAssets`，改需求只动 C#）：

| Action | 类型 | 按键 |
|---|---|---|
| `IA_MoveForward` | Axis1D | `W` / `S`(Negate) / 手柄左摇杆 Y |
| `IA_MoveRight` | Axis1D | `D` / `A`(Negate) / 手柄左摇杆 X |
| `IA_LookYaw` | Axis1D | 鼠标 X / 手柄右摇杆 X |
| `IA_LookPitch` | Axis1D | 鼠标 Y / 手柄右摇杆 Y |
| `IA_Jump` | Boolean | `Space` / 手柄 A |
| `IA_Sprint` | Boolean | `LeftShift` / 手柄左摇杆按下 |

**绑定 EnhancedInput 回调必须满足两点，否则触发时崩：**

1. **标 `[UFunction]`**。UnrealSharp 只把方法名传给 UE 侧，native 调用的是
   `InputComponent->BindAction(Action, TriggerEvent, Object, FunctionName)`，
   UE 再按名字查找 UFUNCTION（见 `Bind_UEnhancedInputComponent.cpp`）。
   普通 C# 方法不会注册成 UFUNCTION，触发时会报
   `Failed to find function XXX` 并导致 PIE 致命错误。
2. **签名必须是 4 参数**：`(FInputActionValue, float, float, UInputAction)`，
   对应 UE 的 `FEnhancedInputActionHandlerDynamicSignature`。
   取值用 `FInputActionValue.GetAxis1D()` / `GetAxis2D()` / `GetAxis3D()`。
3. 触发时机用 `ETriggerEvent`：持续输入用 `Triggered`；Boolean 按键用
   `Started`（按下）/ `Completed`（松开）。

> 历史备注：本项目曾用传统 `BindAxis`/`BindAction` + `Config/DefaultInput.ini` 的
> `+ActionMappings`/`+AxisMappings`，该方案已废弃。传统绑定的回调**同样**必须标
> `[UFunction]`（同样是按方法名查找），这一点与输入方案无关。

### 2.3 蓝图：只用于视觉/资源引用配置，不写逻辑

**类结构是「C# 类 + 蓝图子类」两层：**

| 层 | 放什么 | 例子 |
|---|---|---|
| C# 类（`Script/ManagedRPG/`） | **全部逻辑**：输入、移动、数值、状态机 | `ARPGCharacter` |
| 蓝图子类（`/Game/Blueprint/Actor/`） | **视觉与资源引用**：网格体、动画蓝图、材质、特效、可调数值 | `BP_RPGCharacter` |

**为什么视觉放蓝图**：UnrealSharp 的 C# 类属性默认值写在 C# 构造函数里，
编辑器对 C# 类 CDO 的改动**不会持久化**（每次重新生成类就丢）；
而蓝图资产的默认值会随资产保存。所以"美术/策划要调"的东西一律放蓝图。

做法：C# 类用 `[UProperty(PropertyFlags.EditDefaultsOnly)]` 暴露可配置项，
蓝图子类里填具体资产，然后把**蓝图实例**放进关卡（不要直接放 C# 类实例）。

**仍然不进蓝图的东西**：任何逻辑（连线、分支、计算）。蓝图层里只有资产引用和数值，
不要出现 EventGraph 逻辑 —— 逻辑依然全在 C#。

现成范例：
- 蓝图 `/Game/Blueprint/Actor/BP_RPGCharacter`（父类 = C# 的 `RPGCharacter`）
- 生成脚本 `Tools/make_rpg_character_bp.py`（幂等，可重跑）

### 2.4 类名前缀
- 所有自建类以 **`RPG`** 为标识，例如：
  - `ARPGCharacter`（角色）
  - `ARPGPlayerController`（玩家控制器）
  - `ARPGGameMode`（游戏模式）
- C# 中 UE 基类保留原前缀（`ACharacter`、`AActor`、`UObject` 等）。

### 2.5 资源加载：动态加载 + 软引用
- **动态加载**：用 `LoadObject<T>(path)` / `LoadClass<T>(path)` 等方式在运行时加载资源；
  避免在 C# 中硬编码强引用导致资源常驻内存。
- **软引用**：资源路径配置一律使用软引用类型：
  - `TSoftObjectPtr<T>`（资源）
  - `TSoftClassPtr<T>`（类）
  - 配合 `[UProperty(PropertyFlags.EditDefaultsOnly)]` 暴露到编辑器配置
- 不用裸 `FString` 路径 + 手动拼字符串的方式散落各处；路径集中在数据资产 / DataTable 中。

### 2.6 配置表使用 DataTable

**行结构必须定义在 C++ 侧**，这是硬性约束，原因如下：

- UE 要求 DataTable 的行结构**必须继承 `FTableRowBase`**
  （`Engine/Classes/Engine/DataTable.h:89`：*"Structure to use for each row of the table, must inherit from FTableRowBase"*）。
- 而 UnrealSharp 把 C# 的 `[UStruct]` 编译成 `UCSScriptStruct`，它继承 `UUserDefinedStruct`
  （见 `Plugins/UnrealSharp/Source/UnrealSharpCore/Public/Types/CSScriptStruct.h`）；
  编辑器里手工创建的 User Defined Struct **同样是** `UUserDefinedStruct`。
  两者都不满足 `FTableRowBase` 继承要求 → **都不能作为 DataTable 的行结构**。
- 因此「在蓝图中建个结构体、再在 C# 里读表」这条路走不通：
  编辑器创建的 User Defined Struct 既不能做行结构，也不会生成 C# 类型（它不是 UHT 类型），
  而 `UDataTable` 的读取 API 全部是泛型的（`FindRow<T>` / `TryFindRow<T>` / `ForEachRow<T>`），
  **没有非泛型的动态读行接口**。

**正确做法**：行结构写在 `Source/RPG/` 的 C++ 头里，并 `: public FTableRowBase`，例如
`Source/RPG/RPGTableRows.h` 的 `FRPGItemRow`。UnrealSharp 会为它生成 C# 类型
（`UnrealSharp.RPG.FRPGItemRow`，实现 `MarshalledStruct<T>`），随后即可在 C# 中读取：

```csharp
[UProperty(PropertyFlags.EditDefaultsOnly)]
public partial TSoftObjectPtr<UDataTable> ItemTable { get; set; }

if (RPGDataTable.TryGetRow(ItemTable, new FName("Sword_01"), out FRPGItemRow row))
{
    int stack = row.MaxStack;                          // 直接读字段
    UTexture2D? icon = RPGAssetLoader.Load(row.Icon);   // 软引用按需动态加载
}
```

命名映射（注意与 UCLASS 的区别）：
- C++ `FRPGItemRow` → C# 类型名 **`FRPGItemRow`**（保留 `F`）→ UE 结构体名 **`RPGItemRow`**（去首字符）
- 生成的字段是 **public 字段**（不是属性），用 `row.ItemId` 直接访问

现成工具：
- `Source/RPG/RPGTableRows.h` — `FRPGItemRow` 行结构示例（含 `TSoftObjectPtr` / `TSoftClassPtr`）
- `Script/ManagedRPG/RPGDataTable.cs` — `TryGetRow` / `GetRow` / `ForEachRow`，表资产走软引用动态加载
- `Script/ManagedRPG/RPGAssetLoader.cs` — 软引用 → 动态加载（`StaticLoadObject` / `StaticLoadClass`）

读取也可用 `UDataTable` 自带的 `RowNames` / `HasRow` / `FindRow<T>` / `TryFindRow<T>` / `ForEachRow<T>`。

### 2.7 关闭 Lumen / Nanite
已在 `Config\DefaultEngine.ini` 关闭以下次世代渲染特性，**不要重新打开**：

| 配置项 | 值 | 说明 |
|---|---|---|
| `r.DynamicGlobalIlluminationMethod` | `0` | 关闭 Lumen 动态全局光照 |
| `r.ReflectionMethod` | `0` | 关闭 Lumen 反射 |
| `r.Nanite.ProjectEnabled` | `False` | 关闭 Nanite |
| `r.Shadow.Virtual.Enable` | `0` | 关闭虚拟阴影贴图（Nanite 配套） |
| `r.RayTracing` | `False` | 关闭光追，减少着色器编译 |
| `r.Substrate` | `False` | 关闭实验性 Substrate 材质 |
| `r.GenerateMeshDistanceFields` | `False` | 距离场主要服务 Lumen，一并关闭 |

光照保持**全动态**（`r.AllowStaticLighting=0`）。

### 2.8 非 UFUNCTION 引擎函数：用 C++ 包一层再暴露给 C#

UnrealSharp 基于 UE 反射，**只能访问/覆写带 `UFUNCTION` 标记的函数**。引擎里大量虚函数
（如 `APawn::SetupPlayerInputComponent`、`APawn::PossessedBy`）没有 `UFUNCTION`，
C# 侧既不能 `override` 也不能调用。

**处理流程（遇阻即用，不要绕路）**：

1. 确认目标函数确实无法从 C# 访问（查 UE 头文件是否有 `UFUNCTION`）。
2. 在 C++ 中间基类中覆写/调用该函数。
3. 在覆写中转发到一个 `UFUNCTION` 钩子，暴露给 C#。
4. **先编译**（让 UnrealSharp 生成 C# 绑定）。
5. 编译通过后，再按生成的绑定签名编写/完善 C# 代码。

**命名约定**：包装函数加 `BP_` 前缀，例如 `BP_SetupPlayerInput`。
注意 UnrealSharp 生成 C# 绑定时会**剥掉 `BP_`/`K2_` 前缀**（`NameMapper.GetFunctionName`），
所以 C++ 的 `BP_SetupPlayerInput` 在 C# 中名为 `SetupPlayerInput`。

**现有范例**：`Source/RPG/RPGCharacterBase.h`
- C++ 覆写 `SetupPlayerInputComponent` → 转发 `BP_SetupPlayerInput`
- C++ 覆写 `PossessedBy` → 转发 `BP_PossessedBy`
- C# 的 `ARPGCharacter` 继承 `ARPGCharacterBase` 并实现上述钩子

**用 BlueprintNativeEvent 而非 BlueprintImplementableEvent**：`FunctionFlags.BlueprintEvent`
在 UnrealSharp 中映射到 `BlueprintNativeEvent`，C++ 侧提供空默认实现、C# 侧实现
`_Implementation`，两侧都能编译通过。

### 2.9 C++ 只写工具代码，不写业务逻辑

**硬性分工：C++ 仅用于「让 C# / 蓝图能访问到原本访问不了的东西」，不放业务逻辑。**

允许写在 C++ 里的（工具/胶水层）：
- 覆写**非 UFUNCTION** 的引擎虚函数，并用 `BP_` 前缀的钩子转发出去
  （如 `SetupPlayerInputComponent` / `PossessedBy`）
- 包装 **C# 够不到的接口**，例如 `ULocalPlayer::GetSubsystem<T>()` 这类
  C++ 模板、未反射的 API（见 `BP_AddMappingContext`）
- 构造 **C# 不便构造/不便设默认值**的对象
  （如 `UInputAction::ValueType` 是 `BlueprintReadOnly`，在 C++ 里设置更直接）
- 纯数据/接口声明（`UPROPERTY` 暴露给 C# 的字段）

**不允许**放在 C++ 里的（应写在 C#）：
- 角色/玩法行为逻辑（移动、跳跃、状态机、数值计算、技能、AI……）
- 资源选取与应用逻辑（用哪个网格体/动画、何时加载、如何切换）
- 任何"改需求就要动"的代码

判断标准：**如果这段代码会因为玩法/策划需求变化而改，它就不该在 C++ 里。**
C++ 层的代码应当只在「引擎接口本身变化」时才需要改。

实践提示：动手写 C++ 前先确认 C# 真的做不到。多数 UE 接口都有
`UFUNCTION(BlueprintCallable)` 暴露，C# 直接用即可 —— 例如设置角色外观所需的
`ACharacter.Mesh`、`USkeletalMeshComponent.SetSkeletalMeshAsset`、
`SetAnimInstanceClass`、`TSoftObjectPtr.LoadSynchronous` 全都是暴露的，
所以外观逻辑应当写在 C#（参考 `Script/ManagedRPG/ARPGCharacter.cs` 的 `ApplyVisuals`）。

## 3. 目录结构（参照 SBFC 工程）

### 3.1 游戏框架类放 `/Game/` 根目录（重要）

仿照 SBFC 把核心框架类**集中、扁平**管理的做法，本项目的框架类
**直接放在 `/Game/` 根目录**，不要塞进子文件夹：

| 角色 | 蓝图 | C# 类 |
|---|---|---|
| PlayerPawn | `/Game/BP_RPGCharacter` | `ARPGCharacter` |
| PlayerController | `/Game/BP_RPGPlayerController` | `ARPGPlayerController` |

**项目刻意不自定义 GameMode / GameState / PlayerState：**

- **GameMode** 直接用引擎的 `GameModeBase`
  （`Config/DefaultEngine.ini` → `GlobalDefaultGameMode=/Script/Engine.GameModeBase`）
- **GameState / PlayerState** 都不需要 —— 需要全局或玩家维度数据时，
  放自建 C# 组件或 DataAsset，不要引入这两个子类

这样 GameMode 不做任何事，角色完全靠**关卡里放置**被玩家控制：
`BP_RPGCharacter` 实例放进 NewMap（`/Game/Maps/NewMap`），玩家控制它。

**为什么光靠 `AutoPossessPlayer = Player0` 不够（踩过的坑）**：
`AGameModeBase::DefaultPawnClass` 默认是 `ADefaultPawn`，GameMode 会在 PlayerStart
生成它并**抢先**占据玩家控制器；而关卡里的 Pawn 的 BeginPlay 晚于 GameMode 的出生流程，
引擎的自动占据只在"控制器还没有 Pawn"时才生效，于是关卡 Pawn 反而抢不到，
玩家控制的是一个没有输入绑定的默认 Pawn —— **表现就是键盘鼠标全无响应**。
所以 `ARPGCharacter.BeginPlay` 里显式接管了控制权（`EnsurePlayerPossession`），
并销毁那个没人再控制的占位 Pawn。

> `DefaultPawnClass` 这个属性没有 `config` 标记，**ini 里配不了**；
> 项目又刻意不做自定义 GameMode，所以只能在 C# 里兜底。
> 想换成配置驱动的话，唯一办法就是建一个 `GameModeBase` 的蓝图子类、
> 把 `DefaultPawnClass` 设为 `None`。

角色必须放在关卡里（不要只留 PlayerStart 空着），并且**不要**把关卡里的角色实例删掉
——删了就等于没有 Pawn，输入不会有任何反应。

**地图**放 `/Game/Maps/`（如 `/Game/Maps/NewMap`）。

其余资产按类型进子目录（见下方 3.2）。

### 3.1.1 别在 C# 构造函数里用 `typeof()` 引用其他 C# 类

**踩过的坑**：`TSubclassOf<T>(Type)` 会**立刻**按名字向 UnrealSharp 查类型
（`CallGetType(asm, "RPG", "RPGGameState")`）。而 C# 构造函数可能在托管装配件
注册完成**之前**执行（编辑器启动编译 CDO 时），此时查到 `null`，**这个 null 会被
固化进 CDO**，运行时报：

```
LogGameSession: Error: Player State class is invalid for game mode
LogGameMode: Warning: No GameStateClass was specified
LogUnrealSharp: Warning: Failed to find type: RPG.RPGPlayerState
```

规避方式（按优先级）：
1. **类引用配在蓝图的 Class Defaults 里** —— 蓝图默认值在装配件加载后才确定，
   且随资产持久化（`BP_RPGCharacter` 的 Mesh / AnimClass 就是这么配的）
2. 需要代码里指定时，用**软引用 + 运行时加载**（`TSoftClassPtr` + `LoadSynchronous`）
3. 仅当目标类是**引擎类**（如 `AGameModeBase`）时才可直接 `typeof()`，因为引擎类
   在装配件加载前就已注册

> 注意：如果 CDO 已经带着这个 null 存过盘，光改代码不够，还要重新保存那个资产
> （或在编辑器里重设一次该属性），否则旧值会被继续加载。

**地图**放 `/Game/Maps/`（如 `/Game/Maps/NewMap`）。

归置脚本（幂等，可重跑）：`Tools/layout_framework_bps_root.py`

其余资产按类型进子目录（见下方 3.2）。

### 3.2 资产分类目录

```
Content/
├── BP_RPGGameMode.uasset      # ← 框架类：直接放 /Game/ 根
├── BP_RPGGameState.uasset
├── BP_RPGPlayerController.uasset
├── BP_RPGPlayerState.uasset
├── BP_RPGCharacter.uasset
├── Maps/                      # 地图
├── Blueprint/                 # 其他蓝图（Actor/ Component/ UMG/ Prefabs/ Enum/ ...）
├── Data/
│   ├── Table/                 # DataTable 配置表
│   ├── DA/                    # DataAsset
│   └── Curve/                 # 曲线
├── ControlRig/                # 第三人称模板的 Mannequin（网格体/动画/材质）
├── Mesh/  Material/  Anim/  Particles/  Audio/  Font/
└── Collections/  Developers/
```

放置规则：新资产按类型放入上表对应目录，不要堆在 `Content` 根目录
（框架类那 5 个 BP 是唯一例外）。C# 脚本放在项目根的 `Script/`。

## 4. 环境与工具链

- **IDE**：Visual Studio 2022 Community（安装于 `D:\VS2022`）
  - 工作负载：`.NET 桌面开发`、`使用 C++ 的游戏开发`
  - 用途：编译 C++ 项目/插件 + 编写调试 C#
- **.NET SDK**：10.0.x。**注意波段**——VS2022 只能用 `10.0.1xx`（见 4.0.2）
- **Git**：已启用 **Git LFS**，`.uasset`/`.umap` 等二进制资产走 LFS（规则见仓库根 `.gitattributes`）

### 4.0.2 VS2022 只能用 .NET 10 的 1xx 波段（否则报"找不到指定的 SDK"）

**症状**：在 VS2022 里打开 `RPG.sln`，两个 C# 项目报
`error : 找不到指定的 SDK "Microsoft.NET.Sdk"`，解决方案显示 0 个项目。

**原因**：每个 .NET SDK 会在自己的
`sdk\<版本>\Microsoft.NETCoreSdk.BundledMSBuildInformation.props` 里声明
`MinimumMSBuildVersion`，而 VS 自带的 MSBuild 版本是固定的：

| SDK | 声明的最低 MSBuild | 能配的 VS |
|---|---|---|
| 9.0.3xx | 17.12.0 | VS2022 17.14 ✅ |
| **10.0.1xx** | **17.14.0** | **VS2022 17.14 ✅** |
| 10.0.2xx / 3xx / 4xx | 18.0.0 | 只有 VS 2026（18.x）❌ |

本项目 VS2022 的 MSBuild 是 `17.14.51`，所以**只能用 10.0.1xx 波段的 SDK**。
（官方文档 `.NET SDK, MSBuild, and Visual Studio versioning` 有完整对应表。）

**本项目采用的配法**（免管理员，且装在 D 盘）：

1. `10.0.1xx` 波段最高版是 **10.0.103**，解压到 **`D:\dotnet`**（就是一个合法的 dotnet 根目录）。
2. 设**用户级**环境变量，让 VS 的 SDK 解析器改从 `D:\dotnet` 取 SDK：

   ```powershell
   [Environment]::SetEnvironmentVariable(
       'DOTNET_MSBUILD_SDK_RESOLVER_CLI_DIR', 'D:\dotnet', 'User')
   ```
   （`DOTNET_MSBUILD_SDK_RESOLVER_CLI_DIR` 是 VS 的
   `Microsoft.DotNet.MSBuildSdkResolver` 支持的官方探测项；改完要**重启 VS** 才生效。）
3. `Script/global.json` 请求 **`10.0.100` + `rollForward: latestFeature`**。
   这样两个 SDK 根目录各自都能满足：VS 从 `D:\dotnet` 拿到 10.0.103，
   CLI 从 `C:\Program Files\dotnet` 拿到 10.0.401。

**关键结论：这台机器上是"两个 SDK 分别服务两侧"，这是刻意的**

- **VS**（IntelliSense / 加载项目）：`D:\dotnet\sdk\10.0.103` + MSBuild 17.14.51
- **`dotnet` CLI 与 UnrealSharp 的 UAT 构建**：`C:\Program Files\dotnet\sdk\10.0.401` + MSBuild 18.9.11

已验证该环境变量**不会**干扰 CLI / UAT（`dotnet build` 与 `BuildUserSolution` 仍用 10.0.401，
且 `BuildUserSolution` 照常成功），所以可以放心保留。

**已知现象**：VS 里构建会有一条警告 `NETSDK1233: 不支持在 Visual Studio 2022 17.14 中以
.NET 10.0 或更高版本为目标`。这是微软对该组合的官方提示，**不是错误**，构建仍然成功。
真正出包的是 UnrealSharp 的 `BuildUserSolution`（走 CLI）。

想彻底消除这条警告，只有升级到 **Visual Studio 2026（18.x）**，并让它配 10.0.2xx+ 的 SDK。

**排查命令**（确认到底是谁解析到了哪个 SDK）：

```powershell
# VS 的 MSBuild 解析到哪个 SDK
& 'D:\VS2022\MSBuild\Current\Bin\MSBuild.exe' <某个.csproj> -t:Restore `
    -getProperty:NETCoreSdkVersion,MSBuildVersion
# 各 SDK 声明的最低 MSBuild
Select-String MinimumMSBuildVersion 'D:\dotnet\sdk\*\Microsoft.NETCoreSdk.BundledMSBuildInformation.props'
```


### 4.0 启动编辑器必须带正确的 PATH（否则 UnrealSharp 报“找不到 .NET SDK”）
- UnrealSharp 用 `DotNetUtilities::GetDotNetDirectory()` 判断 SDK 是否存在：
  它**读取进程的 `PATH` 环境变量**，查找包含字符串 `Program Files\dotnet\` 的条目。
  找不到就弹 “UnrealSharp can't be initialized. An installation of .NET 10.0.0 SDK can't be found.”
- 系统 PATH 中该条目为 `C:\Program Files\dotnet\`（含结尾反斜杠）——这是匹配成功的关键。
- **因此不要从 Git Bash / MSYS 等非 Windows 环境直接启动编辑器**（PATH 会被改写为
  `/c/Program Files/dotnet` 形式，导致匹配失败）。
- 需要脚本化启动时，用 PowerShell 显式重建 PATH：
  ```powershell
  $env:PATH = 'C:\Program Files\dotnet\;' +
              [Environment]::GetEnvironmentVariable('PATH','Machine') + ';' +
              [Environment]::GetEnvironmentVariable('PATH','User')
  & 'D:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' '<project>.uproject'
  ```
- 另注：**不要在 commandlet 模式下验证 UnrealSharp**。UnrealSharp 在
  `IsRunningCommandlet()` / unattended 时不会完整初始化，C# 类不会注册；
  且缺失 SDK 时会在无人值守下反复弹窗重试，**把 `Saved/Logs/RPG.log` 写到数 GB**。
  若日志失控，先 `Stop-Process -Name UnrealEditor-Cmd` 再删除日志。

### 4.0.1 UnrealSharp 的 C# 项目结构（本项目实际生成结果）
```
Script/
├── ManagedRPG.sln              # 用户解决方案
├── ManagedRPG/
│   ├── ManagedRPG.csproj       # 用户 C# 项目（放游戏类）
│   └── ARPGCharacter.cs 等
└── global.json                 # 请求 SDK 10.0.100 + rollForward latestFeature（见 4.0.2）
Binaries/Managed/net10.0/
├── RPG.dll                     # 项目 C++ 类的绑定（glue）
├── ManagedRPG.dll              # 用户程序集（游戏类）
├── GlueCode.LoadOrder.json
└── UserCode.LoadOrder.json
```
- 用户 C# 项目由 UnrealSharp 的 UAT 命令生成（等价于编辑器菜单 “Create New C# Project”）：
  ```
  AutomationTool.dll GenerateProject -ScriptDir="<plugin>/Build/Scripts" -Project="<uproject>" \
    -ProjectName=ManagedRPG -ProjectFolder="<project>/Script/ManagedRPG" \
    -GenerateSolution=true -RunUSharpProjectSetup=true
  ```
  其中项目名固定为 `"Managed" + 项目名`（`GetUserManagedProjectName()`）。
- 构建并部署用户程序集：
  ```
  AutomationTool.dll BuildUserSolution -ScriptDir="<plugin>/Build/Scripts" -Project="<uproject>" \
    -OutputPath="<project>/Binaries/Managed/net10.0" -TargetConfiguration=Development
  ```
- **`ManagedRPG.csproj` 需要手动引用 `<project>/Binaries/Managed/net10.0/RPG.dll`**，
  否则用户代码看不到本项目 C++ 类的绑定（`UnrealSharp.RPG.*`），会报
  `inherits from 'X' which does not inherit from 'UObject'`。
- **命名映射（重要）**：UnrealSharp 取 C# 类名 **去掉首字符** 作为 UE 类名
  （`GlueGenerator` 的 `UnrealStructBase.EngineName => SourceName.Substring(1)`，
  类继承自 `UnrealStruct`，同样适用），并把 C# 类注册到 **`/Script/UnrealSharp`** 包下：

  | C# 类（`Script/ManagedRPG/`） | UE 类路径（`load_class` 用） |
  |---|---|
  | `ARPGCharacter` | `/Script/UnrealSharp.RPGCharacter_C` |
  | `ARPGPlayerController` | `/Script/UnrealSharp.RPGPlayerController_C` |
  | `ARPGGameMode` | `/Script/UnrealSharp.RPGGameMode_C` |

  注意：**脚本里要加载的是带 `_C` 后缀的 Blueprint 生成类**
  （`/Script/UnrealSharp.RPGCharacter_C`）；不带 `_C` 的 `/Script/UnrealSharp.RPGCharacter`
  只出现在日志的 `Compiling Blueprint` 行里，`load_class` 取不到。

  所以 C# 类名带 `A`/`U` 前缀是**刻意为之**：`ARPGCharacter` 才能在 UE 侧得到 `RPGCharacter`。
  若把 C# 类命名为 `RPGCharacter`，UE 侧反而会变成 `PGCharacter`。
  同理，`BP_`/`K2_` 前缀的函数名在 C# 侧会去掉 3 个字符（`BP_SetupPlayerInput` → `SetupPlayerInput`）。

### 4.1 安装位置偏好（重要）
- **所有软件一律安装到 D 盘**，不要装在 C 盘。
- 原因：**C 盘空间极度紧张**（约 120 GB 容量常年接近占满，可用空间常在个位数 GB）。
  D 盘空间充裕（300+ GB）。
- 具体做法：
  - winget / 安装器尽量用 `--installPath`（VS、SDK 等）或自定义安装目录指向 `D:\...`
  - 大型缓存/包目录也指向 D 盘（如 VS 的 `--cache D:\VSCache`）
  - 临时文件、下载物、构建中间产物一律放 D 盘
- 若安装因 C 盘空间失败，先排查 `C:\hiberfil.sys`（休眠文件，可达 9 GB 以上，
  可用 `powercfg /h off` 释放）与大体积缓存，再重试；**不要直接删除用户数据**。

### 4.2 关闭 C++ 热重载（Live Coding）

**已关闭，不要重新打开。**

- 配置位置（两处都要保持一致）：
  - `Config/DefaultEditorPerProjectUserSettings.ini` → 项目默认值（可随仓库共享）
  - `Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini` → 当前用户本地值
- 内容：
  ```ini
  [/Script/LiveCoding.LiveCodingSettings]
  bEnabled=False
  bAutomaticallyCompileNewClasses=False
  ```
- 为什么必须显式关：引擎 `BaseEditorPerProjectUserSettings.ini` 里是 `False`，但
  **Windows 平台文件 `Engine/Config/Windows/WindowsEditorPerProjectUserSettings.ini`
  把它覆盖成了 `True`**，所以不写就等于开着。
- 关闭的理由：本项目 C++ 改动统一走 UnrealBuildTool 编译，不在编辑器内做热重载。
  Live Coding 的增量编译与 reinstancing 会干扰 UnrealSharp 的托管程序集加载与
  已加载插件的状态，容易出现「改了 C++ 但编辑器行为不一致」的怪问题。
- 改了 C++ 之后的正确流程：
  1. **先关闭编辑器**（否则 DLL 被占用，编译会失败）
  2. 运行 UBT 编译 Editor 目标
  3. 重新打开编辑器
- 若在编辑器 UI 里（编辑器偏好设置 → Live Coding）改动过该项，本地 `Saved/Config/...`
  那一段会被重写，需复查。

### 4.3 解决方案文件（.sln）与 C# 工程

项目里有**三个** sln，容易搞混，这里说清各自用途：

| 文件 | 内容 | 用途 |
|---|---|---|
| `RPG.sln`（项目根） | UE5.vcxproj + **RPG.vcxproj**（C++）+ ManagedRPG / RPG.RuntimeGlue（C#） | **推荐**：一个 sln 同时打开 C++ 与 C# |
| `Script/ManagedRPG.sln` | 仅 ManagedRPG / RPG.RuntimeGlue（C#） | UnrealSharp 自己的 C# 解决方案 |
| `Automation_RPG.sln`（项目根） | 引擎自动化工程 | UBT 生成，一般不用 |

**为什么根目录的 sln 一开始不存在**：UBT 的 `-ProjectFiles` 只生成 C++ 工程，
它不认识 UnrealSharp 的托管工程，所以需要手动合并。生成命令：

```powershell
dotnet "D:\UE_5.8\Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.dll" `
  -ProjectFiles -Project="<项目>/RPG.uproject" -Game -Engine -Progress
```

**⚠️ 每次重新生成都会被覆盖**：`-ProjectFiles`（或编辑器里的
`Generate Visual Studio project files`）会重写 `RPG.sln`，把手工加进去的
C# 项目冲掉。覆盖后重新执行合并脚本即可：

```powershell
D:\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe Tools\add_csharp_to_sln.py
```

该脚本幂等（已在则跳过），会把 ManagedRPG / RPG.RuntimeGlue 追加进 `RPG.sln`，
并补全 15 条解决方案配置映射。注意 C# 工程路径相对根目录是
`Script\ManagedRPG\ManagedRPG.csproj`，GUID 与 `Script/ManagedRPG.sln` 保持一致。

**C# 工程的实际位置**（别在根目录找）：
- `Script/ManagedRPG/ManagedRPG.csproj` — 游戏代码（ARPGCharacter 等）
- `Script/RPG.RuntimeGlue/RPG.RuntimeGlue.csproj` — UnrealSharp 自动生成的 Glue 工程
- `Script/ManagedRPG.sln` — 上述两者的解决方案

## 5. MCP / 编辑器自动化

### 5.1 UEEditorMCP（本项目使用）
- 已接入 **UEEditorMCP**（`yangskin/UEEditorMCP`，MIT，UE 5.7+），插件在 `Plugins/UEEditorMCP`。
- 架构：C++ 编辑器插件起 **TCP 服务 `127.0.0.1:55558`**；Python 侧经 **stdio** 连 MCP 客户端，
  内部再走 TCP 连编辑器。
- 工作区配置在 **`.zcode/config.json` → `mcp.servers`**，提供两个 server：
  - `ue-editor-mcp` → `ue_editor_mcp.server_unified`（统一 7 个工具，实测注册 **171** 个 action）
  - `ue-editor-mcp-logs` → `ue_editor_mcp.server_unreal_logs`（`unreal.logs.get` 等）
- Python venv 在 `Plugins/UEEditorMCP/Python/.venv`（由 `setup_mcp.ps1` 用引擎自带 Python 3.11 创建）。
  重装/修复：`powershell -ExecutionPolicy Bypass -File Plugins\UEEditorMCP\setup_mcp.ps1 -EngineRoot D:\UE_5.8`
- **前提：编辑器必须在运行**（TCP 服务随编辑器启动）。编辑器没开时 MCP 工具会连不上。
- 该插件自带依赖 `EnhancedInput`、`EditorScriptingUtilities`、`ModelViewViewModel` 三个引擎插件，
  与 2.2 节「项目使用 EnhancedInput」的方向一致，无冲突。
- 注意：UEEditorMCP 侧重**蓝图 / 材质 / UMG**。本项目逻辑在 C#，所以它主要用于
  资产与编辑器层面的辅助操作。

> ⚠️ **按 0.3 节的职责边界，本项目只使用 UEEditorMCP 的只读能力**
> （读 Actor、读资产清单、读蓝图属性、读日志等）。
> 它的写操作（spawn / save / delete / 改蓝图 / 启动 PIE …）**一律不要调用**，
> 这些操作由开发者在编辑器里完成。

### 5.2 会话里另一个 MCP 不属于本项目
- 会话中的 `ue_*`（ugcaskq）MCP **连接的是 SBFC 工程**（和平精英绿洲启元 UE4.18 魔改编辑器），
  **不是本项目**。禁止用这些工具操作 RPG 工程，也不要改动 SBFC 工程。
- `PythonScriptPlugin` 虽已启用，但按 0.3 节约定 **AI 不执行会改动编辑器状态的 Python 脚本**
  （如生成 Actor、保存关卡）。`Tools/` 下的脚本是给开发者手动运行的，
  AI 可以编写和修改它们，但不代跑。

## 6. 测试约定

- **AI 不运行 PIE，也不做任何会改变编辑器状态的操作**（见 0.3 节）。
- AI 完成代码后必须交付**两样东西**：
  1. **编辑器操作清单**：开发者要手动做哪些操作 —— 操作路径、要填的具体值、预期结果
     （例如"打开某地图 → 拖入某蓝图 → 设置某属性 = 某值 → 保存"）。
  2. **测试步骤**：怎么验证功能正常 —— 操作路径 + 预期表现 + 需要观察的日志/输出。
- 允许 AI 自行进行的验证方式：编译（`dotnet build` / UBT / `BuildUserSolution`）、
  静态检查、只读地走查编辑器与日志（非 PIE、不落盘）。
- 若 AI 判断某项编辑器操作做起来有坑（例如时序、默认值不持久化），
  要在清单里写清注意事项，而不是自己代做。

## 7. 版本控制

- 使用 Git + Git LFS。**所有 Git 操作由开发者执行**（见 0.1 节）。
- 二进制资产走 LFS；**`.gitattributes` 的 LFS 规则必须提交**，否则克隆端拿不到资产内容（见 0.2 节）。
- 构建产物不入库：`obj/`、`bin/`、`Binaries/`、`Intermediate/`、`Saved/`（见 `.gitignore`）。
- 不提交 `Binaries/`、`Intermediate/`、`Saved/`、`.vs/` 等生成目录（已在 `.gitignore`）。
- ⚠️ **`.gitignore` 里不要写 `Build/` 通配规则**：UnrealSharp 插件的
  `Build/Scripts/` 是**源码**（UAT 的 `BuildUserSolution`/`PackageProject` 实现在其中），
  被忽略会导致新克隆的工程无法编译 C++（报 `MSB3202: 未找到项目文件
  "..\..\Build\Scripts\UnrealSharp.Automation.csproj"`）。详见 `.gitignore` 内注释。
- ⚠️ **从零克隆后、编译 C++ 前**，需要先让 UBT 生成插件项目文件；
  `Intermediate/ProjectFiles/*.vcxproj` 是生成产物，缺失属正常现象，
  不要试图把它提交进仓库。
