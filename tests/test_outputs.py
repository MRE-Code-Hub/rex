# -*- coding: utf-8 -*-
"""
PyTest file for rex outputs handler
"""
import h5py
import numpy as np
import pandas as pd
import pytest
import os
import tempfile

from rex.version import __version__
from rex import Outputs, Resource
from rex.utilities.exceptions import HandlerRuntimeError, HandlerValueError
from rex.utilities.utilities import pd_date_range


arr1 = np.ones(100)
arr2 = np.ones((8760, 100))
arr3 = np.ones((8760, 100), dtype=float) * 42.42
meta = pd.DataFrame({'latitude': np.ones(100),
                     'longitude': np.zeros(100)})
time_index = pd_date_range('20210101', '20220101', freq='1h', closed='right')


def test_create():
    """Test simple output file creation"""

    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, 'outputs.h5')

        with Outputs(fp, 'w') as f:
            f.meta = meta
            f.time_index = time_index

        with h5py.File(fp, 'r') as f:
            test_meta = pd.DataFrame(f['meta'][...])
            test_ti = f['time_index'][...]
            assert test_meta.shape == (100, 2)
            assert len(test_ti) == 8760

            assert f.attrs['package'] == 'rex'
            assert f.attrs['version'] == __version__


def test_add_dset():
    """Test the addition of datasets to a pre-existing h5 file"""

    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, 'outputs.h5')

        with Outputs(fp, 'w') as f:
            f.meta = meta
            f.time_index = time_index

        with pytest.raises(HandlerRuntimeError):
            Outputs.add_dataset(fp, 'dset1', arr1, int, attrs=None,
                                chunks=None, unscale=True, mode='a',
                                str_decode=True, group=None)

        with pytest.raises(HandlerRuntimeError):
            Outputs.add_dataset(fp, 'dset2', arr2, float,
                                attrs={'scale_factor': 10},
                                chunks=(None, 10), unscale=True, mode='a',
                                str_decode=True, group=None)

        # Float to float
        Outputs.add_dataset(fp, 'dset1', arr1, arr1.dtype,
                            attrs=None,
                            unscale=True, mode='a',
                            str_decode=True, group=None)
        with h5py.File(fp, 'r') as f:
            assert 'dset1' in f
            data = f['dset1'][...]
            assert data.dtype == float
            assert np.allclose(arr1, data)

        # Float to float
        Outputs.add_dataset(fp, 'dset1', arr1, arr1.dtype,
                            attrs={'scale_factor': 1},
                            unscale=True, mode='a',
                            str_decode=True, group=None)
        with h5py.File(fp, 'r') as f:
            assert 'dset1' in f
            data = f['dset1'][...]
            assert data.dtype == float
            assert np.allclose(arr1, data)

        # int16 to in16
        Outputs.add_dataset(fp, 'dset1', arr1.astype(np.int16), np.int16,
                            attrs=None,
                            chunks=None, unscale=True, mode='a',
                            str_decode=True, group=None)
        with h5py.File(fp, 'r') as f:
            assert 'dset1' in f
            data = f['dset1'][...]
            assert np.issubdtype(data.dtype, np.integer)
            assert np.allclose(arr1, data)

        # float to in16
        Outputs.add_dataset(fp, 'dset2', arr2,
                            np.int16, attrs={'scale_factor': 1},
                            chunks=(None, 10),
                            unscale=True, mode='a', str_decode=True,
                            group=None)
        with h5py.File(fp, 'r') as f:
            assert 'dset1' in f
            assert 'dset2' in f
            assert f['dset1'].chunks is None
            assert f['dset2'].chunks == (8760, 10)
            assert np.allclose(f['dset2'][...],
                               np.round(arr2).astype(np.int16))

        # scale to int32
        Outputs.add_dataset(fp, 'dset3', arr3, np.int32,
                            attrs={'scale_factor': 100},
                            chunks=(100, 25),
                            unscale=True, mode='a', str_decode=True,
                            group=None)
        with h5py.File(fp, 'r') as f:
            assert 'dset1' in f
            assert 'dset2' in f
            assert 'dset3' in f
            assert f['dset1'].chunks is None
            assert f['dset2'].chunks == (8760, 10)
            assert f['dset3'].chunks == (100, 25)
            assert f['dset3'].attrs['scale_factor'] == 100
            assert f['dset3'].dtype == np.int32
            assert np.allclose(f['dset3'][...], arr3 * 100)


