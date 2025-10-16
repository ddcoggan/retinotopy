import os
import os.path as op
from utils.config import PROJ_DIR
import matplotlib as mpl
import numpy as np

subject = 'F019'
session = '7T1'
run = 'mean_before_prf'
hemi = 'lh'
colormap = ['colorwheel', 'red_yellow_green'][0]
fs_subj_dir = f'{os.environ["SUBJECTS_DIR"]}/sub-{subject}'
os.chdir(PROJ_DIR)
run_dir = op.abspath(f'derivatives/pRF/sub-{subject}/ses-{session}/{run}')
surface = f'{fs_subj_dir}/surf/{hemi}.inflated'
overlay = f'{run_dir}/polar_angle_{hemi}.mgh'
#overlay = f'{run_dir}/r2_{hemi}.mgh'
mask = op.abspath(f'derivatives/ROIs/sub-{subject}/ses-{session}/mask_r2_thresh_{hemi}.label')
#mask = op.abspath(f'derivatives/ROIs/sub-{subject}/ses-{session}/mask_analyzed_{hemi}.label')
label = f'{fs_subj_dir}/label/{hemi}.tong.V1.label'
for file in [surface, overlay, mask, label]:
    assert op.isfile(file), f'cannot find {file}'

# colormap where vertical meridians are marked with red (90) and green (270)
if colormap == 'red_yellow_green':
    cmap = (
        '0,255,255,0,'
        '45,255,255,0,'
        '90,255,0,0,'
        '135,255,255,0,'
        '180,255,255,0,'
        '225,255,255,0,'
        '270,0,255,0,'
        '315,255,255,0,'
        '360,255,255,0')

# colorwheel
else:
    colors = np.linspace(0, 1, 37)
    if hemi == 'lh':  # flip colormap as datamap was previously flipped
        colors = -(colors + .5) % 1
    colorwheel = np.hstack((
        np.linspace(0, 360, 37, dtype=int).reshape(-1, 1),
        np.array(mpl.colormaps['hsv'](colors) * 255, int)[:,:-1]))
    cmap = ','.join(
        [','.join([str(i) for i in row]) for row in colorwheel])


# freeview
cmd = (
    f'freeview '
    f'-f {surface}'
    f':overlay={overlay}'
    f':curvature_method=binary'
    f':overlay_custom={cmap}'
    f':overlay_smooth=8'
    f':overlay_mask={mask}'
    f':label={label}'
    f':label_outline=true'
    f':label_color=white'
    f' -layout 1 -viewport 3d')
print(cmd)
os.system(cmd)
