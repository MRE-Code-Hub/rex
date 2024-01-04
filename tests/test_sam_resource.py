# -*- coding: utf-8 -*-
"""
pytests for sam_resource
"""
import tempfile
import numpy as np
import shutil
import h5py
import os
import pandas as pd
from pandas.testing import assert_series_equal
import pytest

from rex.renewable_resource import WindResource, NSRDB, WaveResource
from rex.multi_file_resource import MultiFileNSRDB
from rex.sam_resource import SAMResource
from rex.utilities.exceptions import ResourceRuntimeError
from rex.utilities.utilities import roll_timeseries
from rex.outputs import Outputs
from rex import TESTDATADIR


def test_sites_slice():
    """
    Test to ensure SAMResource.sites_slice returns slice when possible, else
    a list
    """
    h5 = os.path.join(TESTDATADIR, 'wtk/ri_100_wtk_2012.h5')
    with WindResource(h5) as f:
        time_index = f.time_index

    sites = list(range(10))
    hub_heights = 80
    sam_res = SAMResource(sites, 'windpower', time_index,
                          hub_heights=hub_heights)
    msg = "sites were not returned as a slice"
    assert isinstance(sam_res.sites_slice, slice), msg

    sites = [0, 2, 5, 7, 9, 4, 3]
    sam_res = SAMResource(sites, 'windpower', time_index,
                          hub_heights=hub_heights)
    msg = "sites were not returned as the same input list"
    assert sam_res.sites == sites


def test_duplicate_sites():
    """
    Test site list with duplicates passed to SAMResource. Can be used for
    getting coarse forecast data that has overlapping generation gids.
    """
    h5 = os.path.join(TESTDATADIR, 'wtk/ri_100_wtk_2012.h5')

    sites = [0, 1, 1, 1, 2, 3, 4, 4, 10, 10, 21, 30, 30]
    hub_heights = 80
    sam_res = WindResource.preload_SAM(h5, sites, hub_heights, means=True)

    assert len(sam_res.meta) == len(sites)
    assert len(sam_res.sites) == len(sites)
    assert any(sam_res.meta.duplicated())
    assert sam_res._res_arrays['windspeed'].shape[1] == len(sites)
    assert sam_res._mean_arrays['windspeed'].shape[0] == len(sites)

    with WindResource(h5) as res:
        for res_gid in sites:
            test = sam_res[res_gid]['windspeed']
            truth = res['windspeed_80m', :, res_gid]
            assert np.allclose(test, truth)

        i = 0
        for res_df, site_meta in sam_res:
            i += 1
            assert isinstance(site_meta, pd.Series)
            test = res_df['windspeed']
            truth = res['windspeed_80m', :, res_df.name]
            assert np.allclose(test, truth)

        assert i == len(sites)


def test_roll():
    """
    Test roll to local time
    """
    h5 = os.path.join(TESTDATADIR, 'wtk/ri_100_wtk_2012.h5')
    with WindResource(h5) as f:
        time_index = f.time_index
        timezone = f.meta['timezone'][0]
        sam_df = f.get_SAM_df(0, 100)
        time_step = np.abs(timezone)
        time_step = np.arange(time_step, len(time_index) - time_step)
        time_step = np.random.choice(time_step, 1)[0]
        wspd = f['windspeed_100m', time_step, 0]

    if not time_index.tz:
        time_index = time_index.tz_localize('UTC')

    if timezone < 0:
        tz = 'Etc/GMT+{}'.format(-1 * timezone)
    else:
        tz = 'Etc/GMT-{}'.format(timezone)

    time_index = time_index.tz_convert(tz)
    time_index = time_index[time_step]
    mask = sam_df['Year'] == time_index.year
    mask &= sam_df['Month'] == time_index.month
    mask &= sam_df['Day'] == time_index.day
    mask &= sam_df['Hour'] == time_index.hour
    if 'Minute' in sam_df:
        mask &= sam_df['Minute'] == time_index.minute

    assert np.isclose(sam_df.loc[mask, 'Speed'], wspd)


def test_roll_timeseries():
    """
    Test roll timeseries array to local time
    """
    utc = np.random.rand(8760, 100)
    timezones = [-5, -6, -7, -8]
    timezones = np.random.choice(timezones, 100)

    local = roll_timeseries(utc, timezones)
    for i, tz in enumerate(timezones):
        truth = np.roll(utc[:, i], int(tz))
        test = local[:, i]
        assert np.allclose(truth, test)


