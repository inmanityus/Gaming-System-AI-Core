# API Contracts & Service Interfaces
**Date**: January 29, 2025  
**Status**: Complete API Specifications

---

## OVERVIEW

Complete API contracts for all service integrations using OpenAPI (HTTP) and Protocol Buffers (gRPC).

---

## HTTP API CONTRACTS (OpenAPI)

### AI Inference Service API

```yaml
openapi: 3.0.0
info:
  title: AI Inference Service API
  version: 1.0.0
  description: LLM model serving for NPC dialogue and content generation

servers:
  - url: https://ai-inference:8000
    description: Production
  - url: http://localhost:8000
    description: Development

paths:
  /v1/dialogue:
    post:
      summary: Generate NPC dialogue
      operationId: generateDialogue
      tags:
        - Dialogue
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DialogueRequest'
      responses:
        '200':
          description: Dialogue response (streaming)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DialogueResponse'
            text/event-stream:
              schema:
                type: string
                description: Server-Sent Events stream
        '429':
          description: Rate limit exceeded
        '402':
          description: Insufficient budget
        '500':
          description: Service error

components:
  schemas:
    DialogueRequest:
      type: object
      required:
        - npc_id
        - prompt
        - tier
      properties:
        npc_id:
          type: string
          format: uuid
          description: NPC identifier
        prompt:
          type: string
          minLength: 1
          maxLength: 1000
          description: Player input prompt
        tier:
          type: integer
          enum: [1, 2, 3]
          description: NPC tier (1=generic, 2=elite, 3=major)
        context:
          type: object
          description: Game context (relationships, history, world state)
          properties:
            player_id:
              type: string
              format: uuid
            relationship:
              type: number
              format: float
              description: NPC relationship score (-1 to 1)
            recent_events:
              type: array
              items:
                type: string
            world_state:
              type: object
    
    DialogueResponse:
      type: object
      properties:
        response_text:
          type: string
          description: Generated dialogue text
        npc_id:
          type: string
          format: uuid
        confidence:
          type: number
          format: float
          minimum: 0
          maximum: 1
        available_actions:
          type: array
          items:
            type: string
          description: Available player actions
        streaming:
          type: boolean
          description: Whether response was streamed
        tokens_used:
          type: integer
          description: Number of tokens consumed
        cost_usd:
          type: number
          format: float
          description: Cost in USD

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

### Orchestration Service API

```yaml
openapi: 3.0.0
info:
  title: Orchestration Service API
  version: 1.0.0

paths:
  /v1/orchestration/generate:
    post:
      summary: Generate content via 4-layer pipeline
      operationId: generateContent
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ContentRequest'
      responses:
        '200':
          description: Generated content
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ContentResponse'

components:
  schemas:
    ContentRequest:
      type: object
      required:
        - seed
        - monster_type
      properties:
        seed:
          type: integer
          description: Random seed for generation
        monster_type:
          type: string
          enum: [vampire, werewolf, lich, zombie, ghoul]
        biome:
          type: string
        size:
          type: object
          properties:
            width: {type: integer}
            height: {type: integer}
        activate_npcs:
          type: boolean
          default: true
        requires_coordination:
          type: boolean
          default: false
    
    ContentResponse:
      type: object
      properties:
        foundation:
          $ref: '#/components/schemas/FoundationOutput'
        customized:
          $ref: '#/components/schemas/CustomizedOutput'
        interactions:
          type: array
          items:
            $ref: '#/components/schemas/InteractionOutput'
        orchestration:
          $ref: '#/components/schemas/OrchestrationOutput'
```

---

## gRPC CONTRACTS (Protocol Buffers)

### Dialogue Service

```protobuf
// proto/dialogue.proto
syntax = "proto3";

package bodybroker.dialogue.v1;

option go_package = "github.com/bodybroker/api/dialogue/v1";

