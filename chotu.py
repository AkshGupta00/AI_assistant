import pyjokes
from ai import AI
from basicsystemcontrol import process_basic_sys_command,extract_app_name,find_application
import spacy
import database as db
import file_functions as ff
import tkinter as tk
from tkinter import scrolledtext
import threading


# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Create AI instance
chotu = AI()
db.create_database()

# Helper Functions
def joke():
    funny = pyjokes.get_joke()
    print(funny)
    chotu.say(funny)

def is_basic_sys_command(command):
    doc = nlp(command.lower())
    valid_keywords = {
        "close", "exit", "quit", "terminate", "stop",
        "open", "launch", "start",
        "shutdown", "restart", "sleep", "lock",
        "volume", "mute", "sound", "audio", "increase", "decrease", "up", "down",
        "brightness", "screen light", "dim", "adjust"
    }
    return any(token.lemma_ in valid_keywords for token in doc)

def is_open_system_command(command):
    """Returns True if 'open' is used as a system-level command (app/software), False if not."""
    command = command.lower()
    if "open" not in command:
        return False

    app_name = extract_app_name(command)
    if app_name:
        return find_application(app_name) is not None

    return False
def is_file_function_cmd(command):
    return ff.intent_detection(command) is not None

def is_greating_cmd(command):
    return True if "hello" or "hi" in command else False

def process_command(command):
    print("command was:", command)

    if command.lower() == "tell me a joke":
        joke()
    elif is_greating_cmd(command):
        chotu.say("Hello! How can I help you?")
        message = "Hello! How can I help you?"
    elif command.lower() == "who are you":
        chotu.say("I am Chotu, your friendly AI assistant!")
        message = "I am Chotu, your friendly AI assistant!"
    elif command.lower() == "who is your creator":
        chotu.say("I was created by Aksh Gupta as a project for his 6 samister!")
        message = "I was created by Aksh Gupta as a project for his 6 samister!"
    elif is_basic_sys_command(command):
        if is_open_system_command(command):
            db.cmd_push(command, 1)
            flag,message = process_basic_sys_command(command)
        else:
            db.cmd_push(command, 2)
            if db.is_latest_cmd_type(2):
                message = ff.incomplete_file_cmd_exe(db.get_latest_cmd_id(), command)
            else:
                message = ff.file_management_cmd_execution(command, db.get_latest_cmd_id())
        chotu.say(message)
        print(message)

    elif is_file_function_cmd(command):
        db.cmd_push(command, 2)
        if db.is_latest_cmd_type(2):
            message = ff.incomplete_file_cmd_exe(db.get_latest_cmd_id(), command)
        else:
            message = ff.file_management_cmd_execution(command, db.get_latest_cmd_id())
        chotu.say(message)
        print(message)
    else:
        chotu.say("Sorry, I didn't understand the command.")
    return message if 'message' in locals() else "Sorry, I didn't understand the command."


# GUI App
class ChatApp:
    def __init__(self, root, assistant: AI):
        self.root = root
        self.a = assistant
        self.root.title("Chotu - Voice/Text Assistant")

        self.chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', width=60, height=20)
        self.chat_area.pack(padx=10, pady=10)

        self.entry = tk.Entry(root, width=50)
        self.entry.pack(side=tk.LEFT, padx=(10, 5), pady=(0, 10))
        self.entry.bind("<Return>", self.handle_text_command)

        self.send_button = tk.Button(root, text="Send", command=self.handle_text_command)
        self.send_button.pack(side=tk.LEFT, padx=5, pady=(0, 10))

        self.voice_button = tk.Button(root, text="🎤 Voice", command=self.handle_voice_command)
        self.voice_button.pack(side=tk.LEFT, padx=(5, 10), pady=(0, 10))

    def display_message(self, sender, message):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"{sender}: {message}\n")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    def handle_text_command(self, event=None):
        command = self.entry.get()
        if command.strip():
            self.entry.delete(0, tk.END)
            self.display_message("You", command)

            # ⬇️ Process the command in a thread to prevent UI freeze
            threading.Thread(target=self.process_and_respond, args=(command,)).start()

    def process_and_respond(self, command):
        message = process_command(command)
        self.display_message("Chotu", message)

    def handle_voice_command(self):
        self.display_message("You", "[Listening...]")
        threading.Thread(target=self.process_voice_command).start()

    def process_voice_command(self):
        command = self.a.listen()
        self.display_message("You", command)
        threading.Thread(target=self.process_and_respond, args=(command,)).start()


# Background listener loop (optional)
def background_listener():
    while True:
        cmd = chotu.listen()
        process_command(cmd)
        if cmd == "goodbye":
            chotu.say("Goodbye, I'm going to sleep now")
            break

# Main Entry
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root, chotu)

    # Run background listener (optional)
    # threading.Thread(target=background_listener, daemon=True).start()

    root.mainloop()
