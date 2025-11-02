# Weather Controller Blueprint Setup
**Date**: 2025-01-29  
**Task**: WS-002 - Weather Controller Integration

---

## Purpose

Create a Blueprint controller that manages weather particle systems (Niagara) based on WeatherManager backend state.

---

## Steps to Create in UE5 Editor

1. **Open UE5 Editor** with `BodyBroker.uproject`

2. **Create Blueprint Class**:
   - Right-click in Content Browser → Blueprint Class
   - Parent Class: Actor
   - Name: `BP_WeatherController`

3. **Add Components**:
   - Add `Scene` component (root)
   - Reference to Niagara particle systems (Rain, Snow, Fog)

4. **Get WeatherManager Backend Reference**:
   - Store backend API URL in variable
   - Create HTTP client component or use C++ HTTP integration

5. **Bind to Weather Changes**:
   - Subscribe to weather state changes via HTTP polling or WebSocket
   - Update particle systems on weather change

6. **Update Logic**:
   ```
   OnWeatherChanged Event:
     - Get CurrentWeatherState (Clear/Rain/Snow/Fog/Storm)
     - Update Rain Particle System:
       * Rain: Spawn rate = 2000 particles/second
       * Heavy Rain: Spawn rate = 5000 particles/second
       * No Rain: Spawn rate = 0
     
     - Update Snow Particle System:
       * Snow: Spawn rate = 1500 particles/second
       * Heavy Snow: Spawn rate = 4000 particles/second
       * No Snow: Spawn rate = 0
     
     - Update Fog System:
       * Fog: Density = High
       * Heavy Fog: Density = Very High
       * No Fog: Density = Low/Off
   ```

7. **Backend API Integration**:
   - HTTP GET request to `/weather/current`
   - Parse JSON response for weather state
   - Update particle systems accordingly
   - Poll every 5-10 seconds or use event-driven updates

8. **Compile and Save**

---

## Integration with Backend WeatherManager

The Blueprint calls the backend Python WeatherManager service:
- Endpoint: `http://localhost:8007/weather/current` (dev) or AWS endpoint (prod)
- Gets current weather state, intensity, wind speed
- Updates Niagara particle systems based on state
- Listens to weather change events for real-time updates

---

## Performance Optimization

- Particle systems use LOD for distance
- Limit max particles based on weather intensity
- Use GPU particles when available
- Throttle API polling (5-10 second intervals)

---

## Testing

1. Play in Editor
2. Verify particle systems respond to weather changes
3. Check performance (60 FPS target)
4. Test all weather states (Clear, Rain, Snow, Fog, Storm)
5. Verify smooth transitions between states

---

**Status**: Ready to create in UE5 Editor



