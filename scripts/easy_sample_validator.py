#!/usr/bin/python
import json
import copy
import numpy as np
import os
import shutil
import sys

if __name__ == "__main__":

    with open(sys.argv[1], 'r') as f:
        qas = json.load(f)['qa_pairs']

    dest_dir = sys.argv[2]
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)

    os.mkdir(dest_dir)

    n_images_to_sample = int(sys.argv[3])

    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    np.random.seed(seed)

    png_dir = os.path.join(os.path.dirname(sys.argv[1]), "png")
    png_template_path = os.path.join(png_dir, "%d.png")

    total_images = len(os.listdir(png_dir))
    ix_for_sample = np.random.choice(range(0, total_images), n_images_to_sample, replace=False)

    print "Copying images"
    for ix in ix_for_sample:
        shutil.copy(png_template_path % ix, os.path.join(dest_dir, "%d.png" % ix))

    new_qas = { k:[] for k in ix_for_sample}

    print "Getting qas"
    for qa in qas:
        if qa['image_index'] not in ix_for_sample:
            continue
        if 'answer' in qa:
            ans_string = "true" if qa['answer'] == 1 else "false"
        else:
            ans_string = "None"
        new_qas[qa['image_index']].append({ 'question': qa['question_string'],
                                            'answer': ans_string})

    print "Dumping json"
    for k, v in new_qas.items():
        with open(os.path.join(dest_dir, "%d.json" % k), 'w') as f:
            json.dump(v, f)