def test_check_units():
    """
    Test SAMResource unit convertion
    """
    h5 = os.path.join(TESTDATADIR, 'wtk/ri_100_wtk_2012.h5')
    var_name = 'pressure_100m'
    with WindResource(h5) as f:
        pa = f[var_name, :, :10]

    atm = SAMResource.check_units(var_name, pa.copy(), 'windpower')
    msg = "Pressure was not converted from pa to atm"
    assert np.allclose(atm, (pa * 9.86923e-6)), msg


def test_valid_range():
    """
    Test SAMResource valid range enforcement
    """
    h5 = os.path.join(TESTDATADIR, 'wtk/ri_100_wtk_2012.h5')
    var = 'pressure'
    var_name = '{}_100m'.format(var)
    tech = 'windpower'
    sites = list(range(10))
    with WindResource(h5) as f:
        pa = f[var_name, :, sites]

    atm = SAMResource.check_units(var_name, pa * 10, 'windpower')
    valid_range = SAMResource.DATA_RANGES[tech][var]
    valid = SAMResource.enforce_arr_range(var, atm, valid_range, sites)

    assert np.all(valid == valid_range[1])


def test_preload_sam():
    """Test the preload_SAM method with invalid resource data ranges.
    """

    h5 = os.path.join(TESTDATADIR, 'wtk/ri_wtk_2012_invalid.h5')
    sites = slice(0, 200)
    hub_heights = 80

    SAM_res = WindResource.preload_SAM(h5, sites, hub_heights)

    msg1 = 'Invalid pressure range was not corrected.'
    msg2 = 'Invalid temperature range was not corrected.'
    msg3 = 'Invalid windspeed range was not corrected.'

    assert np.min(SAM_res._res_arrays['pressure']) >= 0.5, msg1
    assert np.min(SAM_res._res_arrays['temperature']) >= -200, msg2
    assert np.max(SAM_res._res_arrays['windspeed']) <= 120, msg3


def test_preload_sam_hh():
    """Test the preload_SAM method with a single hub height windspeed in res.

    In this case, all variables should be loaded at the single windspeed hh
    """

    h5 = os.path.join(TESTDATADIR, 'wtk/ri_wtk_2012_incomplete_2.h5')
    sites = slice(0, 200)
    hub_heights = 80

    SAM_res = WindResource.preload_SAM(h5, sites, hub_heights)

    assert SAM_res.h == 80
    assert SAM_res.d is None

    with WindResource(h5) as wind:
        p = wind['pressure_100m'] * 9.86923e-6
        t = wind['temperature_100m']
        msg1 = ('Error: pressure should have been loaded at 100m '
                'b/c there is only windspeed at 100m.')
        msg2 = ('Error: temperature should have been loaded at 100m '
                'b/c there is only windspeed at 100m.')
        assert np.allclose(SAM_res['pressure'].values, p), msg1
        assert np.allclose(SAM_res['temperature'].values, t), msg2


@pytest.mark.parametrize('means', [True, False])
def test_preload_sam_means(means):
    """Test the preload_SAM method with means=True.
    """

    h5 = os.path.join(TESTDATADIR, 'wtk/ri_100_wtk_2012.h5')
    sites = slice(0, 200)
    hub_heights = 80

    SAM_res = WindResource.preload_SAM(h5, sites, hub_heights, means=means)
    if means:
        for var in SAM_res.var_list:
            ts = SAM_res[var]
            means = SAM_res['mean_{}'.format(var)]

            msg = "{} means do not match".format(var)
            assert np.allclose(means, ts.mean().values), msg
    else:
        with pytest.raises(ResourceRuntimeError):
            # pylint: disable=pointless-statement
            SAM_res['mean_windspeed']


@pytest.mark.parametrize('sites',
                         [1, [10], [1, 10, 8, 7, 9], slice(10, 20, 2)])
