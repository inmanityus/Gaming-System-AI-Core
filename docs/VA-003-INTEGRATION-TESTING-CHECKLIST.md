# VA-003: Integration Testing Checklist

**Date**: 2025-11-02  
**Feature**: VA-003 Voice & Dialogue System  
**Status**: Ready for Testing

---

## Pre-Testing Requirements

- [ ] UE5 project compiled successfully
- [ ] AudioManager initialized and configured
- [ ] Backend TTS service available (for TTS tests)
- [ ] GameInstance accessible
- [ ] Player pawn exists in world

---

## Component Integration Tests

### DialogueQueue

- [ ] Initialize() sets up priority queues correctly
- [ ] EnqueueDialogue() adds to correct priority queue
- [ ] DequeueNextDialogue() returns items in priority order
- [ ] CanPlayDialogue() respects concurrency limits
- [ ] MarkDialogueActive/Inactive() updates counts correctly
- [ ] GetQueueStatus() returns accurate counts

### DialogueManager

- [ ] Subsystem initializes correctly
- [ ] AudioManager reference set
- [ ] VoicePool initialized
- [ ] PlayDialogue() creates dialogue item
- [ ] ProcessNextDialogue() dequeues and plays
- [ ] StopDialogue() stops playback correctly
- [ ] IsDialoguePlaying() returns correct state

### VoicePool

- [ ] Initialize() sets max size
- [ ] AcquireVoiceComponent() creates/returns component
- [ ] ReleaseVoiceComponent() returns to pool
- [ ] GetAvailableCount() accurate
- [ ] Spatial priority calculation works
- [ ] Drops furthest component when at capacity

---

## System Integration Tests

### Priority System

- [ ] Priority 0 dialogue interrupts all lower priorities
- [ ] Priority 1 dialogue interrupts Priority 2/3
- [ ] Priority 2 dialogue interrupts Priority 3 only
- [ ] Priority 3 dialogue doesn't interrupt anything
- [ ] Same priority dialogues queue correctly (FIFO)

### Concurrency Limits

- [ ] Max 1 Priority 0 dialogue at once
- [ ] Max 2 Priority 1 dialogues at once
- [ ] Max 4 Priority 2 dialogues at once
- [ ] Max 8 Priority 3 dialogues at once
- [ ] Total system maximum: 8 concurrent voices

### Interrupt System

- [ ] Immediate interrupt stops current instantly
- [ ] Crossfade interrupt structure ready (needs AudioManager fade)
- [ ] PauseAndResume interrupt structure ready (needs AudioManager pause)

### Subtitle Broadcasting

- [ ] OnSubtitleShow fires when dialogue starts
- [ ] OnSubtitleHide fires when dialogue completes
- [ ] FSubtitleData contains all required fields
- [ ] DisplayDuration = AudioDuration + 1.0s

### Lip-Sync Generation

- [ ] GenerateLipSyncData() creates valid data
- [ ] PhonemeToViseme() maps correctly
- [ ] GetBlendshapeWeightsForViseme() returns weights
- [ ] GetLipSyncData() retrieves data for active dialogue

### TTS Backend Integration

- [ ] RequestTTSFromBackend() sends HTTP request
- [ ] JSON request body correct format
- [ ] Base64 audio decoded correctly
- [ ] Duration extracted from response
- [ ] Error handling works (network failures)
- [ ] Error handling works (JSON parse failures)

---

## Performance Tests

- [ ] Queue management < 0.05ms per frame
- [ ] No allocation spikes during playback
- [ ] Voice pool prevents component allocation spikes
- [ ] Memory usage within budget (~20MB runtime)

---

## Edge Cases

- [ ] Empty DialogueID handled correctly
- [ ] Empty Text handled correctly
- [ ] Invalid priority (outside 0-3) clamped
- [ ] Multiple dialogues for same NPC
- [ ] Dialogue completes while another enqueuing
- [ ] World cleanup during playback
- [ ] Subsystem deinitialize during active playback

---

## Blueprint Integration Tests

- [ ] All UFUNCTIONs accessible in Blueprint
- [ ] All USTRUCTs visible in Blueprint
- [ ] Event delegates assignable in Blueprint
- [ ] Enum types selectable in Blueprint
- [ ] No compilation errors in Blueprint

---

**Status**: Ready for UE5 compilation and testing

