import numpy as np
import wave
from deepspeech import Model
from time import time

start = time()
# These constants control the beam search decoder
# Beam width used in the CTC decoder when building candidate transcriptions
BEAM_WIDTH = 500
# The alpha hyperparameter of the CTC decoder. Language Model weight
LM_ALPHA = 0.75
# The beta hyperparameter of the CTC decoder. Word insertion bonus.
LM_BETA = 1.85

# These constants are tied to the shape of the graph used (changing them changes
# the geometry of the first layer), so make sure you use the same constants that
# were used during training

# Number of MFCC features to use
N_FEATURES = 26
# Size of the context window used for producing timesteps in the input vector
N_CONTEXT = 9

# Model Path
model_dir = 'gu_model'
model = model_dir + '/output_graph.pb'
alphabet = model_dir + '/alphabet.txt'
lm = model_dir + '/lm.binary'
trie = model_dir + '/trie'

ds = Model(model, N_FEATURES, N_CONTEXT, alphabet, BEAM_WIDTH)
ds.enableDecoderWithLM(alphabet, lm, trie, LM_ALPHA, LM_BETA)

end = time()
print("Saved Time: ", end-start)
while True:
    audio = input("Input file path: ")
    with wave.open(audio, 'rb') as fin:
        audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)
    print('Transcript: ', ds.stt(audio, 16000))