class Test:
    def __init__(self, value):
        self.value = value
        self.parents = []
        self.children = []

    def spawn(self):
        new_one = Test(self.value+1)
        new_one.parents += [self]
        self.children += [new_one]
        return new_one

    def print_parents_values(self):
        print('parents value: ')
        for parent in self.parents:
            print(parent.value)

    def print_children_values(self):
        print('children value: ')
        for child in self.children:
            print(child.value)

import pandas as pd
import numpy as np
from copy import copy

class Crossword:

    def __init__(self, current, word_indexes, crossing_ids=[]):
        self.current = current
        self.parents = []
        self.children = []
        self.word_indexes = word_indexes
        self.crossing_ids = crossing_ids

    #def check_legit_crossing(self, current):

    def is_child_already_in_gen(self, crossing_id, generation):
        child_id = self.crossing_ids + [crossing_id]
        for i, sibling in enumerate(generation):
            if len(sibling.crossing_ids) == len(child_id):
                if set(sibling.crossing_ids) == set(child_id):
                    return i
        return None

    def spawn(self, new_word, word_index, unique_crossings, generation):
        if word_index in self.word_indexes:
            return None

        # Prepare possible crossings
        possible_crossings = pd.merge(self.current, new_word, how='inner',
                                      on='letter', suffixes=('_current', '_new'))

        # Iterate over possible crossings
        print(new_word)
        print(possible_crossings)
        for i, crossing in possible_crossings.iterrows():

            # Identify crossing
            on = ['word_index_first', 'letter_index_first',
                       'word_index_second', 'letter_index_second']

            row_df = pd.Series()
            if crossing['word_index_current'] < crossing['word_index_new']:
                row_df['word_index_first'] = crossing['word_index_current']
                row_df['letter_index_first'] = crossing['letter_index_current']
                row_df['word_index_second'] = crossing['word_index_new']
                row_df['letter_index_second'] = crossing['letter_index_new']
            else:
                row_df['word_index_first'] = crossing['word_index_new']
                row_df['letter_index_first'] = crossing['letter_index_new']
                row_df['word_index_second'] = crossing['word_index_current']
                row_df['letter_index_second'] = crossing['letter_index_current']
            row_df = pd.DataFrame(row_df).T

            crossing_id = pd.merge(unique_crossings, row_df,
                                   how='inner', on=on)['crossing_id'].iloc[0]

            # Check if possible child crossing id is already in generation
            pre_existent_child = self.is_child_already_in_gen(crossing_id,
                                                              generation)
            if pre_existent_child:
                # If so, add child to this node children,
                self.children += [pre_existent_child]
                # And add this node as a parent for the children node
                pre_existent_child.parents += [self]
                continue

            # Create new word
            len_word = new_word.shape[0]
            nw = new_word.copy()
            if crossing.horizontal:
                fix_axis = 'x'
                along_axis = 'y'
                nw['horizontal'] = False
            else:
                fix_axis = 'y'
                along_axis = 'x'
                nw['horizontal'] = True
            nw[fix_axis] = crossing[fix_axis]
            start_word = crossing[along_axis] - crossing.letter_index_new
            nw[along_axis] = np.arange(start_word, start_word+len_word)
            print(nw)

            # Check if crossing is legit
            #new_cw =


            break


