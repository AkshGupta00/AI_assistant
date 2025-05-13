from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import librosa
import numpy as np
import os
import joblib




def extract_features(folder):
    features = []
    labels = []
    for label in os.listdir(folder):
        class_path = os.path.join(folder, label)
        for file in os.listdir(class_path):
            y, sr = librosa.load(os.path.join(class_path, file), sr=16000)
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)  # Corrected line
            features.append(np.mean(mfcc.T, axis=0))
            labels.append(1 if label == "wakeword" else 0)
    return np.array(features), np.array(labels)


X, y = extract_features("processed")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier()
model.fit(X_train, y_train)

print("Accuracy:", model.score(X_test, y_test))

# Save the trained model to a file
joblib.dump(model, 'wakeword_model.pkl')