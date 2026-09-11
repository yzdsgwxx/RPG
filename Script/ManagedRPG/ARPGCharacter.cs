using UnrealSharp;
using UnrealSharp.Attributes;
using UnrealSharp.Core;
using UnrealSharp.CoreUObject;
using UnrealSharp.Engine;
using UnrealSharp.EnhancedInput;
using UnrealSharp.InputCore;
using UnrealSharp.RPG;

namespace RPG;

/// <summary>
/// 第三人称角色（逻辑层）。
///
/// 分工（见 AGENTS.md 2.9）：
///   - **C++ 基类 <see cref="ARPGCharacterBase"/>**：纯工具层 —— 转发非 UFUNCTION 的虚函数，
///     并提供 EnhancedInput 的原子能力（建 Action / 建 Context / 挂按键 / 注册 Context）。
///   - **本 C# 类**：全部业务逻辑 —— 按键表、走跑跳与视角、外观应用。
///   - **蓝图子类**（`/Game/Blueprint/Actor/BP_RPGCharacter`）：**视觉与资源引用**。
///     网格体、动画蓝图这类"美术/策划要调"的东西在蓝图里配置，
///     因为 C# 类的属性默认值不持久化，而蓝图默认值会随资产保存。
///
/// ⚠️ 所有输入回调必须标 <c>[UFunction]</c> 且签名为 4 参数
/// <c>(FInputActionValue, float, float, UInputAction)</c>，
/// 否则 UnrealSharp 按方法名在 UE 侧找不到 UFUNCTION，PIE 会直接致命崩溃。
/// </summary>
[UClass]
public partial class ARPGCharacter : ARPGCharacterBase
{
    /// <summary>相机摇臂，附着到胶囊体。</summary>
    [UProperty(DefaultComponent = true, AttachmentComponent = nameof(CapsuleComponent))]
    public partial USpringArmComponent CameraBoom { get; set; }

    /// <summary>跟随相机，附着到摇臂末端。</summary>
    [UProperty(DefaultComponent = true, AttachmentComponent = nameof(CameraBoom))]
    public partial UCameraComponent FollowCamera { get; set; }

    /// <summary>走路速度（默认状态）。</summary>
    [UProperty(PropertyFlags.EditDefaultsOnly | PropertyFlags.BlueprintReadOnly)]
    public partial float WalkSpeed { get; set; }

    /// <summary>跑步速度（按住 Sprint 时）。</summary>
    [UProperty(PropertyFlags.EditDefaultsOnly | PropertyFlags.BlueprintReadOnly)]
    public partial float RunSpeed { get; set; }

    /// <summary>鼠标视角灵敏度倍率。</summary>
    [UProperty(PropertyFlags.EditDefaultsOnly | PropertyFlags.BlueprintReadOnly)]
    public partial float LookSensitivity { get; set; }

    /// <summary>跳跃初速度。</summary>
    [UProperty(PropertyFlags.EditDefaultsOnly | PropertyFlags.BlueprintReadOnly)]
    public partial float JumpVelocity { get; set; }

    /// <summary>相机摇臂长度。</summary>
    [UProperty(PropertyFlags.EditDefaultsOnly | PropertyFlags.BlueprintReadOnly)]
    public partial float CameraBoomLength { get; set; }

    // ---- EnhancedInput 资产 -------------------------------------------------
    // 由本类在运行时经 C++ 工具函数创建，Outer 是本角色，因此生命周期随角色，
    // 不需要额外声明为 UPROPERTY 来防 GC。

    private UInputMappingContext? _mappingContext;
    private UInputAction? _moveForward;
    private UInputAction? _moveRight;
    private UInputAction? _lookYaw;
    private UInputAction? _lookPitch;
    private UInputAction? _jump;
    private UInputAction? _sprint;

    private bool _inputBound;

    public ARPGCharacter()
    {
        WalkSpeed = 300.0f;
        RunSpeed = 600.0f;
        LookSensitivity = 1.0f;
        JumpVelocity = 600.0f;
        CameraBoomLength = 400.0f;

        // 视角由控制器（鼠标）驱动；角色本体朝向由移动方向决定。
        UseControllerRotationYaw = false;
        UseControllerRotationPitch = false;
        UseControllerRotationRoll = false;
    }

