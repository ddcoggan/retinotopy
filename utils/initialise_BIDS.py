# /usr/bin/python
# Created by David Coggan on 2022 11 02
"""
prepares directory structure and extracts/copies raw data from sourcedata
For future projects, try to use dcm2bids (https://andysbrainbook.readthedocs.io/en/latest/OpenScience/OS/BIDS_Overview.html)
"""

import os
import os.path as op
import sys
import glob
import shutil
import json
import time
import nibabel as nib
from .seconds_to_text import seconds_to_text
from .philips_slice_timing import philips_slice_timing
from .make_anat_slices import make_anat_slices
from .config import PROJ_DIR

def orient_func(func: str = None):

    """
    Reorients raw data in nifti file (in place) by a left-right flip, if header
    states orientation is 'Left-to-Right'.
    Different acquisitions can arrive in different orientations, e.g. at
    3T we get a Right-to-Left and at 7T we get a Left-to-Right acquisition.
    This is not an issue for FSL tools, as this information is stored in the
    file header, but any tool which looks at the raw data will need it
    oriented identically across 3T and 7T.
    WARNING: After fslswapdim, the 'Left-to-Right' signature will still be in
    the file header, but the stored data will be reoriented and the orientation
    matrix will be flipped (which is less preferable than renaming the
    orientation as 'Right-to-Left' but at least keeps the header accurate).

    Args:
        func (str): path to functional image to be reoriented
    """

    func_orient = os.popen(f'fslhd {func} | grep "qform_xorient"').read()
    if 'Left-to-Right' in func_orient:
        os.system(f'fslswapdim {func} -x y z {func}')

