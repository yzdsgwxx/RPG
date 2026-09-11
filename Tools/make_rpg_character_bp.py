"""
为 C# 的 ARPGCharacter 创建蓝图子类，并在蓝图里配置视觉（网格体 / 动画蓝图），
最后把 NewMap 里原来直接放置的 C# 实例替换成该蓝图的实例。

为什么视觉放蓝图：
  UnrealSharp 的 C# 类属性默认值写在 C# 构造函数里，编辑器对 C# 类 CDO 的改动
  不会持久化（每次重新生成类就丢）。而蓝图资产的默认值会随资产保存，
  所以「网格体、动画蓝图、材质」这类美术/策划要调的东西放蓝图最合适。

用法：
  UnrealEditor-Cmd.exe <project>.uproject -run=PythonScript -script="<this file>" -unattended -nopause -nosplash
  或编辑器控制台：py "<this file>"

幂等：蓝图已存在则复用；地图里已有该蓝图实例则只修正位置与 AutoPossessPlayer。
"""

import unreal

LOG_PREFIX = "RPGBP"
MAP_PATH = "/Game/NewMap"
BP_DIR = "/Game/Blueprint/Actor"
BP_NAME = "BP_RPGCharacter"

MESH_PATH = "/Game/ControlRig/Characters/Mannequins/Meshes/SKM_Manny.SKM_Manny"
ANIM_BP_PATH = "/Game/ControlRig/Characters/Mannequins/Animations/ABP_Manny.ABP_Manny_C"

CXX_CLASS_CANDIDATES = [
    "/Script/UnrealSharp.RPGCharacter_C",
]


def log(msg):
    unreal.log(f"[{LOG_PREFIX}] {msg}")


def warn(msg):
    unreal.log_warning(f"[{LOG_PREFIX}] {msg}")


def find_cxx_character_class():
    for path in CXX_CLASS_CANDIDATES:
        cls = unreal.load_class(None, path)
        if cls:
            log(f"C# 角色类: {path}")
            return cls, path
    return None, None


def get_or_create_blueprint(parent_class):
    full = f"{BP_DIR}/{BP_NAME}"
    existing = unreal.load_asset(full)
    if existing:
        log(f"蓝图已存在，复用: {full}")
        return existing

    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent_class)
    # 注意：不要设 bSkipClassPicker —— 它在 UE5.8 里不是编辑器可见属性，
    # Python 设不了会抛 "Failed to find property"。
    # AssetTools.create_asset 是程序化路径，本来就不会弹类选择器对话框。

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    bp = tools.create_asset(BP_NAME, BP_DIR, unreal.Blueprint, factory)
    if bp is None:
        warn("创建蓝图失败（可能已存在或目录不可写）")
        return None
    log(f"已创建蓝图: {full}")
    return bp


def configure_visuals(bp):
    """在蓝图里配置 Mesh 组件的骨骼网格体与动画蓝图。"""
    mesh_asset = unreal.load_asset(MESH_PATH)
    anim_class = unreal.load_class(None, ANIM_BP_PATH)

    if mesh_asset is None:
        warn(f"找不到骨骼网格体: {MESH_PATH}")
    if anim_class is None:
        warn(f"找不到动画蓝图类: {ANIM_BP_PATH}")

    generated_class = bp.generated_class()
    cdo = unreal.get_default_object(generated_class)
    mesh_comp = cdo.get_editor_property("mesh")
    if mesh_comp is None:
        warn("蓝图 CDO 上没有 Mesh 组件")
        return False

    ok = True
    if mesh_asset is not None:
        try:
            mesh_comp.set_editor_property("skeletal_mesh_asset", mesh_asset)
            log(f"已设置 SkeletalMesh: {MESH_PATH}")
        except Exception as exc:  # noqa: BLE001
            warn(f"设置 SkeletalMesh 失败: {exc}")
            ok = False

    if anim_class is not None:
        try:
            mesh_comp.set_editor_property("anim_class", anim_class)
            log(f"已设置 AnimClass: {ANIM_BP_PATH}")
        except Exception as exc:  # noqa: BLE001
            warn(f"设置 AnimClass 失败: {exc}")
            ok = False

    # Mesh 相对胶囊体的默认偏移/朝向（UE 骨架需要 -90 度偏航）
    try:
        mesh_comp.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, -89.0))
        mesh_comp.set_editor_property("relative_rotation", unreal.Rotator(0.0, -90.0, 0.0))
    except Exception as exc:  # noqa: BLE001
        log(f"设置 Mesh 相对变换跳过: {exc}")

    unreal.EditorAssetLibrary.save_asset(f"{BP_DIR}/{BP_NAME}", only_if_is_dirty=False)
    log("蓝图已保存")
    return ok


def main():
    cls, cls_path = find_cxx_character_class()
    if cls is None:
        return False
    run_once(cls)
    return True


def run_once(cls):
    bp = get_or_create_blueprint(cls)
    if bp is None:
        return
    configure_visuals(bp)

    # ---- 把 NewMap 里的实例换成蓝图实例 ----
    bp_class = unreal.load_class(None, f"{BP_DIR}/{BP_NAME}.{BP_NAME}_C")
    if bp_class is None:
        warn("无法解析蓝图生成类，跳过地图替换。")
        return

    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)

    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    old_actor = None
    existing_bp_actor = None
    for actor in actors.get_all_level_actors():
        if actor.get_class() == bp_class:
            existing_bp_actor = actor
        elif actor.get_class() == cls:
            old_actor = actor

    if existing_bp_actor is not None:
        log(f"地图中已有蓝图实例 {existing_bp_actor.get_name()}，复用。")
        target = existing_bp_actor
    else:
        location = unreal.Vector(0.0, 0.0, 212.0)
        rotation = unreal.Rotator(0.0, 0.0, 0.0)
        if old_actor is not None:
            location = old_actor.get_actor_location()
            rotation = old_actor.get_actor_rotation()
            log(f"沿用原实例位置 {location}")

        target = actors.spawn_actor_from_class(bp_class, location, rotation)
        if target is None:
            warn("生成蓝图实例失败。")
            return
        target.set_actor_label("BP_RPGCharacter_0")
        log(f"已生成蓝图实例: {target.get_name()}")

        # 删掉旧的纯 C# 实例，避免地图里有两个角色
        if old_actor is not None:
            actors.destroy_actor(old_actor)
            log(f"已移除旧的纯 C# 实例: {old_actor.get_name()}")

    for name in ("PLAYER0", "Player0"):
        try:
            target.set_editor_property("auto_possess_player", getattr(unreal.AutoReceiveInput, name))
            log(f"AutoPossessPlayer = {name}")
            break
        except Exception as exc:  # noqa: BLE001
            log(f"设置 AutoPossessPlayer[{name}] 失败: {exc}")

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("NewMap 已保存")


# =============================================================================
# 时序处理：-ExecCmds 在编辑器初始化早期执行，而 UnrealSharp 注册 C# 类更晚。
# 因此先试一次，找不到类就注册 Slate tick 回调持续重试（最多约 60 秒）。
# =============================================================================

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
    cls, _ = find_cxx_character_class()

    if cls is not None:
        try:
            run_once(cls)
        finally:
            stop_polling()
        return

    if _state["ticks"] >= MAX_TICKS:
        warn("等待超时：仍未找到 C# 的 RPGCharacter 类。")
        stop_polling()


if main():
    pass
else:
    log("C# 类尚未注册，开始轮询等待 UnrealSharp 完成加载…")
    _state["handle"] = unreal.register_slate_post_tick_callback(on_tick)
