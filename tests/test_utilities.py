# -*- coding: utf-8 -*-
"""
pytests for rex utilities
"""
import os
import json
from tempfile import TemporaryDirectory

import pandas as pd
import pytest

from rex.utilities import parse_table
from rex import TESTDATADIR

NSRDB_DIR = os.path.join(TESTDATADIR, 'nsrdb')


def test_parse_table():
    """Test table parsing"""
    csv_fp = os.path.join(NSRDB_DIR, 'ri_full_meta.csv')
    meta = pd.read_csv(csv_fp)

    df = parse_table(csv_fp)
    assert "Unnamed: 0" in meta
    assert "Unnamed: 0" not in df
    assert meta[df.columns].equals(df)

    df = parse_table(meta)
    assert "Unnamed: 0" in meta
    assert "Unnamed: 0" in df
    assert meta.equals(df)

    test_dict = {"gid": {0: 1, 2: 3}}
    df = parse_table(test_dict)
    assert "gid" in df
    assert (df.index == [0, 2]).all()
    assert (df.gid == [1, 3]).all()

    with TemporaryDirectory() as td:
        sample_file = os.path.join(td, 'sample.json')
        with open(sample_file, "w") as fh:
            json.dump(test_dict, fh)

        df = parse_table(sample_file)
        assert "gid" in df
        assert (df.index == [0, 2]).all()
        assert (df.gid == [1, 3]).all()

    with pytest.raises(ValueError):
        parse_table([0, 1, 2])


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