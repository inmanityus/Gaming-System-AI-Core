# BP_TimeOfDayController Blueprint Setup Guide

**Purpose**: Visual controller Blueprint for time of day visual updates  
**Dependencies**: TimeOfDayManager C++ class, MPC_TimeOfDay Material Parameter Collection

## Blueprint Structure

### Parent Class
- **Base Class**: Actor
- **Purpose**: Manages sky, lighting, and fog visual updates

### Components

1. **Sky Atmosphere Component**
   - Type: `SkyAtmosphereComponent`
   - Purpose: Handles sky rendering and sun/moon positions

2. **Directional Light (Sun)**
   - Type: `DirectionalLightComponent`
   - Purpose: Primary light source (day)
   - Component Name: `SunLight`

3. **Directional Light (Moon)**
   - Type: `DirectionalLightComponent`
   - Purpose: Secondary light source (night)
   - Component Name: `MoonLight`
   - Intensity: Lower than sun (0.3-1.0)

4. **Exponential Height Fog**
   - Type: `ExponentialHeightFogComponent`
   - Purpose: Volumetric fog system
   - Component Name: `VolumetricFog`

5. **Material Parameter Collection Instance**
   - Type: `MaterialParameterCollectionInstance`
   - Collection: `MPC_TimeOfDay`
   - Purpose: Updates material parameters

## Event Graph Setup

### Event BeginPlay
1. Get TimeOfDayManager subsystem
2. Subscribe to OnTimeChanged event
3. Subscribe to OnTimeStateChanged event
4. Fetch initial time from backend
5. Update visuals immediately

### OnTimeChanged Event Handler
```
1. Update Sun Angle based on hour (0-23 → 0-360 degrees)
   - Formula: SunAngle = (Hour / 24.0) * 360.0 + 90.0
   - Dawn: 5-7 AM → ~75-90 degrees
   - Day: 7-18 → 90-270 degrees
   - Dusk: 18-20 → 270-285 degrees
   - Night: 20-5 → 285-360, 0-75 degrees

2. Update Moon Angle (opposite of sun)
   - MoonAngle = SunAngle + 180.0

3. Update Sun/Moon Intensity based on time state
   - Dawn: Sun 0.5-10, Moon 0.3-0.0
   - Day: Sun 10.0, Moon 0.0
   - Dusk: Sun 10.0-0.5, Moon 0.0-0.3
   - Night: Sun 0.0, Moon 0.3-1.0

4. Update Sky Colors via MPC
   - Dawn: Warm orange/pink
   - Day: Blue
   - Dusk: Orange/red
   - Night: Dark blue/purple

5. Update Fog Density/Color
   - Dawn: Higher density, cooler colors
   - Day: Lower density, neutral colors
   - Dusk: Medium density, warm colors
   - Night: Higher density, cooler colors
```

### OnTimeStateChanged Event Handler
```
1. Smoothly interpolate visual parameters
2. Trigger transition effects if needed
3. Update fog density for state changes
```

## Material Parameter Collection Updates

### UpdateMPCParameters Function
1. Calculate normalized time (0.0-1.0)
2. Update scalar parameters:
   - SunAngle, SunIntensity
   - MoonAngle, MoonIntensity
   - FogDensity, TimeOfDay
3. Update vector parameters:
   - SkyHorizonColor, SkyZenithColor, SkyCloudColor
   - SunColor, MoonColor, FogColor

## Sky Atmosphere Setup

### Sun Rotation Curve
- Create Float Curve asset: `Curve_SunRotation`
- X-axis: Time of Day (0-24 hours)
- Y-axis: Sun Angle (0-360 degrees)
- Key points:
  - 0:00 (Midnight) → 270° (West)
  - 6:00 (Dawn) → 90° (East)
  - 12:00 (Noon) → 180° (South)
  - 18:00 (Dusk) → 270° (West)
  - 24:00 (Midnight) → 270° (West)

### Moon Rotation Curve
- Create Float Curve asset: `Curve_MoonRotation`
- Offset by 180° from sun
- Reverse movement (moon rises when sun sets)

## Performance Notes

- Updates happen via events (not tick)
- Smooth interpolation prevents visual artifacts
- MPC updates are efficient (single update per time change)
- Fog density changes are gradual (not instant)

## Testing Checklist

- [ ] Sun position updates correctly throughout day
- [ ] Moon position updates correctly throughout night
- [ ] Sky colors change smoothly during transitions
- [ ] Fog density adjusts appropriately
- [ ] Light intensity transitions smoothly
- [ ] No visual artifacts during state changes
- [ ] Performance is stable (60+ FPS)

## Integration with Backend

The Blueprint uses the TimeOfDayManager C++ subsystem which:
- Communicates with backend Time Manager API
- Receives time updates via HTTP
- Broadcasts events for Blueprint use
- Handles time scale changes
- Manages time progression start/stop

## Next Steps

1. Open UE5 Editor
2. Create Blueprint based on this structure
3. Assign components in editor
4. Implement event graph logic
5. Test with backend Time Manager running
6. Adjust curves and values for desired visual result




