National Solar Radiation Database (NSRDB)
=========================================

The National Solar Radiation Database (NSRDB) is a serially complete
collection of meteorological and solar irradiance data sets for the
United States and a growing list of international locations for 1998-2017. The
NSRDB provides foundational information to support U.S. Department of Energy
programs, research, and the general public.

The NSRDB provides time-series data at 30 minute resolution of resource
averaged over surface cells of 0.038 degrees in both latitude and longitude,
or nominally 4 km in size. The solar radiation values represent the resource
available to solar energy systems. The data was created using cloud properties
which are generated using the AVHRR Pathfinder Atmospheres-Extended (PATMOS-x)
algorithms developed by the University of Wisconsin. Fast all-sky radiation
model for solar applications (FARMS) in conjunction with the cloud properties,
and aerosol optical depth (AOD) and precipitable water vapor (PWV) from
ancillary source are used to estimate solar irradiance (GHI, DNI, and DHI).
The Global Horizontal Irradiance (GHI) is computed for clear skies using the
REST2 model. For cloud scenes identified by the cloud mask, FARMS is used to
compute GHI. The Direct Normal Irradiance (DNI) for cloud scenes is then
computed using the DISC model. The PATMOS-X model uses half-hourly radiance
images in visible and infrared channels from the GOES series of geostationary
weather satellites.  Ancillary variables needed to run REST2 and FARMS (e.g.,
aerosol optical depth, precipitable water vapor, and albedo) are derived from
the the Modern Era-Retrospective Analysis (MERRA-2) dataset. Temperature and
wind speed data are also derived from MERRA-2 and provided for use in SAM to
compute PV generation.

The following variables are provided by the NSRDB:

- Irradiance:

    - Global Horizontal (ghi)
    - Direct Normal (dni)
    - Diffuse (dhi)

- Clear-sky Irradiance
- Cloud Type
- Dew Point
- Temperature
- Surface Albedo
- Pressure
- Relative Humidity
- Solar Zenith Angle
- Precipitable Water
- Wind Direction
- Wind Speed
- Fill Flag
- Angstrom wavelength exponent (alpha)
- Aerosol optical depth (aod)
- Aerosol asymmetry parameter (asymmetry)
- Cloud optical depth (cld_opd_dcomp)
- Cloud effective radius (cld_ref_dcomp)
- cloud_press_acha
- Reduced ozone vertical pathlength (ozone)
- Aerosol single-scatter albedo (ssa)


Data Format
-----------

The data is provided in high density data file (.h5) separated by year. The
variables mentioned above are provided in 2 dimensional time-series arrays
(called "datasets" in h5 files) with dimensions (time x location). The temporal
axis is defined by the ``time_index`` dataset, while the positional axis is
defined by the ``meta`` dataset. We typically refer to a single site in the
data with a ``gid``, which is just the index of the site in the meta data
(zero-indexed). For storage efficiency each variable has been scaled and stored
as an integer. The scale_factor is provided in the ``psm_scale_factor``
attribute. The units for the variable data is also provided as an attribute
(``psm_units``).

*More recent years of NSRDB data have added "scale_factor" and "units" in
addition to "psm_scale_factor" and "psm_units" in order to be consistent
with the other NREL datasets.*


Data Access Examples
--------------------

The easiest way to access and extract WTK and NSRDB data is by using the
Resource eXtraction tool `rex <https://nrel.github.io/rex/>`_.

Example scripts to extract wave resource data using the command line or python
are provided below.

If you are on the NREL Eagle supercomputer, you can use the example below, but
change the filepath to the appropriate WTK or NSRDB file location on
``/datasets/`` and set ``hsds=False``. See the basic `rex Resource handler
examples <https://nrel.github.io/rex/_autosummary/rex.resource.Resource.html#rex-resource-resource>`_
for similar use examples.

You can use ``rex`` to access WTK and NSRDB data from your local computer using
`HSDS
<https://www.hdfgroup.org/solutions/highly-scalable-data-service-hsds/>`_. In
order to do so, you need to setup HSDS and h5pyd. See `the rex-HSDS
instructions <https://nrel.github.io/rex/misc/examples.hsds.html>`_ for more
details on how to do this.

*Please note that the NREL-hosted HSDS API is for demonstration purposes only,
if you would like to use HSDS for production runs of reV please setup your own
service with the instructions here:
https://nrel.github.io/rex/misc/examples.hsds.html*

NSRDB CLI
+++++++++

The `NSRDBX <https://nrel.github.io/rex/rex/rex.resource_extaction.nsrdb_cli.html#nsrdbx>`_
command line utility provides the following options and commands:

.. code-block:: bash

  NSRDBX --help

  Usage: NSRDBX [OPTIONS] COMMAND [ARGS]...

    NSRDBX Command Line Interface

  Options:
    -h5, --solar_h5 PATH  Path to Resource .h5 file  [required]
    -o, --out_dir PATH    Directory to dump output files  [required]
    -v, --verbose         Flag to turn on debug logging. Default is not verbose.
    --help                Show this message and exit.

  Commands:
    dataset     Extract a single dataset
    multi-site  Extract multiple sites given in '--sites' .csv or .json as...
    sam-file    Extract all datasets needed for SAM for the nearest pixel to...

NSRDBX python class
+++++++++++++++++++

.. code-block:: python

  from rex import NSRDBX

  nsrdb_file = '/nrel/nsrdb/v3/nsrdb_2018.h5'
  with NSRDBX(nsrdb_file, hsds=True) as f:
      meta = f.meta
      time_index = f.time_index
      dni = f['dni', :, ::1000]

``NSRDBX`` also allows easy extraction of the nearest site to a desired
(lat, lon) location:

.. code-block:: python

  from rex import NSRDBX

  nsrdb_file = '/nrel/nsrdb/v3/nsrdb_2018.h5'
  nrel = (39.741931, -105.169891)
  with NSRDBX(nsrdb_file, hsds=True) as f:
      nrel_dni = f.get_lat_lon_df('dni', nrel)

or to extract all sites in a given region:

.. code-block:: python

  from rex import NSRDBX

  nsrdb_file = '/nrel/nsrdb/v3/nsrdb_2018.h5'
  state='Colorado'
  with NSRDBX(nsrdb_file, hsds=True) as f:
      date = '2018-07-04 18:00:00'
      dni_map = f.get_timestep_map('dni', date, region=state,
                                   region_col='state')

Lastly, ``NSRDBX`` can be used to extract all variables needed to run SAM at a
given location:

.. code-block:: python

  from rex import NSRDBX

  nsrdb_file = '/nrel/nsrdb/v3/nsrdb_2018.h5'
  nrel = (39.741931, -105.169891)
  with NSRDBX(nsrdb_file, hsds=True) as f:
      nrel_sam_vars = f.get_SAM_lat_lon(nrel)

References
----------

For more information about the NSRDB please see the `website <https://nsrdb.nrel.gov/>`_
Users of the NSRDB should please cite:

- `Sengupta, M., Y. Xie, A. Lopez, A. Habte, G. Maclaurin, and J. Shelby. 2018. "The National Solar Radiation Data Base (NSRDB)." Renewable and Sustainable Energy Reviews  89 (June): 51-60. <https://www.sciencedirect.com/science/article/pii/S136403211830087X?via%3Dihub>`_
