#!/usr/bin/python
from __future__ import division, print_function
import codecs
import json
import os
import sys


COLORS_FILES = ['resources/color_split1.txt', 'resources/color_split2.txt']


if __name__ == '__main__':
    src, dest = sys.argv[1], sys.argv[2]

    master_colors = {}
    for cf in COLORS_FILES:
        with open(os.path.normpath(cf), 'r') as f:
            raw = f.readlines()

        for line in raw:
            name, hexcode = line.split(',')
            master_colors[name.strip()] = hexcode.strip()

    print('Read master colors.')

    with open(src, 'r') as f:
        data = json.load(f)

    print('Loaded data.')

    # { img_index: [{colour_name: code},...]}
    procd_data = {}

    for annot_obj in data:

        color_names = []
        colors = []

        #print(annot_obj['type'], annot_obj['models'][0].keys())

        if 'line' in annot_obj['type']:
            color_names = [model_obj['name'] for model_obj in annot_obj['models']]
            colors = [model_obj['color'] for model_obj in annot_obj['models']]

        elif 'bar_categorical' in annot_obj['type']:
            color_names = annot_obj['models'][0]['labels']
            colors = annot_obj['models'][0]['colors']

        elif 'pie' in annot_obj['type']:
            # Bug: colors field not present in pie annotations anymore
            color_names = [model_obj['name'] for model_obj in annot_obj['models']]
            colors = [master_colors[k] for k in color_names]

        else:
            continue

        #color_names = list(set(color_names))
        #{ k: master_colors[k] for k in color_names}

        procd_data[str(annot_obj['image_index'])] = { k: v for k, v in zip(color_names, colors)}

    with open(dest, 'w') as f:
        json.dump(procd_data, f)
