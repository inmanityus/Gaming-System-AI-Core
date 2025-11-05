# SkyLight Controller Blueprint Setup
**Date**: 2025-01-29  
**Task**: DN-002 - Visual Controllers for Day/Night

---

## Purpose

Create a Blueprint controller that manages SkyLight intensity and color based on TimeOfDayManager state.

---

## Steps to Create in UE5 Editor

1. **Open UE5 Editor** with `BodyBroker.uproject`

2. **Create Blueprint Class**:
   - Right-click in Content Browser → Blueprint Class
   - Parent Class: Actor
   - Name: `BP_SkyLightController`

3. **Add Components**:
   - Add `SkyLight` component
   - Add `SkyAtmosphere` component (if needed)

4. **Get TimeOfDayManager Reference**:
   - In Event Graph, create `Get Time Of Day Manager` node
   - Cast to `TimeOfDayManager` subsystem

5. **Bind to Time Changes**:
   - Subscribe to `OnTimeChanged` delegate
   - Update SkyLight intensity and color on time change

6. **Update Logic**:
   ```
   OnTimeChanged Event:
     - Get CurrentTimeState (Day/Night/Dawn/Dusk)
     - Set SkyLight Intensity based on state:
       * Day: 1.0
       * Night: 0.1
       * Dawn/Dusk: 0.5
     - Set SkyLight Color based on time:
       * Day: Bright blue/white
       * Night: Dark blue/purple
       * Dawn/Dusk: Orange/red
   ```

7. **Material Parameter Collection Updates**:
   - Get `MPC_TimeOfDay` reference
   - Set `DaylightIntensity` parameter
   - Set `SkyColor` parameter
   - Set `HorizonColor` parameter

8. **Compile and Save**

---

## Integration with C++ TimeOfDayManager

The Blueprint subscribes to the C++ `TimeOfDayManager` subsystem:
- Uses `GetCurrentTimeState()` to determine day/night
- Listens to `OnTimeChanged` delegate for real-time updates
- Calls HTTP API to get time from backend Python service

---

## Testing

1. Play in Editor
2. Verify SkyLight changes with time progression
3. Check Material Parameter Collection updates
4. Verify smooth transitions between states

---

**Status**: Ready to create in UE5 Editor




