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
        roi_dir = f'derivatives/ROIs/sub-{subject}/{session}'
        roi = f'{roi_dir}/mask_analyzed.nii.gz'

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

        # convert to surface
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

        # make label to mask out unanalyzed or low r2 voxels
        thresh = 10
        roi_r2_thresh = f'{roi_dir}/mask_r2_thresh.nii.gz'
        if not op.isfile(roi_r2_thresh) or overwrite:
            r2 = f'{prf_dir}/r2.nii'
            os.system(f'fslmaths {r2} -nan -thr {thresh} -bin {roi_r2_thresh}')# -mul {roi}

        # convert to labels
        for hemi in ['lh','rh']:
            surface = roi_r2_thresh.replace('.nii.gz', f'_{hemi}.mgh')
            if not op.isfile(surface) or overwrite:
                print('Converting cortex mask to surface label...')
                os.system(
                    f'mri_vol2surf --mov {roi_r2_thresh} '
                    f'--out {surface} --reg {reg} '
                    f'--hemi {hemi} --interp nearest')
            label = surface.replace('.mgh', '.label')
            if not op.isfile(label) or overwrite:
                os.system(f'mri_cor2label --i {surface} '
                          f'--surf sub-{subject} {hemi} --id 1 --l {label}')

if __name__ == "__main__":
    make_surface_maps()