def initialise_BIDS():

    print(f"Initializing BIDS...")
    subjects = json.load(open(f"participants.json", "r+"))
    for subject, sessions in subjects.items():
        for session, session_info in sessions.items():

            filetypes = ["nii","json"] # do not include other filetypes that may cause BIDS errors
            sourcedir = f"sourcedata/sub-{subject}/{session}/raw_data"
            sessID = session_info["sessID"]

            # detect DICOM or NIFTI format for raw data
            if len(glob.glob(f"{sourcedir}/*.DCM")): # if DICOM format
                os.system(f"dcm2niix {op.abspath(sourcedir)}")  # convert
                copy_or_move = shutil.move  # move files, don't copy
            else: # if NIFTI format
                copy_or_move = shutil.copy  # copy files, don't move


            ### ANAT ###
            anatscan = session_info["anat"]
            if anatscan is not None:

                anatdir = f"sub-{subject}/{session}/anat"
                os.makedirs(anatdir, exist_ok=True)

                # json file
                files = glob.glob(f"{sourcedir}/*{sessID}.{anatscan:02}*.json")
                assert len(files) == 1
                inpath = files[0]
                outpath = f"{anatdir}/sub-{subject}_{session}_T1w.json"
                if not op.isfile(outpath):
                    copy_or_move(inpath, outpath)

                # nii file
                files = glob.glob(f"{sourcedir}/*{sessID}.{anatscan:02}*.nii")
                assert len(files) == 1
                inpath = files[0]

            else:

                anat_ses = 'anat'
                anatdir = f"sub-{subject}/ses-{anat_ses}/anat"
                os.makedirs(anatdir, exist_ok=True)

                # if no anatomical, use most recent anatomical

                # anatomical manually found for this subject
                if subject == 'F013':
                    inpath = 'sourcedata/sub-F013/ses-anat/Tong_352144.04.01.10-24-00.WIP_RL_MPRAGE0.6mm_PEdirRL_SENSE.01.json'
                else:
                    proj_dirs = sorted(['p022_occlusion/in_vivo/fMRI/exp2'])
                    inpath = None
                    proj_counter = 0
                    while not inpath:
                        files = sorted(glob.glob(op.expanduser(
                            f'~/david/projects/{proj_dirs[proj_counter]}/sub-{subject}/ses-*/anat/sub-{subject}_ses-*_T1w.json')))
                        if files:
                            inpath = files[-1]
                        proj_counter += 1

                outpath = f"{anatdir}/sub-{subject}_ses-anat_T1w.json"
                if not op.isfile(outpath):
                    shutil.copy(inpath, outpath)

                # nii file
                inpath = f'{inpath[:-5]}.nii'

            # deidentify anatomical image
            #outpath = f"{anatdir}/sub-{subject}_{session}_T1w.nii"
            #if not op.isfile(outpath):
            #   os.system(f'mideface --i {inpath} --o {outpath}')

            # make T1 images for subject
            slice_dir = op.expanduser(
                f'~/david/subjects/for_subjects/sub-{subject}/2D')
            if not op.isdir(slice_dir):
                make_anat_slices(f'sub-{subject}', inpath, slice_dir)


            ### FUNC ###

            funcdir = f"sub-{subject}/{session}/func"
            os.makedirs(funcdir, exist_ok=True)
            fmapdir = f"sub-{subject}/{session}/fmap"
            os.makedirs(fmapdir, exist_ok=True)
            topup_counter = 1  # BIDS doesn't like task names in topup files so set a run number that is unique across tasks

            for funcscan in session_info["func"]:
                for run, scan_num in enumerate(session_info["func"][funcscan]):

                    for ft in filetypes:
                        files = glob.glob(f"{sourcedir}/*{sessID}.{scan_num:02}*.{ft}")
                        assert len(files) == 1
                        inpath = files[0]
                        outpath = (f"{funcdir}/sub-{subject}_{session}_task"
                                   f"-{funcscan}_dir-AP_run-{run+1}_bold."
                                   f"{ft}")
                        if not op.isfile(outpath):
                            copy_or_move(inpath,outpath)
                        if outpath.endswith('nii'):
                            orient_func(outpath)


                    # add required meta data to json file
                    scandata = json.load(open(outpath, "r+"))
                    if "TaskName" not in scandata:
                        scandata["TaskName"] = funcscan
                    if "PhaseEncodingDirection" not in scandata:
                        scandata["PhaseEncodingDirection"] = "j-"
                    if "SliceTiming" not in scandata:
                        scandata["SliceTiming"] = philips_slice_timing(outpath)
                    if "TotalReadoutTime" not in scandata:
                        if "EstimatedTotalReadoutTime" in scandata:
                            scandata["TotalReadoutTime"] = scandata[
                                "EstimatedTotalReadoutTime"]
                        else:
                            # this value was consistently found in other
                            # experiments using the same scan acquisition
                            scandata["TotalReadoutTime"] = 0.030498
                    json.dump(scandata, open(outpath, "w+"),
                              sort_keys=True, indent=4)

                    # repeat for top up file (assumes next scan was top up scan)
                    # find data
                    if '7T' in session:
                        nifti_target = outpath.replace('json', 'nii')
                        for ft in filetypes:
                            files = glob.glob(
                                f"{sourcedir}/*{sessID}.{scan_num+1:02}*.{ft}")
                            assert len(files) == 1 and 'TU' in files[0]
                            inpath = files[0]
                            outpath = (
                                f"{fmapdir}/sub-{subject}_{session}_acq-topup_"
                                f"dir-PA_run-{topup_counter}_epi.{ft}")
                            if not op.isfile(outpath):
                                copy_or_move(inpath, outpath)
                            if outpath.endswith('nii'):
                                orient_func(outpath)
                        topup_counter += 1

                        # add required meta data to json file
                        scandata = json.load(open(outpath, "r+"))
                        if "PhaseEncodingDirection" not in scandata:
                            scandata["PhaseEncodingDirection"] = "j"
                        if "SliceTiming" not in scandata:
                            scandata["SliceTiming"] = philips_slice_timing(
                                outpath)
                        if "EstimatedTotalReadoutTime" in scandata:
                            scandata["TotalReadoutTime"] = scandata[
                                "EstimatedTotalReadoutTime"]
                        else:
                            # this value was consistently found in other
                            # experiments using the same scan acquisition
                            scandata["TotalReadoutTime"] = 0.030498
                        if "IntendedFor" not in scandata:
                            scandata["IntendedFor"] = nifti_target[9:]
                        json.dump(scandata, open(outpath, "w+"),
                                  sort_keys=True, indent=4)


            ### FMAP ###

            # b0
            for c, component in enumerate(["magnitude", "fieldmap"]):
                if 'b0' in session_info['fmap']:
                    b0scan = session_info['fmap']['b0']
                    for ft in filetypes:
                        files = glob.glob(f"{sourcedir}/*{sessID}.{b0scan:02}"
                                          f"*B0_shimmed*e{c+1}*.{ft}")
                        assert len(files) == 1
                        inpath = files[0]
                        outpath = (f"{fmapdir}/sub-{subject}_{session}_acq-b0_"
                                   f"{component}.{ft}")
                        if not op.isfile(outpath):
                            copy_or_move(inpath, outpath)

                # add required meta data to json file
                scandata = json.load(open(outpath, "r+"))
                if "IntendedFor" not in scandata:
                    intendedscans = glob.glob(
                        f"sub-{subject}/{session}/anat/*.nii")
                    if '3T' in session:  # no topup for 3T so do b0 correction
                        intendedscans += glob.glob(
                            f"sub-{subject}/{session}/func/*.nii")
                    scandata["IntendedFor"] = sorted(
                        [x[9:] for x in intendedscans])
                if component == "fieldmap" and "Units" not in scandata:
                    scandata["Units"] = "Hz"
                json.dump(scandata, open(outpath, "w+"), sort_keys=True,
                          indent=4)


            # funcNoEPI
            if 'funcNoEPI' in session_info['fmap']:
                funcNoEPI = session_info['fmap']['funcNoEPI']
                for ft in filetypes:
                    files = glob.glob(
                        f"{sourcedir}/*{sessID}.{funcNoEPI:02}*.{ft}")
                    assert len(files) == 1
                    inpath = files[0]
                    outpath = (f"{fmapdir}/sub-{subject}_{session}_acq-funcNoEPI_"
                               f"magnitude.{ft}")
                    if not op.isfile(outpath):
                        copy_or_move(inpath, outpath)

                        # Too many slices for F019, trim the top and bottom 4
                        # slices. fslroi automatically handles the positional
                        # shift but annoyingly rescales the data which
                        # affects reg. Therefore, use fslroi to get the
                        # header and nibabel to get the data.
                        if subject == 'F019' and ft == 'nii':
                            orig_data = nib.load(outpath).get_fdata()[:, :,
                                        4:-4]
                            os.system(f'fslroi {outpath} {outpath} '
                                      f'0 -1 0 -1 4 38')
                            nifti = nib.load(f'{outpath}.gz')
                            nifti = nib.Nifti1Image(orig_data, nifti.affine,
                                                    nifti.header)
                            nib.save(nifti, outpath)
                            os.remove(f'{outpath}.gz')


if __name__ == "__main__":

    start = time.time()
    os.chdir(PROJ_DIR)
    initialise_BIDS()
    finish = time.time()
    print(f'analysis took {seconds_to_text(finish - start)} to complete')


