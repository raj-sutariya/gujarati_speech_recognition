import os
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from winsound import PlaySound, SND_FILENAME
from sys import byteorder
from array import array
from struct import pack
from collections import Counter
import math
import json
import requests
import pyaudio
import wave
import datetime
import _thread
import speech_recognition as sr  # import Google ASR API - just for experiment

LANGUAGE_CODE = "gu"
REPLY_ME_BACK = False
TALK_BACK = False
SHOW_OUTPUT_WITHOUT_LM_ALSO = False

# WORD = re.compile(r'\w+')  # User for text to vector conversion
if TALK_BACK:
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty('voice', r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0')


class App:
    def __init__(self, root):
        self.processing_flag = False
        self.welcome = ttk.Label(root, text='Welcome! to Raj ASR Engine', font=("Constantia", 12), anchor=N,
                                 justify=CENTER,
                                 width=27)
        self.welcome.pack(pady=20)

        # Drop-down menu
        self.dropdown_selection = StringVar(root)
        choices = [j for j in [i[1] for i in os.walk(".")][0] if 'model' in j] + ['google_api']
        self.model_selection = ttk.OptionMenu(root, self.dropdown_selection, choices[0], *choices)
        self.dropdown_selection.set("Speech Models")  # set the default option
        self.model_selection.pack()
        self.model_folder = ""

        # on change dropdown value
        def change_dropdown(*args):
            self.model_folder = self.dropdown_selection.get()

        # link function to change dropdown
        self.dropdown_selection.trace('w', change_dropdown)

        # Input text section
        self.transcribed_text = ttk.Label(root)
        self.transcribed_text.config(text="This is input <<",
                                     wraplength=300,
                                     justify=RIGHT,
                                     anchor=E,
                                     font=("Constantia", 10),
                                     background='#e8f2ff'
                                     )
        self.transcribed_text.pack(fill=X, pady=2, ipady=5, padx=8)

        # Output text section
        self.progress_png = PhotoImage(file="assets/wave.png")
        self.response_text = ttk.Label(root)
        if REPLY_ME_BACK:
            self.response_text.config(text=">> This is Response",
                                      wraplength=300,
                                      justify=LEFT,
                                      anchor=W,
                                      font=("Constantia", 10),
                                      background='#fafafa'
                                      )
        self.response_text.pack(fill=X, pady=2, ipady=5, padx=8)

        # Browse Button
        self.file_address = ""
        self.browse_button = ttk.Button(root, text=" Browse ")
        self.browse_button.bind("<Button-1>", self.browse_pressed)
        # self.browse_button.bind("<ButtonRelease-1>", self.transcribing)
        self.browse_button.pack(pady=10)

        # Play Audio Button
        def play_audio():
            playable_audio = convert_file(self.file_address)
            PlaySound(playable_audio, SND_FILENAME)

        self.play_button = ttk.Button(root, text='Play Audio', command=play_audio)

        self.is_recording = True
        # Record Button
        self.mic_start = PhotoImage(file="assets/mic_start.png")
        self.mic_stop = PhotoImage(file="assets/mic_stop.png")
        self.mic_img = Label(root)
        self.mic_img.config(image=self.mic_start)
        self.mic_img.bind("<Button-1>", self.record_pressed)
        self.mic_img.bind("<ButtonRelease-1>", self.recording)
        self.mic_img.pack(pady=15)

        # Send Button
        self.send_button = ttk.Button(root, text=" Send ")
        self.send_button.bind("<Button-1>", self.send_pressed)
        self.send_button.bind("<ButtonRelease-1>", self.transcribing)

    def record_pressed(self, root):
        self.mic_img.config(image=self.mic_stop)

    def send_pressed(self, root):
        self.response_text.config(compound='image', image=self.progress_png, background="#f0f0f0")
        self.transcribed_text.config(text="", background="#f0f0f0")

    def browse_pressed(self, root):
        self.file_address = filedialog.askopenfilename(initialdir="/", title="Select file",
                                                       filetypes=(("Audio files", "*.wav;*.m4a;*.webm;*.mp3"),
                                                                  ("All files", "*.*")))
        if self.file_address is not "":
            self.play_button.pack(pady=4)
            self.browse_button.config(text=self.file_address)
            self.send_button.pack(pady=4)

    def transcribing(self, root):
        if self.processing_flag is False:
            self.processing_flag = True

            if self.model_folder is not "":
                if self.model_folder == 'google_api':
                    transcription = google_speech_api(self.file_address, lang_code=LANGUAGE_CODE)
                else:
                    transcription = deep_speech_engine(self.file_address, self.model_folder)
            else:
                transcription = "^^ Select Speech model"

            if REPLY_ME_BACK:
                response = duckduckgo_api(transcription)
                self.response_text.config(compound='text', text=(">> " + response), background='#fafafa')
                if TALK_BACK:
                    _thread.start_new_thread(speak, (response,))
            else:
                self.response_text.config(compound='text', text="", background="#f0f0f0")
            self.transcribed_text.config(compound='text', text=(transcription.capitalize() + " <<"),
                                         background='#e8f2ff')
            self.processing_flag = False

    def recording(self, root):
        if self.processing_flag is False:
            self.processing_flag = True
            print("Rec started", end=", ")
            self.file_address = "demo.wav"
            record_to_file(self.file_address)
            print("Stopped")
            self.play_button.pack(pady=10)
            self.send_button.pack(pady=10)
            self.mic_img.config(image=self.mic_start)
            self.browse_button.config(text=" Browse ")
            self.processing_flag = False
        else:
            self.response_text.config(compound='text', text="Recording Failed, Try Again", background='#fafafa')
            self.file_address = ""


# RECORD AUDIO WHEN DETECT ACTIVITY
THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16  # 16bit-PCM
RATE = 16000  # 16KHz


def is_silent(snd_data):
    # Returns 'True' if below the 'silent' threshold
    return max(snd_data) < THRESHOLD


def normalize(snd_data):
    # Average the volume out
    MAXIMUM = 16384
    times = float(MAXIMUM) / max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i * times))
    return r


