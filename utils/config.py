# /usr/bin/python
"""
Created by David Coggan on 2023 02 14
Contains variables and functions that are useful across fMRI experiments
"""

import json

PROJ_DIR = 'data'

# subjects
subjects = json.load(open(f'{PROJ_DIR}/participants.json', 'r+'))

# scanning parameters
scan_params = {
    'retinotopy': {'TR': 2, 'dynamics': 150},
    'restingState': {'TR': 2, 'dynamics': 60}}

FEAT_designs = {
    'base': {  # common to all FEAT analyses
        # misc
        'version': 6.00,  # FEAT version
        'inmelodic': 0,  # Are we in MELODIC?'
        'relative_yn': 0,  # Use relative filenames'
        'help_yn': 1,  # Balloon help
        'featwatcher_yn': 0,  # Run Featwatcher
        'brain_thresh': 10,  # Brain/background threshold, %
        'critical_z': 5.3,
        'noise': 0.66,  # Noise level
        'noisear': 0.34,  # Noise AR(1):
        'tagfirst': 1,
        'reginitial_highres_yn': 0,
        'init_init_highres': '\"\"',
        'overwrite_yn': 0,
    },
    'runwise': {
        # main
        'level': 1,  # First or higher-level analysis
        'analysis': 7,  # Which stages to run (7=full first level)
        # data
        'ndelete': 0,  # Delete volumes
        'dwell': 0.52,  # dwell time
        'te': 25, # echo time (ms):
        'totalVoxels': 76744192,
        # prestats
        'alternateReference_yn': 1,
        'regunwarp_yn': 0,  # B0 unwarping
        'unwarp_dir': 'y',  # B0 unwarp direction
        'filtering_yn': 1,  # Carry out pre-stats processing?
        'bet_yn': 0,  # brain extraction
        'smooth': 0,  # spatial smoothing
        'norm_yn': 0,  # Intensity normalization
        'perfsub_yn': 0,  # Perfusion subtraction
        'temphp_yn': 1,  # Highpass temporal filtering
        'paradigm_hp': 100,  # Highpass temporal filtering cutoff
        'templp_yn': 0,  # Lowpass temporal filtering
        'tagfirst': 1,  # Perfusion tag/control order
        'melodic_yn': 0,  # MELODIC ICA data exploration
        # registration
        'reginitial_highres_yn': 0,  # Reg to initial structural
        'reghighres_yn': 0,
        'regstandard_yn': 0,
        'regstandard': '"/usr/local/fsl/data/standard/MNI152_T1_2mm_brain"',
        'regstandard_search': 90,
        'regstandard_dof': 6,
        'regstandard_nonlinear_yn': 0,
        'regstandard_nonlinear_warpres': 10,
        # stats
        'stats_yn': 1,  # Carry out main stats?
        'mixed_yn': 2,  # Mixed effects/OLS
        'prewhiten_yn': 1,  # Carry out prewhitening?'
        'evs_vox': 0,  # Number of EVs
        'con_mode_old': 'orig',  # Contrast & F-tests mode
        'con_mode': 'orig',  # Contrast & F-tests mode
        'nftests_orig': 0,  # Number of F-tests
        'nftests_real': 0,  # Number of F-tests
        # post-stats
        'poststats_yn': 0,  # Carry out post-stats steps?
        'thresh': 0,
        'conmask_zerothresh_yn': 0,  # Contrast masking
        'conmask1_1': 0,  # Do contrast masking at all?
    },
}

