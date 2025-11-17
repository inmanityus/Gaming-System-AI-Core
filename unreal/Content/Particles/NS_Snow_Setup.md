# Snow Particle System Setup (Niagara)
**Date**: 2025-01-29  
**Task**: WS-002 - Weather Particle Systems

---

## Purpose

Create Niagara particle system for snow effects.

---

## Steps to Create in UE5 Editor

1. **Create Niagara System**:
   - Name: `NS_Snow`
   - Template: Snow (or start from scratch)

2. **Particle Properties**:
   - **Velocity**: Downward with wind variation
   - **Color**: White
   - **Size**: Flakes, size variation
   - **Rotation**: Slow rotation for realism
   - **Lifetime**: Longer than rain

3. **Weather Integration**:
   - Controlled by `BP_WeatherController`
   - Spawn rate based on snow intensity:
     * Light Snow: 300 particles/second
     * Moderate Snow: 1500 particles/second
     * Heavy Snow: 4000 particles/second

4. **Wind Effects**:
   - Add wind force to particles
   - Vary based on weather wind speed

---

**Status**: Ready to create in UE5 Editor