def test_preload_sam_sites(sites):
    """Test the preload_SAM method with different sites"""
    h5 = os.path.join(TESTDATADIR, 'wtk/ri_100_wtk_2012.h5')
    hub_heights = 100

    SAM_res = WindResource.preload_SAM(h5, sites, hub_heights)
    test = SAM_res._res_arrays['windspeed']
    if isinstance(sites, int):
        test = test.flatten()

    with WindResource(h5) as wind:
        truth = wind['windspeed_100m', :, sites]

    assert np.allclose(truth, test)


def test_bad_site_req():
    """Test that the preload_SAM method raises an error on a bad site request
    """
    sites = [0, 10, 500]  # 500 is out of the valid site indices
    h5 = os.path.join(TESTDATADIR, 'wtk/ri_100_wtk_2012.h5')
    hub_heights = 100
    with pytest.raises(IndexError):
        WindResource.preload_SAM(h5, sites, hub_heights)


@pytest.mark.parametrize('time_index_step',
                         [None, 1, 2, 10])
def test_preload_sam_time_index_step(time_index_step):
    """Test the preload_SAM method with different sites"""
    h5 = os.path.join(TESTDATADIR, 'wtk/ri_100_wtk_2012.h5')
    hub_heights = 100

    sites = slice(0, 100)

    SAM_res = WindResource.preload_SAM(h5, sites, hub_heights,
                                       time_index_step=time_index_step)
    test = SAM_res._res_arrays['windspeed']
    if isinstance(sites, int):
        test = test.flatten()

    time_slice = slice(None, None, time_index_step)
    with WindResource(h5) as wind:
        truth = wind['windspeed_100m', time_slice, sites]

    assert np.allclose(truth, test)


def test_check_irradiance():
    """
    Test check irradiance method
    """
    h5 = os.path.join(TESTDATADIR, 'nsrdb/nsrdb_2012_invalid.h5')
    sites = slice(0, 100)
    with pytest.raises(ResourceRuntimeError):
        # pylint: disable=pointless-statement
        NSRDB.preload_SAM(h5, sites)


@pytest.mark.parametrize('sites',
                         [1, [10], [1, 10, 8, 7, 9], slice(10, 20, 2)])
def test_meta(sites):
    """
    Test meta iterator
    """
    path = os.path.join(TESTDATADIR, 'nsrdb/ri_100_nsrdb_2012.h5')
    with NSRDB(path) as f:
        meta = f.meta

    test = NSRDB.preload_SAM(path, sites)

    for _, site_meta in test:
        gid = site_meta.name
        assert_series_equal(site_meta, meta.loc[gid])


def test_fill_irradiance():
    """
    Test check irradiance method
    """
    sites = slice(0, 100)

    baseline = os.path.join(TESTDATADIR, 'nsrdb/ri_100_nsrdb_2012.h5')
    baseline = NSRDB.preload_SAM(baseline, sites)

    test = os.path.join(TESTDATADIR, 'nsrdb/nsrdb_2012_missing.h5')
    test = NSRDB.preload_SAM(test, sites)

    for var in ['ghi', 'dni', 'dhi']:
        baseline_arr = baseline[var].values
        test_arr = test[var].values
        assert np.allclose(baseline_arr, test_arr, rtol=0.5)


def test_bifacial():
    """
    Test NSRDB preload sam method with bifacial flag
    """
    fp = os.path.join(TESTDATADIR, 'nsrdb/ri_100_nsrdb_2012.h5')
    sites = slice(0, 100)
    res = NSRDB.preload_SAM(fp, sites, bifacial=True)

    for res_df, _ in res:
        assert 'surface_albedo' in res_df
        assert res_df['surface_albedo'].min() > 0.0
        assert res_df['surface_albedo'].min() < 1.0


def test_wave():
    """
    Test wave preload sam method
    """
    fp = os.path.join(TESTDATADIR, 'wave/ri_wave_2010.h5')
    sites = slice(0, 100)
    res = WaveResource.preload_SAM(fp, sites)

    with WaveResource(fp) as f:
        for var in res.var_list:
            valid_range = SAMResource.DATA_RANGES['wave'][var]
            truth = SAMResource.enforce_arr_range(var, f[var], valid_range,
                                                  np.arange(100))
            test = res[var].values
            assert np.allclose(truth, test)


