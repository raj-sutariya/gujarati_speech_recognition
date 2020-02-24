## This is DeepSpeech speech recognition model for gujarati.
Offline Speech Recognition Engine

###Requirements
* To Use speech recognition engine using command line
`pip install requirements.txt`

* To use UI, additionally you need to do `pip install gui_requirements.txt`

###Use
Using Command line inference is plain and simple.
Note that here we are using sample demo.wav file as input.
```buildoutcfg  
deepspeech --model gu_model/output_graph.pb --alphabet gu_model/alphabet.txt --lm gu_model/lm.binary   --trie gu_model/trie --audio demo.wav 
```
Using gui.py file, you can interact with Speech Recognizer GUI.
Check your mic first and then Select speech model. 

![alt text](assets/gui_screenshot.png | width=290) 

## Acoustic Model
Speech Database has been created from the multiple sources like: Audiobooks, YouTube Audios etc.

## Language model contribution
lm.binary file is generate from web scrapping scrips of Gujarati wikipedia and gujarati news/blogs sites.
Contact me if you want entire corpus.

## What's next
* WER (Word error rate) Improvement
* Language model enhancement.
  
