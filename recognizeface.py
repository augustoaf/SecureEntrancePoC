import json
import time
import os
import shutil
import sys
import threading
import face_recognition
import paho.mqtt.client as mqtt

known_images_path = '/home/pi/workspace/images/known'
unknown_images_path = '/home/pi/workspace/images/unknown'
processed_images_path = '/home/pi/workspace/images/processed'

BROKER_HOST = "192.168.86.42"
BROKER_PORT = 1883
MQTT_TOPIC_SUB = "house/pictures"
MQTT_CLIENT_ID_SUB = "id-8888"
MQTT_TOPIC_PUB = "house/texttospeech"
MQTT_CLIENT_ID_PUB = "id-8888-2"


def instantiate_mqtt_client_and_subscribe():
    client = ""
    try:
        client = mqtt.Client(MQTT_CLIENT_ID_SUB)
        client.connect(BROKER_HOST, port=BROKER_PORT, keepalive=60)
        client.subscribe(MQTT_TOPIC_SUB)

        #bind callback functions
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        client.on_connect = on_connect
        client.on_log = on_log

        client.loop_start()
    except Exception as e:
        error = f"MQTT Client: Logging exception as repr: {e!r}"
        print(error)
            
    return client

# callback method to act when the connection is closed by the broker or by the client
def on_disconnect(client, userdata, rc):
   print("client disconnected ok")

def on_connect(client, userdata, flags, rc):
   print("client connected ok")
   #renew subscrition??

# callback method to receive the message when published on the topic this client has subscribed
def on_message(client, userdata, message):
    message_converted = str(message.payload.decode("utf-8"))
    print("message received on topic ", message.topic, ": " ,message_converted)
    recognize_face(message_converted)

# callback method for log
def on_log(client, userdata, level, buf):
    print("log: ",buf)

def send_message(payload):
    try:
        client = mqtt.Client(MQTT_CLIENT_ID_PUB)
        client.connect(BROKER_HOST, port=BROKER_PORT, keepalive=60)
        client.publish(MQTT_TOPIC_PUB,payload)
        client.disconnect()
        print("message sent to topic " + MQTT_TOPIC_PUB)
    except Exception as e:
        error = f"MQTT Publish: Logging exception as repr: {e!r}"
        print(error)

#def: list files from a folder and return files array
def list_files(input_path):
    list = [] 
    for path,dirs,files in os.walk(input_path):
        for filename in files:
            list.append(path+'/'+filename)
    return list

def return_last_text_split(text):
    result = text
    try:
        separator = '/'
        text_split = text.split(separator)
        result = text_split[len(text_split)-1]
    except:
        result = text
    return result

#source must be the filename with absolute path; passing the filename to destination will force overwrite if file already exists 
def move_file_to_processed_folder(source):
    try:
        filename = return_last_text_split(source)
        destination = processed_images_path
        shutil.move(source, destination+'/'+filename)
    except Exception as ex:
        print ( "wasn't able to move the file to processed folder. Exception: %s" % ex)

#def: load faces from image files and return faces array - input is an array of filenames (with absolute path)
def load_faces(input_filenames):
    #load image files
    counter = -1
    images_loaded_list = []

    #clone list in order to iterate the array, once the original list can have filenames removed if can't load an image
    tmp_input_filenames = input_filenames.copy()
    for image_filename in tmp_input_filenames:
        counter += 1
        try: 
            images_loaded_list.append(face_recognition.load_image_file(image_filename))
        except Exception as ex:
            print("wasn't able to load image: " + image_filename)
            move_file_to_processed_folder(input_filenames[counter])
            #print ("Unexpected error in load_faces(): %s" % ex)
            #once the item was not appended to the array, remove its ocurrence from the input_filenames array in order to match
            #the contents in faces_list array, otherwise the results will mismatch the index for matching faces
            input_filenames.pop(counter)
            #decrease the counter once the current item wasn't appended, otherwise the next pop won't work as expected
            counter -= 1

    #load faces from images loaded
    counter = -1
    faces_list = []
    for image_loaded in images_loaded_list:
        counter += 1
        try:
            #assumption to have only one face in the image, so it is getting the first face using the first index [0]
            tmp_faces = face_recognition.face_encodings(image_loaded)
            faces_list.append(tmp_faces[0])
        except Exception as ex:
            print("wasn't able to locate any faces in image: " + input_filenames[counter])
            move_file_to_processed_folder(input_filenames[counter])
            message_body = 'reconhecimento facial não foi possível!'
            send_message(message_body)
            #print ( "Unexpected error in load_faces(): %s" % ex)
            #once the item was not appended to the array, remove its ocurrence from the input_filenames array in order to match
            # the contents in faces_list array, otherwise the results will mismatch the index for matching faces
            input_filenames.pop(counter)
            #decrease the counter once the current item wasn't appended, otherwise the next pop won't work as expected
            counter -= 1

    return faces_list

#def: routine to recognize face and send result to iot hub 
def recognize_face(picture_to_recognize):
    try:
        print ( "\n RUNNING RECOGNIZE FACE ROUTINE ... \n")

        #load faces
        known_images_filename_list = list_files(known_images_path)
        if (picture_to_recognize == ""):
            unknown_images_filename_list = list_files(unknown_images_path)
        else:    
            unknown_images_filename_list = list = [picture_to_recognize] #handle just one picture

        print('KNOWN IMAGES FILENAME:')
        for known_image_filename in known_images_filename_list:
            print(return_last_text_split(known_image_filename))
        print('UNKNOWN IMAGES FILENAME:')
        for unknown_image_filename in unknown_images_filename_list:
            print(return_last_text_split(unknown_image_filename))
        print ( "\n")
        
        known_faces_list = load_faces(known_images_filename_list)
        unknown_faces_list = load_faces(unknown_images_filename_list)

        #loop all unknown faces
        unknown_counter = -1
        for unknown_face in unknown_faces_list:
            unknown_counter += 1
            known_counter = -1
            face_found = False
            unknown_filename = return_last_text_split(unknown_images_filename_list[unknown_counter])
            unknown_filename_absolute_path = unknown_images_filename_list[unknown_counter]

            print('DETECTING FACE ' + unknown_filename + ' ...')
            # get results is an array of True/False telling if the unknown face matched anyone in the known faces array
            faces_result = face_recognition.compare_faces(known_faces_list, unknown_face)
            #loop the results and check if the unknown face has a match
            for result in faces_result:
                known_counter += 1
                if result:
                    known_filename = return_last_text_split(known_images_filename_list[known_counter])
                    print('MATCH IS ' + known_filename)
                    face_found = True
                    #send message to output1 in order to route to iot hub
                    #message_body = 'face found for ' + unknown_filename + '. Match is ' + known_filename
                    message_body = 'acesso permitido!'
                    send_message(message_body)
                    quit

            if not(face_found):
                print('*** FACE NOT FOUND ***')
                #send message to output1 in order to route to iot hub
                #message_body = 'face not found for ' + unknown_filename
                message_body = 'acesso negado!'
                send_message(message_body)
            
            move_file_to_processed_folder(unknown_filename_absolute_path)
            print ( "\n")
            
    except Exception as ex:
        print ( "Unexpected error in recognizeFace(): %s" % ex )

def main():

    if not sys.version >= "3.5.3":
        raise Exception( "App requires python 3.5.3+. Current version of Python: %s" % sys.version )

    client = ""
    try:
        client = instantiate_mqtt_client_and_subscribe()

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
