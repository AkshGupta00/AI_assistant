from pydub import AudioSegment
import librosa
import numpy as np
import os
import soundfile as sf

def convert_m4a_to_wav(src_path, dst_path):
    audio = AudioSegment.from_file(src_path, format="m4a")
    audio.export(dst_path, format="wav")

def preprocess_audio(src_folder, dst_folder, sample_rate=16000, duration=1):
    os.makedirs(dst_folder, exist_ok=True)
    for file in os.listdir(src_folder):
        if file.lower().endswith((".wav", ".m4a")):
            file_path = os.path.join(src_folder, file)
            print(f"Processing file: {file_path}")  # Add this line to debug
            
            if file.endswith(".m4a"):
                tmp_path = os.path.join(dst_folder, "temp.wav")
                convert_m4a_to_wav(file_path, tmp_path)
                path_to_load = tmp_path
            else:
                path_to_load = file_path

            try:
                print(f"Loading {path_to_load}...")  # Add this line for debugging
                y, sr = librosa.load(path_to_load, sr=sample_rate)
                y = librosa.util.fix_length(y, size=int(sample_rate * duration))
                new_file = os.path.splitext(file)[0] + ".wav"
                sf.write(os.path.join(dst_folder, new_file), y, sample_rate)
                print(f"Saved {new_file}")
            except Exception as e:
                print(f"Error processing {file}: {e}")


# Example
preprocess_audio("D:\\BCA\\6th_semister\\major\\datasets\\wakeword", "D:\\BCA\\6th_semister\\major\\processed\\wakeword")
preprocess_audio("D:\\BCA\\6th_semister\\major\\datasets\\negative", "D:\\BCA\\6th_semister\\major\\processed\\negative")
