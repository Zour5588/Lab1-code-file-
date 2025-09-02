import machine
import dht
import time
import network
import urequests
import json

# WiFi credentials
WIFI_SSID = "Robotic WIFI"
WIFI_PASSWORD = "rbtWIFI@2025"

# Telegram bot details
BOT_TOKEN = "8428954540:AAHc5o2eqAB_fTzvhxbU48cQushT9TU5SCw"  # Replace with your bot token
TELEGRAM_SEND_URL = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
TELEGRAM_UPDATES_URL = "https://api.telegram.org/bot{}/getUpdates".format(BOT_TOKEN)

# Pin configurations
sensor = dht.DHT11(machine.Pin(4))  # DHT11 on GPIO4
relay = machine.Pin(5, machine.Pin.OUT)  # Relay on GPIO5
relay.value(0)  # Start with relay OFF

# Global variables
chat_id = None  # Set from first message
offset = 0  # For Telegram polling
auto_off_sent = False  # Track auto-OFF notice

# Connect to WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(30):  # Increased retry time to 30 seconds
            if wlan.isconnected():
                break
            time.sleep(1)
        else:
            print("WiFi connection failed")
            return False
    print("WiFi connected. IP:", wlan.ifconfig()[0])
    return True

# Send message via Telegram API with retry
def send_telegram_message(cid, message):
    if cid is None:
        print("No chat_id set, skipping send")
        return False
    payload = {
        "chat_id": str(cid),  # Ensure string for JSON
        "text": message
    }
    for attempt in range(3):
        try:
            response = urequests.post(TELEGRAM_SEND_URL, json=payload)
            if response.status_code == 200:
                print("Message sent to Telegram: " + message)
                response.close()
                return True
            else:
                print("Failed to send message, status:", response.status_code, "Response:", response.text)
                response.close()
                return False  # Skip cycle on HTTP error
        except Exception as e:
            print("Error sending to Telegram (attempt {}): {}".format(attempt + 1, e))
            if str(e).find("MBEDTLS_ERR_SSL_CONN_EOF") != -1:
                time.sleep(2)
            else:
                break
    print("Failed to send message after retries")
    return False

# Read sensor with retries
def read_sensor():
    retries = 3
    for _ in range(retries):
        try:
            sensor.measure()
            temp = sensor.temperature()
            hum = sensor.humidity()
            return temp, hum
        except OSError as e:
            print("Sensor read failed:", e)
            time.sleep(1)
    return None, None

# Process incoming commands
def handle_command(text, cid):
    global auto_off_sent
    text = text.lower()
    if text == '/start':
        send_telegram_message(cid, "Bot started! Commands: /on, /off, /temp\nAlerts sent if temperature >= 30C.")
    elif text == '/on':
        relay.value(1)
        send_telegram_message(cid, "Relay turned ON")
        auto_off_sent = False
    elif text == '/off':
        relay.value(0)
        send_telegram_message(cid, "Relay turned OFF")
        auto_off_sent = False
    elif text == '/temp':
        temp, hum = read_sensor()
        if temp is not None and hum is not None:
            message = "Temperature: {:.2f}C\nHumidity: {:.2f}%".format(temp, hum)
            send_telegram_message(cid, message)
        else:
            send_telegram_message(cid, "Failed to read sensor")

# Connect to WiFi on startup
if not connect_wifi():
    print("Stopping due to WiFi failure")
    while True:
        time.sleep(60)  # Prevent tight loop

while True:
    try:
        # Check WiFi and auto-reconnect if dropped
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            print("WiFi disconnected, reconnecting...")
            if not connect_wifi():
                print("Reconnect failed, waiting 10 seconds...")
                time.sleep(10)
                continue
            

        # Print debug info
        print("Current chat_id:", chat_id)

        # Poll Telegram for updates
        try:
            response = urequests.get(TELEGRAM_UPDATES_URL + "?offset=" + str(offset))
            if response.status_code != 200:
                print("Telegram poll failed, status:", response.status_code)
                response.close()
                time.sleep(5)  # Skip this cycle on failure
                continue
            data = json.loads(response.text)
            response.close()
        except Exception as e:
            print("Error polling Telegram:", e)
            time.sleep(5)  # Skip cycle on failure
            continue

        if data.get('ok', False) and data.get('result'):
            for update in data['result']:
                update_id = update['update_id']
                offset = update_id + 1
                if 'message' in update:
                    msg = update['message']
                    if chat_id is None:
                        chat_id = msg['chat']['id']
                        print("Chat ID set to:", chat_id)
                    text = msg.get('text', '').strip()
                    if text.startswith('/'):
                        handle_command(text, chat_id)

        # Read sensor and handle temperature logic
        temp, hum = read_sensor()
        if temp is not None and hum is not None:
            print("Temperature: {:.2f}C, Humidity: {:.2f}%".format(temp, hum))
            if temp >= 30 and relay.value() == 0:
                message = "Alert: Temperature >= 30C ({:.2f}C)! Send /on to activate relay.".format(temp)
                if not send_telegram_message(chat_id, message):
                    print("Skipping cycle due to send failure")
                    time.sleep(5)
                    continue
            elif temp < 30 and relay.value() == 1 and not auto_off_sent:
                relay.value(0)
                message = "Relay auto-OFF: Temperature < 30C ({:.2f}C)".format(temp)
                if not send_telegram_message(chat_id, message):
                    print("Skipping cycle due to send failure")
                    time.sleep(5)
                    continue
                auto_off_sent = True
        else:
            print("Failed to read sensor, skipping cycle")
            time.sleep(5)  # Skip cycle on DHT OSError
            continue

    except Exception as e:
        print("Error in main loop:", e)
        time.sleep(5)  # Skip cycle on any other error

    time.sleep(5)