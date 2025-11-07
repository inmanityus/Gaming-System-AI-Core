# Body Broker - Unreal Engine 5 Project

**Engine Version**: 5.6+  
**Platform**: Windows 10/11  
**Purpose**: Game client for "The Body Broker" AI-driven gaming core

## Project Structure

```
unreal/
├── BodyBroker.uproject          # Main project file
├── Source/
│   └── BodyBroker/
│       ├── BodyBroker.Build.cs  # Build configuration
│       ├── BodyBroker.h/cpp     # Main module
│       └── TimeOfDayManager.h/cpp  # Time management subsystem
├── Content/
│   ├── Materials/
│   │   └── MPC_TimeOfDay.json   # Material Parameter Collection structure
│   └── Blueprints/
│       └── BP_TimeOfDayController_Setup.md  # Blueprint setup guide
└── Config/
    └── DefaultEngine.ini        # Engine configuration
```

## Setup Instructions

1. **Open Project in UE5 Editor**
   - Double-click `BodyBroker.uproject`
   - UE5 will generate Visual Studio project files automatically
   - Wait for compilation to complete

2. **Generate Visual Studio Files** (if needed)
   - Right-click `BodyBroker.uproject`
   - Select "Generate Visual Studio project files"

3. **Compile C++ Code**
   - Open `BodyBroker.sln` in Visual Studio
   - Build Solution (F7)
   - Wait for compilation to complete

4. **Configure Backend API URL**
   - Edit `TimeOfDayManager.cpp`
   - Update `BackendAPIUrl` if backend runs on different port
   - Default: `http://localhost:8002/api/time`

5. **Create Blueprint Controller**
   - Follow guide in `Content/Blueprints/BP_TimeOfDayController_Setup.md`
   - Create Blueprint Actor in UE5 Editor
   - Set up components as described

6. **Test Integration**
   - Start backend Time Manager service
   - Play in editor (PIE)
   - Verify time updates from backend

## Dependencies

### Required Plugins
- **Niagara**: For particle effects (weather system)
- **MetaSounds**: For audio system
- **OnlineSubsystemSteam**: For Steam integration
- **HTTP**: For backend API communication

### Backend Services
- Time Manager API (port 8002)
- Event Bus (for cross-service communication)
- Weather Manager API (port 8003)

## Current Implementation

### ✅ Completed
- UE5 project structure
- TimeOfDayManager C++ subsystem
- Material Parameter Collection structure
- Blueprint controller documentation

### 🚧 In Progress
- Visual controllers (Sky, Light, Fog)
- Blueprint implementation

### 📋 Planned
- Weather particle systems (Niagara)
- Audio Manager subsystem
- Facial expressions system
- Terrain ecosystems

## Development Notes

- All C++ classes use REAL implementations (no mocks)
- HTTP communication with backend services
- Event-driven architecture for cross-system communication
- Blueprint-friendly API design
- Performance-conscious updates (not tick-based)

## Backend Integration

The UE5 client communicates with Python backend services via HTTP:

```
UE5 Client → HTTP → Backend Services → Database/Event Bus
```

Time Manager integration flow:
1. UE5 TimeOfDayManager fetches time from backend API
2. Updates cached time values
3. Broadcasts events to Blueprint systems
4. Visual controllers react to time changes
5. Materials update via Material Parameter Collection

## Troubleshooting

### Compilation Errors
- Ensure Visual Studio C++ tools are installed
- Check UE5 version matches project (5.6+)
- Verify all required plugins are enabled

### API Connection Issues
- Verify backend services are running
- Check `BackendAPIUrl` in TimeOfDayManager
- Ensure firewall allows localhost connections

### Blueprint Errors
- Ensure C++ code compiled successfully
- Check TimeOfDayManager is properly exposed to Blueprint
- Verify event bindings in Blueprint

## Next Steps

1. Implement Sky Atmosphere sun/moon rotation
2. Create light intensity curves
3. Set up fog density transitions
4. Test visual updates with backend
5. Optimize performance






