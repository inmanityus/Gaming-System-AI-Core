# Audio Virtual Routing Integration Specification

**Version**: 1.0.0  
**Date**: 2025-11-15  
**Status**: Draft  
**Domain**: Audio Authentication & Vocal Simulator QA  

## 1. Overview

This specification defines the integration between Unreal Engine 5 (UE5) audio subsystems and the Ethelred Audio Capture Service via virtual audio routing, satisfying requirement **R-AUD-IN-001**.

### 1.1 Goals
- Route game audio from UE5 to Ethelred without physical audio devices
- Capture both mixed output and individual bus streams
- Maintain timing synchronization with game events
- Preserve metadata alignment with narrative elements
- Support real-time and near-real-time analysis

### 1.2 Non-Goals
- Physical microphone capture
- Player voice chat recording
- Audio modification or processing within the routing layer
- Real-time audio feedback to the game

## 2. Architecture

### 2.1 Audio Bus Architecture

```
UE5 Audio System
├── Master Mix
│   └── [To Virtual Device: ethelred_main_mix]
├── Dialogue Bus
│   ├── NPC Dialogue
│   ├── Narrator
│   └── [To Virtual Device: ethelred_dialogue]
├── Vocal Simulator Bus
│   ├── Pre-Simulator
│   │   └── [To Virtual Device: ethelred_vocal_pre]
│   └── Post-Simulator
│       └── [To Virtual Device: ethelred_vocal_post]
├── Ambient Bus
│   ├── Environment
│   ├── Horror Atmosphere
│   └── [To Virtual Device: ethelred_ambient]
└── SFX Bus
    ├── Combat
    ├── UI
    └── [To Virtual Device: ethelred_sfx]
```

### 2.2 Virtual Audio Devices

The following virtual audio devices must be configured:

| Device Name | Purpose | Sample Rate | Bit Depth | Channels |
|------------|---------|-------------|-----------|----------|
| ethelred_main_mix | Full game mix | 48000 Hz | 24-bit | Stereo |
| ethelred_dialogue | Isolated dialogue | 48000 Hz | 24-bit | Mono/Stereo |
| ethelred_vocal_pre | Pre-simulator vocals | 48000 Hz | 24-bit | Mono |
| ethelred_vocal_post | Post-simulator vocals | 48000 Hz | 24-bit | Mono |
| ethelred_ambient | Ambient/atmosphere | 48000 Hz | 24-bit | Stereo |
| ethelred_sfx | Sound effects | 48000 Hz | 24-bit | Stereo |

### 2.3 Platform-Specific Routing

#### Windows
- **Technology**: Windows Audio Session API (WASAPI) with loopback capture
- **Driver**: Virtual Audio Cable (VAC) or similar
- **Configuration**: Registered as WDM audio devices

#### Linux
- **Technology**: PulseAudio virtual sinks or JACK
- **Configuration**: Null sinks with monitor sources

#### Development/Testing
- **Technology**: File-based audio capture for deterministic testing
- **Format**: WAV files with embedded metadata

## 3. UE5 Integration

### 3.1 Audio Routing Plugin

```cpp
// IEthelredAudioRouter.h
class IEthelredAudioRouter : public IModuleInterface
{
public:
    // Initialize virtual audio routing
    virtual bool Initialize(const FEthelredAudioConfig& Config) = 0;
    
    // Route audio buffer to virtual device
    virtual void RouteAudio(
        const FString& BusName,
        const float* AudioData,
        int32 NumSamples,
        int32 NumChannels,
        const FEthelredAudioMetadata& Metadata
    ) = 0;
    
    // Mark dialogue line boundaries
    virtual void BeginDialogueLine(
        const FString& LineId,
        const FString& SpeakerId,
        const FEthelredSpeakerInfo& SpeakerInfo
    ) = 0;
    
    virtual void EndDialogueLine(const FString& LineId) = 0;
};
```

### 3.2 Audio Submix Configuration

```cpp
// Configure submixes to route to virtual devices
void SetupEthelredRouting()
{
    // Main mix submix
    USoundSubmix* MainMixSubmix = NewObject<USoundSubmix>();
    MainMixSubmix->OutputTarget = "ethelred_main_mix";
    
    // Dialogue submix
    USoundSubmix* DialogueSubmix = NewObject<USoundSubmix>();
    DialogueSubmix->OutputTarget = "ethelred_dialogue";
    DialogueSubmix->bSendToMaster = true;
    
    // Vocal simulator submixes
    USoundSubmix* VocalPreSubmix = NewObject<USoundSubmix>();
    VocalPreSubmix->OutputTarget = "ethelred_vocal_pre";
    
    USoundSubmix* VocalPostSubmix = NewObject<USoundSubmix>();
    VocalPostSubmix->OutputTarget = "ethelred_vocal_post";
}
```

### 3.3 Metadata Synchronization

```cpp
// Metadata passed with audio routing
struct FEthelredAudioMetadata
{
    // Timing
    FDateTime GameTimestamp;
    float GameTimeSeconds;
    
    // Context
    FString SceneId;
    FString ExperienceId;
    FString EnvironmentType;
    
    // Speaker (for dialogue)
    FString SpeakerId;
    FString ArchetypeId;
    FString EmotionalTag;
    
    // Technical
    bool bSimulatorApplied;
    float SimulatorParams[8];  // Key simulator parameters
};
```

## 4. Data Flow

### 4.1 Dialogue Flow

1. **Story Teller triggers dialogue line**
   - LineId: "castle_intro_vampire_01"
   - SpeakerId: "npc_vampire_lord"
   - Archetype: "vampire_house_alpha"

