import numpy as np
import pandas as pd
from crossword.crossword import Crossword
from random import shuffle
from copy import copy
from random import random
from math import floor

class TreeNode:

    def __init__(self, words=None, unique_crossings=None,
                 cw=None, layer=None, parents=None, context=None):
        if words:

            # Creation of root of tree
            # Create pointer to layers
            self.layers = [[] for _ in range(len(words)+1)]
            self.layer = 0

            # Create context to be transmitted to all nodes from here
            self.context = {
                'words': words,
                'total_words': pd.concat(words),
                'unique_crossings': unique_crossings,
                'layers': self.layers,
                'best_area': [10000000000]*len(words),
                'best_crossword': [None]*len(words)
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

            self.parents = []
            self.n_visits = 2
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

        self.infinite_score = 100000000000
        self.value = 0
        self.defunct = False

        # Get itself added to layers dict
        self.context['layers'][self.layer].append(self)

        # Get an unique Name in this layer
        self.name = len(self.context['layers'][self.layer])

    def apoptosis(self, name=None, from_child=True):
        """
        Recursive elimination of own links, in order to be properly forgotten by both parents
        and children. :(
        :return:
        """

        if name:
            if from_child:

                # A child is dead. Let's find it
                for child_index, child in enumerate(self.children):
                    if child.name == name:
                        dead_child_index = child_index
                        break

                # Delete dead child from list
                del self.children[dead_child_index]

                # If there are no children left, then we'll recursively eliminate ourselves too
                if len(self.children) == 0:
                    self.defunct = True
                    for parent in self.parents:
                        parent.apoptosis(self.name, from_child=True)
                    self.parents = []

            else:
                # Then message comes from a parent, let's find it
                for parent_index, parent in enumerate(self.parents):
                    if parent.name == name:
                        dead_parent_index = parent_index
                        break

                # Delete dead parent from list
                del self.parents[dead_parent_index]

                # If there are no parents left, then we'll recursively eliminate ourselves too
                if len(self.parents) == 0:
                    self.defunct = True
                    for child in self.children:
                        child.apoptosis(self.name, from_child=False)
                    self.children = []
        else:
            # This is the node dying right now
            self.defunct = True

            if from_child:
                # Send message to parents and then forget them
                for parent in self.parents:
                    parent.apoptosis(self.name, from_child=True)

            else:
                # Send message to children and then forget them
                for child in self.children:
                    child.apoptosis(self.name, from_child=False)
            self.parents = []
            self.children = []

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

        # If I'm the root node, print results of this exhaustive search
        if self.layer == 0:
            layers = self.context['layers']
            for l, layer in enumerate(layers):
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

    def monte_carlo_iteration(self, ln_total_visits=None,
                              ubc1_constant=2,
                              n_visits_for_expansion=1):
        """
        Execute the 4 steps of a classical MCTS iteration
        :return:
        """

        # If this is the root node, derive total visits for nodes below
        if not ln_total_visits:
            ln_total_visits = np.log(self.n_visits)
            if len(self.children) == 0:
                print('No more children!!')

        # Selection
        # Traverse the tree until reaching a leaf node
        if not self.leaf:

            # Select best child node by UBC1 score
            best_child_score = 0
            best_child_index = -1
            for child_index, child in enumerate(self.children):
                child_score = child.get_ubc1_score(ln_total_visits, ubc1_constant)
                if child_score >= best_child_score:
                    best_child_score = child_score
                    best_child_index = child_index
            print('Selection, from node '+str(self.layer)+'-'+str(self.name)+' to '+
                  'node '+str(self.children[best_child_index].layer)+'-'+
                  str(self.children[best_child_index].name))
            # Continue iteration in best child node
            self.children[best_child_index].monte_carlo_iteration(ln_total_visits=ln_total_visits,
                                                                  ubc1_constant=ubc1_constant)

        else:
            print('Leaf node, n_visits: '+str(self.n_visits)+', defunct: '+str(self.defunct))
            # We are in a leaf node. Expand if it's time for that
            if self.n_visits == n_visits_for_expansion:
                print('Expansion')
                self.expand()

                # Then rollout from one of the children, if any
                if len(self.children) > 0:
                    random_son_index = floor(random()*len(self.children))
                    print('Rollout: random son name: '+str(self.layer) + '-' + str(self.children[random_son_index].name))
                    self.children[random_son_index].monte_carlo_iteration(ln_total_visits=ln_total_visits,
                                                                          ubc1_constant=ubc1_constant)
            else:
                print('Rollout: self')
                # Let's make a rollout from this node then
                self.rollout()

    def backpropagate_value(self, rollout_value):
        """
        Propagate value found rollout value to parent nodes
        :param rollout_value:
        :return:
        """

        # If parent is already dead then stop the backpropagation
        if self.defunct:
            return

        # Update self values
        self.value += rollout_value
        self.n_visits += 1

        # Propagate to all parent nodes
        for parent in self.parents:
            parent.backpropagate_value(rollout_value)

    def get_value_from_crossword(self, rollout_crossword):
        """
        Define value of a crossword, check if it's the best score so far, then return it
        :return:
        """
        value = 100/rollout_crossword.area
        self.register_crossword(rollout_crossword)

        return value

    def register_crossword(self, crossword):
        """
        Store crossword if it's the crossword with the lest area for its number of words
        :param crossword:
        :return:
        """

        n_words = len(crossword.word_indexes)
        if crossword.area < self.context['best_area'][n_words-1]:
            self.context['best_area'][n_words - 1] = crossword.area
            self.context['best_crossword'][n_words - 1] = crossword


    def get_ubc1_score(self, ln_total_visits, ubc1_constant):
        """
        UBC1 score
        :param ln_total_visits:
        :param ubc1_constant
        :return:
        """

        # If we haven't had visitors, then return a 'infinite' score
        if self.n_visits == 0:
            return self.infinite_score

        mean_value = self.value/self.n_visits
        return mean_value + ubc1_constant * np.sqrt(ln_total_visits/self.n_visits)

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

                # If child is already dead, ignore and continue
                if pre_existent_child.defunct:
                    continue

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

            # Register crossword just in case
            self.register_crossword(new_child_cw)

            # Put crossword on its own tree node
            new_child = TreeNode(cw=new_child_cw,
                                 layer=self.layer+1,
                                 parents=[self],
                                 context=self.context)

            # Assign node as a child
            self.children.append(new_child)

        # With child nodes, this is no longer a leaf node
        self.leaf = False

        # If the node didn't spawn children, then it shouldn't be longer visited
        if len(self.children) == 0:
            self.apoptosis()

    def rollout(self, n_tryouts=5):
        """
        Perform a rollout from current node
        :return:
        """

        # If there are no words left, backpropagate this value then eliminate itself
        if len(self.context['words']) == len(self.crossword.word_indexes):
            rollout_value = self.get_value_from_crossword(self.crossword)
            self.backpropagate_value(rollout_value)
            self.apoptosis()
            return

        words = self.context['words'][:]
        shuffle(words)

        # Crossword to simulate to completion
        crossword = copy(self.crossword)

        for tryout in range(n_tryouts):

            left_out_words = []

            for word in words:

                # If word is already in crossword, ignore and continue with the rest
                word_index = word.word_index.iloc[0]
                if word_index in crossword.word_indexes:
                    continue

                # Get possible new children from just one word
                possible_crossings = crossword.get_possible_crossings(word)

                # If there were no crossings, save current word as a left out
                # and continue with the rest
                if possible_crossings.shape[0] == 0:
                    left_out_words.append(word)
                    continue

                # Group crossings by similar possible insertions of words
                # Return possible crossings as a Groupby object
                grouped_crossings = possible_crossings.groupby(['new_word_start_x',
                                                                'new_word_start_y',
                                                                'new_word_horizontal',
                                                                ])

                # Iterate over possible crossings
                word_fit = False
                for new_word_coordinates, group in grouped_crossings:

                    # Check if crossing is legal
                    new_word_legal, inserted_new_word = crossword.is_crossing_legal(word, group,
                                                                                    new_word_coordinates[0],
                                                                                    new_word_coordinates[1],
                                                                                    new_word_coordinates[2])

                    # If the word didn't fit like this, we try with the next possible crossing
                    if not new_word_legal:
                        continue

                    # Create a new child from the parent and the new inserted word
                    crossword = crossword.spawn_child(inserted_new_word, group,
                                                      [-1], word_index)

                    # Register new crossword
                    self.register_crossword(crossword)

                    word_fit = True
                    break

                # If word didn't fit, save word as a left out and continue with the rest
                if not word_fit:
                    left_out_words.append(word)

            # If there were left out words, we make another try if we have tryouts left
            if len(left_out_words) > 0:
                if tryout < n_tryouts-1:
                    print('Retrying fit: ' + str(tryout))
                    words = left_out_words[:]
                    shuffle(words)
                else:
                    # If we don't have more tryouts, we lose no further time
                    # and simply kill the complicated node
                    print('Fit failed')
                    self.apoptosis()
                    return

        rollout_value = self.get_value_from_crossword(crossword)
        self.backpropagate_value(rollout_value)

