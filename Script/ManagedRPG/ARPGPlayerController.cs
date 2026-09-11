using UnrealSharp;
using UnrealSharp.Attributes;
using UnrealSharp.Engine;

namespace RPG;

/// <summary>
/// 第三人称玩家控制器。
///
/// 职责分工：
///   - 本控制器：输入模式与光标管理、视角灵敏度配置（Controller.ControlRotation 是视角的权威来源）
///   - <see cref="ARPGCharacter"/>：消费 ControlRotation 驱动弹簧臂相机，并处理移动/跳跃输入
///
/// 不使用 EnhancedInput；鼠标捕获与锁定由 Config/DefaultInput.ini 的
/// DefaultViewportMouseCaptureMode / DefaultViewportMouseLockMode 保证。
/// </summary>
[UClass]
public partial class ARPGPlayerController : APlayerController
{
    /// <summary>鼠标视角灵敏度倍率。</summary>
    [UProperty(PropertyFlags.EditDefaultsOnly | PropertyFlags.BlueprintReadOnly)]
    public partial float MouseSensitivity { get; set; }

    /// <summary>是否反转 Y 轴（俯仰）视角。</summary>
    [UProperty(PropertyFlags.EditDefaultsOnly | PropertyFlags.BlueprintReadOnly)]
    public partial bool InvertLookY { get; set; }

    public ARPGPlayerController()
    {
        MouseSensitivity = 1.0f;
        InvertLookY = false;

        // 第三人称：隐藏鼠标光标
        ShowMouseCursor = false;
    }

    public override void BeginPlay()
    {
        base.BeginPlay();

        ShowMouseCursor = false;

        PrintString($"ARPGPlayerController ready (sensitivity={MouseSensitivity}, invertY={InvertLookY})");
    }
}
