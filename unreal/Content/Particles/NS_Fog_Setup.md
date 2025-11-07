# Fog Particle System Setup (Niagara)
**Date**: 2025-01-29  
**Task**: WS-002 - Weather Particle Systems

---

## Purpose

Create Niagara particle system for fog effects.

---

## Steps to Create in UE5 Editor

1. **Create Niagara System**:
   - Name: `NS_Fog`
   - Use volumetric fog or particle-based fog

2. **Particle Properties**:
   - **Velocity**: Slow upward drift
   - **Color**: White/gray with transparency
   - **Size**: Large, billboard particles
   - **Density**: Varies with fog intensity

3. **Weather Integration**:
   - Controlled by `BP_WeatherController`
   - Density based on fog state:
     * Light Fog: Low density
     * Moderate Fog: Medium density
     * Heavy Fog: High density

4. **Use ExponentialHeightFog**:
   - Alternative: Use UE5's built-in ExponentialHeightFog
   - Update density via Material Parameter Collection
   - Controlled by WeatherManager

---

**Status**: Ready to create in UE5 Editor






