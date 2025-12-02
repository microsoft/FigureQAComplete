#!/usr/bin/python
from __future__ import division
from __future__ import print_function

import argparse
import json
import numpy as np
import pandas as pd

from collections import Counter
from collections import defaultdict
from sklearn.metrics import confusion_matrix


QUESTION_ID_TYPE_MAP = {
    0: "cat_min",
    1: "cat_max",
    2: "cat_less",
    3: "cat_greater",
    4: "cat_low_median",
    5: "cat_high_median",
    6: "cont_min_auc",
    7: "cont_max_auc",
    8: "cont_smoothest",
    9: "cont_roughest",
    10: "cont_global_min",
    11: "cont_global_max",
    12: "cont_less",
    13: "cont_greater",
    14: "cont_intersect"
}


def get_stats(df):

    cm = confusion_matrix(df['answer'], df['human_answer'], labels=[0,1,2])

    n_right = cm[0][0] + cm[1][1]
    n_wrong = np.sum(cm) - n_right

    accuracy = n_right / np.sum(cm)
    print("\naccuracy overall = {0:.2f} %\n".format(np.round(100*accuracy, 2)))

    print("Unknown answers out of all = {0:.2f} %\n".format(np.round(100 * (cm[0][2] + cm[1][2]) / np.sum(cm), 2)))

    print("confusion matrix")
    print(cm, "\n")

    # Breakdown right/wrong per pred category
    for pred, string in [(0, "No"), (1, "Yes"), (2, "Unknown")]:
        n_pred_right = cm[pred][pred]
        n_pred_wrong = np.sum(cm, axis=0)[pred] - n_pred_right

        pct_wrong = n_pred_wrong / n_wrong
        pct_right = n_pred_right / n_right

        print("right answers that are {0} = {1:.2f} %".format(string, np.round(100*pct_right, 2)))
        print("wrong answers that are {0} = {1:.2f} %".format(string, np.round(100*pct_wrong, 2)))

    print()

    # Precision: how many of our preds p_i were correct out of those that we predicted as p_i (TP + FP)
    with np.errstate(divide="ignore", invalid="ignore"):
        precision = cm.astype('float') / cm.sum(axis=0)[np.newaxis, :]

    for pred, string in [(0, "No"), (1, "Yes"), (2, "Unknown")]:
        print("precision for {0} = {1:.2f} %".format(string, np.round(100*precision[pred][pred], 2)))

    print()

    # Recall: how many of our preds p_i where correct out of those that are actually p_i (TP + FN)
    with np.errstate(divide="ignore", invalid="ignore"):
        recall = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        
    for actual, string in [(0, "No"), (1, "Yes")]:
        print("recall for {0} = {1:.2f} %".format(string, np.round(100*recall[actual][actual], 2)))

    print()


def get_stats_groupby(groupby):
    for group_name, group_df in groupby:
        print("\n----- STATS FOR GROUP:", group_name)
        get_stats(group_df)


if __name__ == "__main__":
    """
    To create the combined judgement file:
    python analyze_judgements.py -a fixed_test2\annotations.json -q fixed_test2\qa_pairs.json
        -j judgements\UHRS_Task_FigureQA_test2_gold_25_images.tsv
            judgements\UHRS_Task_FigureQA_test2_internal_250_images.tsv
            judgements\UHRS_Task_FigureQA_test2_internal_1000_more_images.tsv 
        -d judgements\parsed_combined_human_baseline_judgements.tsv

    This only has to be done once, that you can use
    python analyze_judgements.py -d judgements\parsed_combined_human_baseline_judgements.tsv

    to analyze the file.

    Filter with:
    grep "accuracy\|STATS\|wrong.*Unknown\|^Unknown\|Figure" stats.txt > filtered_stats.txt
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--annotations-json", default=None)
    parser.add_argument("-q", "--qa-json")
    parser.add_argument("-j", "--judgement-tsvs", nargs='+')
    parser.add_argument("-d", "--dest-tsv", default=None)
    parser.add_argument("-s", "--source-tsv", default=None)
    args = parser.parse_args()

    if args.source_tsv:
        print("Loading pre-augmented judgement TSV...")
        augmented = pd.read_csv(args.source_tsv, delimiter='\t')

    else:
        if args.annotations_json:
            print("Loading annotations...")
            with open(args.annotations_json, 'r') as f:
                annotations = json.load(f)

        print("Loading question-answer pairs...")
        with open(args.qa_json, 'r') as f:
            qas = json.load(f)['qa_pairs']

        parsed_qas = []

        for judgement_file in args.judgement_tsvs:
            print("reading judgement file", judgement_file) 
            judgement_df = pd.read_csv(judgement_file, delimiter='\t')

            for index, row in judgement_df.iterrows():
                judged_qa_data = json.loads(row['JudgmentDataJson'])

                for judged_qa in judged_qa_data['questions']:
                    aug_qa = qas[judged_qa['question_index']]
                    aug_qa['question_type'] = QUESTION_ID_TYPE_MAP[aug_qa['question_id']]
                    aug_qa['human_answer'] = int(judged_qa['answer'])
                    aug_qa['correct'] = 1 if aug_qa['human_answer'] == aug_qa['answer'] else 0
                    aug_qa['image_url'] = judged_qa_data['image_url']
                    aug_qa['judgement_time_ms'] = int(row['TimeSpentOnJudgment'])

                    annot = annotations[aug_qa['image_index']]
                    if 'figure_type' not in aug_qa:
                        aug_qa['figure_type'] = annot['type']

                    if aug_qa['figure_type'] == 'vbar_categorical':
                        colors = annot['general_figure_info']['x_axis']['major_labels']['values']
                    elif aug_qa['figure_type'] == 'hbar_categorical':
                        colors = annot['general_figure_info']['y_axis']['major_labels']['values']
                    else:
                        colors = [item['label']['text'] for item in annot['general_figure_info']['legend']['items']]

                    aug_qa['all_colors'] = colors

                    parsed_qas.append(aug_qa)

        augmented = pd.DataFrame(parsed_qas)

        if args.dest_tsv:
            print("Dumping combined data to TSV...")
            augmented.to_csv(args.dest_tsv, sep='\t')

    print("="*50, "\n ==== ALL STATS\n", "="*50)
    get_stats(augmented)
    print("="*50, "\n ==== STATS by fig\n", "="*50)
    get_stats_groupby(augmented.groupby(['figure_type']))
    print("="*50, "\n ==== STATS by q\n", "="*50)
    get_stats_groupby(augmented.groupby(['question_type']))

    figure_image_indices = defaultdict(list)

    for index, row in augmented.iterrows():
        figure_image_indices[row['figure_type']].append(row['image_index'])

    figure_counts = {}
    for figure_type, images in figure_image_indices.items():
        figure_counts[figure_type] = len(set(images))

    print("\n ==== Figure Breakdown\n")
    total = sum([count for count in figure_counts.values()])
    print("Total Figures = {0}".format(total))
    print("Total Questions for all Figures = {0}".format(len(augmented)))

    for figure_type, count in figure_counts.items():
        print("Figure = {0}, count = {1}, composition = {2:.2f} %".format(figure_type, count, np.round(100*count/total, 2)))
