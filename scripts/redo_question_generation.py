#!/usr/bin/python
import argparse
import h5py
import json
import os
import numpy as np
import selenium.webdriver as seldriver
import yaml

from bokeh.io import export_png_and_data
from data_utils import combine_source_and_rendered_data
from figure import *
from question_generation.categorical import generate_bar_graph_questions, generate_pie_chart_questions
from question_generation.lines import generate_line_plot_questions
from scipy.misc import imread


def read_png_file_to_numpy_array(filepath):
    img_array = imread(filepath, mode='RGB')
    return img_array


if __name__ == "__main__":

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dest-dir", default="gendata")
    parser.add_argument("-s", "--source-data")
    parser.add_argument("--h5", action='store_true', default=False)
    parser.add_argument("--slim", action='store_true', default=False)
    args = parser.parse_args()

    # Setup dest dirs and h5 file if desired
    if args.h5:

        html_dir = args.dest_dir
        png_dir = args.dest_dir

        if not os.path.exists(args.dest_dir):
            os.mkdir(args.dest_dir)

        h5file = h5py.File(os.path.join(args.dest_dir, "figures.h5"), 'a')
        h5file.create_group("images")

        if not args.slim:
            h5file.create_group("data")

        h5file.flush()
        h5file.close()

    else:
        qa_json_dir = os.path.join(args.dest_dir, "json_qa")
        annotations_json_dir = os.path.join(args.dest_dir, "json_annotations")
        html_dir = args.dest_dir #os.path.join(args.dest_dir, "html")
        png_dir = os.path.join(args.dest_dir, "png")

        for dirpath in [args.dest_dir, qa_json_dir]:
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)

    # Create web driver
    #webdriver = seldriver.PhantomJS()

    # Read in the synthetic data
    with open(args.source_data, 'r') as f:
        source_data = json.load(f)

    total_data_points = 0

    for i, source in enumerate(source_data):

        point_sets = source['data']

        fig = None
        fig_type = source['type']

        if fig_type == 'vbar_categorical':
            fig = VBarGraphCategorical(point_sets[0], source['visuals'])
        elif fig_type == 'hbar_categorical':
            fig = HBarGraphCategorical(point_sets[0], source['visuals'])
        elif fig_type == 'line':
            fig = LinePlot(point_sets, source['visuals'])
        elif fig_type == 'dot_line':
            fig = DotLinePlot(point_sets, source['visuals'])
        elif fig_type == 'pie':
            fig = Pie(point_sets[0], source['visuals'])

        if not fig:
            continue

        print "Creating %s, %d" % (fig_type, i)

        fig_id = str(i)
        #html_file = os.path.join(html_dir, "{0}_{1}.html".format(fig_id, fig_type))
        png_file = os.path.join(png_dir, "{0}_{1}.png".format(fig_id, fig_type))

        # Export to HTML, PNG, and get rendered data
        #rendered_data = export_png_and_data(fig.figure, png_file, html_file, webdriver)

        #all_plot_data = combine_source_and_rendered_data(source, rendered_data)

        if args.h5:

            h5file = h5py.File(os.path.join(args.dest_dir, "figures.h5"), 'a')
            h5file['images'].create_dataset(str(i), data=read_png_file_to_numpy_array(png_file), compression='gzip')

            if not args.slim:
                h5file['data'].create_dataset(str(i), data=json.dumps(all_plot_data))

            for qa_pair in source['qa_pairs']:
                sample_id = str(total_data_points)
                h5file.create_group(sample_id)
                #h5file[sample_id].create_dataset('question', data=np.array(qa_pair['q_vector']), compression='gzip')
                h5file[sample_id].create_dataset('answer', data=np.array(qa_pair['answer'])) # scalars don't support compression
                h5file[sample_id].create_dataset('image', data=np.string_(i)) # scalars don't support compression
                
                h5file[sample_id].create_dataset('question_string', data=np.string_(qa_pair['question_string']))
                h5file[sample_id].create_dataset('question_id', data=np.string_(qa_pair['question_id']))

                h5file[sample_id].create_dataset('color1_name', data=np.string_(qa_pair['color1_name']))
                h5file[sample_id].create_dataset('color1_id', data=np.array(qa_pair['color1_id']))
                h5file[sample_id].create_dataset('color1_rgb', data=np.array(qa_pair['color1_rgb']), compression='gzip')

                h5file[sample_id].create_dataset('color2_name', data=np.string_(qa_pair['color2_name']))
                h5file[sample_id].create_dataset('color2_id', data=np.array(qa_pair['color2_id']))
                h5file[sample_id].create_dataset('color2_rgb', data=np.array(qa_pair['color2_rgb']), compression='gzip')

                h5file[sample_id].create_dataset('total_distinct_questions', data=np.array(qa_pair['total_distinct_questions']))
                h5file[sample_id].create_dataset('total_distinct_colors', data=np.array(qa_pair['total_distinct_colors']))

                if not args.slim:
                    h5file[sample_id].create_dataset('data', data=np.string_(i)) # scalars don't support compression

                total_data_points += 1

            h5file.flush()
            h5file.close()

            # Cleanup
            os.remove(html_file)
            os.remove(png_file)

        else:           
#            all_plot_data['qa_pairs'] = source['qa_pairs']

#            friendly_qa_pairs = [{'question': qa['q'], 'answer': qa['a']} for qa in all_plot_data['qa_pairs']]
#            with open(os.path.join(json_dir, "qa_{0}_{1}.json".format(fig_type, fig_id)), 'w') as f:
#                json.dump({'qa_pairs': friendly_qa_pairs}, f)

            qa_json_file = os.path.join(qa_json_dir, "{0}_{1}.json".format(fig_id, fig_type))
            annotations_json_file = os.path.join(annotations_json_dir, "{0}_{1}_annotations.json".format(fig_id, fig_type))
            aug_qa_pairs = []

            for qa in source['qa_pairs']:
                aug_qa = copy.deepcopy(qa)
                aug_qa['image'] = os.path.basename(png_file)
                aug_qa['annotations'] = os.path.basename(annotations_json_file)
                aug_qa_pairs.append(aug_qa)

            with open(qa_json_file, 'w') as f:
                json.dump({ 'qa_pairs': aug_qa_pairs}, f)

            #with open(annotations_json_file, 'w') as f:
            #    json.dump(all_plot_data, f)

            # Cleanup
            #os.remove(html_file)
