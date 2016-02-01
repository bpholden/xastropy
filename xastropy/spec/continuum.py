"""
#;+
#; NAME:
#; continuum 
#;    Version 1.0
#;
#; PURPOSE:
#;    Module for continuum code 
#;   20-Aug-2015 by JXP
#;-
#;------------------------------------------------------------------------------
"""
from __future__ import print_function, absolute_import, division, unicode_literals

import numpy as np
import os, imp
import astropy as apy

from astropy import units as u
from astropy import constants as const
from astropy.io import fits, ascii
from astropy.table import Table

from linetools.spectra.xspectrum1d import XSpectrum1D

from xastropy.xutils import xdebug as xdb

xa_path = imp.find_module('xastropy')[1]


def init_conti_dict(Norm=0., tilt=0., tilt2=0., piv_wv=0., piv_wv2=None, igm='None', fN_gamma=-1., LL_flatten='True'):
    """Initialize a continuum conti_dict

    Parameters
    ----------
    Norm : float, optional
      Normaliztion
    tilt : float, optional
      Power-law tilt to continuum
    piv_wv : float, optional
      Pivot wave for tilt.  Best kept *without* units
    piv_wv2 : float, optional
      Pivot wave for a second tilt. Better be at wavelength < piv_wv
    igm : str, optional
      Adopt average IGM model? ['None']
    LL_flatten : bool, optional
      Set Telfer to a constant below the LL?

    Returns
    -------
    conti_dict : dict
      Useful for simple modeling.  Keep as a dict for JSON writing
    """
    conti_dict = dict(Norm=Norm, tilt=tilt, piv_wv=piv_wv, piv_wv2=piv_wv2,
                      tilt2=tilt2, igm=igm, fN_gamma=fN_gamma, LL_flatten=LL_flatten)
    #
    if piv_wv2 is None:
        conti_dict.pop('piv_wv2')
    if piv_wv2 > piv_wv:
        raise ValueError("piv_wv2 < piv_wv required!")
    #
    return conti_dict

def get_telfer_spec(zqso=0., igm=False, fN_gamma=None, LL_flatten=True):
    '''Generate a Telfer QSO composite spectrum

    Parameters:
    ----------
    zqso: float, optional
      Redshift of the QSO
    igm: bool, optional
      Include IGM opacity? [False]
    fN_gamma: float, optional
      Power-law evolution in f(N,X)
    LL_flatten: bool, optional
      Set Telfer to a constant below the LL?

    Returns:
    --------
    telfer_spec: XSpectrum1D
      Spectrum
    '''
    # Read
    telfer = ascii.read(
        xa_path+'/data/quasar/telfer_hst_comp01_rq.ascii', comment='#')
    scale = telfer['flux'][(telfer['wrest'] == 1450.)]
    telfer_spec = XSpectrum1D.from_tuple((telfer['wrest']*(1+zqso),
        telfer['flux']/scale[0])) # Observer frame

    # IGM?
    if igm is True:
        '''The following is quite experimental.
        Use at your own risk.
        '''
        import multiprocessing
        from xastropy.igm.fN import model as xifm
        from xastropy.igm import tau_eff as xit
        fN_model = xifm.default_model()
        # Expanding range of zmnx (risky)
        fN_model.zmnx = (0.,5.)
        if fN_gamma is not None:
            fN_model.gamma = fN_gamma
        # Parallel
        igm_wv = np.where(telfer['wrest']<1220.)[0]
        adict = []
        for wrest in telfer_spec.dispersion[igm_wv].value:
            tdict = dict(ilambda=wrest, zem=zqso, fN_model=fN_model)
            adict.append(tdict)
        # Run
        #xdb.set_trace()
        pool = multiprocessing.Pool(4) # initialize thread pool N threads
        ateff = pool.map(xit.map_etl, adict)
        # Apply
        telfer_spec.flux[igm_wv] *= np.exp(-1.*np.array(ateff))
        # Flatten?
        if LL_flatten:
            wv_LL = np.where(np.abs(telfer_spec.dispersion/(1+zqso)-914.*u.AA)<3.*u.AA)[0]
            f_LL = np.median(telfer_spec.flux[wv_LL])
            wv_low = np.where(telfer_spec.dispersion/(1+zqso)<911.7*u.AA)[0]
            telfer_spec.flux[wv_low] = f_LL

    # Return
    return telfer_spec

def wfc3_continuum(wfc3_indx=None, zqso=0., wave=None, smooth=3., NHI_max=17.5, rstate=None):
    '''Use the WFC3 data + models from O'Meara+13 to generate a continuum

    Parameters
    ----------
    wfc3_indx : int, optional
      Index of WFC3 data to use
    zqso : float, optional
      Redshift of the QSO
    wave : Quantity array, optional
      Wavelengths to rebin on
    smooth : float, optional
      Number of pixels to smooth on
    NHI_max : float, optional
      Maximum NHI for the sightline

    Returns
    -------
    wfc3_continuum : XSpectrum1D 
       of the continuum
    idx : int
      Index of the WFC3 spectrum used    
    '''
    # Random number
    if rstate is None:
        rstate = np.random.RandomState()
    # Open
    wfc3_models_hdu = fits.open(os.getenv('DROPBOX_DIR')+'XQ-100/LLS/wfc3_conti_models.fits')
    nwfc3 = len(wfc3_models_hdu)-1
    # Load up models
    wfc_models = []
    for ii in range(1,nwfc3-1):
        wfc_models.append( Table(wfc3_models_hdu[ii].data) )
    # Grab a random one
    if wfc3_indx is None:
        need_c = True
        while(need_c):
            idx = rstate.randint(0,nwfc3-1)
            if wfc_models[idx]['TOTNHI'] > NHI_max:
                continue
            if wfc_models[idx]['QSO'] in ['J122836.05+510746.2', 'J122015.50+460802.4']:
                continue # These QSOs are NG
            need_c=False
    else:
        idx = wfc3_indx

    # Generate spectrum
    wfc_spec = XSpectrum1D.from_tuple( (wfc_models[idx]['WREST'].flatten()*(1+zqso), 
        wfc_models[idx]['FLUX'].flatten()) )
    # Smooth
    wfc_smooth = wfc_spec.gauss_smooth(fwhm=smooth)

    # Rebin?
    if wave is not None:
        wfc_rebin = wfc_smooth.rebin(wave)
        return wfc_rebin, idx
    else:
        return wfc_smooth, idx
