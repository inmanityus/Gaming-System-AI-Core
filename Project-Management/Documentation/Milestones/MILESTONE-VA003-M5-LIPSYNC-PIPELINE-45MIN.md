# MILESTONE VA-003-M5: Lip-Sync Data Pipeline
**Start Time**: 2025-11-02 16:00  
**Target Duration**: 45 minutes  
**Status**: In Progress  
**Feature**: VA-003 Voice & Dialogue System

---

## Goals

- [x] Create FLipSyncData struct
- [x] Create FPhonemeFrame struct
- [x] Implement phoneme-to-viseme mapping (PhonemeToViseme function)
- [x] Create viseme-to-blendshape mapping (GetBlendshapeWeightsForViseme function)
- [x] Add lip-sync data generation functions (GenerateLipSyncData)
- [x] Integrate with dialogue playback (called in StartDialoguePlayback)
- [x] Blueprint integration (GetLipSyncData exposed)
- [ ] Full phoneme analysis from text (deferred - requires TTS backend or phoneme library)

---

## Tasks Included

**VA-003-007**: Lip-Sync Data Structures
- Create FLipSyncData struct
- Create FPhonemeFrame struct
- Add blendshape weight mapping

**VA-003-008**: Phoneme/Viseme Mapping
- Implement phoneme-to-viseme conversion
- Create viseme-to-blendshape mapping
- Add static mapping tables (per architecture doc)

**VA-003-009**: Integration
- Generate lip-sync data from dialogue item
- Pass lip-sync data to facial system (structure ready)
- Event broadcasting for lip-sync updates

---

## Expected Deliverables

1. ✅ FLipSyncData struct
2. ✅ FPhonemeFrame struct
3. ✅ Phoneme-to-viseme mapping tables
4. ✅ Viseme-to-blendshape mapping tables
5. ✅ GenerateLipSyncData() function
6. ✅ Integration with dialogue system
7. ✅ Blueprint API exposed
8. ✅ Peer review complete

---

## Success Criteria

- [ ] All data structures defined per architecture
- [ ] Phoneme mapping matches ARPAbet standard
- [ ] Viseme mapping matches common blendshapes
- [ ] Lip-sync data generated from text/word timings
- [ ] Integration ready for facial system
- [ ] Blueprint-exposed structures
- [ ] Peer review complete

---

## Architecture Reference

Following `docs/VA-003-Voice-Dialogue-Architecture.md`:
- FLipSyncData with Frames array
- FPhonemeFrame with Phoneme/Viseme fields
- PhonemeToVisemeMap (ARPAbet → viseme)
- VisemeToBlendshapes (viseme → blendshape weights)

---

---

## Actual Completion

**Completed**: 2025-11-02 16:45  
**Duration**: ~45 minutes  
**Status**: ✅ Complete (Core Implementation)

### Deliverables Created

1. ✅ `FLipSyncData` struct - Complete with Frames and BlendshapeWeights
2. ✅ `FPhonemeFrame` struct - Time, Phoneme, Viseme fields
3. ✅ `PhonemeToViseme()` - Implements ARPAbet to viseme mapping
4. ✅ `GetBlendshapeWeightsForViseme()` - Returns blendshape weights per viseme
5. ✅ `GenerateLipSyncData()` - Creates lip-sync data from dialogue item
6. ✅ `GetLipSyncData()` - Blueprint function to retrieve lip-sync data
7. ✅ Integration with StartDialoguePlayback

### Implementation Details

**Phoneme-to-Viseme Mapping**: ✅ Complete
- Implements full ARPAbet phoneme set
- Maps to standard visemes (silence, a, p, f, th, i, u, o, r, s, sh, j, t, k)
- Defaults to "silence" for unknown phonemes

**Viseme-to-Blendshape Mapping**: ✅ Complete
- Returns TMap<FString, float> with blendshape weights
- Common blendshapes: jaw_open, lip_pucker, lip_stretch, mouth_wide
- Weights normalized 0.0-1.0

**Lip-Sync Generation**:
- Uses WordTimings if available (creates frames from words)
- Generates blendshape weights from first frame viseme
- Structure ready for phoneme-level timing from backend (Milestone 7)

### Notes

- Core mapping tables complete per architecture
- Phoneme-level analysis deferred (requires backend TTS API or phoneme library)
- Ready for facial system integration
- Blueprint-exposed for designer access

---

**Status**: ✅ **COMPLETE** (Core) - Ready for Milestone 6

