"""
收尾脚本：
  1. 删除 BP_RPGPlayerState（本项目不使用 PlayerState）
  2. 在蓝图 `/Game/BP_RPGGameMode` 的 Class Defaults 里配置类引用：
       - PlayerControllerClass = RPGPlayerController
       - GameStateClass        = RPGGameState
     （PlayerStateClass 保持引擎默认 APlayerState —— 本项目不用 PlayerState）

为什么类引用放蓝图而不放 C# 构造函数：
  `TSubclassOf<T>(Type)` 会立刻按名字向 UnrealSharp 查类型。C# 构造函数可能在托管
  装配件注册完成**之前**执行（编辑器启动编译 CDO 时），此时查到 null 并固化进 CDO，
  运行时报：
      LogGameSession: Error: Player State class is invalid for game mode
      LogGameMode: Warning: No GameStateClass was specified
  蓝图默认值在装配件加载之后才确定，并且随资产持久化，因此可靠。

用法：
  UnrealEditor.exe <project>.uproject -ExecCmds="py <this file>" -nosplash
  或编辑器控制台：py "<this file>"
"""

import unreal

LOG_PREFIX = "RPGDefaults"

PLAYER_STATE_BP = "/Game/BP_RPGPlayerState"
GAME_MODE_BP = "/Game/BP_RPGGameMode"

# 目标类（UnrealSharp 把 C# 类注册在 /Script/UnrealSharp 下，可加载的是 _C 生成类）
PLAYER_CONTROLLER_CLASS = "/Script/UnrealSharp.RPGPlayerController_C"
GAME_STATE_CLASS = "/Script/UnrealSharp.RPGGameState_C"


def log(msg):
    unreal.log(f"[{LOG_PREFIX}] {msg}")


def warn(msg):
    unreal.log_warning(f"[{LOG_PREFIX}] {msg}")


def run_once():
    # ---- 1) 删除 BP_RPGPlayerState ----
    if unreal.EditorAssetLibrary.does_asset_exist(PLAYER_STATE_BP):
        if unreal.EditorAssetLibrary.delete_asset(PLAYER_STATE_BP):
            log(f"已删除: {PLAYER_STATE_BP}")
        else:
            warn(f"删除失败: {PLAYER_STATE_BP}")
    else:
        log(f"不存在，跳过删除: {PLAYER_STATE_BP}")

    # ---- 2) 在 BP_RPGGameMode 的 Class Defaults 上配置类引用 ----
    if not unreal.EditorAssetLibrary.does_asset_exist(GAME_MODE_BP):
        warn(f"找不到蓝图: {GAME_MODE_BP}")
        return False

    bp = unreal.load_asset(GAME_MODE_BP)
    if bp is None:
        warn(f"加载失败: {GAME_MODE_BP}")
        return False

    pc_class = unreal.load_class(None, PLAYER_CONTROLLER_CLASS)
    gs_class = unreal.load_class(None, GAME_STATE_CLASS)
    if pc_class is None:
        warn(f"找不到类: {PLAYER_CONTROLLER_CLASS}（UnrealSharp 可能还没注册）")
        return False
    if gs_class is None:
        warn(f"找不到类: {GAME_STATE_CLASS}（UnrealSharp 可能还没注册）")
        return False

    cdo = unreal.get_default_object(bp.generated_class())

    try:
        cdo.set_editor_property("player_controller_class", pc_class)
        log(f"PlayerControllerClass = {PLAYER_CONTROLLER_CLASS}")
    except Exception as exc:  # noqa: BLE001
        warn(f"设置 PlayerControllerClass 失败: {exc}")

    try:
        cdo.set_editor_property("game_state_class", gs_class)
        log(f"GameStateClass = {GAME_STATE_CLASS}")
    except Exception as exc:  # noqa: BLE001
        warn(f"设置 GameStateClass 失败: {exc}")

    # PlayerStateClass 不动：本项目不用 PlayerState，GameModeBase 会用默认 APlayerState。
    # DefaultPawnClass 也不动：C# 构造里已置为 None（不生成默认 Pawn）。

    unreal.EditorAssetLibrary.save_asset(GAME_MODE_BP, only_if_is_dirty=False)
    log(f"已保存 {GAME_MODE_BP}")
    return True


MAX_TICKS = 3600
_state = {"ticks": 0, "handle": None}


def stop_polling():
    handle = _state.get("handle")
    if handle is not None:
        try:
            unreal.unregister_slate_post_tick_callback(handle)
        except Exception:  # noqa: BLE001
            pass
        _state["handle"] = None


def on_tick(delta_seconds):
    _state["ticks"] += 1
    if run_once():
        stop_polling()
        return
    if _state["ticks"] >= MAX_TICKS:
        warn("等待超时：UnrealSharp 尚未注册 C# 类。")
        stop_polling()


if not run_once():
    log("C# 类尚未注册，开始轮询等待 UnrealSharp 完成加载…")
    _state["handle"] = unreal.register_slate_post_tick_callback(on_tick)
