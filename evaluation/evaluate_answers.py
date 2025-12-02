#!/usr/bin/python
from __future__ import division, print_function
import click
import codecs
import os
import pandas as pd

from collections import Counter
from tqdm import tqdm


QUESTION_TYPE_STRINGS = {
    0: 'categorical_minimum',
    1: 'categorical_maximum',
    2: 'categorical_less_than',
    3: 'categorical_greater_than',
    4: 'categorical_low_median',
    5: 'categorical_high_median',
    6: 'continuous_minimum_auc',
    7: 'continuous_maximum_auc',
    8: 'continuous_smoothest',
    9: 'continuous_roughest',
    10: 'continuous_global_minimum',
    11: 'continuous_global_maximum',
    12: 'continuous_less_than',
    13: 'continuous_greater_than',
    14: 'continuous_intersect'
}

FIGURE_TYPE_STRINGS = {
    0: 'vbar_categorical',
    1: 'hbar_categorical',
    2: 'pie',
    3: 'line',
    4: 'dot_line'
}


@click.group()
def cli():
    pass


@click.option('--judgements',
              default=os.path.normpath('../uhrs/judgements/parsed_combined_human_baseline_judgements.tsv'),
              type=click.Path(file_okay=True, exists=True))
def prepare_human(judgements):

    # input columns:
    # all_colors	answer	color1_id	color1_name	color1_rgb	color2_id	color2_name	color2_rgb	correct	figure_type	human_answer	image_index	image_url	judgement_time_ms	question_id	question_string	question_type
    raw_judgements = pd.read_csv(judgements, sep='\t')

    # output columns:
    # question_index,image_index,question_id,question_string,answer,question_type,figure_type
    INCLUDED_COLUMNS = ['image_index', 'question_id', 'question_string', 'answer', 'question_type', 'figure_type']

    raw_answers_gt = pd.DataFrame(data=raw_judgements, columns=INCLUDED_COLUMNS)

    # fix question type names
    raw_answers_gt['better_question_type'] = raw_answers_gt.apply(lambda row: QUESTION_TYPE_STRINGS[row['question_id']], axis=1)
    raw_answers_gt = raw_answers_gt.drop('question_type', axis=1)
    raw_answers_gt['question_type'] = raw_answers_gt['better_question_type']
    raw_answers_gt = raw_answers_gt.drop('better_question_type', axis=1)

    answers_gt = pd.concat([pd.DataFrame(data={'question_index': list(range(len(raw_answers_gt)))},
                                         columns=['question_index']),
                            raw_answers_gt], axis=1)
    answers_gt.to_csv('answers_human.csv', encoding='utf-8', index=False)


@cli.command('eval')
@click.argument('testset')
@click.argument('infiles', nargs=-1)
def main(testset, infiles):

    testset = testset.lower().strip()

    if testset == 'human':
        answers_file = 'answers_human.csv'

    elif testset.endswith('1'):
        # answers_file = 'answers_validation1.csv'
        answers_file = 'answers_test1.csv'

    elif testset.endswith('2'):
        # answers_file = 'answers_validation2.csv'
        answers_file = 'answers_test2.csv'

    else:
        raise Exception(testset + ' is not a valid testset!')

    raw_truth = pd.read_csv(answers_file)
    # because human experiment was run on 1.0.0 and doesn't make up whole set, we need to index differently
    truth = raw_truth.set_index(['image_index', 'question_string'], drop=False) if testset == 'human' else raw_truth

    overall_accs = {}
    figtype_accs = {}
    qtype_accs = {}
    bad_entries_by_file = {}
    missing_count_by_file = Counter()

    for infile in infiles:

        print('Processing', infile)
        bad_entries = False

        try:
            predictions = pd.read_csv(infile)
        except:
            print('> Error reading', infile, ', skipping')
            continue

        n_correct = 0
        n_correct_figtype = Counter()
        n_correct_qtype = Counter()
        figtype_truth_counts = Counter()
        qtype_truth_counts = Counter()
        # q_index is the index of the item in the file, *not* a distinct question identifier! (the latter is `question_id`)

        # Populate truths
        for i, row in truth.iterrows():
            figtype_truth_counts[row['figure_type']] += 1
            qtype_truth_counts[row['question_type']] += 1

        for i, row in tqdm(predictions.iterrows(), total=len(predictions)):

            try:
                question_index, image_index, question_string, pred = row['question_index'], row['image_index'], row['question_string'], row['answer']
                qa_id = (image_index, question_string) if testset == 'human' else question_index

                if qa_id not in truth.index:
                    missing_count_by_file[infile] += 1
                    continue

                if pred != 0 and pred != 1:
                    if not bad_entries:
                        bad_entries = True
                    continue

                if truth.loc[qa_id]['answer'] == pred:
                    n_correct += 1
                    n_correct_figtype[truth.loc[qa_id]['figure_type']] += 1
                    n_correct_qtype[truth.loc[qa_id]['question_type']] += 1

            except KeyError:
                if not bad_entries:
                    bad_entries = True
                continue

        overall_accs[infile] = round(100 * n_correct / len(truth), 2)
        figtype_accs[infile] = {k: round(100 * n_correct_figtype[v] / figtype_truth_counts[v]
                                         if figtype_truth_counts[v] > 0 else -1, 2)
                                for k, v in FIGURE_TYPE_STRINGS.items()}
        qtype_accs[infile] = {k: round(100 * n_correct_qtype[v] / qtype_truth_counts[v]
                                       if qtype_truth_counts[v] > 0 else -1, 2)
                              for k, v in QUESTION_TYPE_STRINGS.items()}
        bad_entries_by_file[infile] = bad_entries

    print('\n---RESULTS:---')

    for file in infiles:
        print()
        print(file, '=' * 80)
        print('\noverall accuracy = {0:.2f}%'.format(overall_accs[file]))

        print('\n= by question type', '=' * 80, '\n')

        for cc in ['categorical', 'continuous']:
            acc = round(100 * sum([n_correct_qtype[v] for v in QUESTION_TYPE_STRINGS.values() if cc in v]) / sum(
                [qtype_truth_counts[v] for v in QUESTION_TYPE_STRINGS.values() if cc in v]), 2)
            print('total {0} question accuracy = {1:.2f}%'.format(cc, acc))

        for i in range(len(QUESTION_TYPE_STRINGS.items())):
            if i in qtype_accs[file]:
                print('{0:25} (id={1:2}) accuracy = {2:.2f}%'.format(
                    QUESTION_TYPE_STRINGS[i], i, qtype_accs[file][i]))

        print('\n= by figure type', '=' * 80, '\n')

        for i in range(len(FIGURE_TYPE_STRINGS)):
            if i in figtype_accs[file]:
                print('{0:33} accuracy = {1:.2f}%'.format(
                    FIGURE_TYPE_STRINGS[i], figtype_accs[file][i]))

        if bad_entries_by_file[file]:
            print(f'*error, missing entries (#={missing_count_by_file[file]})*')

        if bad_entries_by_file[file]:
            print('*errors while processing*')


if __name__ == '__main__':
    cli()
