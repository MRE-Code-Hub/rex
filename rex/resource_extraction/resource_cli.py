# -*- coding: utf-8 -*-
"""
ResourceX Command Line Interface
"""
import click
import logging
import os
import pandas as pd

from rex.resource_extraction.resource_extraction import (ResourceX,
                                                         MultiFileResourceX)
from rex.utilities.loggers import init_mult
from rex.utilities.utilities import check_res_file

logger = logging.getLogger(__name__)


@click.group()
@click.option('--resource_h5', '-h5', required=True,
              type=click.Path(),
              help=('Path to Resource .h5 file'))
@click.option('--out_dir', '-o', required=True, type=click.Path(),
              help='Directory to dump output files')
@click.option('-v', '--verbose', is_flag=True,
              help='Flag to turn on debug logging. Default is not verbose.')
@click.pass_context
def main(ctx, resource_h5, out_dir, verbose):
    """
    ResourceX Command Line Interface
    """
    ctx.ensure_object(dict)
    ctx.obj['H5'] = resource_h5
    ctx.obj['OUT_DIR'] = out_dir
    ctx.obj['CLS_KWARGS'] = {}

    multi_h5_res, hsds = check_res_file(resource_h5)
    if multi_h5_res:
        assert os.path.exists(os.path.dirname(resource_h5))
        ctx.obj['CLS'] = MultiFileResourceX
    else:
        if hsds:
            ctx.obj['CLS_KWARGS']['hsds'] = hsds
        else:
            assert os.path.exists(resource_h5)

        ctx.obj['CLS'] = ResourceX

    name = os.path.splitext(os.path.basename(resource_h5))[0]
    init_mult(name, out_dir, verbose=verbose, node=True,
              modules=[__name__, 'rex.resource_extraction',
                       'rex.resource'])

    logger.info('Extracting Resource data from {}'.format(resource_h5))
    logger.info('Outputs to be stored in: {}'.format(out_dir))


@main.command()
@click.option('--lat_lon', '-ll', nargs=2, type=click.Tuple([float, float]),
              default=None,
              help='(lat, lon) coordinates of interest')
@click.option('--gid', '-g', type=int, default=None,
              help='Resource gid of interest')
@click.pass_context
def sam_file(ctx, lat_lon, gid):
    """
    Extract all datasets needed for SAM for the nearest pixel to the given
    (lat, lon) coordinates OR the given resource gid
    """
    if lat_lon is None and gid is None:
        click.echo("Must supply '--lat-lon' OR '--gid'!")
        raise click.Abort()
    elif lat_lon and gid:
        click.echo("You must only supply '--lat-lon' OR '--gid'!")
        raise click.Abort()

    logger.info('Saving data to {}'.format(ctx.obj['OUT_DIR']))
    with ctx.obj['CLS'](ctx.obj['H5'], **ctx.obj['CLS_KWARGS']) as f:
        if lat_lon is not None:
            f.get_SAM_lat_lon(lat_lon, out_path=ctx.obj['OUT_DIR'])
        elif gid is not None:
            gid = f._get_nearest(lat_lon)
            f.get_SAM_gid(gid, out_path=ctx.obj['OUT_DIR'])


@main.group()
@click.option('--dataset', '-d', type=str, required=True,
              help='Dataset to extract')
@click.pass_context
def dataset(ctx, dataset):
    """
    Extract a single dataset
    """
    ctx.obj['DATASET'] = dataset


@dataset.command()
@click.option('--lat_lon', '-ll', nargs=2, type=click.Tuple([float, float]),
              default=None,
              help='(lat, lon) coordinates of interest')
@click.option('--gid', '-g', type=int, default=None,
              help='Resource gid of interest')