def test_bad_shape():
    """Negative test for bad data shapes"""

    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, 'outputs.h5')

        with Outputs(fp, 'w') as f:
            f.meta = meta
            f.time_index = time_index

        with pytest.raises(HandlerValueError):
            Outputs.add_dataset(fp, 'dset3', np.ones(10), float, attrs=None)

        with pytest.raises(HandlerValueError):
            Outputs.add_dataset(fp, 'dset3', np.ones((10, 10)), float,
                                attrs=None)


def test_1d_datasets_not_added_before_meta_ti():
    """Test the storing 1D data shapes not allowed before meta/ti."""
    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, 'outputs.h5')

        with Outputs(fp, 'w') as f:
            pass
        with pytest.raises(HandlerRuntimeError):
            Outputs.add_dataset(
                fp, 'dset3', np.ones(10), float, attrs=None
            )
        with Outputs(fp, 'w') as f:
            f.meta = meta
        with pytest.raises(HandlerValueError):
            Outputs.add_dataset(
                fp, 'dset3', np.ones(10), float, attrs=None
            )
        with Outputs(fp, 'w') as f:
            f.time_index = time_index
        with pytest.raises(HandlerValueError):
            Outputs.add_dataset(
                fp, 'dset3', np.ones(10), float, attrs=None
            )
        with Outputs(fp, 'w') as f:
            f.meta = np.empty((0))
            f.time_index = np.empty((0))
        with pytest.raises(HandlerValueError):
            Outputs.add_dataset(
                fp, 'dset3', np.ones(10), float, attrs=None
            )

        with Outputs(fp, 'w') as f:
            f.meta = meta
            f.time_index = np.empty((0))
        with pytest.raises(HandlerValueError):
            Outputs.add_dataset(
                fp, 'dset3', np.ones(10), float, attrs=None
            )

        with Outputs(fp, 'w') as f:
            f.meta = np.empty((0))
            f.time_index = time_index
        with pytest.raises(HandlerValueError):
            Outputs.add_dataset(
                fp, 'dset3', np.ones(10), float, attrs=None
            )


def test_1D_dataset_shape():
    """Tests for storing 1D spatiotemporal data shapes"""

    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, 'outputs.h5')

        with Outputs(fp, 'w') as f:
            f.meta = meta
            f.time_index = time_index

        Outputs.add_dataset(fp, 'dset3', np.ones(100), float, attrs=None,
                            chunks=(100,))

        with Resource(fp) as res:
            assert 'dset3' in res.dsets
            assert res['dset3'].shape == (100,)

    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, 'outputs.h5')

        with Outputs(fp, 'w') as f:
            f.meta = meta
            f.time_index = time_index

        Outputs.add_dataset(fp, 'dset3', np.ones(8760), float, attrs=None,
                            chunks=(100,))

        with Resource(fp) as res:
            assert 'dset3' in res.dsets
            assert res['dset3'].shape == (8760,)

    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, 'outputs.h5')

        with Outputs(fp, 'w') as f:
            f.meta = meta

        Outputs.add_dataset(fp, 'dset3', np.ones(100), float, attrs=None,
                            chunks=(100,))

        with Resource(fp) as res:
            assert 'dset3' in res.dsets
            assert res['dset3'].shape == (100,)

    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, 'outputs.h5')

        with Outputs(fp, 'w') as f:
            f.time_index = time_index

        Outputs.add_dataset(fp, 'dset3', np.ones(8760), float, attrs=None,
                            chunks=(100,))

        with Resource(fp) as res:
            assert 'dset3' in res.dsets
            assert res['dset3'].shape == (8760,)


def test_attrs_multiple_opens():
    """Test that attrs are not overwritten on multiple opens"""

    attrs_to_test = ["package", "version", "full_version_record"]
    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, 'outputs.h5')
        with Outputs(fp, 'a') as f:
            for attr in attrs_to_test:
                assert f.h5.attrs[attr] != "test"
                f.h5.attrs[attr] = "test"
                assert f.h5.attrs[attr] == "test"

        with Outputs(fp, 'a') as f:
            for attr in attrs_to_test:
                assert f.h5.attrs["package"] == "test"


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
