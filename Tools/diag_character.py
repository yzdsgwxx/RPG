"""
诊断脚本：检查 NewMap 里角色实例的关键属性，定位输入失效原因。

检查项：
  1. 地图里 BP_RPGCharacter 实例是否存在、位置
  2. 它的 AutoPossessPlayer 是否为 Player0（输入能否路由到它的前提）
  3. 它的 Mesh 组件是否配好骨骼网格体 + 动画类
  4. 它的类：是蓝图实例还是纯 C# 实例
  5. GameMode 蓝图上的类引用是否配好（DefaultPawnClass / PlayerControllerClass / GameStateClass）

用法：
  UnrealEditor.exe <project>.uproject -ExecCmds="py <this file>" -nosplash
  或编辑器控制台：py "<this file>"
"""

import unreal

LOG = "RPGDiag"
MAP_PATH = "/Game/Maps/NewMap"
CHAR_BP = "/Game/BP_RPGCharacter"
GM_BP = "/Game/BP_RPGGameMode"


def log(msg):
    unreal.log(f"[{LOG}] {msg}")


def warn(msg):
    unreal.log_warning(f"[{LOG}] {msg}")


def describe_actor(actor):
    cls = actor.get_class()
    log(f"实例: {actor.get_name()}  类={cls.get_name()}  路径={cls.get_path_name()}")

    try:
        loc = actor.get_actor_location()
        log(f"  位置: ({loc.x:.0f}, {loc.y:.0f}, {loc.z:.0f})")
    except Exception as exc:  # noqa: BLE001
        log(f"  位置读取失败: {exc}")

    # AutoPossessPlayer —— 输入能否路由到该 Pawn 的关键
    for prop in ("auto_possess_player", "AutoPossessPlayer"):
        try:
            val = actor.get_editor_property(prop)
            log(f"  AutoPossessPlayer = {val}")
            break
        except Exception:  # noqa: BLE001
            continue
    else:
        warn("  读不到 AutoPossessPlayer 属性")

    # Mesh 组件
    try:
        mesh = actor.get_editor_property("mesh")
        if mesh is None:
            warn("  Mesh 组件为空")
        else:
            sk_asset = mesh.get_editor_property("skeletal_mesh_asset")
            anim_cls = mesh.get_editor_property("anim_class")
            log(f"  SkeletalMesh = {sk_asset.get_path_name() if sk_asset else 'None'}")
            log(f"  AnimClass    = {anim_cls.get_path_name() if anim_cls else 'None'}")
    except Exception as exc:  # noqa: BLE001
        warn(f"  Mesh 检查失败: {exc}")


def check_map():
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        warn(f"找不到地图: {MAP_PATH}")
        return
    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    log(f"已加载 {MAP_PATH}")

    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    found = 0
    for a in actors.get_all_level_actors():
        n = a.get_class().get_name()
        if "RPGCharacter" in n:
            found += 1
            describe_actor(a)
    if found == 0:
        warn("地图里没有找到任何 RPGCharacter 实例！")
    else:
        log(f"共找到 {found} 个角色实例")


def check_bp_defaults():
    if not unreal.EditorAssetLibrary.does_asset_exist(GM_BP):
        warn(f"找不到 {GM_BP}")
        return
    bp = unreal.load_asset(GM_BP)
    cdo = unreal.get_default_object(bp.generated_class())
    for prop in ("default_pawn_class", "player_controller_class",
                 "game_state_class", "player_state_class"):
        try:
            val = cdo.get_editor_property(prop)
            path = val.get_path_name() if val else "None"
            log(f"GameMode.{prop} = {path}")
        except Exception as exc:  # noqa: BLE001
            warn(f"GameMode.{prop} 读取失败: {exc}")


log("==================== 诊断开始 ====================")
check_bp_defaults()
check_map()
log("==================== 诊断结束 ====================")
