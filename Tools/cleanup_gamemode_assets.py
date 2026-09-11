"""
清理脚本：删除本项目不再使用的自定义 GameMode / GameState 蓝图。

背景：
  项目决定 GameMode 直接用引擎自带的 GameModeBase，不需要自定义
  GameMode / GameState / PlayerState。对应的 C# 类已删除，这里清掉蓝图资产。

  删除项：
    /Game/BP_RPGGameMode
    /Game/BP_RPGGameState
  保留项（仍在用）：
    /Game/BP_RPGCharacter       （PlayerPawn，关卡里放置 + AutoPossessPlayer）
    /Game/BP_RPGPlayerController

注意：Config/DefaultEngine.ini 的 GlobalDefaultGameMode 已改为 /Script/Engine.GameModeBase。

用法：
  UnrealEditor.exe <project>.uproject -ExecCmds="py <this file>" -nosplash
  或编辑器控制台：py "<this file>"
"""

import unreal

LOG = "RPGCleanup"

TO_DELETE = [
    "/Game/BP_RPGGameMode",
    "/Game/BP_RPGGameState",
]


def log(msg):
    unreal.log(f"[{LOG}] {msg}")


def warn(msg):
    unreal.log_warning(f"[{LOG}] {msg}")


def run_once():
    for path in TO_DELETE:
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            if unreal.EditorAssetLibrary.delete_asset(path):
                log(f"已删除: {path}")
            else:
                warn(f"删除失败: {path}")
        else:
            log(f"不存在，跳过: {path}")

    # 顺带确认保留项还在
    for path in ("/Game/BP_RPGCharacter", "/Game/BP_RPGPlayerController"):
        log(f"{'存在' if unreal.EditorAssetLibrary.does_asset_exist(path) else '缺失'}: {path}")

    return True


run_once()
