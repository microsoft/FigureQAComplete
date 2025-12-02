#!/usr/bin/python
from __future__ import division, print_function
import json
import os

# run in evaluation directory
if __name__ == "__main__":

    ##############################################
    # NOTE! DOESN'T WORK FOR `human`!
    ##############################################

    files = [
        (os.path.normpath('../dataset/v1.0.1/testset_with_answers/test1/annotations.json'), 'figure_types_test1.json'),
        (os.path.normpath('../dataset/v1.0.1/testset_with_answers/test2/annotations.json'), 'figure_types_test2.json')
        # (os.path.normpath('../dataset/v1.0.1/validation1/annotations.json'), 'figure_types_validation1.json'),
        # (os.path.normpath('../dataset/v1.0.1/validation2/annotations.json'), 'figure_types_validation2.json')
    ]

    for src_fp, dest_fp in files:

        with open(src_fp, 'r') as f:
            annots = json.load(f)

        types = []

        print('Read', src_fp)

        for annot in annots:
            types.append({'image_index': annot['image_index'], 'type': annot['type']})

        with open(dest_fp, 'w') as f:
            json.dump(types, f)

        print('Done', dest_fp)
