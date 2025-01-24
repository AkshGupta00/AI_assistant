import pyjokes
from ai import AI

chotu = AI()

def joke():
    funny = pyjokes.get_joke()
    print(funny)
    chotu.say(funny)

command = ""

while True and command != "goodbye":
    command = chotu.listen()
    print("command was:",command)

    if command == "tell me a joke":
        joke()
    
chotu.say("Goodbye, I'm going to sleep now")