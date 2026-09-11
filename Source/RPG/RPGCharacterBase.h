#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "InputActionValue.h"
#include "RPGCharacterBase.generated.h"

class UInputComponent;
class UInputAction;
class UInputMappingContext;
struct FKey;
class AController;

/**
 * ACharacter 的 C++ 中间基类 —— **只放工具/胶水代码，不放业务逻辑**（见 AGENTS.md 2.9）。
 *
 * 本类只做「C# / 蓝图做不到或做起来别扭」的几件事：
 *
 * 1. 暴露非 UFUNCTION 的引擎虚函数
 *    UnrealSharp 只能访问/覆写带 UFUNCTION 标记的函数，而下列虚函数没有：
 *      - APawn::SetupPlayerInputComponent(UInputComponent*)
 *      - APawn::PossessedBy(AController*)
 *    这里覆写它们，并用 BP_ 前缀的钩子转发给 C#（C# 侧名字会去掉 BP_ 前缀）。
 *
 * 2. 提供 EnhancedInput 的原子构造能力
 *      - EInputActionValueType 属于 UPROPERTY(BlueprintReadOnly)，在 C# 里不便赋值
 *      - ULocalPlayer::GetSubsystem<T>() 是 C++ 模板，未反射，C# 拿不到
 *    因此把「建 Action / 建 Context / 挂按键 / 注册 Context」拆成几个原子工具函数，
 *    具体的按键表与绑定逻辑写在 C#（Script/ManagedRPG/ARPGCharacter.cs）。
 */
UCLASS(Abstract)
class RPG_API ARPGCharacterBase : public ACharacter
{
	GENERATED_BODY()

public:
	ARPGCharacterBase();

	//~ Begin APawn interface
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void PossessedBy(AController* NewController) override;
	//~ End APawn interface

	// =========================================================================
	// 钩子：把非 UFUNCTION 的虚函数转发给 C#
	// =========================================================================

	/**
	 * 输入绑定钩子，由原生 SetupPlayerInputComponent 在 InputComponent 就绪后调用。
	 * C# 实现名：SetupPlayerInput。
	 */
	UFUNCTION(BlueprintNativeEvent, Category = "RPG|Input")
	void BP_SetupPlayerInput(UInputComponent* PlayerInputComponent);

	/**
	 * 被控制器占据时的钩子。C# 实现名：PossessedBy。
	 */
	UFUNCTION(BlueprintNativeEvent, Category = "RPG|Input")
	void BP_PossessedBy(AController* NewController);

	// =========================================================================
	// 工具：EnhancedInput 原子能力（供 C# / 蓝图使用）
	// =========================================================================

	/**
	 * 创建一个 UInputAction。
	 * 之所以包一层：EInputActionValueType 在 C# 侧是只读属性，不便赋值。
	 * Outer 用本角色，Action 生命周期随角色。
	 */
	UFUNCTION(BlueprintCallable, Category = "RPG|Input|Tool")
	UInputAction* BP_CreateInputAction(FName Name, EInputActionValueType ValueType);

	/** 创建一个空的 UInputMappingContext（Outer 用本角色）。 */
	UFUNCTION(BlueprintCallable, Category = "RPG|Input|Tool")
	UInputMappingContext* BP_CreateMappingContext(FName Name);

	/**
	 * 把按键映射到 Action。bNegate 为 true 时附加 Negate 修饰器（用于 S / A 这类反向键）。
	 * 之所以包一层：MapKey 返回的是 FEnhancedActionKeyMapping&，C# 侧不好接。
	 */
	UFUNCTION(BlueprintCallable, Category = "RPG|Input|Tool")
	void BP_MapKey(UInputMappingContext* Context, UInputAction* Action, FKey Key, bool bNegate);

	/**
	 * 把映射上下文注册到本地玩家的 EnhancedInput 子系统。
	 * 之所以包一层：ULocalPlayer::GetSubsystem<T>() 是 C++ 模板，未反射。
	 */
	UFUNCTION(BlueprintCallable, Category = "RPG|Input|Tool")
	void BP_AddMappingContext(UInputMappingContext* MappingContext, int32 Priority);

private:
	/** 内部实现：按优先级把上下文加进本地玩家子系统。 */
	void AddMappingContextInternal(UInputMappingContext* MappingContext, int32 Priority);
};
