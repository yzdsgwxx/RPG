#include "RPGCharacterBase.h"

#include "Components/InputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerController.h"
#include "InputAction.h"
#include "InputCoreTypes.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"

ARPGCharacterBase::ARPGCharacterBase()
{
	PrimaryActorTick.bCanEverTick = true;
}

void ARPGCharacterBase::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	// 此时 InputComponent 已就绪，交给 C#（或蓝图）绑定具体 Action
	BP_SetupPlayerInput(PlayerInputComponent);
}

void ARPGCharacterBase::PossessedBy(AController* NewController)
{
	Super::PossessedBy(NewController);

	BP_PossessedBy(NewController);
}

// =============================================================================
// 工具：EnhancedInput 原子能力
// =============================================================================

UInputAction* ARPGCharacterBase::BP_CreateInputAction(FName Name, EInputActionValueType ValueType)
{
	UInputAction* Action = NewObject<UInputAction>(this, Name);
	if (Action != nullptr)
	{
		Action->ValueType = ValueType;
	}
	return Action;
}

UInputMappingContext* ARPGCharacterBase::BP_CreateMappingContext(FName Name)
{
	return NewObject<UInputMappingContext>(this, Name);
}

void ARPGCharacterBase::BP_MapKey(UInputMappingContext* Context, UInputAction* Action, FKey Key, bool bNegate)
{
	if (Context == nullptr || Action == nullptr || !Key.IsValid())
	{
		return;
	}

	FEnhancedActionKeyMapping& Mapping = Context->MapKey(Action, Key);
	if (bNegate)
	{
		Mapping.Modifiers.Add(NewObject<UInputModifierNegate>(Context));
	}
}

void ARPGCharacterBase::BP_AddMappingContext(UInputMappingContext* MappingContext, int32 Priority)
{
	AddMappingContextInternal(MappingContext, Priority);
}

void ARPGCharacterBase::AddMappingContextInternal(UInputMappingContext* MappingContext, int32 Priority)
{
	if (MappingContext == nullptr)
	{
		return;
	}

	APlayerController* PlayerController = Cast<APlayerController>(GetController());
	if (PlayerController == nullptr)
	{
		// 尚未被玩家控制器占据（例如关卡加载阶段），等被占据后再注册
		return;
	}

	if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
			ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PlayerController->GetLocalPlayer()))
	{
		Subsystem->AddMappingContext(MappingContext, Priority);
	}
}

// =============================================================================
// 钩子默认实现（由 C# 覆写）
// =============================================================================

void ARPGCharacterBase::BP_SetupPlayerInput_Implementation(UInputComponent* PlayerInputComponent)
{
}

void ARPGCharacterBase::BP_PossessedBy_Implementation(AController* NewController)
{
}