// Dialogue Service for NPC interactions
service DialogueService {
  // Generate dialogue for NPC
  rpc GenerateDialogue(DialogueRequest) returns (DialogueResponse);
  
  // Stream dialogue (token-by-token)
  rpc StreamDialogue(DialogueRequest) returns (stream DialogueToken);
  
  // Generate dialogue for multiple NPCs (batch)
  rpc BatchGenerateDialogue(BatchDialogueRequest) returns (BatchDialogueResponse);
}

message DialogueRequest {
  string npc_id = 1;
  string prompt = 2;
  int32 tier = 3;  // 1, 2, or 3
  DialogueContext context = 4;
}

message DialogueContext {
  string player_id = 1;
  float relationship = 2;  // -1 to 1
  repeated string recent_events = 3;
  map<string, string> world_state = 4;
}

message DialogueResponse {
  string response_text = 1;
  string npc_id = 2;
  float confidence = 3;
  repeated string available_actions = 4;
  bool streaming = 5;
  int32 tokens_used = 6;
  double cost_usd = 7;
}

message DialogueToken {
  string token = 1;
  bool is_complete = 2;
  string npc_id = 3;
}

message BatchDialogueRequest {
  repeated DialogueRequest requests = 1;
}

message BatchDialogueResponse {
  repeated DialogueResponse responses = 1;
}
```

### Orchestration Service

```protobuf
// proto/orchestration.proto
syntax = "proto3";

package bodybroker.orchestration.v1;

import "dialogue.proto";

service OrchestrationService {
  // Generate content via 4-layer pipeline
  rpc GenerateContent(ContentRequest) returns (ContentResponse);
  
  // Coordinate battle scenario
  rpc CoordinateBattle(BattleRequest) returns (BattleResponse);
}

message ContentRequest {
  int64 seed = 1;
  string monster_type = 2;
  string biome = 3;
  Size size = 4;
  bool activate_npcs = 5;
  bool requires_coordination = 6;
}

message Size {
  int32 width = 1;
  int32 height = 2;
}

message ContentResponse {
  FoundationOutput foundation = 1;
  CustomizedOutput customized = 2;
  repeated InteractionOutput interactions = 3;
  OrchestrationOutput orchestration = 4;
}

message FoundationOutput {
  MonsterBase monster = 1;
  TerrainBase terrain = 2;
  RoomBase room = 3;
}

message MonsterBase {
  string id = 1;
  string type = 2;
  map<string, float> attributes = 3;
}

message TerrainBase {
  string biome = 1;
  repeated int32 height_map = 2;
}

message RoomBase {
  int32 width = 1;
  int32 height = 2;
  repeated string objects = 3;
}

message CustomizedOutput {
  MonsterCustomization monster = 1;
  TerrainCustomization terrain = 2;
  RoomCustomization room = 3;
}

message MonsterCustomization {
  string personality = 1;
  map<string, string> traits = 2;
}

message InteractionOutput {
  string npc_id = 1;
  bodybroker.dialogue.v1.DialogueResponse dialogue = 2;
}

message OrchestrationOutput {
  string plan = 1;
  repeated string actions = 2;
}

message BattleRequest {
  repeated string monster_ids = 1;
  string player_id = 2;
  BattleContext context = 3;
}

message BattleContext {
  string location = 1;
  map<string, float> monster_states = 2;
}

message BattleResponse {
  repeated MonsterAction monster_actions = 1;
  string coordinator_plan = 2;
}

message MonsterAction {
  string monster_id = 1;
  string action_type = 2;
  map<string, string> parameters = 3;
}
```

### State Management Service

```protobuf
// proto/state.proto
syntax = "proto3";

package bodybroker.state.v1;

service StateService {
  rpc GetEntityState(EntityStateRequest) returns (EntityState);
  rpc UpdateEntityState(UpdateEntityRequest) returns (UpdateResponse);
  rpc GetContext(ContextRequest) returns (Context);
  rpc StoreMemory(MemoryRequest) returns (MemoryResponse);
  rpc RetrieveMemories(RetrieveRequest) returns (RetrieveResponse);
}

