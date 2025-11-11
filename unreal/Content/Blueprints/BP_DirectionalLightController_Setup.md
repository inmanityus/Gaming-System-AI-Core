# DirectionalLight Controller Blueprint Setup
**Date**: 2025-01-29  
**Task**: DN-002 - Visual Controllers for Day/Night

---

## Purpose

Create a Blueprint controller for the sun (directional light) that rotates and changes intensity based on TimeOfDayManager.

---

## Steps to Create in UE5 Editor

1. **Create Blueprint Class**:
   - Parent Class: Actor
   - Name: `BP_DirectionalLightController`

2. **Add Components**:
   - Add `DirectionalLight` component (sun)
   - Add `ExponentialHeightFog` component (for atmospheric effects)

3. **Get TimeOfDayManager Reference**:
   - Get `TimeOfDayManager` subsystem
   - Subscribe to `OnTimeChanged` delegate

4. **Update Logic**:
   ```
   OnTimeChanged Event:
     - Get CurrentTime (hour, minute)
     - Calculate Sun Rotation:
       * Hour 0-6: Night (sun below horizon)
       * Hour 6-12: Dawn to Noon (rising)
       * Hour 12-18: Noon to Dusk (setting)
       * Hour 18-24: Dusk to Night (below horizon)
     
     - Set DirectionalLight Intensity:
       * Noon (12:00): 3.0
       * Dawn/Dusk (6:00, 18:00): 0.5
       * Night (0:00, 24:00): 0.0
     
     - Set DirectionalLight Color:
       * Noon: Bright white/yellow
       * Dawn: Orange/red
       * Dusk: Red/orange
       * Night: Dark/off
   ```

5. **Sun Rotation Calculation**:
   - Calculate pitch angle based on hour:
     - Hour 6: -90° (below horizon)
     - Hour 12: 90° (noon)
     - Hour 18: -90° (below horizon)
   - Yaw can be fixed or based on season

6. **Compile and Save**

---

## Integration

- Uses C++ `TimeOfDayManager` for time data
- Updates every time `OnTimeChanged` fires
- Smooth rotation interpolation for visual quality

---

**Status**: Ready to create in UE5 Editor







