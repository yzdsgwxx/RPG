"""
把 BP_RPGCharacter 实例放置到 /Game/Maps/NewMap，并确保 AutoPossessPlayer = Player0。

用法：
  编辑器控制台：  py "D:/UnrealProjects/RPG/Tools/place_character.py"
  启动参数：      UnrealEditor.exe <project>.uproject -ExecCmds="py D:/UnrealProjects/RPG/Tools/place_character.py"

时序说明：
  -ExecCmds 在编辑器初始化早期就会执行，而 BP_RPGCharacter 的父类是 C# 类
  （ARPGCharacter），要等 UnrealSharp 注册完 C# 类型才加载得了这个蓝图。
  因此本脚本先尝试一次，找不到类时注册 Slate tick 回调持续重试（最多约 60 秒）。

幂等：地图中已存在角色实例时复用，仅修正 AutoPossessPlayer。只写 NewMap。

放的是**蓝图子类** BP_RPGCharacter —— 网格体、动画蓝图这类视觉配置都在蓝图里
（见 AGENTS.md 2.3），不要改成放裸的 C# 类。

注意：角色必须留在关卡里。删掉实例就没有 Pawn，玩家输入会全无反应。
      控制权由 ARPGCharacter.BeginPlay 的 EnsurePlayerPossession 显式接管
      （GameModeBase 生成的默认 Pawn 会抢先占据控制器，光靠 AutoPossess 不够）。
"""

import unreal

LOG_PREFIX = "RPGSetup"
MAP_PATH = "/Game/Maps/NewMap"
BP_CLASS_PATHS = [
    "/Game/BP_RPGCharacter.BP_RPGCharacter_C",
    "/Game/BP_RPGCharacter.BP_RPGCharacter",
]
MAX_TICKS = 3600  # 约 60 秒（按 60fps 估算）

SPAWN_OFFSET = unreal.Vector(0.0, 0.0, 120.0)

_state = {"ticks": 0, "handle": None}


def log(msg):
    unreal.log(f"[{LOG_PREFIX}] {msg}")


def warn(msg):
    unreal.log_warning(f"[{LOG_PREFIX}] {msg}")


def actors():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def find_character_class():
    for path in BP_CLASS_PATHS:
        try:
            cls = unreal.load_class(None, path)
        except Exception as exc:  # noqa: BLE001
            log(f"load_class 异常 {path}: {exc}")
            cls = None
        if cls:
            log(f"命中类路径: {path} -> {cls}")
            return cls, path
    return None, None


def place(cls, cls_path):
    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    log(f"已加载 {MAP_PATH}")

    existing = None
    player_start = None
    for actor in actors().get_all_level_actors():
        if actor.get_class() == cls:
            existing = actor
        elif isinstance(actor, unreal.PlayerStart):
            player_start = actor

    if existing is not None:
        character = existing
        log(f"已存在实例 {character.get_name()}，复用。")
    else:
        location = SPAWN_OFFSET
        if player_start is not None:
            location = player_start.get_actor_location() + SPAWN_OFFSET
        character = actors().spawn_actor_from_class(cls, location, unreal.Rotator(0.0, 0.0, 0.0))
        if character is None:
            warn("生成角色失败。")
            return False
        character.set_actor_label("RPGCharacter_0")
        log(f"已生成 {character.get_name()} ({cls_path}) @ {location}")

    for name in ("PLAYER0", "Player0"):
        try:
            character.set_editor_property("auto_possess_player", getattr(unreal.AutoReceiveInput, name))
            log(f"AutoPossessPlayer = {name}")
            break
        except Exception as exc:  # noqa: BLE001
            log(f"AutoPossessPlayer[{name}] 失败: {exc}")

    try:
        unreal.EditorLoadingAndSavingUtils.save_current_level()
        log("NewMap 已保存。")
    except Exception as exc:  # noqa: BLE001
        warn(f"保存地图失败: {exc}")
    return True


def on_tick(delta_seconds):
    _state["ticks"] += 1
    cls, cls_path = find_character_class()

    if cls is not None:
        try:
            place(cls, cls_path)
        finally:
            stop_polling()
        return

    if _state["ticks"] >= MAX_TICKS:
        warn("等待超时：仍未找到 BP_RPGCharacter。请确认 UnrealSharp 已加载 C# 程序集、"
             "且 /Game/BP_RPGCharacter 存在。")
        stop_polling()


def stop_polling():
    handle = _state.get("handle")
    if handle is not None:
        try:
            unreal.unregister_slate_post_tick_callback(handle)
        except Exception:  # noqa: BLE001
            pass
        _state["handle"] = None


def main():
    cls, cls_path = find_character_class()
    if cls is not None:
        place(cls, cls_path)
        return

    log("BP_RPGCharacter 尚未可加载，开始轮询等待 UnrealSharp 完成注册…")
    _state["handle"] = unreal.register_slate_post_tick_callback(on_tick)


main()