message EntityStateRequest {
  string entity_id = 1;
}

message EntityState {
  string entity_id = 1;
  string type = 2;
  map<string, string> data = 3;
  int64 updated_at = 4;
}

message UpdateEntityRequest {
  string entity_id = 1;
  map<string, string> changes = 2;
}

message UpdateResponse {
  bool success = 1;
  int64 timestamp = 2;
}

message ContextRequest {
  string entity_id = 1;
  int32 radius = 2;
}

message Context {
  repeated EntityState entities = 1;
  repeated Event history = 2;
  WorldState world = 3;
}

message Event {
  string id = 1;
  string type = 2;
  int64 timestamp = 3;
  map<string, string> data = 4;
}

message WorldState {
  int64 time = 1;
  string weather = 2;
  map<string, string> factions = 3;
}

message MemoryRequest {
  string npc_id = 1;
  string memory_text = 2;
  repeated float embedding = 3;
}

message MemoryResponse {
  string memory_id = 1;
  bool success = 2;
}

message RetrieveRequest {
  string npc_id = 1;
  repeated float query_embedding = 2;
  int32 top_k = 3;
}

message RetrieveResponse {
  repeated Memory memories = 1;
}

message Memory {
  string id = 1;
  string text = 2;
  float similarity = 3;
  int64 timestamp = 4;
}
```

### Payment Service

```protobuf
// proto/payment.proto
syntax = "proto3";

package bodybroker.payment.v1;

service PaymentService {
  rpc GetUserTier(UserTierRequest) returns (UserTierResponse);
  rpc CheckRateLimit(RateLimitRequest) returns (RateLimitResponse);
  rpc ChargeUser(ChargeRequest) returns (ChargeResponse);
  rpc GetCostProjection(CostProjectionRequest) returns (CostProjectionResponse);
}

message UserTierRequest {
  string user_id = 1;
}

message UserTierResponse {
  string tier = 1;  // "free", "premium", "whale"
  bool active = 2;
  int64 expires_at = 3;
}

message RateLimitRequest {
  string user_id = 1;
  string tier = 2;
  int32 layer = 3;
}

message RateLimitResponse {
  bool allowed = 1;
  string error_message = 2;
  int32 remaining_daily = 3;
  int32 remaining_hourly = 4;
}

message ChargeRequest {
  string user_id = 1;
  double cost_usd = 2;
  string description = 3;
}

message ChargeResponse {
  bool success = 1;
  double new_balance = 2;
}

message CostProjectionRequest {
  string user_id = 1;
}

message CostProjectionResponse {
  double daily_cost = 1;
  double monthly_projection = 2;
  double annual_projection = 3;
}
```

### Settings Service

```protobuf
// proto/settings.proto
syntax = "proto3";

package bodybroker.settings.v1;

service SettingsService {
  rpc GetUserSettings(SettingsRequest) returns (Settings);
  rpc UpdateSettings(UpdateSettingsRequest) returns (UpdateResponse);
  rpc GetUserTier(TierRequest) returns (TierResponse);
}

message SettingsRequest {
  string user_id = 1;
}

message Settings {
  AudioSettings audio = 1;
  VideoSettings video = 2;
  ControlSettings controls = 3;
  map<string, string> preferences = 4;
}

message AudioSettings {
  float master_volume = 1;
  float music_volume = 2;
  float sfx_volume = 3;
}

message VideoSettings {
  int32 resolution_x = 1;
  int32 resolution_y = 2;
  int32 quality_preset = 3;
  bool effects_enabled = 4;
}

message ControlSettings {
  float mouse_sensitivity = 1;
  map<string, string> key_bindings = 2;
}

message UpdateSettingsRequest {
  string user_id = 1;
  Settings settings = 2;
}
```

---

## DATABASE SCHEMAS

### PostgreSQL Schema

```sql
-- Entities table
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_updated_at ON entities(updated_at);

