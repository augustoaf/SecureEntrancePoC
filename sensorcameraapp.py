import random
import time
import threading
import datetime
import os
import RPi.GPIO as GPIO
from picamera import PiCamera
import paho.mqtt.client as mqtt

BROKER_HOST = "192.168.86.42"
BROKER_PORT = 1883
MQTT_TOPIC = "house/pictures"
GPIO_IO = 4
camera_instance = PiCamera()

def instantiate_mqtt_client():
    client = ""
    try:
        client = mqtt.Client()
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

def touch_sensor_listener(gpio_pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(gpio_pin, GPIO.IN,pull_up_down=GPIO.PUD_UP)

    while True:
        if (GPIO.input(gpio_pin) == True):
            print ('touch sensor pressed')
            try:
                image_file = take_picture(camera_instance)

                mqtt_client = instantiate_mqtt_client()
                send_message(mqtt_client, image_file)
                mqtt_client.disconnect()
            except Exception as e:
                error = f"Touch sensor: Logging exception as repr: {e!r}"
                print(error) 
            time.sleep(5)

def take_picture(camera_instance):
        
    file_name = ""

    try:        
        camera_instance.start_preview()

        time.sleep(2) #warmup the camera
        current_date_and_time = str(datetime.datetime.now())
        extension = '.jpg'
        path = '/home/pi/workspace/images/unknown/'
        file_name = path + current_date_and_time + extension

        camera_instance.capture(file_name)
        camera_instance.stop_preview()

        print('Picture taken filename: ' + file_name)
    except Exception as e:
        error = f"Take picture: Logging exception as repr: {e!r}"
        print(error) 

    return file_name

def main():
    try:
        # set camera properties
        camera_instance.rotation = 180
        
        # Start a thread to listen touch sensor 
        touch_sensor_thread = threading.Thread(target=touch_sensor_listener, args=(GPIO_IO,))
        touch_sensor_thread.daemon = True
        touch_sensor_thread.start()

        while True:
            time.sleep(10)
            print(".")
    except KeyboardInterrupt:
        print ( "App stopped" )

if __name__ == '__main__':
    print ( "Press Ctrl-C to exit" )
    main()