    public override void BeginPlay()
    {
        base.BeginPlay();

        // 诊断：确认角色存活、是否已挂到控制器
        PrintString($"[RPGDiag] Character BeginPlay: {Name}  Controller={(Controller != null ? "OK" : "null")}");

        EnsurePlayerPossession();

        UCharacterMovementComponent movement = CharacterMovement;
        movement.MaxWalkSpeed = WalkSpeed;
        movement.JumpZVelocity = JumpVelocity;
        movement.AirControl = 0.35f;
        // 角色朝向移动方向
        movement.OrientRotationToMovement = true;
        movement.RotationRate = new FRotator(0.0f, 540.0f, 0.0f);

        CameraBoom.TargetArmLength = CameraBoomLength;
        CameraBoom.UsePawnControlRotation = true;
        CameraBoom.SocketOffset = new FVector(0.0f, 0.0f, 60.0f);
    }

    /// <summary>
    /// 确保玩家 0 控制的是本角色，而不是 GameModeBase 生成的占位 Pawn。
    ///
    /// 为什么需要这一步：`AGameModeBase::DefaultPawnClass` 默认是 `ADefaultPawn`，
    /// GameMode 会在 PlayerStart 生成它并抢先占据玩家控制器；而本角色是关卡里放置的，
    /// 它的 BeginPlay 晚于 GameMode 的出生流程，因此 `AutoPossessPlayer` 不一定拿得到控制权
    /// （引擎的自动占据只在控制器还没有 Pawn 时才生效）。抢不到就等于玩家控制一个
    /// 没有输入绑定的默认 Pawn —— 表现就是键盘鼠标全无响应。
    ///
    /// 该属性没有 `config` 标记，ini 里配不了；项目又刻意不使用自定义 GameMode，
    /// 所以只能在这里兜底。抢到控制权后，那个没人再控制的占位 Pawn 一并销毁，
    /// 否则场景里会一直浮着一个默认 Pawn 的球体。
    /// </summary>
    private void EnsurePlayerPossession()
    {
        APlayerController? playerController = UGameplayStatics.GetPlayerController(0);
        if (playerController == null)
        {
            PrintString("[RPGDiag] 未找到玩家 0 的 PlayerController，无法接管控制权。");
            return;
        }

        // 先记下当前受控的 Pawn（通常是 GameMode 生成的 ADefaultPawn），接管后要清掉它
        APawn? placeholder = UGameplayStatics.GetPlayerPawn(0);

        if (Controller == null)
        {
            playerController.Possess(this);
            PrintString($"[RPGDiag] 接管控制权: Controller={(Controller != null ? "OK" : "null")}");
        }

        if (placeholder != null && placeholder != this)
        {
            placeholder.DestroyActor();
        }
    }

    /// <summary>
    /// 由 C++ 的 ARPGCharacterBase::SetupPlayerInputComponent 在 InputComponent 就绪后回调。
    /// </summary>
    public override void SetupPlayerInput(UInputComponent playerInputComponent)
    {
        base.SetupPlayerInput(playerInputComponent);

        if (_inputBound)
        {
            return;
        }

        if (playerInputComponent is not UEnhancedInputComponent enhancedInput)
        {
            PrintString("ARPGCharacter: InputComponent 不是 UEnhancedInputComponent，输入未绑定。");
            return;
        }

        _inputBound = true;

        BuildInputAssets();

        PrintString($"[RPGDiag] SetupPlayerInput called. IMC={( _mappingContext != null ? "OK" : "null")} " +
                   $"MoveFwd={(_moveForward != null ? "OK" : "null")} Jump={(_jump != null ? "OK" : "null")}");

        if (_mappingContext != null)
        {
            AddMappingContext(_mappingContext, 0);
        }

        // 诊断：BindAction 返回 false 说明按方法名找不到 UFUNCTION（回调没注册成 UFUNCTION）
        bool ok = true;
        if (_moveForward != null) ok &= enhancedInput.BindAction(_moveForward, ETriggerEvent.Triggered, OnMoveForward);
        if (_moveRight != null) ok &= enhancedInput.BindAction(_moveRight, ETriggerEvent.Triggered, OnMoveRight);
        if (_lookYaw != null) ok &= enhancedInput.BindAction(_lookYaw, ETriggerEvent.Triggered, OnLookYaw);
        if (_lookPitch != null) ok &= enhancedInput.BindAction(_lookPitch, ETriggerEvent.Triggered, OnLookPitch);
        if (_jump != null)
        {
            ok &= enhancedInput.BindAction(_jump, ETriggerEvent.Started, OnJumpStarted);
            ok &= enhancedInput.BindAction(_jump, ETriggerEvent.Completed, OnJumpCompleted);
        }
        if (_sprint != null)
        {
            ok &= enhancedInput.BindAction(_sprint, ETriggerEvent.Started, OnSprintStarted);
            ok &= enhancedInput.BindAction(_sprint, ETriggerEvent.Completed, OnSprintCompleted);
        }

        PrintString($"[RPGDiag] BindAction all-ok = {ok}（false 表示按方法名找不到 UFUNCTION）");
    }

