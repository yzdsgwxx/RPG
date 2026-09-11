"""探测 UnrealSharp 注册的 C# 类的真实 UE 路径。输出到日志，供外部 grep。"""

import unreal

LOG_PREFIX = "RPGProbe"


def log(msg):
    unreal.log(f"[{LOG_PREFIX}] {msg}")


world = unreal.EditorLevelLibrary.get_editor_world()

# 1) 直接试各种候选路径
CANDIDATES = [
    "/Script/UnrealSharp.RPGCharacter",
    "/Script/UnrealSharp.RPGCharacter_C",
    "/Script/ManagedRPG.RPGCharacter",
    "/Script/ManagedRPG.ARPGCharacter",
    "/Script/RPG.RPGCharacter",
    "/Script/RPG.ARPGCharacter",
    "/Script/UnrealSharp.RPGPlayerController",
    "/Script/UnrealSharp.RPGPlayerController_C",
    "/Script/UnrealSharp.RPGGameMode",
    "/Script/UnrealSharp.RPGGameMode_C",
]

for path in CANDIDATES:
    try:
        cls = unreal.load_class(None, path)
    except Exception as exc:  # noqa: BLE001
        log(f"load_class 异常 {path}: {exc}")
        continue
    log(f"{'命中' if cls else '未命中'} {path} -> {cls}")

# 2) 用对象列表命令把名字含 RPG 的 UClass 打到日志
unreal.SystemLibrary.execute_console_command(world, "obj list class=Class")
log("已请求 obj list class=Class，请在外层日志中筛选 RPG 开头的类名")
