# /usr/bin/python
# Created by David Coggan on 2023 06 23
import os
import os.path as op
import json
import glob
import shutil
import pandas as pd


def preprocess(num_procs=8):

    subjects = json.load(open("participants.json", "r+"))
    print('Preprocessing data...')

    # mriqc (data quality measures)
    version="22.0.6"
    indir = op.abspath("")
    outdir = op.abspath(f'derivatives/mriqc-{version}')
    os.makedirs(outdir, exist_ok=True)
    cmd = f"docker run --rm " \
          f"--mount type=bind,src={indir},dst=/data " \
          f"--mount type=bind,src={outdir},dst=/out " \
          f"--memory=32g " \
          f"--memory-swap=32g " \
          f"nipreps/mriqc:{version} " \
          f"--nprocs {num_procs} " \
          f"--verbose-reports " \
          f"/data /out "

    # individual subjects
    new_subjects = False
    for subject in subjects:
        if not op.isdir(f"{outdir}/sub-{subject}"):
            os.system(cmd + f'participant --participant-label {subject}')
            new_subjects = True

    # group level
    if not os.path.isfile(f"{outdir}/group_bold.html") or new_subjects:
        os.system(cmd + 'group')

    # fmriprep (preprocessing)

    # These are performed on individual basis as fmriprep does not check which
    # subjects are already processed
    # TODO: allow to run these in parallel if > 16 available cores, with 8
    #  cores per subject
    # https://fmriprep.org/en/stable/faq.html#running-subjects-in-parallel
    indir = op.abspath("")  # change to a derivative dataset as required,
    # e.g. "derivatives/NORDIC"
    version = "23.2.3"
    outdir = op.abspath(f"derivatives/fmriprep-{version}")
    os.makedirs(outdir, exist_ok=True)
    fs_subjs_dir = os.environ['SUBJECTS_DIR']
    workdir = op.abspath(f"derivatives/fmriprep_work")
    os.makedirs(workdir, exist_ok=True)
    for subject in subjects:
        if not op.isdir(f"{outdir}/sub-{subject}"):
            #derivatives_prev = glob.glob(  # reuse previous fmriprep output
            #    f'/mnt/HDD2_16TB/projects/p022_occlusion/in_vivo/fMRI'
            #    f'/exp?/derivatives/fmriprep-23.0.2/sub-{subject}')[
            #    0])))[0].split('/fmriprep')[0]
            cmd = f"docker run --rm " \
                  f"--mount type=bind,src={indir},dst=/data " \
                  f"--mount type=bind,src={outdir},dst=/out " \
                  f"--mount type=bind,src={fs_subjs_dir},dst=/fs_subjects " \
                  f"--mount type=bind,src={workdir},dst=/work " \
                  f"--memory=32g " \
                  f"--memory-swap=64g " \
                  f"nipreps/fmriprep:{version} " \
                  f"/data /out participant " \
                  f"-w /work " \
                  f"--clean-workdir " \
                  f"--nprocs {num_procs} " \
                  f"--mem-mb 64000 " \
                  f"--fs-license-file /fs_subjects/license.txt " \
                  f"--fs-subjects-dir /fs_subjects " \
                  f"--output-spaces func " \
                  f"--participant-label {subject}"
            os.system(cmd)

    shutil.rmtree(workdir)

    # final steps
    for subject in subjects:

        # convert anatomicals to nifti and extract brain
        # (final preprocessed anatomical and original anatomical)
        fs_dir = f'{os.environ["SUBJECTS_DIR"]}/sub-{subject}'
        for mgz in [f'{fs_dir}/mri/T1.mgz', f'{fs_dir}/mri/orig/001.mgz']:

            # convert to nifti
            nii = f'{mgz[:-4]}.nii'
            if not op.isfile(nii):
                os.system(f'mri_convert {mgz} {nii}')

            # extract brain
            nii_brain = f'{mgz[:-4]}_brain.nii.gz'
            if not op.isfile(nii_brain):
                os.system(f'mri_synthstrip -i {nii} -o {nii_brain}')# -g')
