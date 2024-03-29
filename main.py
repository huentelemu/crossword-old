from crossword.MCTS import TreeNode
from crossword.crossword import Crossword
from crossword.waton import Waton

import pandas as pd
import numpy as np
from time import perf_counter


pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 200)

# Initialize IO object
IO = Waton()

# Erase previous results
IO.erase_previous_results()

# Iterate over groups of words
group_index = 1
for original_words in IO.grouped_original_words:

    init_time_group = perf_counter()
    allowed_time_per_level = 60 * IO.pars['minutos_por_cruzada'] / len(original_words)

    words = IO.list2df(original_words)

    unique_crossings = Crossword.get_unique_crossings(words)

    init_total = perf_counter()
    tree_root = TreeNode(words=words, unique_crossings=unique_crossings)

    #tree_root.expand_all()
    #sys.exit(0)

    for i in range(len(words)):
        while True:
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

            # If we are exceeding allowed time, stop iterations
            time = perf_counter()
            if perf_counter() - init_time_group > allowed_time_per_level * (i+1):
                print("Time's up")
                break

        if len(tree_root.children) == 0:
            break

        # Choose a child from the root as the new root
        best_child_index = 0
        most_visits = tree_root.children[best_child_index].n_visits
        for child_index, child in enumerate(tree_root.children):
            if child.n_visits > most_visits:
                best_child_index = child_index
                most_visits = child.n_visits

        # Prune the rest of the children
        for child_index, child in enumerate(tree_root.children):
            if child_index == best_child_index:
                continue
            child.apoptosis(from_child=False)

        # Make the children the new root
        tree_root.defunct = True
        tree_root = tree_root.children[best_child_index]
        tree_root.parents = []

        live_nodes = [0] * len(tree_root.context['layers'])
        for layer_index, layer in enumerate(tree_root.context['layers']):
            for node in layer:
                if not node.defunct:
                    live_nodes[layer_index] += 1

        print('')
        print('******************')
        print('New root')
        print('Live nodes: ' + str(live_nodes))
        print('******************')
        print('')


    print('Total time: ' + str(perf_counter()-init_total))
    print('Best crosswords: ')
    for cw in tree_root.context['best_crossword']:
        if cw:
            cw.print_crossword()

    new_dir = 'resultados/Grupo ' + str(group_index).zfill(3)
    IO.draw_images(tree_root.context, original_words, files_dir=new_dir)

    group_index += 1

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