    /// <summary>
    /// 构建 EnhancedInput 资产与按键表。
    /// 按键表放在 C# 而不是 C++：它属于业务配置，改需求就要动（见 AGENTS.md 2.9）。
    /// C++ 只提供"建 Action / 建 Context / 挂按键"这些 C# 做不到的原子操作。
    /// </summary>
    private void BuildInputAssets()
    {
        _moveForward = CreateInputAction(new FName("IA_MoveForward"), EInputActionValueType.Axis1D);
        _moveRight = CreateInputAction(new FName("IA_MoveRight"), EInputActionValueType.Axis1D);
        _lookYaw = CreateInputAction(new FName("IA_LookYaw"), EInputActionValueType.Axis1D);
        _lookPitch = CreateInputAction(new FName("IA_LookPitch"), EInputActionValueType.Axis1D);
        _jump = CreateInputAction(new FName("IA_Jump"), EInputActionValueType.Boolean);
        _sprint = CreateInputAction(new FName("IA_Sprint"), EInputActionValueType.Boolean);

        _mappingContext = CreateMappingContext(new FName("IMC_RPG"));
        if (_mappingContext == null)
        {
            PrintString("ARPGCharacter: 创建 IMC_RPG 失败，输入不可用。");
            return;
        }

        // 前后移动：W / S(反向) / 手柄左摇杆 Y
        if (_moveForward != null)
        {
            MapKey(_mappingContext, _moveForward, new FKey("W"), false);
            MapKey(_mappingContext, _moveForward, new FKey("S"), true);
            MapKey(_mappingContext, _moveForward, new FKey("Gamepad_LeftY"), false);
        }

        // 左右移动：D / A(反向) / 手柄左摇杆 X
        if (_moveRight != null)
        {
            MapKey(_mappingContext, _moveRight, new FKey("D"), false);
            MapKey(_mappingContext, _moveRight, new FKey("A"), true);
            MapKey(_mappingContext, _moveRight, new FKey("Gamepad_LeftX"), false);
        }

        // 视角：鼠标 X / Y、手柄右摇杆
        if (_lookYaw != null)
        {
            MapKey(_mappingContext, _lookYaw, new FKey("MouseX"), false);
            MapKey(_mappingContext, _lookYaw, new FKey("Gamepad_RightX"), false);
        }
        if (_lookPitch != null)
        {
            // MouseY 必须取反：鼠标上移时 MouseY 是正值，而 AddControllerPitchInput
            // 约定**负值=抬头**。所以这里加 Negate 修改器，与引擎第三人称模板一致，
            // 否则上下会反（鼠标上移反而低头）。
            MapKey(_mappingContext, _lookPitch, new FKey("MouseY"), true);
            // 手柄右摇杆 Y 的轴向约定与鼠标相反（推上为负），同样取反后才是"推上抬头"。
            MapKey(_mappingContext, _lookPitch, new FKey("Gamepad_RightY"), true);
        }

        // 跳跃：Space / 手柄 A
        if (_jump != null)
        {
            MapKey(_mappingContext, _jump, new FKey("SpaceBar"), false);
            MapKey(_mappingContext, _jump, new FKey("Gamepad_FaceButton_Bottom"), false);
        }

        // 跑步：LeftShift / 手柄左摇杆按下
        if (_sprint != null)
        {
            MapKey(_mappingContext, _sprint, new FKey("LeftShift"), false);
            MapKey(_mappingContext, _sprint, new FKey("Gamepad_LeftThumbstick"), false);
        }
    }

