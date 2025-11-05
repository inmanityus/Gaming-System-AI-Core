# Audio Submix Graph Setup
**Date**: 2025-01-29  
**Task**: VA-002 - Audio Submix Graph

---

## Purpose

Create audio submix graph in UE5 Editor to manage audio routing and effects processing.

---

## Steps to Create in UE5 Editor

1. **Open UE5 Editor** with `BodyBroker.uproject`

2. **Create Submix Graph**:
   - Right-click in Content Browser → Audio → Sound Submix
   - Name: `SM_Master`
   - This will be the master submix

3. **Create Category Submixes**:
   - `SM_Voice` - For voice/character audio
   - `SM_Ambient` - For ambient/environmental audio
   - `SM_Music` - For background music
   - `SM_Effect` - For sound effects
   - `SM_UI` - For UI sounds

4. **Configure Submix Graph**:
   ```
   Master Output
     ├── SM_Voice (100% dry, EQ, Compressor)
     ├── SM_Ambient (80% wet, Reverb)
     ├── SM_Music (90% wet, EQ, Limiter)
     ├── SM_Effect (100% dry, Reverb send)
     └── SM_UI (100% dry, no effects)
   ```

5. **Add Effects to Submixes**:
   - Voice: EQ, Compressor, De-esser
   - Ambient: Reverb, EQ, Low-pass filter
   - Music: EQ, Limiter, Sidechain compression
   - Effect: Reverb send, EQ
   - UI: No effects (dry)

6. **Link to AudioManager**:
   - AudioManager C++ class sets output submix per category
   - Blueprint exposes submix assignment
   - Backend audio API specifies category

7. **Compile and Save**

---

## Integration

- AudioManager C++ class routes audio to correct submix
- Categories map to submix assignment
- Volume control per category affects submix
- Backend API specifies category when requesting audio

---

**Status**: Ready to create in UE5 Editor




