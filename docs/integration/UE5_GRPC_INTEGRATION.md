# UE5 gRPC Integration Guide
**Service**: Language System gRPC Integration  
**Date**: 2025-11-05  
**Status**: Implementation Complete

---

## Overview

This guide provides instructions for integrating the Language System gRPC service with Unreal Engine 5.

---

## Protocol Definition

The gRPC service is defined in:
- **Proto File**: `services/language_system/proto/language_service.proto`
- **Generated Code**: `services/language_system/proto/language_service_pb2.py`, `language_service_pb2_grpc.py`

---

## Available Services

### 1. GenerateSentence
Generate a sentence in a specific language.

**Request**:
```protobuf
message GenerateSentenceRequest {
  string language_name = 1;
  string intent = 2;
  map<string, string> context = 3;
  string emotion = 4;
  int32 complexity = 5;
}
```

**Response**:
```protobuf
message GenerateSentenceResponse {
  string sentence = 1;
  string language_name = 2;
  string intent = 3;
  string phonemes = 4;
  map<string, string> metadata = 5;
}
```

### 2. GenerateSentenceStream
Stream sentence generation token by token for real-time dialogue.

**Request**: Same as GenerateSentenceRequest

**Response Stream**:
```protobuf
message SentenceToken {
  string token = 1;
  bool is_complete = 2;
  float progress = 3;
}
```

### 3. Translate
Translate text between languages.

### 4. Interpret
Provide contextual interpretation of text.

### 5. ListLanguages
List all available languages.

### 6. GetLanguage
Get detailed language definition.

### 7. HealthCheck
Health check endpoint.

---

## UE5 Integration Steps

### Step 1: Install TurboLink Plugin

1. Download TurboLink plugin for UE5
2. Add to UE5 project plugins folder
3. Enable plugin in project settings

### Step 2: Import Proto File

1. Copy `services/language_system/proto/language_service.proto` to UE5 project
2. Use TurboLink to generate UE5 C++ code from proto file

### Step 3: Create UE5 Client Class

```cpp
// LanguageSystemClient.h
UCLASS()
class ABodyBrokerGameMode : public AGameModeBase
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadWrite)
    ULanguageServiceClient* LanguageClient;

    UFUNCTION(BlueprintCallable)
    void GenerateNPCDialogue(
        const FString& LanguageName,
        const FString& Intent,
        const FDialogueResponseDelegate& Callback
    );
};
```

### Step 4: Connect to gRPC Server

```cpp
// LanguageSystemClient.cpp
void ABodyBrokerGameMode::BeginPlay()
{
    Super::BeginPlay();
    
    // Initialize gRPC client
    LanguageClient = NewObject<ULanguageServiceClient>(this);
    LanguageClient->Connect("localhost:50051");
}
```

### Step 5: Call Language Service

```cpp
void ABodyBrokerGameMode::GenerateNPCDialogue(
    const FString& LanguageName,
    const FString& Intent,
    const FDialogueResponseDelegate& Callback
)
{
    FGenerateSentenceRequest Request;
    Request.LanguageName = LanguageName;
    Request.Intent = Intent;
    Request.Complexity = 1;
    
    LanguageClient->GenerateSentence(
        Request,
        [Callback](const FGenerateSentenceResponse& Response) {
            Callback.ExecuteIfBound(Response.Sentence);
        }
    );
}
```

---

## Python Client Example

For testing and development:

```python
from services.language_system.grpc.grpc_client import LanguageSystemClient

async def example():
    async with LanguageSystemClient(host="localhost", port=50051) as client:
        # Generate sentence
        result = await client.generate_sentence(
            language_name="vampire",
            intent="greeting",
            context={"time": "night"},
            complexity=1
        )
        print(result["sentence"])
        
        # Stream sentence
        async for token in client.generate_sentence_stream(
            language_name="vampire",
            intent="greeting"
        ):
            print(token, end="", flush=True)
```

---

## Server Deployment

### Local Development

```bash
python -m services.language_system.grpc.server_main 50051
```

### Docker Deployment

The gRPC server is included in the language system Docker image. Update the ECS task definition to expose port 50051.

### Production Deployment

1. Update ECS task definition to include gRPC port (50051)
2. Update security groups to allow gRPC traffic
3. Configure load balancer if needed
4. Update service discovery for UE5 clients

---

## Performance Considerations

- **Connection Pooling**: Maintain 40-100 persistent gRPC connections per UE5 instance
- **Streaming**: Use streaming for real-time dialogue to reduce perceived latency
- **Caching**: Cache frequently used language content client-side
- **Async**: All gRPC calls are async - never block game thread

---

## Testing

Run comprehensive tests:
```bash
python -m pytest tests/language_system/test_grpc_integration.py -v
```

---

**Status**: Ready for UE5 integration

