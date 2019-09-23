import pandas as pd
import numpy as np
import os
import shutil
from glob import glob
from numpy.random import choice
from PIL import Image, ImageDraw, ImageFont

class Waton:

    def __init__(self):

        self.example_lists = [
            sorted(['ABBBBB', 'ACCCCD', 'DEEEEE']),
            sorted(['MAMA', 'PAPA', 'ABUELA', 'PERRO']),
            sorted(['AMA', 'AMA', 'AMA', 'AMA']),
            sorted(['AMAMA', 'AMAMA', 'AMAMA', 'AMAMA', 'AMAMA', 'AMAMA']),
            sorted(['DRAMA', 'DESOCUPAR', 'PENALIDAD', 'CARGO', 'INVADIR',
                 'PROFESION', 'LIBERAR', 'OCUPACION', 'ADUENARSE',
                 'COMUNICADO', 'APROPIARSE', 'INSTALARSE', 'QUEHACER',
                 'VIVIR', 'EMPLEO', 'DEDICARSE', 'FUNCION', 'HABITAR',
                 'TRAGEDIA', 'ASALTO', 'DOCUMENTO'
                 ])
        ]

        self.original_words = sorted(self.example_lists[1])

        self.words = self.list2df(self.original_words)

        # Erase results from Resultados directory
        filelist = glob('resultados/*')
        for f in filelist:
            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.remove(f)

    def list2df(self, original_words):

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
        return words

    @staticmethod
    def draw_images(context, original_words, files_dir='resultados'):

        crosswords = context['best_crossword']
        square_side = 90
        margin_offset = 10
        widen_rectangle = 2

        n_versions = 5
        n_initial_words = 3

        for ind, crossword in enumerate(crosswords):
            if not crossword:
                continue
            n_words = ind + 1
            shift_cw = crossword.current.copy()
            shift_cw['x'] -= shift_cw['x'].min()
            shift_cw['y'] -= shift_cw['y'].min()
            matrix_cw = np.zeros((n_versions+1, shift_cw.y.max() + 1, shift_cw.x.max() + 1), dtype=str)
            matrix_cw[0, :] = '-'
            matrix_cw[1:, :] = '?'
            initial_word_indexes = []
            for a in range(n_versions):
                if len(crossword.word_indexes) <= n_initial_words:
                    initial_word_indexes.append(crossword.word_indexes)
                else:
                    initial_word_indexes.append(choice(crossword.word_indexes, n_initial_words, replace=False))
            for i, row in shift_cw.iterrows():
                matrix_cw[0, row.y, row.x] = row.letter
                # Fill incomplete versions
                for a in range(n_versions):
                    if row.word_index in initial_word_indexes[a]:
                        matrix_cw[a + 1, row.y, row.x] = row.letter

            images = []
            drawers = []
            for i in range(n_versions+1):
                images += [
                    Image.new('RGBA', tuple(np.array(matrix_cw.shape[1:])[[1, 0]] * square_side + margin_offset * 2),
                              color=(200, 200, 200, 0))]
                drawers += [ImageDraw.Draw(images[i])]
            font = ImageFont.truetype("arial.ttf", 60)

            for (i, j), c in np.ndenumerate(matrix_cw[0, :]):
                if c == '-':
                    continue

                # Prepare squares
                rect_y = margin_offset + j * square_side
                rect_x = margin_offset + i * square_side
                for d in drawers:
                    # Draw squares
                    for w in range(-widen_rectangle, widen_rectangle + 1):
                        d.rectangle(((rect_y + w, rect_x + w), (rect_y + square_side - w, rect_x + square_side - w)),
                                    outline="black")

                    # Make squares interior not transparent but white
                    gris = 255
                    d.rectangle(((rect_y + widen_rectangle + 1, rect_x + widen_rectangle + 1),
                                 (rect_y + square_side - widen_rectangle - 1,
                                  rect_x + square_side - widen_rectangle - 1)),
                                fill=(gris, gris, gris))

                # Draw letter
                text_w, text_h = d.textsize(c, font)
                char_h_offset = int((square_side - text_w) / 2 * 1.05)
                char_w_offset = int((square_side - text_h) / 2 * 0.6)
                drawers[0].text(
                    (j * square_side + char_h_offset + margin_offset,
                     i * square_side + char_w_offset + margin_offset), c,
                    fill=(0, 0, 0), font=font)
                for a in range(1, n_versions+1):
                    if matrix_cw[a, i, j] != '?':
                        drawers[a].text((j * square_side + char_h_offset + margin_offset,
                                         i * square_side + char_w_offset + margin_offset), c, fill=(0, 0, 0),
                                        font=font)

            images[0].save(files_dir+'/' + str(n_words).zfill(2) + ' Palabras.png', 'png')

            new_folder = files_dir + '/' + str(n_words).zfill(2) + ' Palabras'
            os.mkdir(new_folder)

            # Draw Solution
            images[0].save(new_folder + '/Solucion.png', 'png')

            # Draw the different versions
            for a in range(1, n_versions + 1):
                images[a].save(new_folder + '/Cruzada' + str(a) + '.png', 'png')

            # Write words file
            with open(new_folder + '/Palabras.txt', "w", encoding="ISO-8859-1") as writer:
                ordered_word_indexes = sorted(crossword.word_indexes)
                for word_index in ordered_word_indexes:
                    writer.write(original_words[word_index] + '\n')

    @staticmethod
    def draw_images_old(crosswords, coords_word, group):

        square_side = 90
        margin_offset = 10
        widen_rectangle = 2

        n_versions = len(crosswords) - 1

        images = []
        drawers = []
        for i in range(n_versions + 1):
            images += [Image.new('RGBA', tuple(np.array(crosswords[0].shape)[[1, 0]] * square_side + margin_offset * 2),
                                 color=(200, 200, 200, 0))]
            drawers += [ImageDraw.Draw(images[i])]
        font = ImageFont.truetype("arial.ttf", 60)

        for (i, j), c in np.ndenumerate(crosswords[0]):
            if c == '-':
                continue

            # Prepare squares
            rect_y = margin_offset + j * square_side
            rect_x = margin_offset + i * square_side
            for d in drawers:
                # Draw squares
                for w in range(-widen_rectangle, widen_rectangle + 1):
                    d.rectangle(((rect_y + w, rect_x + w), (rect_y + square_side - w, rect_x + square_side - w)),
                                outline="black")

                # Make squares interior not transparent but white
                gris = 255
                d.rectangle(((rect_y + widen_rectangle + 1, rect_x + widen_rectangle + 1),
                             (rect_y + square_side - widen_rectangle - 1, rect_x + square_side - widen_rectangle - 1)),
                            fill=(gris, gris, gris))

            # Draw letter
            text_w, text_h = d.textsize(c, font)
            char_h_offset = int((square_side - text_w) / 2 * 1.05)
            char_w_offset = int((square_side - text_h) / 2 * 0.6)
            drawers[0].text(
                (j * square_side + char_h_offset + margin_offset, i * square_side + char_w_offset + margin_offset), c,
                fill=(0, 0, 0), font=font)
            for a in range(1, len(crosswords)):
                if crosswords[a][i, j] != '?':
                    drawers[a].text((j * square_side + char_h_offset + margin_offset,
                                     i * square_side + char_w_offset + margin_offset), c, fill=(0, 0, 0), font=font)

        images[0].save('Resultados/' + str(group).zfill(3) + '-Solucion.png', 'png')
        for a in range(n_versions):
            images[a + 1].save('Resultados/' + str(group).zfill(3) + '-Cruzada' + str(a + 1) + '.png', 'png')

        coords_word = coords_word.sort_values('word')
        with open('Resultados/' + str(group).zfill(3) + '-Palabras.txt', "w", encoding="ISO-8859-1") as writer:
            for _, row in coords_word.iterrows():
                writer.write(row.word_original + '\n')
