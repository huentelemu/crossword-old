import numpy as np
import pandas as pd
from crossword.crossword import Crossword

class TreeNode:

    def __init__(self, words=None, unique_crossings=None,
                 cw=None, layer=None, parents=None, context=None):
        if words:

            ## Creation of root of tree

            # Create pointer to layers and put myself on the first layer
            self.layers = [[] for _ in range(len(words)+1)]
            self.layers[0].append(self)
            self.layer = 0

            # Create context to be transmitted to all nodes from here
            self.context = {
                'words': words,
                'total_words': pd.concat(words),
                'unique_crossings': unique_crossings,
                'layers': self.layers
            }

            # Automatically expand to crosswords with one word
            self.children = []
            for word_index, word in enumerate(words):
                mono_crossword = Crossword(word, [word_index])
                node = TreeNode(cw=mono_crossword,
                                layer=1,
                                parents=self.layers[0],
                                context=self.context)
                self.children.append(node)

            self.layers[1] = self.children
            self.n_visits = 1
            self.leaf = False

        else:

            # Create standard node
            self.crossword = cw
            self.layer = layer
            self.parents = parents
            self.context = context

            self.children = []
            self.n_visits = 0
            self.leaf = True

    def expand_all(self):
        """
        Recursively find and expand all nodes.
        :return: None
        """

        # If this is a leaf node, we expand it
        if self.leaf:
            self.expand()

        # Then we proceed to expand the children
        for child in self.children:
            child.expand_all()

    def expand(self):
        """
        Get all possible sons from current crossword
        :return:
        """

        # Get possible new children from parent
        possible_crossings = self.crossword.get_possible_crossings(self.context['total_words'])

        # Group crossings by similar possible insertions of words
        # Return possible crossings as a Groupby object
        grouped_crossings = possible_crossings.groupby(['new_word_start_x',
                                                        'new_word_start_y',
                                                        'new_word_horizontal',
                                                        'word_index_new'])

        # Iterate over possible children
        for new_word_coordinates, group in grouped_crossings:
            # Get Ids of specific crossing
            child_id, crossing_df = self.crossword.identify_crossing(group,
                                                                     self.context['unique_crossings'])

            # Check if Id match with an already existent child
            children_generation = self.context['layers'][self.layer+1]
            pre_existent_child = None
            for sibling_index, sibling in enumerate(children_generation):
                if len(sibling.crossword.crossing_ids) == len(child_id):
                    if sibling.crossword.crossing_ids == child_id:
                        # The child already exists
                        pre_existent_child = children_generation[sibling_index]
                        break

            if pre_existent_child:
                # If child already exists, add it as one of the parent's children
                self.children += [pre_existent_child]

                # And add itself as one of the parents of the children node
                pre_existent_child.parents.append(self)

                # Continue with next possible crossing
                continue

            # Check if crossing is legal
            new_word_start_x = new_word_coordinates[0]
            new_word_start_y = new_word_coordinates[1]
            new_word_horizontal = new_word_coordinates[2]
            word_index = new_word_coordinates[3]
            new_word = self.context['total_words'].loc[self.context['total_words']
                                                           .word_index == word_index, :].copy()
            new_word_legal, inserted_new_word = self.crossword.is_crossing_legal(new_word, crossing_df,
                                                                                 new_word_start_x,
                                                                                 new_word_start_y,
                                                                                 new_word_horizontal)

            # If the word didn't fit, we just ignore and continue with the next crossing
            if not new_word_legal:
                continue

            # Create a new child from the parent and the new inserted word
            new_child_cw = self.crossword.spawn_child(inserted_new_word, crossing_df,
                                                      child_id, word_index)

            # Put crossword on its own tree node
            new_child = TreeNode(cw=new_child_cw,
                                 layer=self.layer+1,
                                 parents=[self],
                                 context=self.context)

            # Assign node as a child
            self.children.append(new_child)

            # Put the child in the layers pointer
            self.context['layers'][self.layer+1].append(new_child)

        # With child nodes, this is no longer a leaf node
        self.leaf = False
