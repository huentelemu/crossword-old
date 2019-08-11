from crossword.MCTS import TreeNode

import pandas as pd
import numpy as np
from time import perf_counter


pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 200)

#original_words = sorted(['ABBBBB', 'ACCCCD', 'DEEEEE'])
#original_words = sorted(['MAMA', 'PAPA', 'ABUELA', 'PERRO'])
#original_words = sorted(['AMA', 'AMA', 'AMA', 'AMA'])
original_words = sorted(['DRAMA', 'DESOCUPAR', 'PENALIDAD', 'CARGO', 'INVADIR',
                        'PROFESION', 'LIBERAR', 'OCUPACION', 'ADUENARSE',
                        'COMUNICADO', 'APROPIARSE', 'INSTALARSE', 'QUEHACER',
                        'TRABAJO', 'DESHABITAR', 'INVASION', 'VIVIR', 'EMPLEO',
                        'DEDICARSE', 'FUNCION', 'HABITAR', 'TRAGEDIA',
                        'ASALTO', 'DOCUMENTO'])

# Words to DataFrames
words = []
for i, word in enumerate(original_words):
    word_df = pd.DataFrame()
    for j, letter in enumerate(word):
        row = pd.Series()
        row['letter'] = letter
        row['letter_index'] = j
        word_df = word_df.append(row, ignore_index=True)
    word_df['word_index'] = i
    word_df.letter_index = word_df.letter_index.astype(int)
    words += [word_df]
total_words = pd.concat(words)


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
tree_root = TreeNode(words=words, unique_crossings=unique_crossings)
#tree_root.expand_all()
for i in range(1):
    cw = tree_root.layers[1][0].rollout()
    cw.print_crossword()
    print('')
print('Total time: ' + str(perf_counter()-init_total))
