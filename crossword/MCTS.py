import numpy as np
from crossword.crossword import Crossword

class TreeNode:

    def __init__(self, cw=None, words=None, layer=None, parents=None):
        if not cw:

            ## Creation of root of tree

            # Create pointer to layers and put myself on the first layer
            self.layers = [[] for _ in range(len(words)+1)]
            self.layers[0].append(self)
            self.my_layer = 0

            # Automatically expand to crosswords with one word
            self.children = []
            for word_index, word in enumerate(words):
                mono_crossword = Crossword(word, [word_index])
                node = TreeNode(cw=mono_crossword,
                                layer=1,
                                parents=self.layers[0])
                self.children.append(node)

            self.layers[1] = self.children

        else:

            # Create standard node
            self.crossword = cw
            self.my_layer = layer
            self.parents = parents
            self.children = []
