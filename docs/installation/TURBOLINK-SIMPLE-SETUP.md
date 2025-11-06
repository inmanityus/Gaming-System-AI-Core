# Simple TurboLink Setup Guide
**For users new to UE5**

---

## Step 1: Open the Project

1. **Find this file**: `unreal\BodyBroker.uproject`
2. **Double-click it** - This will open Unreal Engine 5 Editor
3. Wait for UE5 to load (may take a few minutes first time)

---

## Step 2: Enable TurboLink Plugin

Once UE5 Editor is open:

1. Click **"Edit"** in the top menu bar
2. Click **"Plugins"** from the dropdown menu
3. In the Plugins window, type **"TurboLink"** in the search box
4. Find **"TurboLink"** in the list
5. **Check the box** next to it to enable it
6. UE5 will ask to restart - click **"Restart Now"**

That's it! TurboLink is now enabled.

---

## Step 3: After Restart

UE5 will automatically:
- Detect TurboLink plugin
- Compile the plugin code
- Make it available in your project

You may see compilation messages - this is normal.

---

## What Happens Next?

After TurboLink is enabled and compiled:
- The gRPC code I created will be ready to use
- You'll need to generate code from the `.proto` file (I can help with this)
- Then uncomment the TurboLink code in `BodyBrokerGRPCClient.cpp`

---

## Troubleshooting

**Project won't open?**
- Make sure you have Unreal Engine 5.6 installed
- The `.uproject` file should show UE5 icon

**TurboLink not in Plugins list?**
- Check that `unreal\Plugins\TurboLink\` folder exists
- Make sure `TurboLink.uplugin` file is in that folder
- Try closing and reopening UE5

**Compilation errors?**
- This is normal on first enable - UE5 needs to compile the plugin
- Wait for compilation to finish
- If errors persist, let me know

---

## That's All You Need To Do!

Just open `unreal\BodyBroker.uproject` and enable TurboLink plugin. Everything else is already set up!

