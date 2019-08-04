import pandas as pd
import numpy as np


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


class Crossword:

    def __init__(self, current, word_indexes, crossing_ids=[]):
        self.current = current
        self.parents = []
        self.children = []
        self.word_indexes = word_indexes
        self.crossing_ids = crossing_ids
        self.left_on = ['word_index_first', 'letter_index_first',
                        'word_index_second', 'letter_index_second']
        self.right_on = ['word_index_current', 'letter_index_current',
                         'word_index_new', 'letter_index_new']
        self.right_on_inverse = ['word_index_new', 'letter_index_new',
                                 'word_index_current', 'letter_index_current']
    #def check_legit_crossing(self, current):

    def is_child_already_in_gen(self, crossing_id, generation):
        child_id = self.crossing_ids + crossing_id
        for i, sibling in enumerate(generation):
            if len(sibling.crossing_ids) == len(child_id):
                if set(sibling.crossing_ids) == set(child_id):
                    return generation[i]
        return None

    def spawn(self, new_word, word_index, unique_crossings, generation):
        if word_index in self.word_indexes:
            return None

        new_children = []
        # Prepare possible crossings
        possible_crossings = pd.merge(self.current, new_word, how='inner',
                                      on='letter', suffixes=('_current', '_new'))

        # Figure out start coordinates of the new word in each crossing
        possible_crossings['new_word_start_x'] = 0
        possible_crossings['new_word_start_y'] = 0
        possible_crossings['new_word_horizontal'] = 0
        for i, crossing in possible_crossings.iterrows():
            if crossing.horizontal:
                possible_crossings.loc[i, 'new_word_horizontal'] = False
                possible_crossings.loc[i, 'new_word_start_x'] = crossing.x
                possible_crossings.loc[i, 'new_word_start_y'] = crossing.y - crossing.letter_index_new
            else:
                possible_crossings.loc[i, 'new_word_horizontal'] = True
                possible_crossings.loc[i, 'new_word_start_x'] = crossing.x - crossing.letter_index_new
                possible_crossings.loc[i, 'new_word_start_y'] = crossing.y

        # Iterate over each possible position of the new word
        grouped_crossings = possible_crossings.groupby(['new_word_start_x',
                                                        'new_word_start_y',
                                                        'new_word_horizontal'])
        for nw_coords, group in grouped_crossings:

            # Identify the ID/s of this specific crossing
            if group.word_index_current.iloc[0] < group.word_index_new.iloc[0]:
                crossing_df = pd.merge(unique_crossings, group, how='inner',
                                        left_on=self.left_on,
                                        right_on=self.right_on)
            else:
                crossing_df = pd.merge(unique_crossings, group, how='inner',
                                        left_on=self.left_on,
                                        right_on=self.right_on_inverse)

            # Check if possible child crossing id is already in generation
            crossing_ids = crossing_df['crossing_id'].tolist()
            pre_existent_child = self.is_child_already_in_gen(crossing_ids,
                                                              generation)
            if pre_existent_child:
                # If so, add child to this node children,
                self.children += [pre_existent_child]
                # And add this node as a parent for the children node
                pre_existent_child.parents += [self]
                continue

            # This is a new position to explore then, let's create a new word
            inserted_new_word = new_word.copy()
            start = {'x': nw_coords[0], 'y': nw_coords[1]}
            horizontal = nw_coords[2]
            fix_axis = ['x', 'y'][horizontal]
            along_axis = ['x', 'y'][not horizontal]
            len_word = new_word.shape[0]
            inserted_new_word[fix_axis] = start[fix_axis]
            inserted_new_word[along_axis] = np.arange(start[along_axis],
                                                      start[along_axis]+len_word)
            inserted_new_word['horizontal'] = horizontal

            # Create area that should not merge with any element of the current crossword
            fa = start[fix_axis]
            aa = start[along_axis]
            # Forbid start tip
            forbidden_area_dict = [{fix_axis: fa, along_axis: aa-1}]
            # Forbid borders along the new word
            for i, coord in enumerate(inserted_new_word[along_axis]):
                # Except in places where we cross with the current crossword
                if coord in crossing_df[along_axis].tolist():
                    continue
                forbidden_area_dict += [{fix_axis: fa-1, along_axis: coord},
                                        {fix_axis: fa, along_axis: coord},
                                        {fix_axis: fa+1, along_axis: coord}]
            # Forbid end tip
            forbidden_area_dict += [{fix_axis: fa, along_axis: aa+len_word}]

            # Merge forbidden area to current crossword to check if word fits
            forbidden_area = pd.DataFrame(forbidden_area_dict)
            n_forbidden_contacts = pd.merge(self.current, forbidden_area).shape[0]

            if n_forbidden_contacts > 0:
                # Word doesn't fit like this, so we just continue with the next position
                continue

            # We are ready to spawn a new child crossword with the new word
            new_crossword = self.current.copy()
            new_crossword = new_crossword.append(inserted_new_word, sort=False)

            # Erase the letters involved in the current crossing
            crossing_letters = np.logical_and(new_crossword.x.isin(crossing_df.x),
                                              new_crossword.y.isin(crossing_df.y))
            new_crossword = new_crossword.loc[~crossing_letters]

            # Create child
            child_id = self.crossing_ids + crossing_ids
            child_word_indexes = self.word_indexes + [word_index]
            new_child = Crossword(new_crossword, child_word_indexes, child_id)

            # Assign family to child
            self.children += [new_child]
            new_child.parents += [self]

            new_children += [new_child]

        return new_children