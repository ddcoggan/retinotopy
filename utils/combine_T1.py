# /usr/bin/python
# Created by David Coggan on 2024 07 08

import os
import glob

subject = 'F016'

#anatomicals = [
#    '/home/tonglab/david/projects/p019_objectSpace/data/fMRI/individual/F016'
#    '/210317/rawData/Tong_341863.06.01.10-25-32.WIP_T1_LGN_SENSE.01.nii',
#    '/home/tonglab/david/projects/p013_retinotopyTongLab/sourcedata/sub-F016'
#    '/ses-7T1/raw_data/Tong_341844.06.01.13-25-23.WIP_T1_LGN_SENSE.01.nii']
#anat0_flirt = 'anat2_F016_flirt.nii.gz'
#os.system(f'flirt -in {anatomicals[0]} -ref {anatomicals[1]} -out
# {anat0_flirt}')
out_path = 'anat_avg.nii.gz'
#os.system(f'fslmaths {anat0_flirt} -add {anatomicals[1]} -div 2 {out_path}')
os.system(f'recon-all -i {out_path} -s sub-F016-avg -threads 12 -all')
