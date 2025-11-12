// Game Observer Plugin - AI-Driven Game Testing System
// Screenshot Capture & Telemetry Implementation

#include "GameObserverComponent.h"
#include "Engine/GameViewportClient.h"
#include "ImageWriteQueue.h"
#include "ImageWriteTask.h"
#include "Misc/FileHelper.h"
#include "Json.h"
#include "JsonUtilities.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/Engine.h"

UGameObserverComponent::UGameObserverComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	
	bObserverEnabled = true;
	BaselineCaptureInterval = 0.5f; // Default: 2 FPS baseline capture
	TimeSinceLastCapture = 0.0f;
	CaptureCounter = 0;
	bHTTPServerRunning = false;
	
	// Set output directory
	OutputDirectory = FPaths::ProjectDir() / TEXT("GameObserver") / TEXT("Captures");
	
	// Create directory if it doesn't exist
	IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();
	if (!PlatformFile.DirectoryExists(*OutputDirectory))
	{
		PlatformFile.CreateDirectoryTree(*OutputDirectory);
	}
}

void UGameObserverComponent::BeginPlay()
{
	Super::BeginPlay();
	
	UE_LOG(LogTemp, Log, TEXT("GameObserver: Component initialized - Output: %s"), *OutputDirectory);
}

void UGameObserverComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (bHTTPServerRunning)
	{
		StopHTTPServer();
	}
	
	Super::EndPlay(EndPlayReason);
}

void UGameObserverComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (bObserverEnabled)
	{
		BaselineCaptureTimer(DeltaTime);
	}
}

void UGameObserverComponent::SetObserverEnabled(bool bEnabled)
{
	bObserverEnabled = bEnabled;
	UE_LOG(LogTemp, Log, TEXT("GameObserver: %s"), bEnabled ? TEXT("Enabled") : TEXT("Disabled"));
}

void UGameObserverComponent::SetBaselineCaptureRate(float CapturesPerSecond)
{
	if (CapturesPerSecond > 0.0f)
	{
		BaselineCaptureInterval = 1.0f / CapturesPerSecond;
		UE_LOG(LogTemp, Log, TEXT("GameObserver: Baseline capture rate set to %.2f FPS"), CapturesPerSecond);
	}
}

void UGameObserverComponent::CaptureEventSnapshot(EGameObserverCaptureEvent EventType, const FString& EventDetails)
{
	if (!bObserverEnabled)
	{
		return;
	}

	CaptureCounter++;
	
	// Generate filenames
	FString Timestamp = FDateTime::Now().ToString(TEXT("%Y%m%d_%H%M%S_%f"));
	FString EventName = UEnum::GetValueAsString(EventType);
	EventName.RemoveFromStart(TEXT("EGameObserverCaptureEvent::"));
	
	FString ScreenshotFilename = FString::Printf(TEXT("%s_%04d_%s.png"), *EventName, CaptureCounter, *Timestamp);
	FString TelemetryFilename = FString::Printf(TEXT("%s_%04d_%s.json"), *EventName, CaptureCounter, *Timestamp);
	
	// Collect telemetry
	FGameObserverTelemetry Telemetry = CollectTelemetry(EventType, EventDetails);
	Telemetry.ScreenshotFilename = ScreenshotFilename;
	Telemetry.Timestamp = FDateTime::Now().ToIso8601();
	Telemetry.EventType = EventName;
	
	// Capture screenshot
	CaptureScreenshot(ScreenshotFilename);
	
	// Export telemetry JSON
	ExportTelemetryJSON(Telemetry, TelemetryFilename);
	
	UE_LOG(LogTemp, Log, TEXT("GameObserver: Captured %s - %s"), *EventName, *EventDetails);
}

void UGameObserverComponent::BaselineCaptureTimer(float DeltaTime)
{
	TimeSinceLastCapture += DeltaTime;
	
	if (TimeSinceLastCapture >= BaselineCaptureInterval)
	{
		CaptureEventSnapshot(EGameObserverCaptureEvent::Baseline, TEXT("Periodic baseline capture"));
		TimeSinceLastCapture = 0.0f;
	}
}

void UGameObserverComponent::CaptureScreenshot(const FString& Filename)
{
	if (!GEngine || !GEngine->GameViewport)
	{
		UE_LOG(LogTemp, Warning, TEXT("GameObserver: Cannot capture screenshot - no viewport"));
		return;
	}

	FString FullPath = OutputDirectory / Filename;
	
	// Request screenshot
	FScreenshotRequest::RequestScreenshot(FullPath, false, false);
}

