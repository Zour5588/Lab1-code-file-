# ESP32 Temperature Monitor and Relay Control with Telegram Bot

This project uses an ESP32 running MicroPython to monitor temperature and humidity with a DHT11 sensor, control a relay, and interact with a Telegram bot in a private chat. The bot sends alerts based on temperature thresholds and responds to commands to control the relay.

## Features

- **No messages** when temperature (T) &lt; 30°C.
- **Alerts every 5 seconds** when T ≥ 30°C and relay is OFF, until `/on` is received.
- **After** `/on`, alerts stop; when T &lt; 30°C, relay turns OFF automatically with a one-time "Relay auto-OFF" notice.
- **Commands**:
  - `/start`: Initializes the bot and provides command list.
  - `/on`: Turns relay ON, stops alerts.
  - `/off`: Turns relay OFF, resets auto-OFF notice.
  - `/temp`: Sends current temperature and humidity.
- **Auto-reconnect WiFi** when dropped.
- **Handles Telegram HTTP errors** and DHT11 sensor errors without crashing.

### Wiring Photo 

- **Photo**: Take a clear, well-lit photo showing all connections, labeled if possible (e.g., with arrows or text in an editor). Include in your project repository or video evidence.

1. **Set Up Telegram Bot**:

   - **Bot Token**:
     - Open Telegram, search for `@BotFather`, and send `/newbot`.
     - Follow prompts to create a bot and receive a token (e.g., `123456789:ABCDEF...`).
     - In `main.py`, replace `BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"` with your token.
   - **Chat ID**:
     - Start a private chat with your bot (e.g., `@YourBotName`), send `/start`.
     - The code automatically sets `chat_id` from the first message. To verify manually:
       - Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` in a browser.
       - Find `"chat":{"id":123456789,"type":"private"}`. The `id` is your chat ID (not needed in code but useful for debugging).

2. **Update WiFi Credentials**:

   - In `main.py`, replace `WIFI_SSID = "YourWiFiName"` and `WIFI_PASSWORD = "YourWiFiPassword"` with your WiFi details.

3. **Upload Code**:

   - Save the provided `main.py` in Thonny.
   - Upload to ESP32: **File &gt; Save as &gt; MicroPython device**, select `main.py`.
   - Reset ESP32 (press reset button or reconnect USB).

## Usage Instructions

1. **Start the Bot**:

   - Open Telegram, send `/start` to your bot in a private chat.
   - Expect response: "Bot started! Commands: /on, /off, /temp\\nAlerts sent if temperature &gt;= 30C."
   - Check Thonny’s Shell for: `Chat ID set to: <number>`.

2. **Monitor and Control**:

   - **T &lt; 30°C**: No Telegram messages. Shell shows sensor readings.
   - **T ≥ 30°C, Relay OFF**: Warm DHT11 (e.g., with hand/hairdryer). Expect alerts every 5s: "Alert: Temperature &gt;= 30C (X.XXC)! Send /on to activate relay."
   - **Send** `/on`: Relay turns ON (e.g., LED on), alerts stop, Telegram: "Relay turned ON".
   - **T &lt; 30°C, Relay ON**: Cool DHT11 (e.g., fan/wait). Expect relay OFF, one-time message: "Relay auto-OFF: Temperature &lt; 30C (X.XXC)".
   - **Send** `/off`: Relay turns OFF, Telegram: "Relay turned OFF". Alerts resume if T ≥ 30°C.
   - **Send** `/temp`: Get current readings: "Temperature: X.XXC\\nHumidity: X.XX%".
   - **WiFi Drops**: Auto-reconnects with retries every 10s.
   - **Errors**: Telegram HTTP errors (e.g., 400) or DHT OSErrors skip the cycle without crashing.