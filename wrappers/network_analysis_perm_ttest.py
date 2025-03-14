#!/usr/bin/env python

#=============================================================================
# Created by Kirstie Whitaker
# at Neurohackweek 2016 in Seattle, September 2016
# Contact: kw401@cam.ac.uk
#=============================================================================

#=============================================================================
# IMPORTS
#=============================================================================
import os
import sys
import argparse
import textwrap

import numpy as np
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '../scripts/'))
import make_graphs as mkg
from corrmat_from_regionalmeasures import corrmat_from_regionalmeasures

#=============================================================================
# FUNCTIONS
#=============================================================================
def setup_argparser():
    '''
    Code to read in arguments from the command line
    Also allows you to change some settings
    '''
    # Build a basic parser.
    help_text = (('Compare two groups according to their structural covariance network measures\n')+
                 ('(global and nodal) and assess significance by permuting the original data.'))

    sign_off = 'Author: Kirstie Whitaker <kw401@cam.ac.uk>'

    parser = argparse.ArgumentParser(description=help_text,
                                     epilog=sign_off,
                                     formatter_class=argparse.RawTextHelpFormatter)

    # Now add the arguments
    parser.add_argument(dest='regional_measures_file_A',
                            type=str,
                            metavar='regional_measures_file_A',
                            help=textwrap.dedent(('CSV file that contains regional values for each participant in group A.\n')+
                                                 ('Column labels should be the region names or covariate variable\n')+
                                                 ('names. All participants in the file will be included in the\n')+
                                                 ('correlation matrix.')))

    parser.add_argument(dest='regional_measures_file_B',
                            type=str,
                            metavar='regional_measures_file_B',
                            help=textwrap.dedent(('CSV file that contains regional values for each participant in group B.\n')+
                                                 ('Column labels should be the region names or covariate variable\n')+
                                                 ('names. All participants in the file will be included in the\n')+
                                                 ('correlation matrix.')))

    parser.add_argument(dest='names_file',
                            type=str,
                            metavar='names_file',
                            help=textwrap.dedent(('Text file that contains the names of each region, in the same\n')+
                                                 ('order as the two correlation matrices. One region name on each line.')))

    parser.add_argument(dest='centroids_file',
                            type=str,
                            metavar='centroids_file',
                            help=textwrap.dedent(('Text file that contains the x, y, z coordinates of each region,\n')+
                                                 ('in the same order as the two correlation matrices. One set of three\n')+
                                                 ('coordinates, tab or space delimited, on each line.')))

    parser.add_argument(dest='output_dir',
                            type=str,
                            metavar='output_dir',
                            help=textwrap.dedent(('Location in which to save global and nodal measures for the two groups.')))

    parser.add_argument('--nameA',
                            type=str,
                            metavar='nameA',
                            help=textwrap.dedent(('Name of group A')),
                            default='GroupA')

    parser.add_argument('--nameB',
                            type=str,
                            metavar='nameA',
                            help=textwrap.dedent(('Name of group B')),
                            default='GroupB')

    parser.add_argument('-c', '--cost',
                            type=float,
                            metavar='cost',
                            help=textwrap.dedent(('Cost at which to threshold the matrix.\n')+
                                                 ('  Default: 10.0')),
                            default=10.0)

    parser.add_argument('-n', '--n_perm',
                            type=int,
                            metavar='n_perm',
                            help=textwrap.dedent(('Number of permutations of the data to compare with the real groupings.\n')+
                                                 ('  Default: 1000')),
                            default=1000)

    parser.add_argument('--names_308_style',
                            action='store_true',
                            help=textwrap.dedent(('Include this flag if your names are in the NSPN 308\n')+
                                                 ('parcellation style (which means you have 41 subcortical regions)\n')+
                                                 ('that are still in the names and centroids files and that\n')+
                                                 ('the names are in <hemi>_<DK-region>_<part> format.\n')+
                                                 ('  Default: False')),
                            default=False)

    arguments = parser.parse_args()

    return arguments, parser


def read_in_data(corr_mat_file, names_file, centroids_file, names_308_style):
    '''
    Read in the data from the three input files:
        * corr_mat_file
        * names_file
        * centroids_file
    '''
    # Load the input files
    M = np.loadtxt(corr_mat_file)
    names = [ line.strip() for line in open(names_file) ]
    centroids = np.loadtxt(centroids_file)

    # If you have your names in names_308_style you need to strip the
    # first 41 items
    if names_308_style:
        names = names[41:]
        centroids = centroids[41:,:]

    return M, names, centroids


