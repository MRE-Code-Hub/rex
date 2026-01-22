**********************************************
Welcome to The REsource eXtraction (rex) tool!
**********************************************

|Docs| |Tests| |Linter| |PyPi| |PythonV| |Conda| |Licence| |CodeCov| |Zeonodo|

.. |Docs| image:: https://github.com/NatLabRockies/rex/workflows/Documentation/badge.svg
    :target: https://natlabrockies.github.io/rex/

.. |Tests| image:: https://github.com/NatLabRockies/rex/workflows/Pytests/badge.svg
    :target: https://github.com/NatLabRockies/rex/actions?query=workflow%3A%22Pytests%22

.. |Linter| image:: https://github.com/NatLabRockies/rex/workflows/Lint%20Code%20Base/badge.svg
    :target: https://github.com/NatLabRockies/rex/actions?query=workflow%3A%22Lint+Code+Base%22

.. |PyPi| image:: https://img.shields.io/pypi/pyversions/NLR-rex.svg
    :target: https://pypi.org/project/NLR-rex/

.. |PythonV| image:: https://badge.fury.io/py/NLR-rex.svg
    :target: https://badge.fury.io/py/NLR-rex

.. |Conda| image:: https://anaconda.org/nrel/nrel-rex/badges/version.svg
    :target: https://anaconda.org/nrel/nrel-rex

.. |Licence| image:: https://anaconda.org/nrel/nrel-rex/badges/license.svg
    :target: https://anaconda.org/nrel/nrel-rex

.. |CodeCov| image:: https://codecov.io/gh/natlabrockies/rex/branch/main/graph/badge.svg?token=WQ95L11SRS
    :target: https://codecov.io/gh/natlabrockies/rex

.. |Zeonodo| image:: https://zenodo.org/badge/253541811.svg
   :target: https://zenodo.org/badge/latestdoi/253541811

.. inclusion-intro

What is rex?
=============
``rex`` stands for **REsource eXtraciton** tool.

``rex`` enables the efficient and scalable extraction, manipulation, and
computation with NLRs flagship renewable resource datasets such as: the Wind
Integration National Dataset (WIND Toolkit), the National Solar Radiation
Database (NSRDB), the Ocean Surface Wave Hindcast (US Wave) Data, and the
High-resolution downscaled climate change data (Sup3rCC).

To get started accessing NLR's datasets, see the primer on `NLR Renewable
Energy Resource Data
<https://natlabrockies.github.io/rex/misc/examples.nlr_data.html>`_ or the
`installation instructions <https://natlabrockies.github.io/rex/#installing-rex>`_.

You might also want to check out the basic `Resource Class
<https://natlabrockies.github.io/rex/_autosummary/rex.resource.Resource.html>`_ that
can be used to efficiently query NLR data, or our various `example use cases
<https://natlabrockies.github.io/rex/misc/examples.html>`_.

Installing rex
==============

NOTE: The installation instruction below assume that you have python installed
on your machine and are using `conda <https://docs.conda.io/en/latest/index.html>`_
as your package/environment manager.

Option 1: Install from PIP or Conda (recommended for analysts):
---------------------------------------------------------------

1. Create a new environment:
    ``conda create --name rex``

2. Activate directory:
    ``conda activate rex``

3. Basic ``rex`` install:
    ``pip install NLR-rex``

4. Install for users outside of NLR that want to access data via HSDS or S3 as per the instructions `here <https://natlabrockies.github.io/rex/misc/examples.nlr_data.html#data-location-external-users>`_:
    1) ``pip install NLR-rex[hsds]`` for more performant access of the data on HSDS with slightly more setup as per `this hsds example <https://natlabrockies.github.io/rex/misc/examples.hsds.html>`_. Note that the highest version of Python currently supported by ``hsds`` is Python 3.11.

Option 2: Clone repo (recommended for developers)
-------------------------------------------------

1. from home dir, ``git clone git@github.com:NatLabRockies/rex.git``

2. Create ``rex`` environment and install package
    1) Create a conda env: ``conda create -n rex``
    2) Run the command: ``conda activate rex``
    3) cd into the repo cloned in 1.
    4) prior to running ``pip`` below, make sure the branch is correct (install
       from main!)
    5) Install ``rex`` and its dependencies by running:
       ``pip install .`` (or ``pip install -e .`` if running a dev branch
       or working on the source code)

3. Check that ``rex`` was installed successfully
    1) From any directory, run the following commands. This should return the
       help pages for the CLI's.

        - ``rex``
        - ``NSRDBX``
        - ``WINDX``
        - ``US-wave``

rex command line tools
======================

- `rex <https://natlabrockies.github.io/rex/_cli/rex.html#rex>`_
- `NSRDBX <https://natlabrockies.github.io/rex/_cli/NSRDBX.html#NSRDBX>`_
- `WINDX <https://natlabrockies.github.io/rex/_cli/WINDX.html#WINDX>`_
- `US-wave <https://natlabrockies.github.io/rex/_cli/US-wave.html#US-wave>`_
- `WaveX <https://natlabrockies.github.io/rex/_cli/WaveX.html#Wavex>`_
- `MultiYearX <https://natlabrockies.github.io/rex/_cli/MultiYearX.html#MultiYearX>`_
- `rechunk <https://natlabrockies.github.io/rex/_cli/rechunk.html#rechunk>`_
- `temporal-stats <https://natlabrockies.github.io/rex/_cli/temporal-stats.html#temporal-stats>`_
- `wind-rose <https://natlabrockies.github.io/rex/_cli/wind-rose.html#wind-rose>`_
