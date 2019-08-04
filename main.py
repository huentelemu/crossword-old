from crossword.test import Crossword

import pandas as pd
import numpy as np
from copy import copy
from time import perf_counter


pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 200)

original_words = sorted(['MAMA', 'PAPA', 'ABUELA', 'PERRO'])
#original_words = sorted(['AMA','AMA','AMA'])
#original_words = ['DRAMA',
#         'DESOCUPAR',
#         'PENALIDAD',
#         'CARGO',
#         'INVADIR',
#         'PROFESION',
#         'LIBERAR',
#         'OCUPACION',
#         'ADUENARSE',
#         'COMUNICADO',
#         'APROPIARSE',
#         'INSTALARSE',
#         'QUEHACER',
#         'TRABAJO',
#         'DESHABITAR',
#         'INVASION',
#         'VIVIR',
#         'EMPLEO',
#         'DEDICARSE',
#         'FUNCION',
#         'HABITAR',
#         'TRAGEDIA',
#         'ASALTO',
#         'DOCUMENTO',
#         ]

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

print(unique_crossings)
init_total = perf_counter()

# Create set of first crosswords with only one word each
crosswords = {0: []}
for word_index, word in enumerate(words):
    one_word_cw = word.copy()
    one_word_cw['horizontal'] = True
    one_word_cw['x'] = np.arange(word.shape[0])
    one_word_cw['y'] = 0
    cw = Crossword(one_word_cw, [word_index])
    crosswords[0] += [cw]

print('')
print('Layer: 0')
print('Number of crosswords in generation: '+str(len(crosswords[0])))

# Create sets of crosswords with consecutively more words in them
for layer in range(1, len(words)):
    init = perf_counter()
    # Initialize empty layer
    generation = []

    # Reproduce parents
    for parent_cw in crosswords[layer-1]:
        for word_index, word in enumerate(words):
            children = parent_cw.spawn(word, word_index,
                                       unique_crossings,
                                       generation)
            if children is None:
                continue

            generation += children

    # Save the current generation
    crosswords[layer] = copy(generation)
    print('')
    print('Layer: ' + str(layer))
    print('Number of crosswords in generation: ' + str(len(generation)))
    print('Time: '+str(perf_counter()-init))

print('')
print('Total time: '+str(perf_counter()-init_total))