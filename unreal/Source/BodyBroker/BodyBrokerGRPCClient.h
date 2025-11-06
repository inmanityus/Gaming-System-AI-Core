// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "BodyBrokerGRPCClient.generated.h"

// Forward declarations for TurboLink
// These will be available once TurboLink plugin is installed
// class UGrpcService;
// class UGrpcClient;

/**
 * BodyBrokerGRPCClient - gRPC client for AI inference service
 * GE-004: gRPC Integration (Production)
 * Uses TurboLink plugin for gRPC communication
 */
UCLASS(BlueprintType)
class BODYBROKER_API UBodyBrokerGRPCClient : public UObject
{
	GENERATED_BODY()

public:
	UBodyBrokerGRPCClient(const FObjectInitializer& ObjectInitializer);

	// Initialize gRPC client
	UFUNCTION(BlueprintCallable, Category = "gRPC")
	void Initialize(const FString& ServerURL = TEXT("localhost:50051"));

	// Request NPC dialogue via gRPC (streaming)
	UFUNCTION(BlueprintCallable, Category = "gRPC|Dialogue")
	void RequestNPCDialogueStreaming(
		const FString& NPCID,
		const FString& PlayerPrompt,
		const FString& ContextJSON = TEXT("{}"),
		int32 Tier = 2,
		const FString& LoRAAdapter = TEXT("")
	);

	// Request NPC dialogue via gRPC (non-streaming)
	UFUNCTION(BlueprintCallable, Category = "gRPC|Dialogue")
	void RequestNPCDialogue(
		const FString& NPCID,
		const FString& PlayerPrompt,
		const FString& ContextJSON = TEXT("{}"),
		int32 Tier = 2,
		const FString& LoRAAdapter = TEXT("")
	);

	// Delegate for streaming dialogue tokens
	DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnDialogueTokenReceived, const FString&, Token, bool, bIsComplete);
	UPROPERTY(BlueprintAssignable, Category = "gRPC|Dialogue|Events")
	FOnDialogueTokenReceived OnDialogueTokenReceived;

	// Delegate for dialogue completion
	DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnDialogueComplete, const FString&, NPCID, const FString&, FullDialogue);
	UPROPERTY(BlueprintAssignable, Category = "gRPC|Dialogue|Events")
	FOnDialogueComplete OnDialogueComplete;

	// Delegate for errors
	DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnGRPCError, const FString&, ErrorMessage, int32, ErrorCode);
	UPROPERTY(BlueprintAssignable, Category = "gRPC|Events")
	FOnGRPCError OnGRPCError;

private:
	// Server URL
	UPROPERTY()
	FString ServerURL;

	// gRPC service instance (TurboLink)
	// UPROPERTY()
	// UGrpcService* GRPCService;

	// gRPC client instance (TurboLink)
	// UPROPERTY()
	// UGrpcClient* GRPCClient;

	// Handle streaming response
	void OnStreamingTokenReceived(const FString& Token, bool bIsComplete);
	
	// Handle non-streaming response
	void OnDialogueResponseReceived(const FString& NPCID, const FString& DialogueText);
	
	// Handle error
	void OnError(const FString& ErrorMessage, int32 ErrorCode);
};

