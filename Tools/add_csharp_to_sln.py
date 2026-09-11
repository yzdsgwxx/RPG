"""
把 UnrealSharp 的 C# 项目合并进 UBT 生成的 RPG.sln。

背景：
  - UBT 的 -ProjectFiles 只生成 C++ 工程（UE5.vcxproj / RPG.vcxproj），
    它不认识 UnrealSharp 的托管工程，所以 RPG.sln 里没有 C# 项目。
  - UnrealSharp 自己生成的 Script/ManagedRPG.sln 只含 C# 项目，不含 C++ 游戏模块。
  - 本脚本把两边合并：在 RPG.sln 里追加 ManagedRPG / RPG.RuntimeGlue 两个 C# 项目。

注意：
  **每次重新运行 UBT 的 -ProjectFiles（或在编辑器里 Generate Visual Studio project files）
  都会重写 RPG.sln，覆盖本脚本的改动。** 覆盖后重新执行本脚本即可。

用法：
  python Tools/add_csharp_to_sln.py
  python Tools/add_csharp_to_sln.py "D:\\path\\to\\RPG.sln"
"""

import os
import re
import sys

DEFAULT_SLN = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "RPG.sln"
)

# UnrealSharp 生成的两个托管工程（GUID 与 Script/ManagedRPG.sln 保持一致）
CS_GUID = "{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}"  # C# 项目类型 GUID
CS_PROJECTS = [
    ("ManagedRPG", r"Script\ManagedRPG\ManagedRPG.csproj",
     "{DE089AAE-9914-41FF-988C-D037EC15CBB1}"),
    ("RPG.RuntimeGlue", r"Script\RPG.RuntimeGlue\RPG.RuntimeGlue.csproj",
     "{D5563F72-7008-44FA-8480-9870FE10944F}"),
]
GAMES_FOLDER = "{DE1F8B53-6C02-3C13-9101-A7C8D96F3FF6}"  # sln 里的 "Games" 分组


def csharp_config_for(solution_config):
    """把 UE 的解决方案配置映射到 C# 的 Debug/Release。"""
    return "Debug|Any CPU" if "DebugGame" in solution_config else "Release|Any CPU"


def main():
    sln_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SLN
    if not os.path.isfile(sln_path):
        print(f"[错误] 找不到解决方案文件: {sln_path}")
        return 1

    with open(sln_path, "r", encoding="utf-8-sig") as f:
        text = f.read()

    if CS_PROJECTS[0][2] in text:
        print("[跳过] RPG.sln 里已包含 ManagedRPG，无需重复合并。")
        return 0

    # 1) 收集 UE 的解决方案配置
    m = re.search(
        r"GlobalSection\(SolutionConfigurationPlatforms\) = preSolution(.*?)EndGlobalSection",
        text, re.S)
    if not m:
        print("[错误] 解析 SolutionConfigurationPlatforms 失败。")
        return 1
    solution_configs = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if "=" in line:
            solution_configs.append(line.split("=")[0].strip())

    # 2) 追加 C# 的项目声明（插到 Global 之前）
    project_block = ""
    for name, rel_path, guid in CS_PROJECTS:
        project_block += (
            f'Project("{CS_GUID}") = "{name}", "{rel_path}", "{guid}"\n'
            f"EndProject\n"
        )
    text = text.replace("\nGlobal\n", "\n" + project_block + "Global\n", 1)

    # 3) 追加 C# 的配置映射（插到 ProjectConfigurationPlatforms 末尾）
    mapping_lines = []
    for _, _, guid in CS_PROJECTS:
        for cfg in solution_configs:
            cs = csharp_config_for(cfg)
            mapping_lines.append(f"\t\t{guid}.{cfg}.ActiveCfg = {cs}")
            mapping_lines.append(f"\t\t{guid}.{cfg}.Build.0 = {cs}")
    mapping_block = "\n".join(mapping_lines) + "\n"

    text, count = re.subn(
        r"(GlobalSection\(ProjectConfigurationPlatforms\) = postSolution\n)(.*?)(\tEndGlobalSection\n)",
        lambda mm: mm.group(1) + mm.group(2) + mapping_block + mm.group(3),
        text, count=1, flags=re.S)
    if count == 0:
        print("[错误] 解析 ProjectConfigurationPlatforms 失败。")
        return 1

    # 4) 把 C# 项目挂到 Games 分组下
    nested_lines = "".join(f"\t\t{guid} = {GAMES_FOLDER}\n" for _, _, guid in CS_PROJECTS)
    text, count = re.subn(
        r"(GlobalSection\(NestedProjects\) = preSolution\n)(.*?)(\tEndGlobalSection\n)",
        lambda mm: mm.group(1) + mm.group(2) + nested_lines + mm.group(3),
        text, count=1, flags=re.S)
    if count == 0:
        # 没有分组段就自己建一个
        text = text.replace(
            "\tGlobalSection(SolutionProperties) = preSolution",
            "\tGlobalSection(NestedProjects) = preSolution\n" + nested_lines + "\tEndGlobalSection\n"
            "\tGlobalSection(SolutionProperties) = preSolution", 1)

    with open(sln_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"[完成] 已把 {len(CS_PROJECTS)} 个 C# 项目合并进: {sln_path}")
    for name, rel_path, guid in CS_PROJECTS:
        print(f"         {name}  ->  {rel_path}")
    print(f"         配置映射 {len(solution_configs)} 条 x {len(CS_PROJECTS)} 个项目")
    return 0


if __name__ == "__main__":
    sys.exit(main())
