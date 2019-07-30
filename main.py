from crossword.test import Crossword

import pandas as pd
import numpy as np
from copy import copy


pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 200)

original_words = sorted(['MAMA', 'PAPA', 'ABUELA', 'PERRO'])

words = []
for i, word in enumerate(original_words):
    word_df = pd.DataFrame()
    for j, letter in enumerate(word):
        row = pd.Series()
        row['letter'] = letter
        row['letter_index'] = j
        word_df = word_df.append(row, ignore_index=True)
    word_df['word_index'] = i
    #word_df['word'] = word
    word_df.letter_index = word_df.letter_index.astype(int)
    words += [word_df]
#print(words)


# Unique id crossings stored in a dataframe
unique_crossings = pd.DataFrame()

for i in range(len(words)):
    for j in range(i+1, len(words)):
        cross = pd.merge(words[i], words[j], how='inner', on='letter',
                         suffixes=('_first', '_second'))
        unique_crossings = unique_crossings.append(cross)
unique_crossings['crossing_id'] = np.arange(unique_crossings.shape[0],
                                            dtype=int)

#print(unique_crossings)

crosswords = {0: []}
for word_index, word in enumerate(words):
    one_word_cw = word.copy()
    one_word_cw['horizontal'] = True
    one_word_cw['x'] = 0
    one_word_cw['y'] = np.arange(word.shape[0])
    cw = Crossword(one_word_cw, [word_index])
    crosswords[0] += [cw]

for layer in range(1, len(words)):
    # Initialize empty layer
    generation = []

    # Reproduce parents
    for parent_cw in crosswords[layer-1]:
        for word_index, word in enumerate(words):
            if word_index==0:continue
            child = parent_cw.spawn(word, word_index, unique_crossings,
                                    generation)
            #if child is None:
            #    continue
            break
        break
    break
    # Save the current generation
    crosswords[layer] = copy(generation)
