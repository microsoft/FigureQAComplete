#!/usr/bin/python
from __future__ import print_function, division
import json
import os
import pandas as pd
import shutil
import sys

if __name__ == '__main__':

    parsed_file = sys.argv[1]
    src_images_path = sys.argv[2]
    src_annotations_path = sys.argv[3]

    dest_dir = 'test2_human_subset'

    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)

    os.mkdir(dest_dir)

    print('Reading parsed QA data...')

    parsed = pd.read_csv(parsed_file, delimiter='\t')

    qa_fields = [
        'answer',
        'color1_id',
        'color1_name',
        'color1_rgb',
        'color2_id',
        'color2_name',
        'color2_rgb',
        'image_index',
        'question_id',
        'question_string'
    ]

    qa_data = {'total_distinct_questions': 15, 'total_distinct_colors': 100, 'qa_pairs': []}
    img_count = 0
    ix_map = {}

    dest_images_path = os.path.join(dest_dir, 'png')
    os.mkdir(dest_images_path)

    print('Munging parsed QA data and copying image files...')

    for _, row in parsed.iterrows():
        datum = {k: row[k] for k in qa_fields}

        if row['image_index'] not in ix_map:
            ix_map[row['image_index']] = img_count
            img_count += 1

        datum['image_index'] = ix_map[row['image_index']]
        qa_data['qa_pairs'].append(datum)

        # Copy the image over
        shutil.copy(os.path.join(src_images_path, '%d.png' % row['image_index'] ), 
                    os.path.join(dest_images_path, '%d.png' % datum['image_index']))

    with open(os.path.join(dest_dir, 'qa_pairs.json'), 'w') as f:
        json.dump(qa_data, f)

    # Copy images and annotations
    print('Loading source annotations...')
    with open(src_annotations_path, 'r') as f:
        src_annotations = json.load(f)
        print('Done loading source annotations')

    new_annots = {}
    for i, old_annot in enumerate(src_annotations):
        if i in ix_map:
            new_annots[ix_map[i]] = old_annot

    del src_annotations

    new_annots_list = []
    for k in sorted(new_annots.keys()):
        new_annots_list.append(new_annots[k])

    # Dump annotations
    with open(os.path.join(dest_dir, 'annotations.json'), 'w') as f:
        json.dump(new_annots_list, f)

    print('Done.')
    