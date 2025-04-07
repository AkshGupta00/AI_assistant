import pyjokes
from ai import AI
from basicsystemcontrol import process_basic_sys_command
import spacy
import database as db
import file_functions as ff
# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

chotu = AI()
db.create_database()
def joke():
    funny = pyjokes.get_joke()
    print(funny)
    chotu.say(funny)

def is_basic_sys_command(command):
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

def is_file_function_cmd(command):
    """Returns True if the command is related to file management"""
    intent = ff.intent_detection(command)
    if intent != None:
        return True
    else:
        return False

command = ""

while True and command != "goodbye":
    command = chotu.listen()

    print("command was:",command)

    if command == "tell me a joke":
        joke()
    if is_basic_sys_command(command):
        db.is_latest_cmd_type(1)
        db.cmd_push(command,1)
        process_basic_sys_command(command)
    if is_file_function_cmd(command):
        if db.is_latest_cmd_type(2):
            db.cmd_push(command,2)
            massage = ff.incomplete_file_cmd_exe(db.get_latest_cmd_id,command)
            chotu.say(massage)
            print(massage)
        else:    
            db.cmd_push(command,2)
            massage = ff.file_management_cmd_execution(command,db.get_latest_cmd_id())
            chotu.say(massage)
            print(massage)
    
chotu.say("Goodbye, I'm going to sleep now")