# Setup Guide — DQH-RS (Archipelago)

## Requirements

- A legal copy of the game ROM (`.nds` file)
- [BizHawk](https://tasvideos.org/BizHawk/ReleaseHistory) 2.9.1 or newer
- The Archipelago client (installed with the Archipelago launcher)

## Step 1 — Configure BizHawk

1. Open BizHawk.
2. Load the ROM via **File → Open ROM**.

## Step 2 — Load the Lua connector

1. In BizHawk, open **Tools → Lua Console**.
2. Click **Script → Open Script** and select `data\lua\connector_bizhawk_generic.lua`
   from your Archipelago installation folder.
3. You should see "Looking for client..." in the Lua console output. 
   If not, push the red button on the left.

## Step 3 — Launch the Archipelago client

1. Open the Archipelago Launcher.
2. Click **BizHawk Client**.
3. The client window will open and attempt to connect to BizHawk.

## Step 4 — Connect to the server

1. In the client window, enter the server address in the **Host** field.
2. Click **Connect**.
3. Enter your slot name and password if required.

## Troubleshooting

- **Client cannot find BizHawk**: make sure BizHawk is open and the Lua script is running.
- **ROM validation failed**: confirm you are using the correct game revision.
- **Items are not being received**: check that `connector_bizhawk_generic.lua` is active.
