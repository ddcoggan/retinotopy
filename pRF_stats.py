# /usr/bin/python
# Created by David Coggan on 2023 06 28
import os
import os.path as op
import glob
from itertools import product as itp
import nibabel as nib
import matplotlib.pyplot as plt
from scipy.stats import linregress

from config import PROJ_DIR, subjects

R2_THR = 50
MIN_ECCEN = 0.5
PRF_ECCEN = 7
STIM_ECCEN = 4.5

def prf_stats():

    for subject, session in zip(['F019','M015','M015'], ['7T1','7T1','7T2']):
        outdir = f'derivatives/pRF/sub-{subject}/ses-{session}/mean_before_prf'
        roi_dir = f'derivatives/ROIs/sub-{subject}/ses-{session}'
        ref_func = glob.glob(f'derivatives/registration/sub-{subject}/'
                             f'ses-{session}/example_func.nii*')[0]
        reg = (f'derivatives/registration/sub-{subject}/ses-{session}/'
               f'example_func2highres.lta')

        # V1 labels to nifti
        fs_subj_dir = f'{os.environ["SUBJECTS_DIR"]}/sub-{subject}'
        for hemi in ['lh', 'rh']:

            # label should either exist or be created by merging dorsal, ventral
            label = f'{fs_subj_dir}/label/{hemi}.tong.V1.label'
            if not op.isfile(label):
                os.system(f'mri_mergelabels '
                          f'-i {label.replace(".V1.", ".V1d.")} '
                          f'-i {label.replace(".V1.", ".V1v.")} '
                          f'-o {label}')

            # label to nifti
            outpath = f'{roi_dir}/V1_{hemi}.nii.gz'
            if not op.isfile(outpath):
                os.system(
                    f'mri_label2vol '
                    f'--label {label} '
                    f'--temp {ref_func} '
                    f'--reg {reg} '
                    f'--subject sub-{subject} '
                    f'--hemi {hemi} '
                    f'--o {outpath}')

        # combine across hemispheres
        V1s = glob.glob(f'{roi_dir}/V1_?h.nii.gz')
        V1 = f'{roi_dir}/V1.nii.gz'
        if not op.isfile(V1):
            os.system(f'fslmaths {" -add ".join(V1s)} -bin {V1}')

        # get eccentricity, rfsize and r2
        roi = nib.load(V1).get_fdata().flatten()
        eccens_all = (nib.load(f'{outdir}/eccentricity_deg.nii')
                      .get_fdata().flatten())
        sizes_all = (nib.load(f'{outdir}/rfsize_sigma_deg.nii')
                 .get_fdata().flatten())
        r2s = nib.load(f'{outdir}/r2.nii').get_fdata().flatten()

        for max_eccen in [PRF_ECCEN, STIM_ECCEN]:

            # restrict to mask and threshold based on r2
            voxels = (roi > 0) & (r2s > R2_THR) & (eccens_all > MIN_ECCEN) & (
                eccens_all < max_eccen)
            eccens = eccens_all[voxels]
            sizes = sizes_all[voxels]

            # fit linear model to all voxels and plot
            slope, intercept, r_value, p_value, std_err = linregress(eccens, sizes)
            plt.scatter(eccens, sizes, s=2, alpha=.5)
            plt.xlabel('Eccentricity (deg)')
            plt.ylabel('RF SD (deg)')
            plt.title(f'V1 pRFs for {subject} {session}\n'
                      f'intercept: {intercept:.3f}, slope: {slope:.3f}\n'
                      f'minimum r2: {R2_THR/100:.2f}, voxels: {sum(voxels)}\n')
            plt.plot([0, max_eccen], [intercept, intercept + slope*max_eccen], 'r')
            plt.tight_layout()
            plt.savefig(f'{outdir}/pRF_size_by_eccen_{max_eccen:.1f}.png')
            plt.close()

            print(f'{subject} {session} estimated FWHM if line fitted to '
                  f'{max_eccen:.1f} deg:\n'
                  f'\t{(intercept + 1 * slope) * 2.355:.3f} at 1deg\n'
                  f'\t{(intercept + 2 * slope) * 2.355:.3f} at 2deg\n'
                  f'\t{(intercept + 3 * slope) * 2.355:.3f} at 3deg\n'
                  f'\t{(intercept + 4 * slope) * 2.355:.3f} at 4deg\n')


if __name__ == "__main__":
    os.chdir(PROJ_DIR)
    prf_stats()
