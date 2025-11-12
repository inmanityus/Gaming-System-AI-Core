// Game Observer Plugin - AI-Driven Game Testing System
// Screenshot Capture & Telemetry Component

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Http.h"
#include "GameObserverComponent.generated.h"

UENUM(BlueprintType)
enum class EGameObserverCaptureEvent : uint8
{
	OnPlayerDamage UMETA(DisplayName = "Player Damage"),
	OnEnemySpawn UMETA(DisplayName = "Enemy Spawn"),
	OnEnterNewZone UMETA(DisplayName = "Enter New Zone"),
	OnUIPopup UMETA(DisplayName = "UI Popup"),
	OnHarvestComplete UMETA(DisplayName = "Harvest Complete"),
	OnNegotiationStart UMETA(DisplayName = "Negotiation Start"),
	OnDeathTriggered UMETA(DisplayName = "Death Triggered"),
	OnCombatStart UMETA(DisplayName = "Combat Start"),
	OnCombatEnd UMETA(DisplayName = "Combat End"),
	Baseline UMETA(DisplayName = "Baseline (Periodic)")
};

USTRUCT(BlueprintType)
struct FGameObserverTelemetry
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "Telemetry")
	FString ScreenshotFilename;

	UPROPERTY(BlueprintReadWrite, Category = "Telemetry")
	FString Timestamp;

	UPROPERTY(BlueprintReadWrite, Category = "Telemetry")
	FString EventType;

	UPROPERTY(BlueprintReadWrite, Category = "Telemetry")
	FVector PlayerLocation;

	UPROPERTY(BlueprintReadWrite, Category = "Telemetry")
	FRotator PlayerRotation;

	UPROPERTY(BlueprintReadWrite, Category = "Telemetry")
	FVector PlayerVelocity;

	UPROPERTY(BlueprintReadWrite, Category = "Telemetry")
	float PlayerHealth;

	UPROPERTY(BlueprintReadWrite, Category = "Telemetry")
	bool bIsInCombat;

	UPROPERTY(BlueprintReadWrite, Category = "Telemetry")
	FString CurrentZone;

	UPROPERTY(BlueprintReadWrite, Category = "Telemetry")
	FString CurrentObjective;

	UPROPERTY(BlueprintReadWrite, Category = "Telemetry")
	int32 CurrentFPS;

	UPROPERTY(BlueprintReadWrite, Category = "Telemetry")
	FString VeilFocus;
};

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class GAMEOBSERVER_API UGameObserverComponent : public UActorComponent
{
	GENERATED_BODY()

public:	
	UGameObserverComponent();

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

public:	
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	// Capture screenshot and telemetry on specific event
	UFUNCTION(BlueprintCallable, Category = "Game Observer")
	void CaptureEventSnapshot(EGameObserverCaptureEvent EventType, const FString& EventDetails = "");

	// Enable/disable observer system
	UFUNCTION(BlueprintCallable, Category = "Game Observer")
	void SetObserverEnabled(bool bEnabled);

	// Configure baseline capture rate (captures per second)
	UFUNCTION(BlueprintCallable, Category = "Game Observer")
	void SetBaselineCaptureRate(float CapturesPerSecond);

	// Get current telemetry data
	UFUNCTION(BlueprintCallable, Category = "Game Observer")
	FGameObserverTelemetry GetCurrentTelemetry();

	// HTTP API endpoint for external queries
	UFUNCTION(BlueprintCallable, Category = "Game Observer")
	void StartHTTPServer(int32 Port = 8765);

	UFUNCTION(BlueprintCallable, Category = "Game Observer")
	void StopHTTPServer();

private:
	// Screenshot capture
	void CaptureScreenshot(const FString& Filename);
	
	// Telemetry collection
	FGameObserverTelemetry CollectTelemetry(EGameObserverCaptureEvent EventType, const FString& EventDetails);
	
	// JSON export
	void ExportTelemetryJSON(const FGameObserverTelemetry& Telemetry, const FString& Filename);
	
	// Baseline capture timer
	void BaselineCaptureTimer(float DeltaTime);

	// HTTP request handler
	void HandleHTTPRequest(FHttpServerRequest&Request, const FHttpResultCallback& OnComplete);

	UPROPERTY()
	bool bObserverEnabled;

	UPROPERTY()
	float BaselineCaptureInterval; // Seconds between baseline captures

	UPROPERTY()
	float TimeSinceLastCapture;

	UPROPERTY()
	FString OutputDirectory;

	UPROPERTY()
	int32 CaptureCounter;

	UPROPERTY()
	bool bHTTPServerRunning;
};

