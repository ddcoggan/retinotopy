# /usr/bin/python
# Created by David Coggan on 2023 06 28
import os
import os.path as op
import glob
import shutil
import subprocess
import json
from .config import PROJ_DIR


def registration(subjects=None, overwrite=[]):

    print('Performing registration...')

    # default to all subjects
    if subjects is None:
        subjects = json.load(open("participants.json", "r+"))

    for subject, sessions in subjects.items():


        # directories
        fs_dir = f'{os.environ["SUBJECTS_DIR"]}/sub-{subject}'
        xform_dir = f'{fs_dir}/mri/transforms'
        fnirt_dir = f'{fs_dir}/mri/transforms/fnirt'
        os.makedirs(fnirt_dir, exist_ok=True)


        # reference images
        ref_anat = f'{fs_dir}/mri/orig/001.nii'
        ref_anat_brain = f'{fs_dir}/mri/orig/001_brain.nii.gz'
        ref_std = f'{os.environ["FSLDIR"]}/data/standard/MNI152_T1_2mm.nii.gz'
        ref_std_brain = f'{ref_std[:-7]}_brain.nii.gz'
        ref_std_mask = f'{ref_std[:-7]}_brain_mask_dil.nii.gz'


        # transform 1: between standard space and anatomical space
        # this is all done in subject's freesurfer directory

        # freesurfer method
        standard2highres_lta = f'{xform_dir}/reg.mni152.2mm.lta'
        if not op.isfile(standard2highres_lta):
            os.system(f'mni152reg --s sub-{subject}')

        # FSL method

        # make links to reference images
        for in_path, label in zip(
                [ref_anat, ref_std, ref_std_brain],
                ['highres.nii.gz', 'standard_head.nii.gz', 'standard.nii.gz']):
            out_path = f'{fnirt_dir}/{label}'
            if not op.exists(out_path):
                os.system(f'ln -s {in_path} {out_path}')

        # linear
        highres2standard = f'{fnirt_dir}/highres2standard.mat'
        if not op.isfile(highres2standard) or 'anat_std' in overwrite:
            os.system(f'flirt '
                      f'-in {ref_anat} '
                      f'-ref {ref_std} '
                      f'-omat {highres2standard} '
                      f'-cost corratio '
                      f'-dof 12 '
                      f'-searchrx -90 90 '
                      f'-searchry -90 90 '
                      f'-searchrz -90 90 '
                      f'-interp trilinear')
        standard2highres = f'{fnirt_dir}/standard2highres.mat'
        if not op.isfile(standard2highres) or 'anat_std' in overwrite:
            os.system(f'convert_xfm -inverse '
                      f'-omat {standard2highres} '
                      f'{highres2standard}')

        # non-linear
        highres2standard_warp = f'{fnirt_dir}/highres2standard_warp.nii.gz'
        if not op.isfile(highres2standard_warp) or 'anat_std' in overwrite:
            os.system(f'fnirt '
                      f'--in={ref_anat} '
                      f'--ref={ref_std} '
                      f'--refmask={ref_std_mask} '
                      f'--config=T1_2_MNI152_2mm '
                      f'--aff={highres2standard} '
                      f'--cout={highres2standard_warp} '
                      f'--iout={fnirt_dir}/highres2standard_head '
                      f'--jout={fnirt_dir}/highres2highres_jac '
                      f'--warpres=10,10,10')
        standard2highres_warp = f'{fnirt_dir}/standard2highres_warp.nii.gz'
        if not op.isfile(standard2highres_warp) or 'anat_std' in overwrite:
            os.system(f'invwarp '
                      f'-w {highres2standard_warp} '
                      f'-o {standard2highres_warp} '
                      f'-r {ref_anat}')
        
        # apply transform to ref anat
        highres2standard_img = f'{fnirt_dir}/highres2standard.nii.gz'
        if not op.isfile(highres2standard_img) or 'anat_std' in overwrite:
            os.system(f'applywarp '
                      f'-i {ref_anat_brain} '
                      f'-r {ref_std_brain} '
                      f'-o {highres2standard_img} '
                      f'-w {highres2standard_warp}')

        # make reg images
        d = fnirt_dir
        if not op.isfile(f'{d}/highres2standard.png') or 'anat_std' in overwrite:
            slicer_str = (
                f'-x 0.35 {d}/sla.png -x 0.45 {d}/slb.png '
                f'-x 0.55 {d}/slc.png -x 0.65 {d}/sld.png '
                f'-y 0.35 {d}/sle.png -y 0.45 {d}/slf.png '
                f'-y 0.55 {d}/slg.png -y 0.65 {d}/slh.png '
                f'-z 0.35 {d}/sli.png -z 0.45 {d}/slj.png '
                f'-z 0.55 {d}/slk.png -z 0.65 {d}/sll.png')
            append_str = ' + '.join([f'{d}/sl{i}.png' for i in 'abcdefghijkl'])

            cmd = f'slicer {d}/highres2standard {d}/standard -s 2 {slicer_str}'
            subprocess.Popen(cmd.split()).wait()

            cmd = f'pngappend {append_str} {d}/highres2standard1.png'
            subprocess.Popen(cmd.split()).wait()

            cmd = f'slicer {d}/standard {d}/highres2standard -s 2 {slicer_str}'
            subprocess.Popen(cmd.split()).wait()

            cmd = f'pngappend {append_str} {d}/highres2standard2.png'
            subprocess.Popen(cmd.split()).wait()

            cmd = (f'pngappend {d}/highres2standard1.png - '
                   f'{d}/highres2standard2.png {d}/highres2standard.png')
            subprocess.Popen(cmd.split()).wait()

        # clean up
        for search in ['*1.png', '*2.png', 'sl?.png']:
            imgs = glob.glob(f'{d}/{search}')
            for img in imgs:
                os.remove(img)

        # transform 2: between anatomical space and functional space
        for session in sessions:

            reg_dir = f'derivatives/registration/sub-{subject}/{session}'
            os.makedirs(reg_dir, exist_ok=True)

            # put link to everything in local project reg dir
            in_paths = glob.glob(f'{fnirt_dir}/*')
            for path in in_paths:
                out_path = f'{reg_dir}/{op.basename(path)}'
                if not op.exists(out_path):
                    os.system(f'ln -s {path} {out_path}')

            method = 'FSL'  # some subjects may do better with freesurfer method

            # reference images
            if not len(glob.glob(f'{reg_dir}/example_func.nii*')):
                # try using funcNoEPI
                ref_func = (f'sub-{subject}/{session}/fmap/sub-{subject}_{session}_'
                            f'acq-funcNoEPI_magnitude.nii')
                if op.isfile(ref_func):
                    out_path = f'{reg_dir}/example_func.nii'
                    os.system(f'ln -s {op.abspath(ref_func)} {out_path}')
                # otherwise the mean of the middle func scan
                else:
                    func_scans = sorted(glob.glob('derivatives/fmriprep-*/'
                        f'sub-{subject}/{session}/func/*bold.nii*'))
                    func_scan = func_scans[len(func_scans) // 2]
                    out_path = f'{reg_dir}/example_func.nii.gz'
                    os.system(f'fslmaths {func_scan} -Tmean {out_path}')
            ref_func = out_path

            # make freesurfer reg for surface maps
            lta = f'{reg_dir}/example_func2highres.lta'
            if not op.isfile(lta) or 'func_anat' in overwrite:
                os.system(f'bbregister '
                          f'--s sub-{subject} '
                          f'--mov {ref_func} '
                          f'--init-fsl '
                          f'--lta {lta} '
                          f'--bold')

            if method == 'FSL':

                example_func2highres = f'{reg_dir}/example_func2highres.mat'
                if not op.isfile(example_func2highres) or 'func_anat' in overwrite:

                    # BBR
                    os.system(
                        f'epi_reg '
                        f'--epi={ref_func} '
                        f'--t1={ref_anat} '
                        f'--t1brain={ref_anat_brain} '
                        f'--out={example_func2highres[:-4]}')

                    # linear search
                    # os.system(f'flirt -in {ref_anat_brain} -ref {ref_func}
                    #     -omat {highres2example_func}')

                highres2example_func = f'{reg_dir}/highres2example_func.mat'
                if not op.isfile(highres2example_func) or 'func_anat' in overwrite:
                    os.system(f'convert_xfm '
                              f'-omat {highres2example_func} '
                              f'-inverse '
                              f'{example_func2highres}')


            elif method == 'freesurfer':

                example_func2highres = f'{reg_dir}/example_func2highres.mat'
                if not op.isfile(example_func2highres) or 'func_anat' in overwrite:
                    os.system(f'lta_convert '
                              f'--inlta {lta} '
                              f'--outfsl {example_func2highres} '
                              f'--src {ref_func} '
                              f'--trg {ref_anat}')

                lta_inv = f'{reg_dir}/highres2example_func.lta'
                if not op.isfile(lta_inv) or 'func_anat' in overwrite:
                    os.system(f'lta_convert '
                              f'--inlta {lta} '
                              f'--outlta {lta_inv} '
                              f'--invert')

                highres2example_func = f'{reg_dir}/highres2example_func.mat'
                if not op.isfile(highres2example_func) or 'func_anat' in overwrite:
                    os.system(f'lta_convert '
                              f'--inlta {lta_inv} '
                              f'--outfsl {highres2example_func} '
                              f'--src {ref_anat} '
                              f'--trg {ref_func}')

            # make reg images
            d = reg_dir
            if (not op.isfile(f'{d}/example_func2highres.png') or 'func_anat' in
                    overwrite):
                slicer_str = (
                    f'-x 0.35 {d}/sla.png -x 0.45 {d}/slb.png '
                    f'-x 0.55 {d}/slc.png -x 0.65 {d}/sld.png '
                    f'-y 0.35 {d}/sle.png -y 0.45 {d}/slf.png '
                    f'-y 0.55 {d}/slg.png -y 0.65 {d}/slh.png '
                    f'-z 0.35 {d}/sli.png -z 0.45 {d}/slj.png '
                    f'-z 0.55 {d}/slk.png -z 0.65 {d}/sll.png')
                append_str = ' + '.join(
                    [f'{d}/sl{i}.png' for i in 'abcdefghijkl'])

                cmd = f'slicer {d}/example_func2highres {d}/highres -s 2 {slicer_str}'
                subprocess.Popen(cmd.split()).wait()

                cmd = f'pngappend {append_str} {d}/example_func2highres1.png'
                subprocess.Popen(cmd.split()).wait()

                cmd = (f'slicer {d}/highres {d}/example_func2highres -s 2'
                       f' {slicer_str}')
                subprocess.Popen(cmd.split()).wait()

                cmd = f'pngappend {append_str} {d}/example_func2highres2.png'
                subprocess.Popen(cmd.split()).wait()

                cmd = (f'pngappend {d}/example_func2highres1.png - '
                       f'{d}/example_func2highres2.png {d}/example_func2highres.png')
                subprocess.Popen(cmd.split()).wait()


if __name__ == "__main__":

    import json
    overwrite = []  # ['func_anat', 'anat_std', 'func_std']
    os.chdir(PROJ_DIR)
    registration(None, overwrite)
