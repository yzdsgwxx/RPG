using UnrealBuildTool;
using System.Collections.Generic;

public class RPGEditorTarget : TargetRules
{
	public RPGEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.V7;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("RPG");
	}
}
