import paho.mqtt.client as mqtt 
import time
import gtts
import pygame

BROKER_HOST = "192.168.86.42"
BROKER_PORT = 1883
MQTT_TOPIC = "house/texttospeech"
MQTT_CLIENT_ID = "id-321"

def instantiate_mqtt_client():
    client = ""
    try:
        client = mqtt.Client(MQTT_CLIENT_ID)
        client.connect(BROKER_HOST, port=BROKER_PORT, keepalive=60)
        client.subscribe(MQTT_TOPIC)

        #attach callback functions
        client.on_message=on_message
        client.on_disconnect = on_disconnect
        client.on_connect = on_connect
        client.on_log=on_log

        client.loop_start()
    except Exception as e:
        error = f"MQTT Client: Logging exception as repr: {e!r}"
        print(error)
            
    return client

def play_text(message):
    # to get all available languages along with their IETF tag, use: print(gtts.lang.tts_langs())
    tts = gtts.gTTS(message, lang="pt-br")
    
    # save the audio file
    audio_file_name = "speech.mp3"
    tts.save(audio_file_name)
    
    # play the audio file
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file_name)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy() == True:
        continue
    
    print("audio play done!")

# callback method to act when the connection is closed by the broker or by the client
def on_disconnect(client, userdata, rc):
   print("client disconnected ok")

def on_connect(client, userdata, flags, rc):
   print("client connected ok")

# callback method to receive the message when published on the topic this client has subscribed
def on_message(client, userdata, message):
    message_converted = str(message.payload.decode("utf-8"))
    print("message received on topic ", message.topic, ": " ,message_converted)
    play_text(message_converted)

# callback method for log
def on_log(client, userdata, level, buf):
    print("log: ",buf)

def main():

    client = ""
    try:
        client = instantiate_mqtt_client()

        while True:
            time.sleep(10)
            print(".")

    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()
        print ( "App stopped" )

if __name__ == '__main__':
    print ( "Press Ctrl-C to exit" )
    main()
