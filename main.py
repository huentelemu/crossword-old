from crossword.MCTS import TreeNode

import pandas as pd
import numpy as np
from time import perf_counter


pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 200)

#original_words = sorted(['ABBBBB', 'ACCCCD', 'DEEEEE'])
original_words = sorted(['MAMA', 'PAPA', 'ABUELA', 'PERRO'])
#original_words = sorted(['AMA', 'AMA', 'AMA', 'AMA'])
#original_words = sorted(['AMAMA', 'AMAMA', 'AMAMA', 'AMAMA', 'AMAMA', 'AMAMA'])
#original_words = sorted(['DRAMA', 'DESOCUPAR', 'PENALIDAD', 'CARGO', 'INVADIR',
#                        'PROFESION', 'LIBERAR', 'OCUPACION', 'ADUENARSE',
#                        'COMUNICADO', 'APROPIARSE', 'INSTALARSE', 'QUEHACER',
#                        'TRABAJO', 'DESHABITAR', 'INVASION',
#                       'VIVIR', 'EMPLEO', 'DEDICARSE', 'FUNCION', 'HABITAR', 'TRAGEDIA',
#                        'ASALTO', 'DOCUMENTO',
#                        ])

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
#sys.exit(0)
for i in range(400):
    init = perf_counter()
    if len(tree_root.children) == 0:
        print('Tree explored completely')
        break
    tree_root.monte_carlo_iteration(ubc1_constant=0.1)
    print('Time: ' + str(perf_counter()-init))
    print('n_visits: ' + str(tree_root.n_visits))
    print('Layers:     ' + str([len(layer) for layer in tree_root.context['layers']]))
    live_nodes = [0] * len(tree_root.context['layers'])
    for layer_index, layer in enumerate(tree_root.context['layers']):
        for node in layer:
            if not node.defunct:
                live_nodes[layer_index] += 1
    print('Live nodes: '+str(live_nodes))
    #print(tree_root.value)
    print('')

print('Total time: ' + str(perf_counter()-init_total))
print('Best crossword: ')
tree_root.context['best_crossword'].print_crossword()

#for layer in tree_root.context['layers']:
#    for node in layer:
#        print(node.name)

# Count dead nodes
'''
for layer_index, layer in enumerate(tree_root.context['layers']):
    live_nodes = 0
    for node in layer:
        if not node.defunct:
            live_nodes += 1
            if layer_index>0:
                node.crossword.print_crossword()
                print('')
    print('Layer: '+str(layer_index)+', live nodes: '+str(live_nodes))
'''