    // ---- 移动 ----------------------------------------------------------

    /// <summary>
    /// 把控制器朝向的偏航角（度）换算为水平面的前/右单位向量。
    /// UnrealSharp 未向 C# 暴露 FRotator::Vector()/RotateVector()，这里用等价三角函数实现。
    /// </summary>
    private static void GetYawBasis(double yawDegrees, out FVector forward, out FVector right)
    {
        double yawRadians = yawDegrees * (System.Math.PI / 180.0);
        float cos = (float)System.Math.Cos(yawRadians);
        float sin = (float)System.Math.Sin(yawRadians);

        forward = new FVector(cos, sin, 0.0f);
        right = new FVector(-sin, cos, 0.0f);
    }

    [UFunction]
    private void OnMoveForward(FInputActionValue actionValue, float elapsedTime, float triggeredTime, UInputAction sourceAction)
    {
        if (Controller == null)
        {
            return;
        }

        float axis = actionValue.GetAxis1D();
        if (axis == 0.0f)
        {
            return;
        }

        GetYawBasis(Controller.ControlRotation.Yaw, out FVector forward, out _);
        AddMovementInput(forward, axis);
    }

    [UFunction]
    private void OnMoveRight(FInputActionValue actionValue, float elapsedTime, float triggeredTime, UInputAction sourceAction)
    {
        if (Controller == null)
        {
            return;
        }

        float axis = actionValue.GetAxis1D();
        if (axis == 0.0f)
        {
            return;
        }

        GetYawBasis(Controller.ControlRotation.Yaw, out _, out FVector right);
        AddMovementInput(right, axis);
    }

    // ---- 视角 ----------------------------------------------------------

    [UFunction]
    private void OnLookYaw(FInputActionValue actionValue, float elapsedTime, float triggeredTime, UInputAction sourceAction)
    {
        AddControllerYawInput(actionValue.GetAxis1D() * LookSensitivity);
    }

    [UFunction]
    private void OnLookPitch(FInputActionValue actionValue, float elapsedTime, float triggeredTime, UInputAction sourceAction)
    {
        // 映射层已用 Negate 把 MouseY 修正为"负值=抬头"的约定（见 BuildInputAssets）。
        // 这里再叠一次可选的 Y 轴反转，让 ARPGPlayerController.InvertLookY 真正生效。
        float scale = LookSensitivity;
        if (Controller is ARPGPlayerController playerController && playerController.InvertLookY)
        {
            scale = -scale;
        }

        AddControllerPitchInput(actionValue.GetAxis1D() * scale);
    }

    // ---- 跳跃 ----------------------------------------------------------

    [UFunction]
    private void OnJumpStarted(FInputActionValue actionValue, float elapsedTime, float triggeredTime, UInputAction sourceAction)
    {
        Jump();
    }

    [UFunction]
    private void OnJumpCompleted(FInputActionValue actionValue, float elapsedTime, float triggeredTime, UInputAction sourceAction)
    {
        StopJumping();
    }

    // ---- 走 / 跑 -------------------------------------------------------

    [UFunction]
    private void OnSprintStarted(FInputActionValue actionValue, float elapsedTime, float triggeredTime, UInputAction sourceAction)
    {
        CharacterMovement.MaxWalkSpeed = RunSpeed;
    }

    [UFunction]
    private void OnSprintCompleted(FInputActionValue actionValue, float elapsedTime, float triggeredTime, UInputAction sourceAction)
    {
        CharacterMovement.MaxWalkSpeed = WalkSpeed;
    }
}
