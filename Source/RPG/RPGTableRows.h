#pragma once

#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "RPGTableRows.generated.h"

class UTexture2D;
class AActor;

/**
 * DataTable 行结构示例。
 *
 * 为什么必须在 C++ 里定义：
 *   UE 要求 DataTable 的行结构必须继承 FTableRowBase（见 Engine/Classes/Engine/DataTable.h:89）。
 *   而 UnrealSharp 把 C# 的 [UStruct] 编译成 UCSScriptStruct（继承 UUserDefinedStruct），
 *   编辑器里手工创建的 User Defined Struct 也是 UUserDefinedStruct —— 都不满足这个继承要求，
 *   因此不能作为 DataTable 的行结构。
 *
 * 反过来，C++ 里定义的行结构会由 UnrealSharp 生成对应的 C# 类型，
 * 于是可以在 C# 中写 DataTable.FindRow<FRPGItemRow>(RowName) 直接读取。
 */
USTRUCT(BlueprintType)
struct RPG_API FRPGItemRow : public FTableRowBase
{
	GENERATED_BODY()

	/** 物品唯一 ID。 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RPG|Item")
	FName ItemId;

	/** 显示名。 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RPG|Item")
	FText DisplayName;

	/** 图标：软引用，运行时按需动态加载。 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RPG|Item")
	TSoftObjectPtr<UTexture2D> Icon;

	/** 生成物类：软类引用。 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RPG|Item")
	TSoftClassPtr<AActor> SpawnActorClass;

	/** 最大堆叠数。数值类型必须给默认值，否则 UHT 报 "not initialized properly"。 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RPG|Item")
	int32 MaxStack = 1;
};
