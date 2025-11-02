# VA-002 MetaSound Asset Setup Guide
**Date**: 2025-11-02  
**Status**: Asset Creation Guide

---

## OVERVIEW

VA-002 Audio Integration requires MetaSound templates to be created in Unreal Engine 5 Editor. This guide provides step-by-step instructions for creating all required MetaSound assets.

---

## METASOUND TEMPLATE REQUIREMENTS

### Total Assets Needed
- **4** Time-of-day ambient MetaSounds
- **15** Weather layer MetaSounds
- **N** Zone profile MetaSounds (project-specific)
- **1** Thunder event MetaSound

---

## ASSET ORGANIZATION

### Directory Structure
```
Content/Audio/MetaSounds/
├── TimeOfDay/
│   ├── MS_DawnAmbient
│   ├── MS_DayAmbient
│   ├── MS_DuskAmbient
│   └── MS_NightAmbient
├── Weather/
│   ├── MS_Weather_Wind_Light
│   ├── MS_Weather_Wind_Moderate
│   ├── MS_Weather_Wind_Strong
│   ├── MS_Weather_Wind_Howling
│   ├── MS_Weather_Rain
│   ├── MS_Weather_Rain_Heavy
│   ├── MS_Weather_Snow
│   ├── MS_Weather_Snow_Heavy
│   ├── MS_Weather_Blizzard
│   ├── MS_Weather_Fog_Ambient
│   ├── MS_Weather_Mist_Ambient
│   ├── MS_Weather_Heat_Haze
│   ├── MS_Weather_Cold_Wind
│   └── MS_Weather_Thunder
└── Zones/
    ├── MS_Zone_Warehouse
    ├── MS_Zone_Morgue
    ├── MS_Zone_Apartment
    └── [Additional zone profiles...]
```

---

## TIME-OF-DAY AMBIENT METAOUNDS

### MS_DawnAmbient
**Characteristics:**
- Birds chirping
- Morning wind (gentle)
- Distant city sounds
- Occasional ambient life

**Settings:**
- Looping: ✅ Yes
- Volume: 0.6-0.8 (base)
- Spatialization: 3D (optional)
- Dynamic elements: Random intervals (30-60 seconds)

### MS_DayAmbient
**Characteristics:**
- Traffic sounds
- Crowds/city life
- Construction (distant)
- Urban atmosphere

**Settings:**
- Looping: ✅ Yes
- Volume: 0.7-0.9 (base)
- Spatialization: Ambient (non-3D)
- Dynamic elements: Variable intensity

### MS_DuskAmbient
**Characteristics:**
- Wind picks up
- Distant sirens
- Evening atmosphere
- Transition to night

**Settings:**
- Looping: ✅ Yes
- Volume: 0.6-0.8 (base)
- Spatialization: 3D (optional)
- Dynamic elements: Sirens every 60-120 seconds

### MS_NightAmbient
**Characteristics:**
- Quiet atmosphere
- Occasional wind
- Distant sounds (muffled)
- Eerie silence
- Occasional ambient life

**Settings:**
- Looping: ✅ Yes
- Volume: 0.4-0.6 (base) - Quieter than day
- Spatialization: 3D (optional)
- Dynamic elements: Sporadic (rare)

---

## WEATHER LAYER METAOUNDS

### Wind Layers

#### MS_Weather_Wind_Light
- Gentle wind loop
- Volume: Controlled by intensity
- Looping: ✅ Yes

#### MS_Weather_Wind_Moderate
- Moderate wind loop
- Volume: Controlled by intensity
- Looping: ✅ Yes

#### MS_Weather_Wind_Strong
- Strong wind loop
- Volume: Controlled by intensity
- Looping: ✅ Yes

#### MS_Weather_Wind_Howling
- Howling wind (blizzard)
- Volume: Controlled by intensity
- Looping: ✅ Yes
- Low-pass filter for distance

### Precipitation Layers

#### MS_Weather_Rain
- Rain loop (moderate)
- Volume: Controlled by intensity
- Looping: ✅ Yes
- Spatialization: 3D (optional)

#### MS_Weather_Rain_Heavy
- Heavy rain loop
- Volume: Controlled by intensity
- Looping: ✅ Yes
- Spatialization: 3D (optional)

#### MS_Weather_Snow
- Snow loop (moderate)
- Volume: Controlled by intensity
- Looping: ✅ Yes
- Spatialization: 3D (optional)

#### MS_Weather_Snow_Heavy
- Heavy snow loop
- Volume: Controlled by intensity
- Looping: ✅ Yes
- Spatialization: 3D (optional)

#### MS_Weather_Blizzard
- Blizzard loop (intense)
- Volume: Controlled by intensity
- Looping: ✅ Yes
- Low-pass filter
- Spatialization: 3D (optional)

### Atmospheric Layers

#### MS_Weather_Fog_Ambient
- Fog ambient muffling
- Volume: Controlled by intensity
- Looping: ✅ Yes
- Low-pass filter applied

#### MS_Weather_Mist_Ambient
- Light mist ambient
- Volume: Controlled by intensity (lower)
- Looping: ✅ Yes

#### MS_Weather_Heat_Haze
- Distant heat haze effect
- Volume: Low
- Looping: ✅ Yes
- Subtle, atmospheric