FGameObserverTelemetry UGameObserverComponent::CollectTelemetry(EGameObserverCaptureEvent EventType, const FString& EventDetails)
{
	FGameObserverTelemetry Telemetry;
	
	// Get player controller
	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (PC)
	{
		// Player location & rotation
		FVector Location;
		FRotator Rotation;
		PC->GetPlayerViewPoint(Location, Rotation);
		
		Telemetry.PlayerLocation = Location;
		Telemetry.PlayerRotation = Rotation;
		
		// Player character data
		if (ACharacter* Character = PC->GetCharacter())
		{
			Telemetry.PlayerVelocity = Character->GetVelocity();
			
			// Health (assuming character has health - customize for your game)
			// Telemetry.PlayerHealth = Character->GetHealth(); // Implement based on your game
			Telemetry.PlayerHealth = 100.0f; // Placeholder
		}
		
		// Combat state (customize based on your game)
		Telemetry.bIsInCombat = false; // Placeholder
	}
	
	// Zone information (customize based on your game)
	Telemetry.CurrentZone = TEXT("Unknown"); // Placeholder
	Telemetry.CurrentObjective = TEXT("None"); // Placeholder
	
	// FPS
	Telemetry.CurrentFPS = FMath::RoundToInt(1.0f / GetWorld()->GetDeltaSeconds());
	
	// Veil Focus (customize based on your game)
	Telemetry.VeilFocus = TEXT("Both"); // Placeholder
	
	return Telemetry;
}

void UGameObserverComponent::ExportTelemetryJSON(const FGameObserverTelemetry& Telemetry, const FString& Filename)
{
	TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject());
	
	// Basic info
	JsonObject->SetStringField(TEXT("screenshot_filename"), Telemetry.ScreenshotFilename);
	JsonObject->SetStringField(TEXT("timestamp"), Telemetry.Timestamp);
	JsonObject->SetStringField(TEXT("event_type"), Telemetry.EventType);
	
	// Player data
	TSharedPtr<FJsonObject> PlayerData = MakeShareable(new FJsonObject());
	
	TSharedPtr<FJsonObject> Location = MakeShareable(new FJsonObject());
	Location->SetNumberField(TEXT("x"), Telemetry.PlayerLocation.X);
	Location->SetNumberField(TEXT("y"), Telemetry.PlayerLocation.Y);
	Location->SetNumberField(TEXT("z"), Telemetry.PlayerLocation.Z);
	PlayerData->SetObjectField(TEXT("location"), Location);
	
	TSharedPtr<FJsonObject> Rotation = MakeShareable(new FJsonObject());
	Rotation->SetNumberField(TEXT("pitch"), Telemetry.PlayerRotation.Pitch);
	Rotation->SetNumberField(TEXT("yaw"), Telemetry.PlayerRotation.Yaw);
	Rotation->SetNumberField(TEXT("roll"), Telemetry.PlayerRotation.Roll);
	PlayerData->SetObjectField(TEXT("rotation"), Rotation);
	
	TSharedPtr<FJsonObject> Velocity = MakeShareable(new FJsonObject());
	Velocity->SetNumberField(TEXT("x"), Telemetry.PlayerVelocity.X);
	Velocity->SetNumberField(TEXT("y"), Telemetry.PlayerVelocity.Y);
	Velocity->SetNumberField(TEXT("z"), Telemetry.PlayerVelocity.Z);
	PlayerData->SetObjectField(TEXT("velocity"), Velocity);
	
	PlayerData->SetNumberField(TEXT("health"), Telemetry.PlayerHealth);
	PlayerData->SetBoolField(TEXT("is_in_combat"), Telemetry.bIsInCombat);
	
	JsonObject->SetObjectField(TEXT("player_data"), PlayerData);
	
	// World data
	TSharedPtr<FJsonObject> WorldData = MakeShareable(new FJsonObject());
	WorldData->SetStringField(TEXT("zone_name"), Telemetry.CurrentZone);
	WorldData->SetStringField(TEXT("current_objective_id"), Telemetry.CurrentObjective);
	JsonObject->SetObjectField(TEXT("world_data"), WorldData);
	
	// Rendering data
	TSharedPtr<FJsonObject> RenderingData = MakeShareable(new FJsonObject());
	RenderingData->SetNumberField(TEXT("current_fps"), Telemetry.CurrentFPS);
	JsonObject->SetObjectField(TEXT("rendering_data"), RenderingData);
	
	// Veil sight data (game-specific)
	JsonObject->SetStringField(TEXT("veil_focus"), Telemetry.VeilFocus);
	
	// Convert to JSON string
	FString JsonString;
	TSharedRef<TJsonWriter<>> JsonWriter = TJsonWriterFactory<>::Create(&JsonString);
	FJsonSerializer::Serialize(JsonObject.ToSharedRef(), JsonWriter);
	
	// Write to file
	FString FullPath = OutputDirectory / Filename;
	FFileHelper::SaveStringToFile(JsonString, *FullPath);
}

FGameObserverTelemetry UGameObserverComponent::GetCurrentTelemetry()
{
	return CollectTelemetry(EGameObserverCaptureEvent::Baseline, TEXT("Manual query"));
}

void UGameObserverComponent::StartHTTPServer(int32 Port)
{
	UE_LOG(LogTemp, Log, TEXT("GameObserver: HTTP server starting on port %d"), Port);
	// HTTP server implementation - requires additional module setup
	// This is a placeholder for future implementation
	bHTTPServerRunning = true;
}

void UGameObserverComponent::StopHTTPServer()
{
	UE_LOG(LogTemp, Log, TEXT("GameObserver: HTTP server stopped"));
	bHTTPServerRunning = false;
}

void UGameObserverComponent::HandleHTTPRequest(FHttpServerRequest& Request, const FHttpResultCallback& OnComplete)
{
	// HTTP request handler implementation
	// This is a placeholder for future implementation
}

