The entire solution is a proof of concept for secure entrance in a restricted area using motion detector, audio notification and face recognition.  
  
The solution was built in modules (decoupling the components) to enable plug and play N devices.  
  
-----------------------------------------------------------------------------------------

sensorcameraapp.py  App

This app take a picture using a camera (OmniVision OV5647 - 5MP) attached to Raspberry PI and send notification to a Mqtt topic.
The trigger to take a picture is through a Touch Sensor TP223 (this part of the code use the RPi.GPIO lib)  
  
Requirements:
-Mqtt broker running  
-pip3 install picamera  
-pip3 install RPi.GPIO  
-pip3 install paho-mqtt 

-----------------------------------------------------------------------------------------

playtextfrommqtttopic.py  App

This app is a Mqtt client to subscribe to a topic, convert the text received in the topic message to speech using a google service through gtts lib, and then play the audio file generated.  
  
Requirements:  
-pip3 install paho-mqtt  
-pip3 install gTTS  
apt-get install python-pygame  
The usage of the gtts lib requires internet connection.  

-----------------------------------------------------------------------------------------

presencenotification App  

This app detect motion in the environment and publish a message about the presence detected.  
  
Requirements:  
-pip3 install paho-mqtt  
-pip3 install gpiozero  

-----------------------------------------------------------------------------------------

recognizeface.py App  
  
This app receive a notification (image filename) in a Mqtt topic in order to start face recognition. The app detect and compare the face inside the image received against known faces and then send the result to another Mqtt topic.  
  
Assumptions:  
- The code is handling images with only one face.  
- The image could not be upsidedown (or 90º rotation)  
- The trigger to recognize faces is a Mqtt topic which this app subscribe  
  
Requirements:  
- pip3 install paho-mqtt  
- requirements to app using face_recognition lib: cmake, dlib and face_recognition  
usually the steps below works:  
apt-get update  
apt-get --yes install libatlas-base-dev  
pip3 install cmake  
pip3 install dlib  
pip3 install face_recognition  