-- Player history table (partitioned by timestamp)
CREATE TABLE player_history (
    id BIGSERIAL,
    player_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL,
    context JSONB,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Monthly partitions
CREATE TABLE player_history_2025_01 PARTITION OF player_history
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE INDEX idx_player_history_player_id ON player_history(player_id);
CREATE INDEX idx_player_history_timestamp ON player_history(timestamp);

-- Events table (event sourcing)
CREATE TABLE events (
    id BIGSERIAL PRIMARY KEY,
    stream_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    sequence BIGINT NOT NULL,
    data JSONB NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(stream_id, sequence)
);

CREATE INDEX idx_events_stream_id ON events(stream_id);
CREATE INDEX idx_events_timestamp ON events(timestamp);

-- User settings
CREATE TABLE user_settings (
    user_id UUID PRIMARY KEY,
    audio_settings JSONB,
    video_settings JSONB,
    control_settings JSONB,
    preferences JSONB,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Subscriptions (for tier tracking)
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tier VARCHAR(20) NOT NULL,  -- "free", "premium", "whale"
    status VARCHAR(20) NOT NULL,  -- "active", "canceled", "expired"
    stripe_subscription_id VARCHAR(255),
    starts_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- Rate limiting tracking
CREATE TABLE rate_limits (
    user_id UUID NOT NULL,
    layer INTEGER NOT NULL,
    period VARCHAR(20) NOT NULL,  -- "daily", "hourly"
    count INTEGER NOT NULL DEFAULT 0,
    reset_at TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, layer, period)
);

CREATE INDEX idx_rate_limits_reset_at ON rate_limits(reset_at);

-- Cost tracking
CREATE TABLE cost_tracking (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    service VARCHAR(50) NOT NULL,
    layer INTEGER,
    model VARCHAR(100),
    tokens INTEGER,
    cost_usd DECIMAL(10, 6) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cost_tracking_user_id ON cost_tracking(user_id);
CREATE INDEX idx_cost_tracking_timestamp ON cost_tracking(timestamp);
```

### Redis Key Patterns

```python
# Entity state (hot cache)
entity:{entity_id} -> Hash
  - data: JSON string
  - updated_at: timestamp
  - TTL: 3600 seconds

# Rate limiting
rate_limit:{user_id}:layer{layer}:{period} -> Integer
  - period: "daily" or "hourly"
  - TTL: 86400 (daily) or 3600 (hourly)

# Cost tracking
cost:{user_id}:daily -> Float
cost:{user_id}:monthly -> Float
  - TTL: 86400 (daily) or 2592000 (monthly)

# Cache (L1)
L1:{prompt_hash} -> JSON string
  - TTL: 300 seconds (5 minutes)

# Semantic cache (L3)
L3:{embedding_hash} -> JSON string
  - TTL: 86400 seconds (24 hours)
```

---

## KINESIS EVENT SCHEMA

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["event_type", "timestamp", "user_id"],
  "properties": {
    "event_type": {
      "type": "string",
      "enum": [
        "dialogue_generated",
        "npc_interaction",
        "player_action",
        "model_performance",
        "cost_tracking"
      ]
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "user_id": {
      "type": "string",
      "format": "uuid"
    },
    "data": {
      "type": "object",
      "additionalProperties": true
    },
    "model_version": {
      "type": "string"
    },
    "partition_key": {
      "type": "string",
      "description": "user_id for partitioning"
    }
  }
}
```

---

## ERROR CODES

### Standard HTTP Status Codes

- `200 OK`: Success
- `400 Bad Request`: Invalid request format
- `401 Unauthorized`: Missing/invalid authentication
- `402 Payment Required`: Insufficient budget
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Custom Error Response Format

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Daily Layer 3 limit exceeded (5)",
    "details": {
      "tier": "free",
      "limit": 5,
      "used": 5,
      "reset_at": "2025-01-30T00:00:00Z"
    },
    "timestamp": "2025-01-29T15:30:00Z",
    "request_id": "req_abc123"
  }
}
```

---

**Status**: Complete API contracts for all services