def write_out_nodal_measures(nodal_dict, centroids, output_dir, corr_mat_file, cost):
    '''
    Write the nodal dictionary into a pandas data frame and then
    save this data frame into a csv file where columns are the nodal measures
    and the rows are each region.
    '''
    # Put the nodal dict into a pandas dataframe
    df = pd.DataFrame(nodal_dict)

    # Add in the centroids
    df['x'] = centroids[:, 0]
    df['y'] = centroids[:, 1]
    df['z'] = centroids[:, 2]

    # Make the output directory if it doesn't exist already
    if not os.path.isdir(output_dir):
        os.path.makedirs(output_dir)

    # Figure out the output file name
    basename_corr_mat_file = os.path.basename(corr_mat_file).strip('.txt')
    output_f_name = os.path.join(output_dir,
                                    'NodalMeasures_{}_COST{:03.0f}.csv'.format(basename_corr_mat_file,
                                                                          cost))

    # Write the data frame out (with the name column first)
    new_col_list = ['name'] + [ col_name for col_name in df.columns if not col_name == 'name' ]
    df.to_csv(output_f_name, columns=new_col_list)


def write_out_global_measures(global_dict, output_dir, corr_mat_file, cost):
    '''
    Write the global dictionary into a pandas data frame and then
    save this data frame into a csv file where columns are the global measures
    and the rows are each of the random networks. Note that this means the
    non-randomised graph measures are the same in every row.

    (If there's a better way to write this out then I'm totally down!)
    '''
    # Put the global dict into a pandas dataframe
    df = pd.DataFrame(global_dict)

    # Make the output directory if it doesn't exist already
    if not os.path.isdir(output_dir):
        os.path.makedirs(output_dir)

    # Figure out the output file name
    basename_corr_mat_file = os.path.basename(corr_mat_file).strip('.txt')
    output_f_name = os.path.join(output_dir,
                                    'GlobalMeasures_{}_COST{:03.0f}.csv'.format(basename_corr_mat_file,
                                                                          cost))

    # Write the data frame out (with the name column first)
    df.to_csv(output_f_name)


def network_analysis_from_corrmat(corr_mat_file,
                                  names_file,
                                  centroids_file,
                                  output_dir,
                                  cost=10,
                                  n_rand=1000,
                                  names_308_style=False):
    '''
    This is the big function!
    It reads in the correlation matrix, thresholds it at the given cost
    (incorporating a minimum spanning tree), creates a networkx graph,
    calculates global and nodal measures (including random comparisons
    for the global measures) and writes them out to csv files.
    '''
    # Read in the data
    M, names, centroids = read_in_data(corr_mat_file,
                                        names_file,
                                        centroids_file,
                                        names_308_style)

    # Make your graph at cost
    G = mkg.graph_at_cost(M, cost)

    # Calculate the modules
    nodal_partition = mkg.calc_nodal_partition(G)

    # Get the nodal measures
    # (note that this takes a bit of time because the participation coefficient
    # takes a while)
    G, nodal_dict = mkg.calculate_nodal_measures(G,
                                                 centroids,
                                                 names,
                                                 nodal_partition=nodal_partition,
                                                 names_308_style=names_308_style)

    # Save your nodal measures
    write_out_nodal_measures(nodal_dict, centroids, output_dir, corr_mat_file, cost)

    # Get the global measures
    # (note that this takes a bit of time because you're generating random
    # graphs)
    R_list, R_nodal_partition_list = mkg.make_random_list(G, n_rand=n_rand)

    global_dict = mkg.calculate_global_measures(G,
                                                R_list=R_list,
                                                nodal_partition=nodal_partition,
                                                R_nodal_partition_list=R_nodal_partition_list)

    # Write out the global measures
    write_out_global_measures(global_dict, output_dir, corr_mat_file, cost)


def create_real_corrmats(regional_measures_file_A,
                            nameA,
                            regional_measures_file_B,
                            nameB,
                            names_file,
                            covars_file,
                            output_dir,
                            names_308_style):
    """
    Create the two real correlation matrices from the original data.
    These will be saved inside the output directory as 'M_[GroupName].txt'
    """
    # Create the real correlation matrices from the real data
    group_dict = { arg.nameA : arg.regional_measures_file_A,
                   arg.nameB : arg.regional_measures_file_B }

    for group_name, f_name in group_dict.items():

        output_name = os.path.join(output_dir, 'CorrMat_{}.txt'.format(group_name))

        corrmat_from_regionalmeasures(f_name,
                                        names_file,
                                        covars_file,
                                        output_name,
                                        names_308_style)

def real_network_measures():
    """
    """


if __name__ == "__main__":

    # Read in the command line arguments
    arg, parser = setup_argparser()

    # Create the real correlation matrices
    create_real_corrmats(arg.regional_measures_file_A,
                                arg.nameA,
                                arg.regional_measures_file_B,
                                arg.nameB,
                                arg.names_file,
                                arg.covars_file,
                                arg.output_dir,
                                arg.names_308_style)

    network_analysis_from_corrmat(arg.corr_mat_file,
                                      arg.names_file,
                                      arg.centroids_file,
                                      arg.output_dir,
                                      cost=arg.cost,
                                      n_rand=arg.n_rand,
                                      names_308_style=arg.names_308_style)

#=============================================================================
# Wooo! All done :)
#=============================================================================
