
import spacy
import os
import re
import glob
import send2trash
import shutil


nlp = spacy.load("en_core_web_sm")
nlp.Defaults.stop_words.remove("move")
nlp.vocab["move"].is_stop = False

def intent_detection(command):
    """Extract the intent of the user from the user input"""
    command = command.lower()
    doc = nlp(command)

    intents = {
        "open": ["open", "find and open"],
        "search": ["find", "locate", "search"],
        "create": ["create", "make", "new file"],
        "rename": ["rename", "change name"],
        "move": ["move", "transfer"],
        "copy": ["copy", "duplicate"],
        "delete": ["delete", "remove"],
        "compress": ["compress", "zip"],
        "extract": ["extract", "unzip"],
        "storage": ["storage", "disk space", "free space", "disk usage"]
    }

    # First check for exact multi-word phrases
    for intent, phrases in intents.items():
        for phrase in phrases:
            if phrase in command:
                return intent

    # Check individual words
    for token in doc:
        for intent, words in intents.items():
            if token.lemma_ in words:
                return intent

    return None

print(intent_detection("Open the filename.txt"))