@click.pass_context
def site(ctx, lat_lon, gid):
    """
    Extract the nearest pixel to the given (lat, lon) coordinates OR the given
    resource gid
    """
    if lat_lon is None and gid is None:
        click.echo("Must supply '--lat-lon' OR '--gid'!")
        raise click.Abort()
    elif lat_lon and gid:
        click.echo("You must only supply '--lat-lon' OR '--gid'!")
        raise click.Abort()

    dataset = ctx.obj['DATASET']
    with ctx.obj['CLS'](ctx.obj['H5'], **ctx.obj['CLS_KWARGS']) as f:
        if lat_lon is not None:
            site_df = f.get_lat_lon_df(dataset, lat_lon)
        elif gid is not None:
            site_df = f.get_gid_df(dataset, gid)

    gid = site_df.name
    out_path = "{}-{}.csv".format(dataset, gid)
    out_path = os.path.join(ctx.obj['OUT_DIR'], out_path)
    logger.info('Saving data to {}'.format(out_path))
    site_df.to_csv(out_path)


@dataset.command
@click.option('--region', '-r', type=str, required=True,
              help='Region to extract')
@click.option('--region_col', '-col', type=str, default='state',
              help='Meta column to search for region')
@click.option('--timestep', '-ts', type=str, default=None,
              help='Timestep to extract')
@click.pass_context
def region(ctx, region, region_col, timestep):
    """
    Extract all pixels in the given region
    """
    dataset = ctx.obj['DATASET']
    if timestep is None:
        with ctx.obj['CLS'](ctx.obj['H5'], **ctx.obj['CLS_KWARGS']) as f:
            region_df = f.get_region_df(dataset, region, region_col=region_col)
            meta = f['meta']

        out_path = "{}-{}.csv".format(dataset, region)
        out_path = os.path.join(ctx.obj['OUT_DIR'], out_path)
        logger.info('Saving data to {}'.format(out_path))
        region_df.to_csv(out_path)

        out_path = "{}-meta.csv".format(region)
        out_path = os.path.join(ctx.obj['OUT_DIR'], out_path)
        meta = meta.loc[region_df.columns]
        logger.info('Saving meta data to {}'.format(out_path))
        meta.to_csv(out_path)
    else:
        with ctx.obj['CLS'](ctx.obj['H5'], **ctx.obj['CLS_KWARGS']) as f:
            map_df = f.get_timestep_map(dataset, timestep, region=region,
                                        region_col=region_col)

        out_path = "{}-{}-{}.csv".format(dataset, region, timestep)
        out_path = os.path.join(ctx.obj['OUT_DIR'], out_path)
        logger.info('Saving data to {}'.format(out_path))
        map_df.to_csv(out_path)


@dataset.command()
@click.option('--lat_lon_1', '-ll1', nargs=2, type=click.Tuple([float, float]),
              required=True,
              help='One corner of the bounding box')
@click.option('--lat_lon_2', '-ll2', nargs=2, type=click.Tuple([float, float]),
              required=True,
              help='The other corner of the bounding box')
@click.option('--file_suffix', '-fs', default=None,
              help='File name suffix')
@click.option('--timestep', '-ts', type=str, default=None,
              help='Timestep to extract')
@click.pass_context
def box(ctx, lat_lon_1, lat_lon_2, file_suffix, timestep):
    """
    Extract all pixels in the given bounding box
    """
    dataset = ctx.obj['DATASET']
    if file_suffix is None:
        file_suffix = 'box'

    if timestep is None:
        with ctx.obj['CLS'](ctx.obj['H5'], **ctx.obj['CLS_KWARGS']) as f:
            region_df = f.get_box_df(dataset, lat_lon_1, lat_lon_2)
            meta = f['meta']

        out_path = "{}-{}.csv".format(dataset, file_suffix)
        out_path = os.path.join(ctx.obj['OUT_DIR'], out_path)
        logger.info('Saving data to {}'.format(out_path))
        region_df.to_csv(out_path)

        out_path = "{}-meta.csv".format(file_suffix)
        out_path = os.path.join(ctx.obj['OUT_DIR'], out_path)
        meta = meta.loc[region_df.columns]
        logger.info('Saving meta data to {}'.format(out_path))
        meta.to_csv(out_path)
    else:
        with ctx.obj['CLS'](ctx.obj['H5'], **ctx.obj['CLS_KWARGS']) as f:
            map_df = f.get_timestep_map(dataset, timestep,
                                        box=(lat_lon_1, lat_lon_2))

        out_path = "{}-{}-{}.csv".format(dataset, file_suffix, timestep)
        out_path = os.path.join(ctx.obj['OUT_DIR'], out_path)
        logger.info('Saving data to {}'.format(out_path))
        map_df.to_csv(out_path)


