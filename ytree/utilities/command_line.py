"""
ytree command line interface



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import argparse
import ytree
import pprint

def statistics(args):
    arbor = ytree.load(args.arbor_file)
    return { 'box_size': arbor.box_size,
             'omega_lambda': arbor.omega_lambda,
             'omega_matter': arbor.omega_matter,
             'tree_count': arbor.trees.size,
             'field_list': arbor.field_list,
             'derived_field_list': arbor.derived_field_list }

def tree_info(args):
    arbor = ytree.load(args.arbor_file)
    if args.tree_id == -1:
        return arbor[args.field]
    tree = arbor[args.tree_id]
    return tree[args.field]

def main():
    parser = argparse.ArgumentParser(description='Compute things on ytree arbors')
    # We'll need a subparser here eventually

    subparsers = parser.add_subparsers()

    stats_parser = subparsers.add_parser("info",
            help="Statistics on the arbor")
    stats_parser.set_defaults(func = statistics)
    stats_parser.add_argument('arbor_file', help="the merger tree collection")

    tree_info_parser = subparsers.add_parser("tree_info",
            help="Get info on a specific tree")
    tree_info_parser.set_defaults(func = tree_info)
    tree_info_parser.add_argument('arbor_file', help="the merger tree collection")
    tree_info_parser.add_argument('tree_id', type=int, default = -1,
            help="which trees to examine; -1 for all")
    tree_info_parser.add_argument('field', type=str, default="mass",
            help="which field to return")

    args = parser.parse_args()
    pprint.pprint(args.func(args))

if __name__ == "__main__":
    main()
