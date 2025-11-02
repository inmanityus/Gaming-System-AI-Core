# VA-003: Voice & Dialogue System - Blueprint API Guide

**Date**: 2025-11-02  
**Feature**: VA-003 Voice & Dialogue System  
**Status**: Implementation Complete

---

## Overview

The VA-003 Voice & Dialogue System provides a complete priority-based dialogue playback system with subtitle broadcasting, lip-sync data generation, and backend TTS integration.

---

## Getting Started

### Accessing DialogueManager

DialogueManager is a GameInstance Subsystem, accessible from any Blueprint:

```
Get Game Instance → Get Subsystem (Dialogue Manager)
```

Or from C++:
```cpp
UDialogueManager* DialogueMgr = GetGameInstance()->GetSubsystem<UDialogueManager>();
```

---

## Core Functions

### Playing Dialogue

**PlayDialogue**
- **Input**: NPCID (String), Text (String), Priority (Integer, default 2), DialogueID (String, optional)
- **Description**: Plays dialogue for NPC with automatic priority management
- **Usage**: Call when NPC needs to speak

**Example**:
```
Play Dialogue
  NPCID: "vampire_lord_marcus"
  Text: "You dare to challenge me?"
  Priority: 0  (Critical)
```

---

### Queue Management

**GetQueueStatus**
- **Returns**: FDialogueQueueStatus struct
- **Fields**: CriticalQueueSize, HighQueueSize, MediumQueueSize, LowQueueSize, ActiveDialogueCount
- **Usage**: Query current queue state for UI/debugging

**IsDialoguePlaying**
- **Input**: DialogueID (String)
- **Returns**: Boolean
- **Usage**: Check if specific dialogue is currently playing

**StopDialogue**
- **Input**: DialogueID (String)
- **Usage**: Manually stop a playing dialogue

**StopDialogueByNPC**
- **Input**: NPCID (String)
- **Usage**: Stop all dialogue for a specific NPC

---

## Priority System

**Priority Levels**:
- **0 (Critical)**: Immediate playback, interrupts everything
- **1 (High)**: Important dialogue, 2 concurrent max
- **2 (Medium)**: Standard dialogue, 4 concurrent max
- **3 (Low)**: Background chatter, 8 concurrent max

**Total Maximum**: 8 concurrent voices across all priorities

---

## Event Delegates

### Dialogue Events

**OnDialogueStarted**
- **Parameters**: DialogueID (String), SpeakerName (String)
- **Usage**: Bind to know when dialogue begins

**OnDialogueComplete**
- **Parameters**: DialogueID (String)
- **Usage**: Bind to know when dialogue ends

### Subtitle Events

**OnSubtitleShow**
- **Parameters**: Subtitle (FSubtitleData), Duration (Float)
- **Usage**: Display subtitles in UI
- **FSubtitleData Fields**: Text, SpeakerName, DialogueID, DisplayDuration, WordTimings

**OnSubtitleHide**
- **Parameters**: DialogueID (String)
- **Usage**: Hide subtitles when dialogue completes

**OnSubtitleUpdate**
- **Parameters**: DialogueID (String), NewText (String), ElapsedTime (Float)
- **Usage**: Update subtitle display (word-level highlighting if available)

---

## Lip-Sync Integration

**GetLipSyncData**
- **Input**: DialogueID (String)
- **Returns**: FLipSyncData struct
- **Usage**: Get lip-sync data for facial animation system
- **FLipSyncData Fields**: AudioID, DialogueID, Frames (array), BlendshapeWeights (map)

**Blendshape Weights**:
- Common blendshapes: "jaw_open", "lip_pucker", "lip_stretch", "mouth_wide"
- Weights: 0.0-1.0 float values

---

## Integration Examples

### Basic Dialogue Playback

```
Event BeginPlay
  → Get Subsystem (Dialogue Manager)
  → Initialize With Audio Manager (Audio Manager Reference)
  → Play Dialogue
      NPCID: "npc_guard_01"
      Text: "Halt! Who goes there?"
      Priority: 1
```

### Handling Dialogue Events

```
Bind Event to OnDialogueStarted
  → Display Subtitle (FSubtitleData)
  → Start Facial Animation (FLipSyncData)

Bind Event to OnDialogueComplete
  → Hide Subtitle
  → Stop Facial Animation
```

### Priority-Based Playback

```
Play Dialogue (Priority 0 - Critical)
  → Interrupts any lower priority dialogue
  
Play Dialogue (Priority 2 - Medium)
  → Queued if higher priority is playing
  → Plays when capacity available
```

---

## Testing Checklist

- [ ] DialogueManager accessible from GameInstance
- [ ] PlayDialogue enqueues and plays dialogue
- [ ] Priority system works (higher interrupts lower)
- [ ] Concurrent limits enforced (max 8 voices)
- [ ] Subtitle events fire correctly
- [ ] Lip-sync data generated
- [ ] TTS backend integration (when backend available)
- [ ] Error handling works (failed TTS requests)
- [ ] Queue status accurate
- [ ] Stop functions work correctly

---

**Reference**: See `docs/VA-003-Voice-Dialogue-Architecture.md` for full architecture details

