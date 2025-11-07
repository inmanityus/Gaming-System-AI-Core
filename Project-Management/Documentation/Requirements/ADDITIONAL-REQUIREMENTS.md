# Additional Requirements - Game Systems & Features
**Project**: "The Body Broker" - AI-Driven Horror Game  
**Last Updated**: 2025-01-29  
**Status**: Consolidated from "More Requirements.md"
**Location**: Moved to docs/requirements/ subfolder

---

## TABLE OF CONTENTS

1. [Terrain System](#terrain-system)
2. [Weather System](#weather-system)
3. [Day vs. Night Worlds](#day-vs-night-worlds)
4. [Facial Expressions](#facial-expressions)
5. [Voice & Audio System](#voice--audio-system)
6. [Immersive Features](#immersive-features)

---

## 1. TERRAIN SYSTEM

### Geography Considerations
- **Mountain Setting**: Deep forests, glens, wildfires, creatures of the deep, bears, mountain lions, magical streams, fairies, river lords, elementals, caves
- **Ocean Shore Setting**: Deep sea creatures, sharks, giant squid, hurricanes, tsunamis, fog, sea breezes, fishing adventures, pirate attacks, giant spiders
- **Plains Setting**: Rolling hills, plains, woods, roaming monsters, big cats, wolves, snakes, tornados, floods, rivers
- **Combined Settings**: Unique combinations (tropic rainforests, deserts, etc.)

**Requirement**: All player worlds must use the SAME terrain configuration initially.

---

## 2. WEATHER SYSTEM

### Seasonal Requirements
- **Four Seasons**: Fall (beautiful colors), Winter (bitter cold, white landscapes), Spring (vibrant reawakening), Summer (hot and humid)
- **Weather Events**:
  - Storms, ice, snow (driving restrictions, slick surfaces)
  - Flash floods, thunderstorms, mud puddles (Spring)
  - Windy conditions (Fall)
  - Intense heat, cloudless days (Summer)
  - Unpredictable changes (hot to cold in Spring/Fall, sunshine to thunderstorm in Summer)

---

## 3. DAY VS. NIGHT WORLDS

### World Transition System
- **Same Buildings, Different Interiors**: Same city structure, completely different residents (human vs. monster)
- **Alternative**: Similar cities with reality transitions (normal Earth by day, monster reality by night)
- **Transition Mechanics**:
  - Way to transition between versions
  - Monster leaks into human world (occasional)
  - Monster families can steal people (crime syndicates/mob style)
  - Human criminals can reverse-leak
  - Player must prevent/stop these actions
  - Story teller must leverage these options

---

## 4. FACIAL EXPRESSIONS

### Requirements
- **Personality Models**: Already have personality models for emotions, dialogue, actions
- **Facial Emotions**: Must consider facial emotions - humans are very sensitive to facial expressions
- **Body Language Integration**: Combined with body language, heavily influences perception
- **Example**: Same sentence with hostile stance/scowl vs. open stance/smile reads completely differently

**Requirement**: Facial expression models must be trained to understand emotions, expressions, actions, inherent traits.

---

## 5. VOICE & AUDIO SYSTEM

### Voice Requirements
- **Monster Voices**: Different sounds for different monsters
- **Personality Impact**: How personalities impact voices
- **AI Quality**: Voices must NOT sound like they came from an AI model
- **Sound Effects**: Everything makes sounds:
  - Buildings creak
  - Cars rumble
  - Animals make sounds (cats meow, etc.)
  - Trees groan in heavy winds
  - MANY other sounds

### Music System
- **Mood Setting**: Eerie and barely audible, loud and high energy
- **Jump Scare Emphasis**: Music for jump scares
- **Contextual**: When radio turns on, etc.
- **Realistic**: NOT constantly running soundtracks
- **Background Noise**: City always has background (insects, vehicles, sirens, people talking, plates/glasses clinking, etc.)

**Requirement**: Sound models must be trained for all sounds, music tracks, and voice generation.

---

## 6. IMMERSIVE FEATURES

### Multi-Sensory Immersion
- **High-End Visualizations**: Visual quality to impact other senses
- **Audio Integration**: Great audio integration
- **Visceral Responses**: 
  - Seeing putrid trash with flies = visceral sense of stink
  - Night insect bite with welt + visuals/audio = dizziness/weakness
  - Careful: Don't go too far (no vomiting - queasy is fine)

**Requirement**: System must create immersive experiences through visual and audio cues.

---

*Full content from original "More Requirements.md" - see ../More Requirements.md for complete details*

