# -*- coding: utf-8 -*-
"""
pytests for accessing NREL .h5 files on the cloud via hsds/h5pyd
"""
import numpy as np
import xarray as xr
from rex import NSRDB, WindResource, MultiYearResource


def test_nsrdb():
    """Test retrieving NSRDB data"""
    fp = "s3://nrel-pds-nsrdb/current/nsrdb_1998.h5"
    with NSRDB(fp) as res:
        dsets = res.dsets
        ghi = res['ghi', 0:10, 0]
        assert isinstance(dsets, list)
        assert isinstance(ghi, np.ndarray)

    with xr.open_dataset(fp, engine="rex") as ds:
        assert np.allclose(ds["ghi"].isel(time=slice(0, 10), gid=0), ghi)


def test_wtk():
    """Test retrieving WTK data"""
    fp = 's3://nrel-pds-wtk/conus/v1.0.0/wtk_conus_2007.h5'
    with WindResource(fp) as res:
        dsets = res.dsets
        ws = res['windspeed_80m', 0:10, 0]
        assert isinstance(dsets, list)
        assert isinstance(ws, np.ndarray)

    with xr.open_dataset(fp, engine="rex") as ds:
        xr_ws = ds["windspeed_80m"].isel(time=slice(0, 10), gid=0)
        assert np.allclose(xr_ws, ws)


def test_sup3rcc():
    """Test retrieving sup3rcc data"""
    fp = ('s3://nrel-pds-sup3rcc/conus_ecearth3_ssp585_r1i1p1f1/v0.1.0/'
          'sup3rcc_conus_ecearth3_ssp585_r1i1p1f1_trh_2059.h5')
    with WindResource(fp) as res:
        dsets = res.dsets
        temp = res['temperature_2m', 0:10, 0]
        assert isinstance(dsets, list)
        assert isinstance(temp, np.ndarray)

    with xr.open_dataset(fp, engine="rex") as ds:
        xr_temp = ds["temperature_2m"].isel(time=slice(0, 10), gid=0)
        assert np.allclose(xr_temp, temp)


def test_multiyear():
    """Test retrieving multi year NSRDB data"""
    files = ["s3://nrel-pds-nsrdb/current/nsrdb_199*.h5"]
    with MultiYearResource(files) as res:
        dsets = res.dsets
        ghi = res['ghi', 0:10, 0]
        assert res.shape[0] == 35040  # 2x years at 30min (1998 and 1999)
        assert isinstance(dsets, list)
        assert isinstance(ghi, np.ndarray)

    files = ["s3://nrel-pds-nsrdb/current/nsrdb_1998.h5",
             "s3://nrel-pds-nsrdb/current/nsrdb_1999.h5"]
    with xr.open_mfdataset(files, engine="rex") as ds:
        xr_ghi = ds["ghi"].isel(time=slice(0, 10), gid=0)
        assert np.allclose(xr_ghi, ghi)
        assert ds.sizes['time'] == 35040
