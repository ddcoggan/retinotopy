# /usr/bin/python
# Created by David Coggan on 2023 06 28
import os
import os.path as op
import glob
import json
import shutil
from .config import PROJ_DIR
from .get_wang_atlas import get_wang_atlas


def make_ROIs(subjects=None, overwrite=False):

    print('Making ROIs...')

    if subjects is None:
        from .config import subjects
        
    # get set of posterior cortical voxels to analyse in each subject
    for subject, sessions in subjects.items():

        fs_subj = f'sub-{subject}'
        fs_subj_dir = f'{os.environ["SUBJECTS_DIR"]}/{fs_subj}'
        reg_dir = f'derivatives/registration/sub-{subject}'

        ref_anat = f'{fs_subj_dir}/mri/orig/001.nii'

        # get retinotopy estimates from public atlas
        get_wang_atlas(fs_subj)  # automatically skips if done

        # make bilateral cortical ribbon nifti in freesurfer directory
        for hemi in ['lh', 'rh']:

            # cortex mgz to nifti
            mgz_fs = f'{fs_subj_dir}/mri/{hemi}.ribbon.mgz'
            mgz_native = f'{fs_subj_dir}/mri/orig/{hemi}.ribbon.mgz'
            ref_anat_mgz = f'{fs_subj_dir}/mri/orig/001.mgz'
            nii = f'{fs_subj_dir}/mri/orig/{hemi}.ribbon.nii.gz'
            if not os.path.exists(nii) or overwrite:
                print(
                    f'Converting {hemi} cortex from fs to native space...')
                os.system(f'mri_vol2vol '
                          f'--mov {mgz_fs} '
                          f'--targ {ref_anat_mgz} '
                          f'--regheader '
                          f'--o {mgz_native} '
                          f'--nearest '
                          f'--no-save-reg')
                print(f'Converting {hemi} cortex from mgz to nifti...')
                os.system(f'mri_convert '
                          f'--in_type mgz '
                          f'--out_type nii '
                          f'-rt nearest '
                          f'{mgz_native} {nii}')

        cortex_highres = f'{fs_subj_dir}/mri/orig/bi.ribbon.nii.gz'
        if not op.isfile(cortex_highres) or overwrite:
            print(f'Combining left and right hemispheres...')
            os.system(
                f'fslmaths {fs_subj_dir}/mri/orig/lh.ribbon.nii.gz -add'
                f' {fs_subj_dir}/mri/orig/rh.ribbon.nii.gz'
                f' -bin {cortex_highres}')


        # create ROI masks in retinotopy project directory
        mask_dir = f'derivatives/ROIs/sub-{subject}'
        anat_dir = f'{mask_dir}/anat_space'
        os.makedirs(anat_dir, exist_ok=True)
        # make links to reference anat image
        cortex_anat = f'{anat_dir}/cortex.nii.gz'
        if not op.isfile(cortex_anat):
            os.system(f'ln -s {op.abspath(cortex_highres)} {cortex_anat}')

        for session in sessions:

            ref_func = glob.glob(f'{reg_dir}/{session}/example_func.nii*')[0]
            reg = f'{reg_dir}/{session}/example_func2highres.lta'
            func_dir = f'{mask_dir}/{session}'
            os.makedirs(func_dir, exist_ok=True)

            # get cortex in func space, with trilinear interpolation
            cortex_func = f'{func_dir}/cortex.nii.gz'
            if not op.isfile(cortex_func) or overwrite:
                print('Transforming cortex mask to functional space...')
                highres2example_func = (
                    f'{reg_dir}/{session}/highres2example_func.mat')
                os.system(f'flirt -in {cortex_anat} -ref {ref_func} '
                          f'-out {cortex_func} -applyxfm '
                          f'-init {highres2example_func}')
                os.system(f'fslmaths {cortex_func} -bin {cortex_func}')


            # make mask of voxels to be analysed by setting y-axis cutoff
            mask = f'{func_dir}/mask_analyzed.nii.gz'
            if not os.path.exists(mask):
                os.system(
                    f'fslmaths {cortex_func} -roi 0 -1 0 33 0 -1 0 1 {mask}')

            # convert to surface label
            for hemi in ['lh', 'rh']:
                surface = mask.replace('.nii.gz', f'_{hemi}.mgh')
                if not op.isfile(surface) or overwrite:
                    print('Converting cortex mask to surface label...')
                    os.system(
                        f'mri_vol2surf --mov {mask} '
                        f'--out {surface} --reg {reg} '
                        f'--hemi {hemi} --interp nearest')
                label = surface.replace('.mgh', '.label')
                if not op.isfile(label):
                    os.system(f'mri_cor2label --i {surface} '
                              f'--surf sub-{subject} {hemi} --id 1 --l {label}')


            # ROI plots
            plot_dir = f'derivatives/ROIs/plots'
            os.makedirs(plot_dir, exist_ok=True)
            for space, ref, mask_path in zip(
                    ['anat', 'func', 'mask'],
                    [ref_anat, ref_func, ref_func],
                    [cortex_anat, cortex_func, mask]):
                plot_file = (f'{plot_dir}/sub-{subject}_'
                             f'{session}_{space}_cortex.png')
                if not op.isfile(plot_file) or overwrite:
                    ref_range = os.popen(f'fslstats {ref} -R')
                    ref_max = float(ref_range.read().split()[1])
                    coords = (os.popen(f'fslstats {mask_path} -C')
                        .read()[:-2].split(' '))
                    coords = [int(float(c)) for c in coords]
                    cmd = f'fsleyes render --outfile {plot_file} --size 3200 ' \
                          f'600 --scene ortho --autoDisplay -vl {coords[0]} ' \
                          f'{coords[1]} {coords[2]} ' \
                          f'{ref} -dr 0 {ref_max} {mask_path} -dr 0 1 -cm ' \
                          f'greyscale'
                    os.system(cmd)

            # make links to reference anat image
            local_anat = f'{mask_dir}/anat_space/ref_anat.nii'
            if op.exists(local_anat) and overwrite:
                os.remove(local_anat)
            if not op.exists(local_anat):
                os.system(f'ln -s {op.abspath(ref_anat)} {local_anat}')

            # make links to reference func image
            local_func = f'{func_dir}/ref_func.nii'
            if op.exists(local_func) and overwrite:
                os.remove(local_func)
            if not op.exists(local_func):
                os.system(f'ln -sf {op.abspath(ref_func)} {local_func}')

            # native func brain mask
            mask_path = f'{func_dir}/brain_mask.nii.gz'
            if not op.exists(mask_path):
                if not op.isfile(mask_path):  # or overwrite:
                    os.system(f'mri_synthstrip -i {ref_func} -m {mask_path}')# -g')


if __name__ == "__main__":

    overwrite = False

    os.chdir(PROJ_DIR)
    subjects = json.load(open("participants.json", "r+"))
    for subject in subjects:
        make_ROIs(overwrite, subject)
