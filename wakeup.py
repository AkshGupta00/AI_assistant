import pyaudio
import numpy as np
import librosa
import joblib
import time

# Load the trained model
model = joblib.load('wakeword_model.pkl')

# Initialize PyAudio to capture audio from the microphone
p = pyaudio.PyAudio()

# Define the parameters for audio capture
chunk_size = 1024  # Number of audio samples per frame
sample_rate = 16000  # 16 kHz sample rate
device_index = None  # None for the default microphone
seconds_to_record = 2  # Duration of each buffer in seconds
frames_per_buffer = seconds_to_record * sample_rate  # Number of frames per 2 seconds

# Start recording audio from the microphone
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                frames_per_buffer=chunk_size,
                input_device_index=device_index)

print("Listening for wakeword...")

def extract_mfcc_features_from_audio(audio_chunk):
    # Convert raw audio (int16) to floating-point format (float32)
    audio_chunk = np.array(audio_chunk, dtype=np.float32) / 32768.0  # Normalizing to [-1, 1]
    
    # Extract MFCC features
    mfcc = librosa.feature.mfcc(y=audio_chunk, sr=sample_rate, n_mfcc=13)
    return np.mean(mfcc.T, axis=0).reshape(1, -1)

while True:
    # Read a chunk of audio from the microphone (2 seconds of audio)
    audio_chunk = np.frombuffer(stream.read(frames_per_buffer), dtype=np.int16)

    # Extract MFCC features from the 2-second audio chunk
    features = extract_mfcc_features_from_audio(audio_chunk)

    # Predict whether it's a wakeword
    prediction = model.predict(features)

    if prediction == 1:
        print("Wakeword detected!")
    else:
        print("No wakeword detected.")
    
    time.sleep(1)  # Sleep for a short time to avoid excessive CPU usage
