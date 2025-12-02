#!/usr/bin/python
from __future__ import division, print_function
import codecs
import os
import shutil

if __name__ == '__main__':

    folder = 'testfiles'

    if os.path.exists(folder):
        shutil.rmtree(folder)

    os.mkdir(folder)

    with codecs.open('template_test1.csv', 'r', 'utf-8') as f:
        inlines = f.readlines()

    filtered_lines = [inlines[0]]

    for line in inlines[1:]:
        filtered_lines.append(line.replace('<0/1>', '0'))

    testfile_combos = [('sample_answers_%s_%s.csv' % (le, enc), le, enc) \
                        for le in ['unix', 'win'] \
                        for enc in ['ascii', 'utf-8']]

    for filename, le, enc in testfile_combos:

        ending = '\r\n' if le == 'win' else '\n'

        print('Writing', filename)

        with codecs.open(os.path.join(folder, filename), 'w', encoding=enc) as fp:
            for line in filtered_lines:
                fp.write(line.strip() + ending)
        