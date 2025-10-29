# Website Startup Protocol

## Trigger Phrases
When the user says any of these phrases:
- "get the website running"
- "start the website"
- "bring up the site"
- "get both servers running"

## Automated Protocol

Execute this sequence automatically:

### 1. Shutdown Existing Servers
Kill any servers on web ports (3000-3005):
```powershell
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -ge 3000 -and $_.LocalPort -le 3005 } | ForEach-Object { $processId = $_.OwningProcess; Write-Host "Stopping process $processId on port $($_.LocalPort)"; Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue }
```

Kill any servers on API ports (4000-4005):
```powershell
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -ge 4000 -and $_.LocalPort -le 4005 } | ForEach-Object { $processId = $_.OwningProcess; Write-Host "Stopping process $processId on port $($_.LocalPort)"; Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue }
```

### 2. Run TypeScript Checks
Check both apps for TypeScript errors:
```powershell
# Check API
cd "E:\Vibe Code\Be Free Fitness\Website\apps\api" && npx tsc --noEmit

# Check Web
cd "E:\Vibe Code\Be Free Fitness\Website\apps\web" && npx tsc --noEmit
```

**If TypeScript errors found:** Fix all errors before proceeding.

### 3. Start Servers in Background (First Attempt)
Try starting both servers in hidden background mode (no visible windows):
```powershell
# Start API Server
cd "E:\Vibe Code\Be Free Fitness\Website" && Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd 'E:\Vibe Code\Be Free Fitness\Website'; npm run dev:api" -WindowStyle Hidden

# Start Web Server (wait 2 seconds between starts)
Start-Sleep -Seconds 2
cd "E:\Vibe Code\Be Free Fitness\Website" && Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd 'E:\Vibe Code\Be Free Fitness\Website'; npm run dev:web" -WindowStyle Hidden
```

Wait 12 seconds for startup, then verify health:
```powershell
# Check API (correct endpoint: /healthz)
Invoke-WebRequest -Uri "http://localhost:4000/healthz" -UseBasicParsing -TimeoutSec 5

# Check Web
Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
```

### 4. Fallback: Foreground Debugging (If Background Fails)
If either server is unhealthy after hidden background start:

1. **Shut down hidden background servers:**
   ```powershell
   Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { ($_.LocalPort -ge 3000 -and $_.LocalPort -le 3005) -or ($_.LocalPort -ge 4000 -and $_.LocalPort -le 4005) } | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
   ```

2. **Start servers in VISIBLE foreground windows** (to see errors):
   ```powershell
   # Start API in visible window to see errors
   cd "E:\Vibe Code\Be Free Fitness\Website" && Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd 'E:\Vibe Code\Be Free Fitness\Website'; npm run dev:api" -WindowStyle Normal
   
   # Start Web in visible window to see errors
   cd "E:\Vibe Code\Be Free Fitness\Website" && Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd 'E:\Vibe Code\Be Free Fitness\Website'; npm run dev:web" -WindowStyle Normal
   ```

3. **Fix all displayed errors** in the code

4. **Stop foreground servers:** Close the visible PowerShell windows or kill processes on ports 3000-4005

5. **Verify all console windows are closed**

6. **Restart in HIDDEN background:** Return to Step 3 (use `-WindowStyle Hidden`)

### 5. Final Verification
Confirm both servers are healthy:
- ✅ API Server: `http://localhost:4000/healthz` returns status 200
- ✅ Web Server: `http://localhost:3000` returns status 200

## Health Check Endpoints

- **API Server:** `http://localhost:4000/healthz`
  - Returns: `{"status":"healthy","timestamp":"...","database":"connected"}`
  
- **Web Server:** `http://localhost:3000`
  - Returns: Next.js page (status 200)

## Port Ranges

- **Web Server:** 3000-3005
- **API Server:** 4000-4005

## Important Notes

1. **Always check TypeScript first** - prevents runtime errors
2. **Always use absolute paths** - prevents directory confusion
3. **Wait 12 seconds** after background start before health checks
4. **MCP Protection:** These commands are safe and won't kill MCP servers
5. **Background = HIDDEN PowerShell processes** with `-WindowStyle Hidden` (NO visible windows)
6. **Foreground = VISIBLE PowerShell windows** with `-WindowStyle Normal` (for debugging only)
7. **If debugging needed:** Use visible windows to see errors, fix them, close windows, restart HIDDEN
8. **Never leave visible windows running** - always return to hidden background mode

## Success Criteria

Protocol is complete when:
- ✅ No TypeScript errors in either app
- ✅ Both servers running in HIDDEN background (no visible windows)
- ✅ API health check returns 200 on `/healthz`
- ✅ Web health check returns 200 on `/`
- ✅ NO visible console windows on screen
- ✅ Servers running as hidden PowerShell processes only

---

**Status:** Active  
**Priority:** High  
**Applies To:** Be Free Fitness Website Project  
**Created:** 2025-10-17