2. **UE5 Audio System plays dialogue**
   - Routes to DialogueSubmix
   - Applies character voice processing

3. **Ethelred Router captures**
   - Marks line start with metadata
   - Streams audio to virtual device
   - Marks line end

4. **Capture Service processes**
   - Segments by line boundaries
   - Enriches with metadata
   - Stores and emits events

### 4.2 Vocal Simulator Flow

1. **Base voice generated**
   - Routed to ethelred_vocal_pre

2. **Simulator processing**
   - Physical cord simulation applied
   - Parameters logged

3. **Processed voice**
   - Routed to ethelred_vocal_post
   - Marked with simulator_applied=true

### 4.3 Ambient/Environmental Flow

1. **Scene loads**
   - Environment type tagged
   - Ambient submix configured

2. **Continuous capture**
   - Fixed window segments
   - Tagged with scene/environment

## 5. Timing and Synchronization

### 5.1 Latency Requirements

| Path | Maximum Latency | Notes |
|------|-----------------|-------|
| Audio generation → Virtual device | < 10ms | Audio subsystem latency |
| Virtual device → Capture service | < 50ms | Loopback capture latency |
| Line marker → Audio alignment | < 100ms | Metadata sync tolerance |

### 5.2 Clock Synchronization

- All timestamps use UTC
- Game time tracked separately for replay alignment
- Audio sample position used for precise alignment

### 5.3 Line Boundary Detection

```cpp
// Ensure clean line boundaries
class FDialogueLineTracker
{
    // Buffer pre-roll for capture
    static constexpr float PreRollSeconds = 0.1f;
    
    // Buffer post-roll for reverb tails
    static constexpr float PostRollSeconds = 0.3f;
    
    void MarkLineStart(const FString& LineId)
    {
        // Send marker ahead of audio
        SendMarker(LineId, -PreRollSeconds);
    }
    
    void MarkLineEnd(const FString& LineId)
    {
        // Delay marker for tails
        SendMarker(LineId, PostRollSeconds);
    }
};
```

## 6. Error Handling

### 6.1 Virtual Device Unavailable

- **Detection**: Device enumeration fails
- **Response**: 
  - Log warning
  - Continue game without capture
  - Emit health degradation event
  - Retry connection periodically

### 6.2 Buffer Overflow

- **Detection**: Capture buffer full
- **Response**:
  - Drop oldest unprocessed audio
  - Increment dropped_frames counter
  - Log if drops exceed threshold

### 6.3 Metadata Desync

- **Detection**: Line markers without matching audio
- **Response**:
  - Use heuristics to align
  - Flag segments as "metadata_uncertain"
  - Include in degradation metrics

## 7. Configuration

### 7.1 UE5 Configuration

```ini
[EthelredAudio]
bEnableRouting=true
RoutingLatencyCompensationMs=10
DialoguePreRollMs=100
DialoguePostRollMs=300
MaxBufferSizeBytes=10485760  ; 10MB per bus
bDebugLogging=false
```

### 7.2 Capture Service Configuration

```yaml
audio_routing:
  devices:
    - name: ethelred_main_mix
      type: main_mix
      enabled: true
    - name: ethelred_dialogue
      type: dialogue
      enabled: true
    - name: ethelred_vocal_pre
      type: vocal_pre
      enabled: true
    - name: ethelred_vocal_post
      type: vocal_post
      enabled: true
  
  capture:
    buffer_size_ms: 1000
    segment_timeout_ms: 5000
    
  metadata:
    line_boundary_tolerance_ms: 100
    scene_transition_delay_ms: 500
```

## 8. Testing Strategy

### 8.1 Unit Tests
- Virtual device enumeration
- Buffer management
- Metadata synchronization
- Error condition handling

### 8.2 Integration Tests
- Full dialogue capture flow
- Vocal simulator pre/post comparison
- Multi-bus synchronization
- Latency measurement

### 8.3 Load Tests
- Simultaneous multi-bus capture
- Extended capture sessions (hours)
- High-frequency dialogue sequences
- Memory leak detection

## 9. Performance Considerations

### 9.1 CPU Usage
- Target: < 2% CPU for routing layer
- Use lock-free queues where possible
- Batch metadata updates

### 9.2 Memory Usage
- Pre-allocate buffers
- Ring buffer per virtual device
- Maximum 50MB total for routing

### 9.3 Bandwidth
- ~370 KB/s per stereo 48kHz stream
- ~185 KB/s per mono 48kHz stream
- Total: ~1.5 MB/s for all buses

## 10. Security Considerations

- No external network access from routing layer
- Audio data never leaves local system
- Metadata sanitized before storage
- No player voice data captured

## 11. Future Considerations

### 11.1 Real-time Analysis Feedback
- Possibility for real-time metrics display
- Developer dashboard integration
- Live quality monitoring

### 11.2 Compression
- Optional lossless compression for storage efficiency
- FLAC or ALAC for archival
- Maintain uncompressed path for analysis

### 11.3 Cloud Streaming
- Potential for cloud-based analysis
- Streaming protocols (WebRTC, RTSP)
- Bandwidth optimization

## 12. References

- Windows Audio Session API: https://docs.microsoft.com/en-us/windows/win32/coreaudio/
- PulseAudio Documentation: https://www.freedesktop.org/wiki/Software/PulseAudio/
- UE5 Audio System: https://docs.unrealengine.com/5.0/en-US/audio-system-in-unreal-engine/
- Virtual Audio Cable: https://vac.muzychenko.net/en/

---

*This specification is subject to revision based on implementation feedback and performance testing results.*
