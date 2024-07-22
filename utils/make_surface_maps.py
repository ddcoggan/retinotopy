import os
import os.path as op
import glob
import nibabel as nib
import numpy as np
import shutil


def make_surface_maps(overwrite=False):

    prf_dirs = sorted(glob.glob('derivatives/pRF/sub-*/*/mean_before_prf'))
    prf_dirs = [d for d in prf_dirs if op.isfile(f'{d}/r2.nii')]
    parameters = ['polar_angle', 'eccentricity_deg', 'rfsize_sigma_deg', 'r2']
    for prf_dir in prf_dirs:

        # get subject and session
        subject = prf_dir.split('/')[2].split('-')[1]
        session = prf_dir.split('/')[3]
        reg = (f'derivatives/registration/sub-{subject}/'
               f'{session}/example_func2highres.lta')
        roi = (f'derivatives/ROIs/sub-{subject}/{session}/'
               f'mask_analyzed.nii.gz')

        # for left hemisphere, any smoothing in the polar angle map will
        # cause issues where the map wraps around the 0/360 degree boundary.
        # Flip the map so the boundary moves to the left horizontal meridian
        ang_reverse = f'{prf_dir}/polar_angle_flip.nii.gz'
        if not os.path.isfile(ang_reverse) or overwrite:
            os.system(f'fslmaths {prf_dir}/polar_angle.nii '
                      f'-mul -1 -add 540 -rem 360 -mul {roi} {ang_reverse}')

        # copy hdr from example func so they align
        for parameter in parameters + ['polar_angle_flip']:
            example_func = glob.glob(f'derivatives/registration/sub-{subject}/'
                            f'{session}/example_func.nii*')[0]
            nii = glob.glob(f'{prf_dir}/{parameter}.nii*')[0]
            os.system(f'fslcpgeom {example_func} {nii}')

        # convert  to surface
        for parameter in parameters:
            for hemi in ['lh','rh']:

                if parameter == 'polar_angle' and hemi == 'lh':
                    nifti = f'{prf_dir}/polar_angle_flip.nii.gz'
                else:
                    nifti = f'{prf_dir}/{parameter}.nii'

                surface = f'{prf_dir}/{parameter}_{hemi}.mgh'
                if not op.isfile(surface) or overwrite:
                    os.system(
                        f'mri_vol2surf --mov {nifti} --out {surface} '
                        f'--reg {reg} --hemi {hemi} --interp nearest')

if __name__ == "__main__":
    make_surface_maps()