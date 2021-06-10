import time
import datetime
import threading
from gpiozero import MotionSensor
import paho.mqtt.client as mqtt

BROKER_HOST = "192.168.86.42"
BROKER_PORT = 1883
MQTT_TOPIC = "house/texttospeech"
MQTT_CLIENT_ID = "id-14332"
GPIO_IO = 27

def instantiate_mqtt_client():
    client = ""
    try:
        client = mqtt.Client(MQTT_CLIENT_ID)
        client.connect(BROKER_HOST, port=BROKER_PORT, keepalive=60)
        #client.loop_start()
    except Exception as e:
        error = f"MQTT Client: Logging exception as repr: {e!r}"
        print(error)
            
    return client

def send_message(mqtt_client, payload):
    if not isinstance(mqtt_client, str):
        try:            
            mqtt_client.publish(MQTT_TOPIC,payload)
            print("message sent to topic " + MQTT_TOPIC)
        except Exception as e:
            error = f"MQTT Publish: Logging exception as repr: {e!r}"
            print(error)

def motion_listener():
    
    try:
        pir = MotionSensor(GPIO_IO)
        notification_to_environment = "o acesso apartir daqui é restrito, por favor se identifique!"

        while True:

            pir.wait_for_motion()
            print("presence detected!")

            mqtt_client = instantiate_mqtt_client()
            send_message(mqtt_client, notification_to_environment)
            mqtt_client.disconnect()

            time.sleep(5)

    except RuntimeError:
        print('runtime error')

def main():

    try:
        # Start a thread to listen motion sensor
        motion_thread = threading.Thread(target=motion_listener, args=())
        motion_thread.daemon = True
        motion_thread.start()

        while True:
            time.sleep(10)
            print(".")

    except KeyboardInterrupt:
        print ( "App stopped" )

if __name__ == '__main__':
    print ( "Press Ctrl-C to exit" )
    main()