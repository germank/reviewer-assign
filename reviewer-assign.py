#!/usr/bin/env python3
# tested on Python 3.5.1
# Written by Germán Kruszewski (firstname.lastname@unitn.it)

import sys
import argparse
try:
    import pulp
except ImportError:
    print("Error: pulp python package is required", file=sys.stderr)
    raise
try:
    import yaml
except ImportError:
    print('Error: yaml python package is required', file=sys.stderr)
    raise


def main():
    ap = argparse.ArgumentParser('Reviewer Assigner')
    ap.add_argument('--weight-no', default=-10, 
        help='How happy a reviewer is if you assign him a paper she didn\'t'\
        ' want')
    ap.add_argument('--weight-maybe', default=-3,
        help='How happy a reviewer is if you assign him a paper he maybe'\
        ' wanted')
    ap.add_argument('--weight-yes', default=-1,
        help='How happy a reviewer is if you assign him a paper she did'\
        ' want')
    ap.add_argument('--max-assignments', default=3,
        help='Maximum number of papers per reviewer')
    ap.add_argument('--reduced-max-assignments', default=1,
        help='Maximum number of papers per reviewer if he asked for reduced'
        ' load')
    ap.add_argument('--min-paper-reviewers', default=1,
        help='Minimum number of reviewers there can be for a paper')
    ap.add_argument('--max-paper-reviewers', default=3,
        help='Maximum number of reviewers there can be for a paper')
    ap.add_argument('description', help='File containing papers, reviewers, '
    'biddings and other problem description information')

    args = ap.parse_args()

    with open(args.description) as f:
        try:
            description = yaml.load(f)
        except:
            print('An error occurred while reading the description file. Please,\
            check that it\'s well-formatted', file=sys.stderr)
            raise

    
    # Decision X
    # X_i_j: Reviewer i is assigned to review paper j
    assert(isinstance(description['reviewers'],list))
    assert(isinstance(description['papers'],list))
    reviewers = description['reviewers']
    papers = description['papers']
    X = {}
    for i,reviewer in enumerate(reviewers):
        for j,paper in enumerate(papers):
            X[(reviewer,paper)] = pulp.LpVariable("X_{0}_{1}".format(i,j),
                None, None, pulp.LpBinary)


    assert(isinstance(description['biddings'],dict))

    weights = {
        'no': args.weight_no,
        False: args.weight_no,
        0: args.weight_no,
        'maybe': args.weight_maybe,
        'yes': args.weight_yes,
        True: args.weight_yes,
        1: args.weight_yes
    }
    biddings_d = description['biddings']
    print (reviewers)
    for reviewer in reviewers:
        for paper in papers:
            print(biddings_d[reviewer][paper])
    objective = sum(weights[biddings_d[reviewer][paper]] *
        X[(reviewer, paper)] 
        for reviewer in reviewers
        for paper in papers
        if biddings_d[reviewer][paper] != 'coi')

    problem = pulp.LpProblem("Reviewer assignment", sense=pulp.LpMaximize)
    problem += objective, 'Reviewers happiness'

    #Add COI constraints
    for reviewer in reviewers:
        for paper in papers:
            if biddings_d[reviewer][paper] == 'coi':
                problem += X[(reviewer, paper)] == 0, 'rev {0} declared '\
                'COI on {1}'.format(reviewer, paper)

    #Add max load constraint:
    for reviewer in reviewers:
        reduced_load = description['reduced_load']
        total_assignments = sum(X[(reviewer, paper)] for paper
                in papers)
        if reduced_load and reviewer in reduced_load:
            problem +=  total_assignments <= args.reduced_max_assignments, \
                'rev {0} asked for reduced load'.format(reviewer)
        else:
            problem +=  total_assignments <= args.max_assignments, \
                'rev {0} max paper assignments limit'.format(reviewer)
            

    for paper in papers:
        total_reviewers = sum(X[(reviewer, paper)] for reviewer
                in reviewers)
        problem += total_reviewers >= args.min_paper_reviewers, \
            'paper {0} minimum reviewers number'.format(paper)
        problem += total_reviewers <= args.max_paper_reviewers, \
            'paper {0} maximum reviewers number'.format(paper)
    
    solver = pulp.solvers.GLPK()

    problem.solve(solver)
    for reviewer in reviewers:
        for paper in papers:
            if pulp.value(X[(reviewer, paper)]) == 1:
                print (reviewer, 'assigned to', paper)





if __name__ == '__main__':
    main()


