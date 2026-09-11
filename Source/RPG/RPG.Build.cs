using UnrealBuildTool;

public class RPG : ModuleRules
{
	public RPG(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			// 输入走 EnhancedInput（编辑器会把 DefaultPlayerInputClass 强制改回 EnhancedInput.*，
			// 因此项目统一使用 EnhancedInput，不再依赖传统 Action/Axis Mapping）
			"EnhancedInput",
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
		});
	}
}
