"""
把游戏框架类蓝图统一放到 `/Game/` 根目录下。

位置依据：用户明确要求「GameMode / PlayerPawn / GameState 这些东西全都放到 /Game/ 下」，
并已手动把 BP_RPGCharacter 移到 /Game/ 根。本脚本把其余框架类也归位到同一层级。

框架类集合（与 SBFC 的 UGCGameMode / UGCGameState / UGCPlayerController /
UGCPlayerPawn / UGCPlayerState 一一对应）：
    /Game/BP_RPGGameMode
    /Game/BP_RPGGameState
    /Game/BP_RPGPlayerController
    /Game/BP_RPGPlayerState
    /Game/BP_RPGCharacter          （承担 PlayerPawn 角色）

幂等：已在根目录的跳过；在 /Game/Blueprint/ 下的移过来（rename_asset 会自动更新引用）；
重复的旧副本会被清理。

用法：
  UnrealEditor.exe <project>.uproject -ExecCmds="py <this file>" -nosplash
  或编辑器控制台：py "<this file>"
"""

import unreal

LOG_PREFIX = "RPGLayout2"

FRAMEWORK = [
    "BP_RPGGameMode",
    "BP_RPGGameState",
    "BP_RPGPlayerController",
    "BP_RPGPlayerState",
    "BP_RPGCharacter",
]

# 需要搬到 /Game/ 根的来源目录（按优先级）
SOURCE_DIRS = ["/Game/Blueprint", "/Game/Blueprint/Actor"]


def log(msg):
    unreal.log(f"[{LOG_PREFIX}] {msg}")


def warn(msg):
    unreal.log_warning(f"[{LOG_PREFIX}] {msg}")


def exists(path):
    return unreal.EditorAssetLibrary.does_asset_exist(path)


def run_once():
    moved = []
    kept = []
    removed = []

    for name in FRAMEWORK:
        target = f"/Game/{name}"

        if exists(target):
            kept.append(name)
            log(f"已在目标位置: {target}")
        else:
            src = None
            for d in SOURCE_DIRS:
                if exists(f"{d}/{name}"):
                    src = f"{d}/{name}"
                    break
            if src is None:
                warn(f"找不到来源资产（{name}），跳过")
                continue
            if unreal.EditorAssetLibrary.rename_asset(src, target):
                moved.append(name)
                log(f"已移动: {src} -> {target}")
            else:
                warn(f"移动失败: {src}")

    # 清理 /Game/Blueprint/ 下与根目录重复的框架类 BP
    for name in FRAMEWORK:
        dup = f"/Game/Blueprint/{name}"
        if name != "BP_RPGCharacter":
            continue
        if exists(dup) and exists(f"/Game/{name}"):
            if unreal.EditorAssetLibrary.delete_asset(dup):
                removed.append(dup)
                log(f"已删除重复副本: {dup}")
            else:
                warn(f"删除重复副本失败: {dup}")

    for name in FRAMEWORK:
        p = f"/Game/{name}"
        if exists(p):
            unreal.EditorAssetLibrary.save_asset(p, only_if_is_dirty=False)

    log(f"完成。移动 {len(moved)} 个 / 已在位 {len(kept)} 个 / 清理重复 {len(removed)} 个")


run_once()
