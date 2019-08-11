from crossword.crossword import Crossword
from crossword.MCTS import TreeNode

import pandas as pd
import numpy as np
from copy import copy
from time import perf_counter
import matplotlib.pyplot as plt


pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 200)

#original_words = sorted(['ABBBBB', 'ACCCCD', 'DEEEEE'])
original_words = sorted(['MAMA', 'PAPA', 'ABUELA', 'PERRO', 'GATO'])
#original_words = sorted(['AMA', 'AMA', 'AMA', 'AMA'])
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

# Create set of first crosswords with only one word each
crosswords = {0: []}
for word_index, word in enumerate(words):
    one_word_cw = word.copy()
    one_word_cw['horizontal'] = True
    one_word_cw['x'] = np.arange(word.shape[0])
    one_word_cw['y'] = 0
    one_word_cw['available_for_crossing'] = True
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
    for parent_cw in crosswords[layer - 1]:

        # Get possible new children from parent
        possible_crossings = parent_cw.get_possible_crossings(total_words)

        # Group crossings by similar possible insertions of words
        # Return possible crossings as a Groupby object
        grouped_crossings = possible_crossings.groupby(['new_word_start_x',
                                                        'new_word_start_y',
                                                        'new_word_horizontal',
                                                        'word_index_new'])

        # Iterate over possible children
        for new_word_coordinates, group in grouped_crossings:

            # Get Ids of specific crossing
            child_id, crossing_df = parent_cw.identify_crossing(group, unique_crossings)

            # Check if Id match with an already existent child
            pre_existent_child = None
            for sibling_index, sibling in enumerate(generation):
                if len(sibling.crossing_ids) == len(child_id):
                    if sibling.crossing_ids == child_id:

                        # The child already exists
                        pre_existent_child = generation[sibling_index]
                        break

            if pre_existent_child:

                # If child already exists, add it as one of the parent's children
                parent_cw.children += [pre_existent_child]

                # And add the parent as one of the parents of the children node
                pre_existent_child.parents += [parent_cw]

                # Continue with next possible crossing
                continue

            # Check if crossing is legal
            new_word_start_x = new_word_coordinates[0]
            new_word_start_y = new_word_coordinates[1]
            new_word_horizontal = new_word_coordinates[2]
            word_index = new_word_coordinates[3]
            new_word = words[word_index]
            new_word_legal, inserted_new_word = parent_cw.is_crossing_legal(new_word, crossing_df,
                                                                            new_word_start_x,
                                                                            new_word_start_y,
                                                                            new_word_horizontal)

            # If the word didn't fit, we just ignore and continue with the next crossing
            if not new_word_legal:
                continue

            # Create a new child from the parent and the new inserted word
            new_child = parent_cw.spawn_child(inserted_new_word, crossing_df,
                                              child_id, word_index)

            # Assign family to child
            parent_cw.children += [new_child]
            new_child.parents += [parent_cw]

            # Add child to current generation
            generation += [new_child]



    '''
    # Reproduce parents
    for parent_cw in crosswords[layer-1]:
        for word_index, word in enumerate(words):
            children = parent_cw.spawn(word, word_index,
                                       unique_crossings,
                                       generation)
            if children is None:
                continue

            generation += children'''


    # Save the current generation
    crosswords[layer] = copy(generation)
    print('')
    print('Layer: ' + str(layer))
    print('Number of crosswords in generation: ' + str(len(generation)))
    print('Time: '+str(perf_counter()-init))

print('')
print('Total time: '+str(perf_counter()-init_total))

minimum_area = 100000000
minimum_area_index = -1
for i, cw in enumerate(crosswords[len(original_words)-1]):
    if cw.area < minimum_area:
        minimum_area_index = i
        minimum_area = cw.area
    #print(i)
    #print(cw.crossing_ids)
    #cw.print_crossword()
    #print(cw.area)
    #print('')

best_cw = crosswords[len(original_words)-1][minimum_area_index]
print('Best crossword:')
print(minimum_area_index)
print(best_cw.crossing_ids)
best_cw.print_crossword()
print(best_cw.area)

# Test with MCTS
print('*** Test with MCTS ***')
print('')

init = perf_counter()
tree_root = TreeNode(words=words, unique_crossings=unique_crossings)
tree_root.expand_all()
print('Total time: ' + str(perf_counter()-init))

layers = tree_root.context['layers']
for l, layer in enumerate(layers):
    print('')
    print('Layer: ' + str(l))
    print('Number of crosswords in generation: ' + str(len(layer)))
    print('')

minimum_area = 100000000
minimum_area_index = -1
for i, node in enumerate(layers[-1]):
    if node.crossword.area < minimum_area:
        minimum_area_index = i
        minimum_area = node.crossword.area

best_cw = layers[-1][minimum_area_index].crossword
print('Best crossword:')
print(minimum_area_index)
print(best_cw.crossing_ids)
best_cw.print_crossword()
print(best_cw.area)

