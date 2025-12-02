#!/usr/bin/python
from __future__ import division, print_function
import codecs
import json
import os

from collections import Counter
from traceback import print_exc

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


if __name__ == '__main__':

    ##############################################
    # NOTE! DOESN'T WORK FOR `human`!
    ##############################################

    testsets = ['test1', 'test2']
    # testsets = ['validation1', 'validation2']

    for testset in testsets:

        print('Processing', testset, '...')

        test_qa_json_fp = os.path.join('..', 'dataset', 'v1.0.1', 'testset_with_answers', testset, 'qa_pairs.json')
        # test_qa_json_fp = os.path.join('..', 'dataset', 'v1.0.1', testset, 'qa_pairs.json') # For validation

        with open(test_qa_json_fp, 'r') as f:
            qas = json.load(f)['qa_pairs']

        test_figtype_json_fp = 'figure_types_%s.json' % testset

        with open(test_figtype_json_fp, 'r') as f:
            figtypes = {x['image_index']: x['type'] for x in json.load(f)}

        common = ['question_index', 'image_index',
                  'question_id', 'question_string', 'answer']
        header_template = ','.join(common) + '\n'
        header_answers = ','.join(
            common + ['question_type', 'figure_type']) + '\n'

        answers_fp = 'answers_%s.csv' % testset
        template_fp = 'template_%s.csv' % testset

        with codecs.open(answers_fp, 'w', 'utf-8') as af:
            with codecs.open(template_fp, 'w', 'utf-8') as tf:

                af.write(header_answers)
                tf.write(header_template)

                filtered = []
                known_counter = Counter()
                unknown_counter = Counter()
                for i, qa in enumerate(qas):
                    try:
                        x = []
                        x.append(qa['image_index'])
                        x.append(qa['question_id'])
                        x.append(qa['question_string'])
                        x.append(qa['answer'])
                        x.append(QUESTION_TYPE_STRINGS[qa['question_id']])
                        x.append(figtypes[qa['image_index']])
                        filtered.append(x)
                        known_counter[qa['image_index']] += 1
                    except KeyError as e:
                        print(e, 'unknown image_index=', qa['image_index'])
                        unknown_counter[qa['image_index']] += 1
                print(len(known_counter), len(unknown_counter))

                for qa in filtered:
                    af.write(','.join([str(s) for s in qa]) + '\n')
                    tf.write(','.join([str(s)
                                       for s in qa[:-3]] + ['<0/1>']) + '\n')

        print('Done', testset)
