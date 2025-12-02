#!/usr/bin/python
import random

def sample_from_scratch(source, dests, ns):
    with open(source, 'r') as f:
        all_colors = [ l.strip() for l in f.readlines() if len(l.strip()) > 0 ]

    sampled_colors = random.sample(all_colors, ns[0])

    with open(dests[0], 'w') as f:
        for color in sampled_colors:
            f.write(color + "\n")


def sample_given_file(source, others, dests, ns):
    print source, others, dests, ns
    with open(source, 'r') as f:
        all_colors = [ l.strip() for l in f.readlines() if len(l.strip()) > 0 ]

    other_colors = []
    for other in others:
        with open(other, 'r') as f:
            other_colors += [ l.strip() for l in f.readlines() if len(l.strip()) > 0 ]    

    random_unused_colors = list(set(all_colors) - set(other_colors))
    random.shuffle(random_unused_colors)

    if not ns:
        split = len(random_unused_colors) / len(dests)
        ns = [split] * len(dests)

    i = 0
    dest_colors = [[] for n in ns]

    for dest_i, n in enumerate(ns):
        j = 0
        while i < len(random_unused_colors) and j < n:
            dest_colors[dest_i].append(random_unused_colors[i])
            i += 1
            j += 1

    for dest_i, dest in enumerate(dests):
        with open(dest, 'w') as f:
            for color in dest_colors[dest_i]:
                f.write(color + "\n")

def even_sampling(source, dests):
    with open(source, 'r') as f:
        all_colors = [ l.strip() for l in f.readlines() if len(l.strip()) > 0 ]

    n_each = len(all_colors) / len(dests)

    permuted_colors = random.sample(all_colors, len(all_colors))

    for i, dest in enumerate(dests):
        with open(dest, 'w') as f:
            for col in permuted_colors[i*n_each:(i+1)*n_each]:
                f.write(col + "\n")

if __name__ == "__main__":
    import argparse

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--src")
    parser.add_argument("--ns", nargs='+', type=int, default=None)
    parser.add_argument("--dests", nargs='+')
    parser.add_argument("--other-srcs", nargs='+')
    parser.add_argument("--existing", action='store_true', default=False)
    parser.add_argument("--even", action='store_true', default=False)
    args = parser.parse_args()

    if args.even:
        even_sampling(args.src, args.dests)
    elif args.existing:
        sample_given_file(args.src, args.other_srcs, args.dests, args.ns)
    else: 
        sample_from_scratch(args.src, args.dests, args.ns)