def test_nsrdb_and_wtk():
    """Test a mixed resource style with solar from an nsrdb-styled file and
    wind+temp interpolated from a wtk file. This was implemented to load data
    from Sup3rCC which combines Solar+Wind data into multi-file resource sets.
    """
    sites = slice(0, 10)
    with tempfile.TemporaryDirectory() as td:
        og_fp_nsrdb = os.path.join(TESTDATADIR, 'nsrdb/ri_100_nsrdb_2012.h5')
        og_fp_wtk = os.path.join(TESTDATADIR, 'wtk/ri_100_wtk_2012.h5')
        fp_nsrdb = os.path.join(td, 'ri_100_nsrdb_2012.h5')
        fp_wtk = os.path.join(td, 'ri_100_wtk_2012.h5')
        shutil.copy(og_fp_nsrdb, fp_nsrdb)
        shutil.copy(og_fp_wtk, fp_wtk)

        with Outputs(fp_nsrdb, mode='a') as f:
            ti = f.time_index
        with h5py.File(fp_nsrdb, 'a') as f:
            dni, dhi, ghi = f['dni'][...], f['dhi'][...], f['ghi'][...]
            for var in ('wind_speed', 'air_temperature', 'dni', 'dhi', 'ghi',
                        'time_index'):
                del f[var]
            f.create_dataset('ghi', data=ghi[::2])
            f.create_dataset('dhi', data=dhi[::2])
            f.create_dataset('dni', data=dni[::2])
        with Outputs(fp_nsrdb, mode='a') as f:
            f.time_index = ti[::2]
        with h5py.File(fp_wtk, 'a') as f:
            f.create_dataset('temperature_2m', data=f['temperature_80m'][...])
            for k, v in f['temperature_80m'].attrs.items():
                f['temperature_2m'].attrs[k] = v

        with pytest.raises(ResourceRuntimeError):
            res = NSRDB.preload_SAM(fp_nsrdb, sites, bifacial=False)
            _ = res._get_res_df(0)

        res = MultiFileNSRDB.preload_SAM([fp_nsrdb, fp_wtk], sites,
                                         bifacial=False)
        _ = res._get_res_df(0)


def test_bias_correct_errors():
    """Negative tests for bad bias correction inputs"""
    h5 = os.path.join(TESTDATADIR, 'wtk/ri_100_wtk_2012.h5')
    sites = slice(0, 20)
    hub_heights = 80

    n = 10
    res = WindResource.preload_SAM(h5, sites, hub_heights)

    bc = pd.DataFrame({'gid': np.arange(n),
                       'adder': np.random.uniform(-1, 1, n),
                       'scalar': np.random.uniform(0.9, 1.1, n)})
    with pytest.raises(KeyError) as record:
        res.bias_correct(bc)
    assert '"method" column not found!' in str(record.value)

    bc = pd.DataFrame({'gidasdfasf': np.arange(n),
                       'adder': np.random.uniform(-1, 1, n),
                       'scalar': np.random.uniform(0.9, 1.1, n),
                       'method': 'lin_ws'})
    with pytest.raises(KeyError) as record:
        res.bias_correct(bc)
    assert 'must have "gid" column' in str(record.value)

    bc = pd.DataFrame({'gid': np.arange(n),
                       'adder': np.random.uniform(-1, 1, n),
                       'scalar': np.random.uniform(0.9, 1.1, n),
                       'method': 'testfasdfasdf'})
    with pytest.raises(KeyError) as record:
        res.bias_correct(bc)
    assert 'Could not find method name "test' in str(record.value)


def test_bias_correct_wind_lin():
    """Test linear bias correction function on windspeed"""
    h5 = os.path.join(TESTDATADIR, 'wtk/ri_100_wtk_2012.h5')
    sites = slice(0, 20)
    hub_heights = 80
    base_res = WindResource.preload_SAM(h5, sites, hub_heights)

    n = 10
    bc = pd.DataFrame({'gid': np.arange(n),
                       'adder': np.random.uniform(-1, 1, n),
                       'scalar': np.random.uniform(0.9, 1.1, n),
                       'method': 'lin_ws'})

    res = WindResource.preload_SAM(h5, sites, hub_heights)

    with pytest.warns() as record:
        res.bias_correct(bc)

        assert len(record) == 1
        assert 'missing from the bias correction' in str(record[0].message)
        assert np.allclose(res._res_arrays['windspeed'][:, 10:],
                           base_res._res_arrays['windspeed'][:, 10:])
        assert not (res._res_arrays['windspeed'][:, :10]
                    == base_res._res_arrays['windspeed'][:, :10]).any()
        assert (res._res_arrays['windspeed'] >= 0).all()

    n = 200
    bc = pd.DataFrame({'gid': np.arange(n),
                       'adder': np.random.uniform(-1, 1, n),
                       'scalar': np.random.uniform(0.9, 1.1, n),
                       'method': 'lin_ws'})

    with pytest.warns(None) as record:
        res = WindResource.preload_SAM(h5, sites, hub_heights)
        res.bias_correct(bc)

        assert not any(record)
        assert not (res._res_arrays['windspeed']
                    == base_res._res_arrays['windspeed']).any()
        assert (res._res_arrays['windspeed'] >= 0).all()


