"""
#;+ 
#; NAME:
#; abs_line
#;    Version 1.0
#;
#; PURPOSE:
#;    Module for individual absorption lines
#;   01-Nov-2014 by JXP
#;-
#;------------------------------------------------------------------------------
"""
from pdb import *
from xastropy.xutils.printing import printcol as xpcol
from xastropy.plotting.simple import plot_1d_arrays as xplot
from xastropy.plotting.simple import plot_hist as xhist
#from xastropy.xguis.spec_guis import run_xspec as xspec

try:
	from xastropy.xutils.xginga import show_fits as xshow_fits
except ImportError:
    'Need Ginga for this portions of xdebug.  See https://github.com/ejeschke/ginga.git'
else:
	from xastropy.xutils.xginga import show_img as ximshow

""" Didn't work
def pyqt_trace():
    from PyQt4.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook()
    set_trace()
"""
