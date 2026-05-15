# Allow running app.py from different working directories (UI.py, terminal, etc.)
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function import *


from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import model_from_json
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import TensorBoard
from gtts import gTTS
import os
import json
import cv2
import numpy as np
import mediapipe as mp

# Function to convert text to speech
def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    tts.save('output.mp3')
    os.system("start output.mp3")  # For Windows, for other OS, use appropriate command

# Load the trained model
# NOTE: use absolute paths relative to this file so it works when launched
# from UI.py or a different working directory.
from tensorflow.keras.models import load_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_H5_PATH = os.path.join(BASE_DIR, "model.h5")

# Keras/TF 2.15+ may fail deserializing legacy H5/JSON containing
# InputLayer(batch_shape). To avoid this entirely, we reconstruct the
# architecture used during training and then load only the weights.
#
# Architecture (from trainmodel.py):
# LSTM(64, return_sequences=True, input_shape=(30,63))
# LSTM(128, return_sequences=True)
# LSTM(64, return_sequences=False)
# Dense(64) -> Dense(32) -> Dense(num_classes)
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

model = Sequential()
model.add(LSTM(64, return_sequences=True, activation='relu', input_shape=(30, 63)))
model.add(LSTM(128, return_sequences=True, activation='relu'))
model.add(LSTM(64, return_sequences=False, activation='relu'))
model.add(Dense(64, activation='relu'))
model.add(Dense(32, activation='relu'))
model.add(Dense(actions.shape[0], activation='softmax'))

model.load_weights(MODEL_H5_PATH)






# Define colors for visualization
colors = [(245,117,16) for _ in range(20)]

# Function to visualize probabilities
def prob_viz(res, actions, input_frame, colors, threshold):
    output_frame = input_frame.copy()
    for num, prob in enumerate(res):
        cv2.rectangle(output_frame, (0,60+num*40), (int(prob*100), 90+num*40), colors[num], -1)
        cv2.putText(output_frame, actions[num], (0, 85+num*40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
    return output_frame

# New detection variables
sequence = []
sentence = []
accuracy = []
predictions = []
prev_prediction = -1  # Variable to store previous prediction
threshold = 0.8 

# Open the camera feed
cap = cv2.VideoCapture(0)
with mp_hands.Hands(model_complexity=0, min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
    while cap.isOpened():
        # Read feed
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        # Make detections
        cropframe = frame[40:400, 0:300]
        frame = cv2.rectangle(frame, (0, 40), (300, 400), 255, 2)
        image, results = mediapipe_detection(cropframe, hands)
        
        # Prediction logic
        keypoints = extract_keypoints(results)
        sequence.append(keypoints)
        sequence = sequence[-30:]

        try: 
            if len(sequence) == 30:
                res = model.predict(np.expand_dims(sequence, axis=0))[0]
                predictions.append(np.argmax(res))
                
                if np.unique(predictions[-10:])[0] == np.argmax(res):
                    if res[np.argmax(res)] > threshold:
                        if len(sentence) > 0:
                            if actions[np.argmax(res)] != sentence[-1]:
                                sentence.append(actions[np.argmax(res)])
                                accuracy.append(str(res[np.argmax(res)]*100))
                        else:
                            sentence.append(actions[np.argmax(res)])
                            accuracy.append(str(res[np.argmax(res)]*100)) 

                if len(sentence) > 1:
                    sentence = sentence[-1:]
                    accuracy = accuracy[-1:]

                # Visualize probabilities
                frame = prob_viz(res, actions, frame, colors, threshold)
                
                # Convert recognized word to speech and play it
                recognized_text = ' '.join(sentence)
                print(recognized_text)  # Print recognized word in terminal
                
                # Play audio only when detected sign changes
                if prev_prediction != np.argmax(res):
                    text_to_speech(recognized_text)
                    prev_prediction = np.argmax(res)
                
        except Exception as e:
            pass
            
        # Display recognized word on the window
        cv2.rectangle(frame, (0, 0), (300, 40), (245, 117, 16), -1)
        cv2.putText(frame, "Output: -" + ' '.join(sentence) + ''.join(accuracy), (3, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Show frame
        cv2.imshow('OpenCV Feed', frame)

        # Break gracefully
        if cv2.waitKey(10) & 0xFF == ord('q') or cv2.waitKey(10) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
