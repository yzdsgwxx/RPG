using UnrealSharp;
using UnrealSharp.Attributes;
using UnrealSharp.Engine;

namespace RPG;

/// <summary>
/// 游戏模式（逻辑层）。
///
/// 为什么需要它：引擎的 <c>AGameModeBase</c> 会把 <c>DefaultPawnClass</c> 默认设为
/// <c>ADefaultPawn</c>，然后在 PlayerStart 生成它并**抢先占据**玩家控制器。
/// 而本项目的角色是**关卡里手工放置**的 <c>BP_RPGCharacter</c> 实例，它的 BeginPlay
/// 晚于 GameMode 的出生流程，于是引擎的 AutoPossess 抢不到控制权 ——
/// 玩家最终控制的是一个没有输入绑定的默认 Pawn，表现就是键盘鼠标全无反应。
///
/// 这个类把这个"出生什么、由谁控制"的决策从引擎默认行为里接管过来：
///   - <c>默认pawn类</c> 设为 <c>None</c> —— 不生成任何占位 Pawn，
///     让关卡里放置的角色成为唯一的 Pawn（AutoPossessPlayer 就能正常生效）；
///   - <c>玩家控制器类</c> 指向 <c>BP_RPGPlayerController</c> ——
///     让 <see cref="ARPGPlayerController"/> 真正生效
///     （原本用引擎 GameModeBase 时，这个子类根本不会被生成）。
///
/// 配置方式：全部在**蓝图子类** `/Game/BP_RPGGameMode` 的 Class Defaults 里填
/// （「类」分类下的 `默认pawn类` / `玩家控制器类` 就是 <c>AGameModeBase</c> 的原生属性）。
/// 这些属性没有 `config` 标记，**ini 里配不了**，只能在蓝图默认值里配；
/// 而蓝图默认值会随资产持久化，正是本项目"C# 放逻辑、蓝图放资源引用"的分工（见 AGENTS.md 2.3）。
///
/// 构造函数刻意**不写**任何类引用：C# 类的属性默认值不持久化，
/// 写了也会被蓝图默认值覆盖，反而造成"代码和实际生效值不一致"的困惑。
/// 唯一的例外是 <c>DefaultPawnClass</c> —— 显式置空是本项目的核心设定，
/// 见下方构造函数注释。
/// </summary>
[UClass]
public partial class ARPGGameMode : AGameModeBase
{
    public ARPGGameMode()
    {
        // 核心设定：不生成默认 Pawn，让关卡里放置的 BP_RPGCharacter 成为唯一 Pawn。
        // C# 类的默认值不持久化，所以这行只是让"新建的蓝图子类"有个正确的起点；
        // 真正生效的值以 BP_RPGGameMode 的 Class Defaults 为准。
        DefaultPawnClass = default;
    }

    public override void BeginPlay()
    {
        base.BeginPlay();

        PrintString($"[RPGDiag] GameMode BeginPlay: DefaultPawnClass=" +
                   $"{(DefaultPawnClass.IsValid ? "有（会生成占位 Pawn）" : "null（由关卡角色担任 Pawn）")} " +
                   $"PlayerControllerClass={(PlayerControllerClass.IsValid ? "已设置" : "null（引擎默认）")}");
    }
}
