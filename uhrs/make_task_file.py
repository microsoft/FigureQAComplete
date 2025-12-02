#!/usr/bin/python
import argparse
import json
import numpy as np
import random

from collections import defaultdict

"""
Assumes that image indices are contiguous by figure type
E.g. if there's 1000 images and 5 figure types, [0:200] are type 1, [200:400] are type 2, etc.
"""

N_FIGURE_TYPES = 5

if __name__ == "__main__":

    np.random.seed(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source-json")
    parser.add_argument("-d", "--dest-taskfile")
    parser.add_argument("-i", "--n-images", type=int, default=0,
        help="Total number of images to select from the whole set of images")
    parser.add_argument("--image-start-range", type=int, default=0,
        help="Start index within images broken down by figure")
    parser.add_argument("--image-end-range", type=int, default=-1,
        help="End (exclusive) index within images broken down by figure")
    parser.add_argument("-q", "--max-qs-per-hit", type=int, default=5)
    parser.add_argument("--require-max-qs-per-hit", action='store_true', default=False)
    args = parser.parse_args()

    with open(args.source_json, 'r') as f:
        qas = json.load(f)['qa_pairs']

    # Process the qas and sort by image index, and get how many images total per bucket
    qas_by_img = defaultdict(list)

    for q_ix, qa in enumerate(qas):
        img_ix = qa['image_index']
        new_qa = {'question': qa['question_string'], 'question_index': q_ix, 'image_index': qa['image_index']}
        qas_by_img[img_ix].append(new_qa)

    # figure index = image index / total_images_per_bucket
    total_images_per_bucket = len(qas_by_img.keys()) / N_FIGURE_TYPES
    print "total_images_per_bucket", total_images_per_bucket

    if args.n_images > 0 and args.n_images < N_FIGURE_TYPES:
        raise Exception("Number of images < # figure types = %d", N_FIGURE_TYPES)

    if args.image_end_range < 0:
        args.image_end_range = total_images_per_bucket

    if args.image_end_range <= args.image_start_range:
        raise Exception("Bad image ranges! %d:%d" % (args.image_start_range, args.image_end_range))

    if args.n_images > 0 and ((args.image_end_range - args.image_start_range) * N_FIGURE_TYPES) < args.n_images:
        raise Exception("Not enough images for n_images! required: %d, allowable: %d" % \
                (args.n_images, (args.image_end_range - args.image_start_range) * N_FIGURE_TYPES))

    n_images_per_bucket = (args.n_images / N_FIGURE_TYPES) if args.n_images > 0 else \
                                                                        args.image_end_range - args.image_start_range
    print "n_images_per_bucket", n_images_per_bucket

    sorted_img = sorted(qas_by_img.keys())
    sorted_img_by_figure = {i: sorted_img[i*total_images_per_bucket:(i+1)*total_images_per_bucket] \
                                for i in range(N_FIGURE_TYPES)}

    eligible_img_by_figure = {i: sorted_img_by_figure[i][args.image_start_range:args.image_end_range] \
                                for i in range(N_FIGURE_TYPES)}

    selected_img_by_figure = {i: np.random.choice(eligible_img_by_figure[i], n_images_per_bucket, replace=False) \
                                for i in range(N_FIGURE_TYPES)}

    hit_string = "QuestionImageJson\n"
    hit_id = 0
    chosen_image_indices = []

    for image_indices in selected_img_by_figure.values():

        for ix, image_index in enumerate(image_indices):
            chosen_image_indices.append(image_index)
            qa_list = qas_by_img[image_index]

            # Shuffle the sublist to avoid learning the pattern
            random.shuffle(qa_list)

            image_url = "https://figureqadataset.blob.core.windows.net/human-baseline-uhrs/v1.0.0/test2/%d.png" % image_index

            for jx in range(0, (len(qa_list)/5) + 1):
                sublist = qa_list[jx*args.max_qs_per_hit:(jx+1)*args.max_qs_per_hit]

                if not sublist or (args.require_max_qs_per_hit and len(sublist) < args.max_qs_per_hit):
                    continue
                
                hit = { 'hit_id': hit_id,
                        'image_url': image_url,
                        'image_index': image_index,
                        'questions': sublist
                }
                hit_string += "%s\n" % json.dumps(hit)
                hit_id += 1

    with open(args.dest_taskfile, 'w') as f:
        f.write(hit_string)

    print "images selected:", len(chosen_image_indices)
    #print chosen_image_indices # for debugging
