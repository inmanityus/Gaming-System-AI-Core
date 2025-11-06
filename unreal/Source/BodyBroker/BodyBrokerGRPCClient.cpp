// Copyright Epic Games, Inc. All Rights Reserved.

#include "BodyBrokerGRPCClient.h"
// GE-004: TurboLink includes (uncomment when TurboLink plugin is installed)
// #include "TurboLinkGrpcManager.h"
// #include "TurboLinkGrpcClient.h"
// #include "TurboLinkGrpcService.h"
// #include "BodyBroker.grpc.pb.h"  // Generated from .proto file

UBodyBrokerGRPCClient::UBodyBrokerGRPCClient(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, ServerURL(TEXT("localhost:50051"))
{
}

void UBodyBrokerGRPCClient::Initialize(const FString& InServerURL)
{
	ServerURL = InServerURL;
	
	UE_LOG(LogTemp, Log, TEXT("[BodyBrokerGRPCClient] Initializing gRPC client - Server: %s"), *ServerURL);
	
	// GE-004: Initialize TurboLink gRPC service
	// This code will work once TurboLink plugin is installed
	/*
	UTurboLinkGrpcManager* GrpcManager = GetGameInstance()->GetSubsystem<UTurboLinkGrpcManager>();
	if (GrpcManager)
	{
		GRPCService = GrpcManager->MakeService();
		GRPCClient = GRPCService->MakeClient();
		
		UE_LOG(LogTemp, Log, TEXT("[BodyBrokerGRPCClient] TurboLink gRPC service initialized"));
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("[BodyBrokerGRPCClient] Failed to get TurboLink gRPC manager"));
		OnError(TEXT("TurboLink gRPC manager not available"), -1);
	}
	*/
	
	// Temporary: Log that TurboLink needs to be installed
	UE_LOG(LogTemp, Warning, TEXT("[BodyBrokerGRPCClient] TurboLink plugin not installed. Install from Epic Games Launcher or Marketplace."));
}

void UBodyBrokerGRPCClient::RequestNPCDialogueStreaming(
	const FString& NPCID,
	const FString& PlayerPrompt,
	const FString& ContextJSON,
	int32 Tier,
	const FString& LoRAAdapter
)
{
	UE_LOG(LogTemp, Log, TEXT("[BodyBrokerGRPCClient] Requesting streaming dialogue for NPC: %s"), *NPCID);
	
	// GE-004: Create gRPC streaming request
	// This code will work once TurboLink plugin is installed and .proto files are generated
	/*
	if (!GRPCClient)
	{
		OnError(TEXT("gRPC client not initialized"), -1);
		return;
	}
	
	// Create request message
	BodyBroker::DialogueRequest Request;
	Request.set_npc_id(TCHAR_TO_UTF8(*NPCID));
	Request.set_player_prompt(TCHAR_TO_UTF8(*PlayerPrompt));
	Request.set_context_json(TCHAR_TO_UTF8(*ContextJSON));
	Request.set_tier(Tier);
	if (!LoRAAdapter.IsEmpty())
	{
		Request.set_lora_adapter(TCHAR_TO_UTF8(*LoRAAdapter));
	}
	
	// Create streaming call
	auto StreamingCall = GRPCClient->CreateStreamingCall<BodyBroker::DialogueRequest, BodyBroker::DialogueToken>();
	
	// Set up response handler
	StreamingCall->OnResponse.AddLambda([this, NPCID](const BodyBroker::DialogueToken& Token)
	{
		FString TokenText = UTF8_TO_TCHAR(Token.token().c_str());
		bool bIsComplete = Token.is_complete();
		
		OnStreamingTokenReceived(TokenText, bIsComplete);
	});
	
	StreamingCall->OnError.AddLambda([this](const FGrpcError& Error)
	{
		OnError(UTF8_TO_TCHAR(Error.Message.c_str()), Error.Code);
	});
	
	// Send request
	StreamingCall->Send(Request);
	*/
	
	// Temporary: Fallback to HTTP if gRPC not available
	UE_LOG(LogTemp, Warning, TEXT("[BodyBrokerGRPCClient] gRPC not available, falling back to HTTP"));
	// TODO: Fallback to HTTP implementation
}

void UBodyBrokerGRPCClient::RequestNPCDialogue(
	const FString& NPCID,
	const FString& PlayerPrompt,
	const FString& ContextJSON,
	int32 Tier,
	const FString& LoRAAdapter
)
{
	UE_LOG(LogTemp, Log, TEXT("[BodyBrokerGRPCClient] Requesting dialogue for NPC: %s"), *NPCID);
	
	// GE-004: Create gRPC unary request
	// This code will work once TurboLink plugin is installed
	/*
	if (!GRPCClient)
	{
		OnError(TEXT("gRPC client not initialized"), -1);
		return;
	}
	
	// Create request message
	BodyBroker::DialogueRequest Request;
	Request.set_npc_id(TCHAR_TO_UTF8(*NPCID));
	Request.set_player_prompt(TCHAR_TO_UTF8(*PlayerPrompt));
	Request.set_context_json(TCHAR_TO_UTF8(*ContextJSON));
	Request.set_tier(Tier);
	if (!LoRAAdapter.IsEmpty())
	{
		Request.set_lora_adapter(TCHAR_TO_UTF8(*LoRAAdapter));
	}
	
	// Create unary call
	auto UnaryCall = GRPCClient->CreateUnaryCall<BodyBroker::DialogueRequest, BodyBroker::DialogueResponse>();
	
	// Set up response handler
	UnaryCall->OnResponse.AddLambda([this, NPCID](const BodyBroker::DialogueResponse& Response)
	{
		FString DialogueText = UTF8_TO_TCHAR(Response.dialogue_text().c_str());
		OnDialogueResponseReceived(NPCID, DialogueText);
	});
	
	UnaryCall->OnError.AddLambda([this](const FGrpcError& Error)
	{
		OnError(UTF8_TO_TCHAR(Error.Message.c_str()), Error.Code);
	});
	
	// Send request
	UnaryCall->Send(Request);
	*/
	
	// Temporary: Fallback to HTTP if gRPC not available
	UE_LOG(LogTemp, Warning, TEXT("[BodyBrokerGRPCClient] gRPC not available, falling back to HTTP"));
	// TODO: Fallback to HTTP implementation
}

void UBodyBrokerGRPCClient::OnStreamingTokenReceived(const FString& Token, bool bIsComplete)
{
	UE_LOG(LogTemp, VeryVerbose, TEXT("[BodyBrokerGRPCClient] Received token: %s (complete: %d)"), *Token, bIsComplete);
	
	// Broadcast token received event
	OnDialogueTokenReceived.Broadcast(Token, bIsComplete);
}

void UBodyBrokerGRPCClient::OnDialogueResponseReceived(const FString& NPCID, const FString& DialogueText)
{
	UE_LOG(LogTemp, Log, TEXT("[BodyBrokerGRPCClient] Received dialogue for NPC %s: %s"), *NPCID, *DialogueText);
	
	// Broadcast completion event
	OnDialogueComplete.Broadcast(NPCID, DialogueText);
}

void UBodyBrokerGRPCClient::OnError(const FString& ErrorMessage, int32 ErrorCode)
{
	UE_LOG(LogTemp, Error, TEXT("[BodyBrokerGRPCClient] Error (code %d): %s"), ErrorCode, *ErrorMessage);
	
	// Broadcast error event
	OnGRPCError.Broadcast(ErrorMessage, ErrorCode);
}