#### MS_Weather_Cold_Wind
- Cold wind effect
- Volume: Controlled by intensity
- Looping: ✅ Yes

### Event-Based Audio

#### MS_Weather_Thunder
- Thunder strike (one-shot)
- Volume: 0.7-1.0 (randomized in code)
- Looping: ❌ No (event-based)
- Low-pass filter for distance
- 3D spatialization (random direction)

---

## ZONE PROFILE METAOUNDS

### Zone Profile Structure
Each zone profile should match the environment:

#### MS_Zone_Warehouse
- Large echo chamber
- Metallic reverberation
- Distant machinery (optional)
- Looping: ✅ Yes

#### MS_Zone_Morgue
- Cold tile room reverb
- Quiet, sterile atmosphere
- Occasional ambient (refrigeration)
- Looping: ✅ Yes

#### MS_Zone_Apartment
- Small room reverb
- Domestic sounds (distant)
- Neighbor sounds (optional)
- Looping: ✅ Yes

#### MS_Zone_Street
- City street ambient
- Traffic, pedestrians
- Urban atmosphere
- Looping: ✅ Yes

---

## CREATION WORKFLOW IN UE5

### Step 1: Create MetaSound Graph

1. **Content Browser** → Right-click → `Audio` → `MetaSound Source`
2. Name: `MS_DawnAmbient` (or appropriate name)
3. Double-click to open MetaSound Editor

### Step 2: Configure Audio Graph

**Basic Setup:**
1. Add **Output Node** (Audio Out)
2. Add **Input Node** (Trigger: Play)
3. Add **Sound Source Node** (your audio file)
4. Connect: Trigger → Sound Source → Output

**For Looping:**
1. Add **Loop Node**
2. Connect: Trigger → Loop → Sound Source → Output

**For Volume Control:**
1. Add **Multiply Node** (for intensity/volume)
2. Add **Input Node** (Float: Volume)
3. Connect: Volume Input → Multiply → Sound Source Volume

### Step 3: Add Dynamic Elements (Optional)

**For Random Intervals:**
1. Add **Random Node** (delay range)
2. Add **Trigger Delay Node**
3. Connect: Trigger → Delay → Sound Source (for sporadic sounds)

### Step 4: Configure Asset Settings

**In Asset Details:**
- **Loop**: Checked (for ambient/weather)
- **Volume**: 0.7 (default, controlled by intensity)
- **Spatialization**: 3D or Ambient (project preference)

### Step 5: Save and Compile

1. **Compile** MetaSound graph
2. **Save** asset
3. Verify in Content Browser

---

## METAOUND PARAMETER EXPOSURE

### Required Parameters

**Time-of-Day Ambient:**
- None (static looping)

**Weather Layers:**
- `Intensity` (Float, 0.0-1.0) - Controls volume

**Zone Profiles:**
- None (static looping)

### Exposing Parameters

1. In MetaSound Editor, select parameter node
2. Set **Expose Parameter** = true
3. Set **Parameter Name** = "Intensity"
4. Connect to volume multiplier

---

## AUDIO FILE REQUIREMENTS

### Format
- **WAV** or **OGG Vorbis** (recommended for compression)
- **48kHz sample rate** (UE5 standard)
- **16-bit or 24-bit** depth

### File Organization
```
Content/Audio/Source/
├── TimeOfDay/
│   ├── dawn_ambient.wav
│   ├── day_ambient.wav
│   ├── dusk_ambient.wav
│   └── night_ambient.wav
├── Weather/
│   ├── wind_light.wav
│   ├── rain_loop.wav
│   └── [weather source files...]
└── Zones/
    ├── warehouse_ambient.wav
    └── [zone source files...]
```

---

## INTEGRATION CHECKLIST

### Before Testing
- [ ] All MetaSound templates created
- [ ] Asset names match code expectations exactly
- [ ] All assets compile successfully
- [ ] Looping configured correctly
- [ ] Volume parameters exposed (for weather)
- [ ] Assets in `/Game/Audio/MetaSounds/` directory

### Testing in Blueprint
1. Add AudioManager component to test actor
2. Call `SetTimeOfDayAmbient("day")`
3. Verify audio plays
4. Test weather layers
5. Test zone profiles

---

## TROUBLESHOOTING

### MetaSound Not Loading
1. Check asset name matches exactly (case-sensitive)
2. Verify asset path: `/Game/Audio/MetaSounds/[Name]`
3. Check asset is compiled
4. Verify MetaSound Source type (not SoundWave)

### No Audio Playing
1. Check AudioManager logs
2. Verify MetaSound has Output node connected
3. Check volume multiplier settings
4. Verify audio file is imported correctly

### Volume Not Controlled
1. Verify intensity parameter is exposed
2. Check parameter connection to volume multiplier
3. Verify SetWeatherAudioLayer is passing intensity

---

## PERFORMANCE NOTES

### Memory Budget
- Each MetaSound: ~2-5MB (compressed)
- Total time-of-day: ~12MB
- Total weather: ~30MB
- Total zones: ~15MB (varies)

### CPU Budget
- MetaSound playback: ~0.1ms per instance
- Multiple layers: Additive
- Keep concurrent MetaSounds < 10 for performance

---

**Document Status**: ✅ Complete - Ready for UE5 Asset Creation

