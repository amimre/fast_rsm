#!/usr/bin/env python3
"""
A simple command line program that takes a single image and maps it to
reciprocal space.
"""

# pylint: disable=invalid-name

import argparse
import os
from datetime import datetime

import numpy as np

from diffraction_utils import I07Nexus, Frame
from fast_rsm.scan import Scan
import argparse
import os
from yaml import load, dump, Loader
from pathlib import Path

if __name__ == "__main__":

    HELP_STR = (
        "Takes in configuration settings from YAML file and uses it\n"
        "to create job, then sends this job to the cluster."
    )
    parser = argparse.ArgumentParser(description=HELP_STR)

    HELP_STR = (
        "Path to the YAML file with configuration settings. "
    )
    parser.add_argument("-y", "--yaml_path", help=HELP_STR)

    HELP_STR = (
        "Path to the template job file. "
    )
    parser.add_argument("-t", "--template_path", help=HELP_STR)
    
    HELP_STR = (
        "Scan numbers to be mapped into one reciprocal volume"
    )
    parser.add_argument("-s", "--scan_nums", help=HELP_STR, type=int)

    HELP_STR = (
        "Path to the directory for saving output files to. "
    )
    parser.add_argument("-o", "--out_path", help=HELP_STR)

    # Extract the arguments from the parser.
    args = parser.parse_args()

    y_file = open(args.yaml_path, 'r', encoding='utf-8')
    recipe = load(y_file, Loader=Loader)
    y_file.close()

    EXP_N=recipe['visit']['experiment_number']
    YEAR=recipe['visit']['year']#
    SCANS=args.scan_nums
    OUTDIR=args.out_path

    yaml_file=r"testconfig.yaml"
    y_file = open(yaml_file, 'r', encoding='utf-8')
    recipe = load(y_file, Loader=Loader)
    y_file.close()

    i=1
    save_file_name = f"job_scan_{SCANS[0]}_{i}.py"
    save_path = Path(OUTDIR)/Path(save_file_name)
    # Make sure that this name hasn't been used in the past.
    while (os.path.exists(str(save_path))):
        i += 1
        save_file_name = f"job_scan_{SCANS[0]}_{i}.py"
        save_path = Path(OUTDIR)/Path(save_file_name)
        if i > 1e7:
            raise ValueError(
                "naming counter hit limit therefore exiting ")
    f=open(args.template_path)
    lines=f.readlines()
    f.close()
    f=open(save_path,'w')
    for line in lines:
        if '$' in line:
            phrase=line[line.find('$'):line.find('}')+1]
            outphrase=phrase.strip('$').strip('{').strip('}')
            outline=line.replace(phrase,str(locals()[f'{outphrase}']))
            print(outline)
            f.write(outline)
        else:
            f.write(line)
    f.close()



