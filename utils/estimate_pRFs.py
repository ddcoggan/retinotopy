# /usr/bin/python
# Created by David Coggan on 2023 06 28
import os
import os.path as op
import matlab.engine
import glob
from . import PROJ_DIR, subjects, MSTR_DIR, scan_params

def prf(func, mask, out_dir, TR, remove_outliers, stim):
    eng = matlab.engine.start_matlab()
    eng.addpath(f'{MSTR_DIR}/fMRI')
    eng.addpath(eng.genpath(f'/home/tonglab/david/repos/analyzePRF'))
    eng.addpath(eng.genpath(f'/home/tonglab/david/repos/mrTools-4.8.0.0'))
    eng.analyzePRF_call(
        func, mask, out_dir, TR, remove_outliers, stim, nargout=0)
    eng.quit()


def estimate_pRFs():

    print('Estimating pRFs...')
    TR = scan_params['retinotopy']['TR']
    for subject, sessions in subjects.items():
        stim = 'wedge_ring' if subject != 'F019' else 'multibar'
        for session in sessions:

            mask = (f'derivatives/ROIs/sub-{subject}/{session}/'
                    f'mask_analyzed.nii.gz')
            ref_func = glob.glob(f'derivatives/registration/sub-{subject}/'
                        f'{session}/example_func.nii*')[0]
            sess_dir = f'derivatives/pRF/sub-{subject}/{session}'
            os.makedirs(sess_dir, exist_ok=True)

            # get timeseries, ensure alignment to ref func and no drift
            funcs = sorted(glob.glob(
                f'derivatives/fmriprep-*/sub-{subject}/'
                f'{session}/func/*task-retinotopy*bold.nii*'))
            for func in funcs:
                run = func.split('_')[-3]
                func_local = f'{sess_dir}/timeseries_{run}.nii.gz'
                if not op.isfile(func_local):
                    # align run to reference functional volume
                    os.system(f'mcflirt -in {func} -reffile {ref_func} -out '
                              f'{func_local}')
                    # linear trend removal
                    tmean = f'{func_local.replace(".nii", "_tmean.nii")}'
                    os.system(f'fslmaths {func_local} -Tmean {tmean}')
                    os.system(f'fslmaths {func_local} -bptf 60 -1 '
                              f'-add {tmean} -nan {func_local}')
                    os.remove(tmean)
            """
            # analyze separately for each run
            funcs = sorted(glob.glob(f'{sess_dir}/timeseries_run*.nii.gz'))
            funcs = [op.abspath(f) for f in funcs]
            if not op.isfile(f'{sess_dir}/prfs.mat'):
                prf(funcs, mask, sess_dir, TR, True, stim)
            """
            # analyze mean timeseries across all runs in session
            out_dir = f'{sess_dir}/mean_before_prf'
            os.makedirs(out_dir, exist_ok=True)
            func = f'{out_dir}/timeseries.nii.gz'
            if not op.isfile(func):
                funcs = glob.glob(f'{sess_dir}/timeseries_run-*.nii.gz')
                os.system(f'fslmaths {" -add ".join(funcs)} -div '
                          f'{len(funcs)} {func}')
            if not op.isfile(f'{out_dir}/prfs.mat'):
                prf([func], mask, out_dir, TR, True, stim)
            """
            # analyze concatenated timeseries across all runs in session
            out_dir = f'{sess_dir}/concatenated_before_prf'
            os.makedirs(out_dir, exist_ok=True)
            func_concat = f'{out_dir}/timeseries.nii.gz'
            if not op.isfile(func_concat):

                # get mean func across all runs
                mean_func_all = f'{out_dir}/timeseries_all_mean.nii.gz'
                os.system(f'fslmaths '
                          f'{sess_dir}/mean_before_prf/timeseries.nii.gz '
                          f'-Tmean {mean_func_all}')

                # replace the mean func of each run with mean func of all runs
                funcs = sorted(glob.glob(f'{sess_dir}/timeseries_run-*.nii.gz'))
                for func in funcs:
                    mean_func = func.replace(sess_dir, out_dir)
                    mean_func = mean_func.replace('.nii.gz', '_mean.nii.gz')
                    os.system(f'fslmaths {func} -Tmean {mean_func}')
                    demeaned_func = mean_func.replace('_mean', '_demeaned')
                    os.system(f'fslmaths {func} -sub {mean_func} {demeaned_func}')
                    remeaned_func = demeaned_func.replace('demean', 'remean')
                    os.system(f'fslmaths {demeaned_func} -add {mean_func_all} '
                              f'{remeaned_func}')
                remeaned_funcs = sorted(glob.glob(
                    f'{out_dir}/timeseries_*_remeaned.nii.gz'))
                os.system(f'fslmerge -t {func_concat} {" ".join(remeaned_funcs)}')
                files_to_remove = glob.glob(f'{out_dir}/timeseries_*.nii.gz')
                for f in files_to_remove:
                    os.remove(f)
                if not op.isfile(f'{out_dir}/prfs.mat'):
                    prf([func_concat], mask, out_dir, TR, True, stim)
                """

if __name__ == "__main__":
    os.chdir(PROJ_DIR)
    estimate_pRFs()
