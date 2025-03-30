import pyttsx3
import speech_recognition as sr

class AI():
    __name = ""
    __skill = []

    def __init__(self,name=None):
        self.engin = pyttsx3.init()

        self.r = sr.Recognizer()
        self.m = sr.Microphone()

        if(name is not None):
            self.__name = name
        print("Listening")
        with self.m as source:
            self.r.adjust_for_ambient_noise(source)
    @property
    def name(self):
        return self.__name
    
    @name.setter
    def name(self,value):
        sentence = "Hello, my name is"+self.__name
        self.__name = value
        self.engin.say(sentence)
        self.engin.runAndWait()

    def say(self,sentence):
        self.engin.say(sentence)
        self.engin.runAndWait()

    def listen(self):
        print("say someting")
        with self.m as source:
            audio = self.r.listen(source)
        print("got it")
        try:
            phrase = self.r.recognize_google(audio,show_all=False,language="engb").lower().rstrip('?')
            sentence = "got it ,you said"+phrase
            self.engin.say(sentence)
            self.engin.runAndWait()
        except Exception as e :
            sentence = "sorry did'nt catch that"
            self.engin.say(sentence)
            self.engin.runAndWait()
            print("sorry did'nt catch that",e)
        print("you said",phrase)
        return phrase