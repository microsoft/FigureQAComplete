#!/usr/bin/python
from __future__ import division

import argparse
import json
import numpy as np
import os
import shutil

FIGURE_TYPES = ["pie", "line", "dot_line", "vbar_categorical", "hbar_categorical"]
PRINT_FREQ = 50

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source")
    parser.add_argument("-d", "--dest")
    parser.add_argument("-b", "--balance", action="store_true", default=False)
    parser.add_argument("-n", "--num", type=int)
    args = parser.parse_args()

    src_base_png_file = os.path.join(args.source, "png", "%d.png")
    src_json_qa_file = os.path.join(args.source, "qa_pairs.json")
    src_json_annotations_file = os.path.join(args.source, "annotations.json")

    dest_png_dirpath = os.path.join(args.dest, "png")
    dest_base_png_file = os.path.join(dest_png_dirpath, "%d.png")
    dest_json_qa_file = os.path.join(args.dest, "qa_pairs.json")
    dest_json_annotations_file = os.path.join(args.dest, "annotations.json")

    if not os.path.exists(args.dest):
        os.mkdir(args.dest)

    if not os.path.exists(dest_png_dirpath):
        os.mkdir(dest_png_dirpath)

    print "Reading QA json..."
    with open(src_json_qa_file, 'r') as f:
        orig_qas = json.load(f)['qa_pairs']

    print "Reading annotations json.."
    with open(src_json_annotations_file, 'r') as f:
        orig_annotations = json.load(f)

    print "Sampling some data points"
    new_qas = []
    new_annotations = []

    if args.balance:

        n_per = int(args.num / len(FIGURE_TYPES))

        # Get the indices
        indices_to_select = {fig: set() for fig in FIGURE_TYPES}
        count = 0
        for rand_ix in np.random.permutation(range(0, len(orig_annotations))):

            fig_type = orig_annotations[rand_ix]['type']

            if rand_ix in indices_to_select[fig_type] or len(indices_to_select[fig_type]) >= n_per:
                continue

            indices_to_select[fig_type].add(rand_ix)
            count += 1

            if count % PRINT_FREQ == 0:
                print "Sampled", count

            if all([len(v) == n_per for v in indices_to_select.values()]):
                break

        # Copy images and form the new JSON
        count = 0
        for fig_type in indices_to_select:
            for ix in indices_to_select[fig_type]:

                original_image_index = orig_annotations[ix]['image_index']

                for orig_qa in orig_qas:
                    if orig_qa['image_index'] != original_image_index:
                        continue

                    new_qas.append(orig_qa)
                    new_qas[-1]['image_index'] = count

                new_annotations.append(orig_annotations[ix])
                new_annotations[-1]['image_index'] = count

                shutil.copy(src_base_png_file % original_image_index, dest_base_png_file % count)
                count += 1

        with open(dest_json_qa_file, 'w') as f:
            json.dump({'qa_pairs': new_qas}, f)

        with open(dest_json_annotations_file, 'w') as f:
            json.dump(new_annotations, f)
