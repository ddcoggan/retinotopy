#!/usr/bin/python
"""
controller script for running the analysis pipeline
"""
import itertools
import os
import os.path as op
import time
import glob
import json
import shutil
from utils import PROJ_DIR, seconds_to_text

stop_for_checks = False
#os.system('source ~/.bashrc_neuro')

if __name__ == "__main__":

    start = time.time()
    num_procs = 16
    os.chdir(PROJ_DIR)
    """
    # initialise BIDS dataset
    # requires a configured participants.json file and raw data downloaded
    # and unpacked in sourcedata
    from utils import initialise_BIDS
    initialise_BIDS()

    # preprocess data
    from utils import preprocess
    preprocess(num_procs)

    # check anatomical segmentation quality and fix errors
    from utils import check_segmentation
    if stop_for_checks:
        check_segmentation()

    # perform registration
    from utils import registration
    overwrite = []  # ['func_anat', 'anat_std']
    registration(subjects=None, overwrite=overwrite)

    # make ROIs
    from utils import make_ROIs
    make_ROIs(subjects=None, overwrite=False)

    # do prf mapping
    #from utils import estimate_pRFs
    #estimate_pRFs()
    """
    # do some post-processing on maps and convert to surfaces
    from utils import make_surface_maps
    make_surface_maps(overwrite=False)

    # manually make retinotopic ROI labels using create_retinotopy_labels.py

    finish = time.time()
    print(f'analysis took {seconds_to_text(finish - start)} to complete')


