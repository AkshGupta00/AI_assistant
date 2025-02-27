import pyjokes
from ai import AI
from basicsystemcontrol import process_basic_sys_command
import spacy

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

chotu = AI()

def joke():
    funny = pyjokes.get_joke()
    print(funny)
    chotu.say(funny)

def is_basic_sys_command_command(command):
    """Returns True if the command is related to system control, volume, brightness, or application management."""
    doc = nlp(command.lower())

    # Keywords for different operations
    valid_keywords = {
        "close", "exit", "quit", "terminate", "stop",  # Closing apps/windows
        "open", "launch", "start",                     # Opening apps
        "shutdown", "restart", "sleep", "lock",        # System control
        "volume", "mute", "sound", "audio", "increase", "decrease", "up", "down",  # Volume
        "brightness", "screen light", "dim", "adjust"  # Brightness
    }

    # Check if any word in the command matches the valid keywords
    return any(token.lemma_ in valid_keywords for token in doc)


command = ""

while True and command != "goodbye":
    command = chotu.listen()
    print("command was:",command)

    if command == "tell me a joke":
        joke()
    if is_basic_sys_command_command(command):
        process_basic_sys_command(command)
    
chotu.say("Goodbye, I'm going to sleep now")