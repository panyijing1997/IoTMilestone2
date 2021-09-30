import json

import RPi.GPIO as GPIO
import board
import adafruit_dht
import time
import paho.mqtt.client as mqtt
import socket

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# set ports for LEDs
GPIO.setup(4, GPIO.OUT)  # set #4 as ouput port
GPIO.output(4, GPIO.LOW)  # initially turned off
GPIO.setup(2, GPIO.OUT)
GPIO.output(2, GPIO.LOW)
GPIO.setup(22, GPIO.OUT)
GPIO.output(22, GPIO.LOW)

# set ports for distance sensor
TRIG = 23
ECHO = 24
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)



"""
mqtt functions for server
"""
def on_subscribe_led(client, userdata, mid, granted_qos):
    print("led subscribed")
    print(granted_qos)

def on_connect_led(client, userdata, flags, rc):
    print(f"leds connected with result code {rc}")
    client.subscribe("queen/led/action",1)
    client.subscribe("check_led",1)
    client.subscribe("test",1)

# when LED receives message of changing states
def on_message_led(client, userdata, message):
    print(f"led receivedd a message")
    if message.topic == "check_led":
        ledState_blue = GPIO.input(4)
        ledState_red = GPIO.input(2)
        ledState_green = GPIO.input(22)
        ledState = {
            'led_blue': ledState_blue,
            'led_red': ledState_red,
            'led_green': ledState_green,
        }
        client.publish("queen/led/state", json.dumps(ledState),retain=True)
    elif message.topic == "queen/led/action":
        msg=str(message.payload.decode("utf-8"))
        msg=json.loads(msg)
        print(msg)
        if msg['color']=="blue":
            if msg['action']=="on":
                GPIO.output(4, GPIO.HIGH)
            else:
                GPIO.output(4, GPIO.LOW)
        elif msg['color']=="green":
            if msg['action'] == "on":
                GPIO.output(22, GPIO.HIGH)
            else:
                GPIO.output(22, GPIO.LOW)
        elif msg['color']=="red":
            if msg['action']=="on":
                GPIO.output(2, GPIO.HIGH)
            else:
                GPIO.output(2, GPIO.LOW)

        # after change publish state:
        ledState_blue = GPIO.input(4)
        ledState_red = GPIO.input(2)
        ledState_green = GPIO.input(22)
        ledState = {
            'led_blue': ledState_blue,
            'led_red': ledState_red,
            'led_green': ledState_green,
        }
        client.publish("queen/led/state",json.dumps(ledState))
    else:
        print(str(message.payload.decode("utf-8")))

def on_connect_sensort(client, userdata, flags, rc):
    print(f"dht11 client Connected with result code {rc}")
    client.subscribe("queen/dht11_check")

def on_message_sensort(client, userdata, message):
    r_msg=str(message.payload.decode("utf-8"))
    print("temp received check")

    dhtDevice = adafruit_dht.DHT11(board.D12, use_pulseio=False)
    try:
        temperature = dhtDevice.temperature
        humidity = dhtDevice.humidity
        if humidity is not None and temperature is not None:
            msg = "read from the sensor successfully"
            templateData = {
                'temperature': temperature,
                'humidity': humidity,
                'msg': msg
            }
        client.publish("queen/dht11_store",json.dumps(templateData))
    except RuntimeError as error:
        client.publish("queen/dht11_error", "read_failed")
        dhtDevice.exit()

    except Exception as error:
        client.publish("queen/dht11_error", "read_failed")
        dhtDevice.exit()

def on_connect_sensord(client, userdata, flags, rc):
    print(f"distance measure client Connected with result code {rc}")
    client.subscribe("queen/distance_check")

def on_publish_sensord(client, userdata, mid):
    print("distance data published")

def on_message_sensord(client, userdata, message):
    print(f"distance sensor receivedd a message")
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    pulse_start = 0
    pulse_end = 0

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    templateData = {
        'dist': distance,
    }
    client.publish("queen/distance_store", json.dumps(templateData))



ledc = mqtt.Client()
ledc.on_connect = on_connect_led
ledc.on_message = on_message_led
ledc.on_subscribe=on_subscribe_led
ledc.connect("mosquitto", 1883, 200)
ledc.loop_start()


sensord=mqtt.Client()
sensord.on_connect=on_connect_sensord
sensord.on_publish=on_publish_sensord
sensord.on_message=on_message_sensord
sensord.connect("mosquitto", 1883, 200)
sensord.loop_start()

sensort=mqtt.Client()
sensort.on_connect=on_connect_sensort
sensort.on_message=on_message_sensort
sensort.connect("mosquitto", 1883, 200)
sensort.loop_start()


ledc.publish("test","sdfgdsdfg")


print("yayaya")
while True:
    pass