def trim(snd_data):
    # Trim the blank spots at the start and end

    def _trim(snd_data):
        snd_started = False
        r = array('h')

        for i in snd_data:
            if not snd_started and abs(i) > THRESHOLD:
                snd_started = True
                r.append(i)

            elif snd_started:
                r.append(i)
        return r

    # Trim to the left
    snd_data = _trim(snd_data)

    # Trim to the right
    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data


def add_silence(snd_data, seconds):
    # Add silence to the start and end of 'snd_data' of length 'seconds' (float)
    r = array('h', [0 for _ in range(int(seconds * RATE))])
    r.extend(snd_data)
    r.extend([0 for _ in range(int(seconds * RATE))])
    return r


def record():
    """
    Record a word or words from the microphone and
    return the data as an array of signed shorts.

    Normalizes the audio, trims silence from the
    start and end, and pads with 0.5 seconds of
    blank sound to make sure VLC et al can play
    it without getting chopped off.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
                    input=True, output=True,
                    frames_per_buffer=CHUNK_SIZE)

    num_silent = 0
    snd_started = False

    r = array('h')

    while 1:
        # little endian, signed short
        snd_data = array('h', stream.read(CHUNK_SIZE))
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

        silent = is_silent(snd_data)

        if silent and snd_started:
            num_silent += 1
        elif not silent and not snd_started:
            snd_started = True

        if snd_started and num_silent > 30:
            break

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()

    stream.close()
    p.terminate()

    r = normalize(r)
    r = trim(r)
    r = add_silence(r, 0.5)
    return sample_width, r


def record_to_file(path):
    # Records from the microphone and outputs the resulting data to 'path'
    sample_width, data = record()
    data = pack('<' + ('h' * len(data)), *data)

    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()


def google_speech_api(file_name, lang_code):
    file_name = convert_file(file_name)
    file_data = sr.AudioFile(file_name)
    r = sr.Recognizer()
    with file_data as source:
        audio = r.record(source)
        return r.recognize_google(audio, language=lang_code)
        # return r.recognize_sphinx(audio)


def convert_file(file_path):
    file_name, file_extension = os.path.splitext(file_path)

    if (file_extension == '.mp3') | (file_extension == '.m4a') | (file_extension == '.webm'):
        command = "ffmpeg -y -loglevel quiet -i \"" + file_path + "\" -ar 16000 -ac 1 \"" + file_name + ".wav\""
        try:
            print(command)
            os.popen(command).read()
        except:
            pass
    return file_name + ".wav"


def deep_speech_engine(file_name, model_folder):
    file_name = convert_file(file_name)

    if os.path.isfile(file_name):
        command = "deepspeech " \
                  "--model " + model_folder + "/output_graph.pb " \
                                              "--alphabet " + model_folder + "/alphabet.txt " \
                                                                             "--lm " + model_folder + "/lm.binary " \
                                                                                                      "--trie " + model_folder + "/trie " \
                                                                                                                                 "--audio \"" + file_name + '\"'
        command2 = "deepspeech " \
                   "--model " + model_folder + "/output_graph.pb " \
                                               "--alphabet " + model_folder + "/alphabet.txt " \
                                                                              "--lm " + model_folder + "/lm2.binary " \
                                                                                                       "--trie " + model_folder + "/trie " \
                                                                                                                                  "--audio \"" + file_name + '\"'
        try:
            if SHOW_OUTPUT_WITHOUT_LM_ALSO:
                transcript = os.popen(command).read()[:-1] + "\n<<\n" + os.popen(command2).read()[:-1] + "\n" + 'new LM'
            else:
                transcript = os.popen(command).read()[:-1]
        except:
            transcript = "Speech Recognition Failed, Try Again"
    else:
        transcript = "File not found"
    return transcript


def duckduckgo_api(input_text):
    try:
        return str(eval(
            input_text.replace("x", "*").replace("X", "*").replace("multiply", "*").replace("multiplied", "*").replace(
                "into", "*")))
    except:
        # url = "https://api.duckduckgo.com/?q="+input_text.replace(" ", "+")+"&format=json&pretty=1"
        url = "https://api.duckduckgo.com/?q=" + input_text + "&format=json&pretty=1"
        response = requests.get(url=url)
        # print(response.text)
        json_response = response.json()
        a = json_response["Abstract"].split(".")
        try:
            if a[0] is "":
                return json_response["RelatedTopics"][0]["Text"]
            else:
                a[0] = a[0] + "."
                return "".join(a[0:1])
        except:
            return "Sorry, I don't know."


if TALK_BACK:
    def speak(text):
        engine.say(text)
        engine.runAndWait()

if __name__ == '__main__':
    main = Tk()
    app = App(main)
    main.title("Speech Recognizer")
    main.mainloop()
