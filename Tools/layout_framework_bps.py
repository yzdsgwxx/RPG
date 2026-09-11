"""
按 SBFC 的目录约定归置游戏框架类：GameMode / GameState / PlayerController / PlayerState / PlayerPawn
全部放在 **`/Game/Blueprint/` 根下**（与 SBFC 的 `Asset/Blueprint/UGCGameMode.uasset` 等一致），
并为它们创建蓝图子类（父类 = 对应的 C# 类）。

SBFC 参考布局：
    Asset/Blueprint/
      ├── UGCGameMode.uasset        ← 框架类直接在 Blueprint/ 下
      ├── UGCGameState.uasset
      ├── UGCPlayerController.uasset
      ├── UGCPlayerPawn.uasset
      ├── UGCPlayerState.uasset
      ├── Actor/  AIBehavior/  Attributes/  Component/  Enum/  Prefabs/  UMG/   ← 其他资产才分子目录

本脚本幂等：已存在的资产复用；BP_RPGCharacter 若在 Actor/ 下会自动移到 Blueprint/。

用法：
  UnrealEditor.exe <project>.uproject -ExecCmds="py <this file>" -nosplash
  或编辑器控制台：py "<this file>"
"""

import unreal

LOG_PREFIX = "RPGLayout"
BP_DIR = "/Game/Blueprint"

# (资产名, C# 父类路径)  —— 父类路径来自 UnrealSharp 的挂载点 /Script/UnrealSharp
BLUEPRINTS = [
    ("BP_RPGGameMode", "/Script/UnrealSharp.RPGGameMode_C"),
    ("BP_RPGGameState", "/Script/UnrealSharp.RPGGameState_C"),
    ("BP_RPGPlayerController", "/Script/UnrealSharp.RPGPlayerController_C"),
    ("BP_RPGPlayerState", "/Script/UnrealSharp.RPGPlayerState_C"),
    ("BP_RPGCharacter", "/Script/UnrealSharp.RPGCharacter_C"),
]

# 需要从旧位置搬到 Blueprint/ 根下的资产
MOVE_FROM = {
    "BP_RPGCharacter": "/Game/Blueprint/Actor",
}

MAX_TICKS = 3600
_state = {"ticks": 0, "handle": None}


def log(msg):
    unreal.log(f"[{LOG_PREFIX}] {msg}")


def warn(msg):
    unreal.log_warning(f"[{LOG_PREFIX}] {msg}")


def resolve_parent(candidates):
    for path in candidates:
        cls = unreal.load_class(None, path)
        if cls:
            return cls, path
    return None, None


def ensure_blueprint(name, parent_class):
    """在 BP_DIR 下确保存在名为 name 的蓝图（父类为 parent_class）。"""
    target = f"{BP_DIR}/{name}"

    # 1) 目标位置已存在
    if unreal.EditorAssetLibrary.does_asset_exist(target):
        log(f"已存在，复用: {target}")
        return unreal.load_asset(target)

    # 2) 需要从旧位置搬过来
    old_dir = MOVE_FROM.get(name)
    if old_dir and unreal.EditorAssetLibrary.does_asset_exist(f"{old_dir}/{name}"):
        moved = unreal.EditorAssetLibrary.rename_asset(f"{old_dir}/{name}", target)
        if moved:
            log(f"已移动: {old_dir}/{name} -> {target}")
            return unreal.load_asset(target)
        warn(f"移动失败: {old_dir}/{name}")

    # 3) 新建
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent_class)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    bp = tools.create_asset(name, BP_DIR, unreal.Blueprint, factory)
    if bp is None:
        warn(f"创建蓝图失败: {target}")
        return None
    log(f"已创建: {target}")
    return bp


def run_once():
    # C# 类是否就绪（UnrealSharp 加载完才有）
    probe, probe_path = resolve_parent([BLUEPRINTS[0][1]])
    if probe is None:
        return False

    created = []
    for name, parent_path in BLUEPRINTS:
        parent, resolved = resolve_parent([parent_path])
        if parent is None:
            warn(f"找不到父类 {parent_path}（{name} 跳过）")
            continue
        bp = ensure_blueprint(name, parent)
        if bp is not None:
            created.append(name)

    # 逐个保存
    for name in created:
        unreal.EditorAssetLibrary.save_asset(f"{BP_DIR}/{name}", only_if_is_dirty=False)

    log(f"完成。{BP_DIR} 下的框架类：{', '.join(created)}")
    return True


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


if run_once():
    pass
else:
    log("C# 类尚未注册，开始轮询等待 UnrealSharp 完成加载…")
    _state["handle"] = unreal.register_slate_post_tick_callback(on_tick)
