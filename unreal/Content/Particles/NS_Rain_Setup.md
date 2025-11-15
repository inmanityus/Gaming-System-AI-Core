# Rain Particle System Setup (Niagara)
**Date**: 2025-01-29  
**Task**: WS-002 - Weather Particle Systems

---

## Purpose

Create Niagara particle system for rain effects that responds to WeatherManager backend.

---

## Steps to Create in UE5 Editor

1. **Create Niagara System**:
   - Right-click in Content Browser → FX → Niagara System
   - Name: `NS_Rain`
   - Template: None (start from scratch) or use Rain template

2. **Add Emitter**:
   - Add `Rain Emitter`
   - Set spawn rate based on weather intensity

3. **Particle Properties**:
   - **Velocity**: Downward with slight variation
   - **Color**: Gray/blue tint
   - **Size**: Small droplets, size variation
   - **Lifetime**: Based on fall distance

4. **Weather Integration**:
   - Create Blueprint controller: `BP_WeatherController`
   - Subscribe to WeatherManager backend events
   - Control particle spawn rate:
     * Light Rain: 500 particles/second
     * Moderate Rain: 2000 particles/second
     * Heavy Rain: 5000 particles/second
     * No Rain: 0 particles/second

5. **Performance Optimization**:
   - Use LOD system for distance
   - Limit max particles
   - Use GPU particles if available

---

## Integration with WeatherManager

The `BP_WeatherController` Blueprint:
- Calls backend WeatherManager API to get current weather
- Updates particle system spawn rate based on weather state
- Listens to weather change events for real-time updates

---

**Status**: Ready to create in UE5 Editor











