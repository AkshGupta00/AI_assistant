import tkinter as tk
from tkinter import scrolledtext
import threading

# Mock functions (replace with actual AI, chotu, and processing logic)
def get_voice_command():
    return "open myfile.txt from downloads"

def process_command_ui(command):
    # Place your processing logic here
    response = f"You said: {command}"
    return response

# Main App Class
class ChatApp:
    def __init__(self, root):
        self.root = root
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
            response = process_command_ui(command)
            self.display_message("Chotu", response)

    def handle_voice_command(self):
        self.display_message("You", "[Listening...]")
        threading.Thread(target=self.process_voice_command).start()

    def process_voice_command(self):
        command = get_voice_command()  # Replace with actual chotu.listen()
        self.display_message("You", command)
        response = process_command_ui(command)
        self.display_message("Chotu", response)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