def _parse_sites(sites):
    """
    Parse sites

    Parameters
    ----------
    sites : str
        Path to .csv of .json containing sites to extract

    Returns
    -------
    name : str
        sites file name
    gid : list | None
        Gids to extract
    lat_lon : list | None
        Lat, lon pairs to extract
    """
    name = os.path.splitext(os.path.basename(sites))[0]
    if sites.endswith('.csv'):
        sites = pd.read_csv(sites)
    elif sites.endswith('.json'):
        sites = pd.read_json(sites)
    else:
        raise RuntimeError("'--sites' must be a .csv or .json file!")

    if 'gid' in sites:
        gid = sites['gid'].values
        lat_lon = None
    elif 'latitude' in sites and 'longitude' in sites:
        gid = None
        lat_lon = sites[['latitude', 'longitude']].values
    else:
        raise RuntimeError('Must supply site "gid"s or "latitude" and '
                           '"longitude" as columns in "--sites" file')

    return name, gid, lat_lon


@main.command()
@click.option('--sites', '-s', type=click.Path(exists=True), required=True,
              help=('.csv or .json file with columns "latitude", "longitude" '
                    'OR "gid"'))
@click.option('--dataset', '-d', type=str, required=True,
              help='Dataset to extract, if sam datasets us "SAM" or "sam"')
@click.pass_context
def multi_site(ctx, sites, dataset):
    """
    Extract multiple sites given in '--sites' .csv or .json as
    "latitude", "longitude" pairs OR "gid"s
    """
    name, gid, lat_lon = _parse_sites(sites)
    if dataset.lower() == 'sam':
        with ctx.obj['CLS'](ctx.obj['H5'], **ctx.obj['CLS_KWARGS']) as f:
            meta = f['meta']
            if lat_lon is not None:
                SAM_df = f.get_SAM_lat_lon(lat_lon)
            elif gid is not None:
                SAM_df = f.get_SAM_gid(gid)

        gids = []
        for df in SAM_df:
            gids.append(int(df.name.split('-')[-1]))
            out_path = "{}-{}.csv".format(df.name, name)
            out_path = os.path.join(ctx.obj['OUT_DIR'], out_path)
            logger.info('Saving data to {}'.format(out_path))
            df.to_csv(out_path)

        out_path = "{}-meta.csv".format(name)
        out_path = os.path.join(ctx.obj['OUT_DIR'], out_path)
        meta = meta.loc[gids]
        logger.info('Saving meta data to {}'.format(out_path))
        meta.to_csv(out_path)
    else:
        with ctx.obj['CLS'](ctx.obj['H5'], **ctx.obj['CLS_KWARGS']) as f:
            meta = f['meta']
            if lat_lon is not None:
                site_df = f.get_lat_lon_df(dataset, lat_lon)
            elif gid is not None:
                site_df = f.get_gid_df(dataset, gid)

        out_path = "{}-{}.csv".format(dataset, name)
        out_path = os.path.join(ctx.obj['OUT_DIR'], out_path)
        logger.info('Saving data to {}'.format(out_path))
        site_df.to_csv(out_path)

        out_path = "{}-meta.csv".format(name)
        out_path = os.path.join(ctx.obj['OUT_DIR'], out_path)
        meta = meta.loc[site_df.columns]
        logger.info('Saving meta data to {}'.format(out_path))
        meta.to_csv(out_path)


if __name__ == '__main__':
    try:
        main(obj={})
    except Exception:
        logger.exception('Error running ResourceX CLI')
        raise