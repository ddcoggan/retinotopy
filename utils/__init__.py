# /usr/bin/python
from .config import PROJ_DIR, MSTR_DIR, subjects, scan_params
from .make_ROIs import make_ROIs
from .get_wang_atlas import get_wang_atlas
from .plot_utils import export_legend, custom_defaults
from .preprocess import preprocess
from .seconds_to_text import seconds_to_text
from .initialise_BIDS import initialise_BIDS
from .check_segmentation import check_segmentation
from .registration import registration
from .estimate_pRFs import estimate_pRFs
from .make_surface_maps import make_surface_maps
import datetime


def now():
    return datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