def test_bias_correct_solar_lin():
    """Test adder bias correction function on irradiance"""
    h5 = os.path.join(TESTDATADIR, 'nsrdb/ri_100_nsrdb_2012.h5')
    sites = slice(0, 10)
    base_res = NSRDB.preload_SAM(h5, sites)

    n = 10
    bc = pd.DataFrame({'gid': np.arange(n),
                       'adder': np.random.uniform(-100, 100, n),
                       'scalar': np.random.uniform(1, 1, n),
                       'method': 'lin_irrad'})

    res = NSRDB.preload_SAM(h5, sites)
    res.bias_correct(bc)

    for gid in res.sites:
        adder = bc.at[gid, 'adder']
        base_ghi = base_res._res_arrays['ghi'][:, gid]
        base_dni = base_res._res_arrays['dni'][:, gid]
        base_dhi = base_res._res_arrays['dhi'][:, gid]
        ghi = res._res_arrays['ghi'][:, gid]
        dni = res._res_arrays['dni'][:, gid]
        dhi = res._res_arrays['dhi'][:, gid]
        assert (ghi >= 0).all()
        assert (dni >= 0).all()
        assert (dhi >= 0).all()
        ghi_mask = (ghi > np.abs(adder)) & (base_ghi > np.abs(adder))
        dni_mask = (dni > np.abs(adder)) & (base_dni > np.abs(adder))
        assert np.allclose(ghi[ghi_mask], base_ghi[ghi_mask] + adder)
        assert np.allclose(dni[dni_mask], base_dni[dni_mask] + adder)

        ghi_mask = (ghi > np.abs(adder)) & (base_ghi > np.abs(adder))
        dni_mask = (dni > np.abs(adder)) & (base_dni > np.abs(adder))
        dhi_mask = (dhi > np.abs(adder)) & (base_dhi > np.abs(adder))
        mask = ghi_mask & dni_mask & dhi_mask
        cos_sza = (ghi[mask] - dhi[mask]) / (dni[mask])
        base_cos_sza = (base_ghi[mask] - base_dhi[mask]) / (base_dni[mask])
        assert np.allclose(cos_sza, base_cos_sza, atol=0.005)


def test_bias_correct_wind_pqdm():
    """Test parametric QDM bias correction function on windspeed"""
    h5 = os.path.join(TESTDATADIR, 'wtk/ri_100_wtk_2012.h5')
    sites = slice(0, 20)
    hub_heights = 80
    base_res = WindResource.preload_SAM(h5, sites, hub_heights)

    n = 10
    bc = pd.DataFrame({'gid': np.arange(n),
                       'method': 'pqdm_ws',
                       'params_oh': '[2.6, -0.8, 8.9]',
                       'params_mh': '[2.6, -0.8, 8.9]',
                       'params_mf': '[2.6, -0.8, 8.9]',
                       'dist': 'weibull_min',
                       'relative': True,
                       })

    res = WindResource.preload_SAM(h5, sites, hub_heights)
    res.bias_correct(bc)



def execute_pytest(capture='all', flags='-rapP'):
    """Execute module as pytest with detailed summary report.

    Parameters
    ----------
    capture : str
        Log or stdout/stderr capture option. ex: log (only logger),
        all (includes stdout/stderr)
    flags : str
        Which tests to show logs and results for.
    """

    fname = os.path.basename(__file__)
    pytest.main(['-q', '--show-capture={}'.format(capture), fname, flags])


if __name__ == '__main__':
    execute_pytest()
