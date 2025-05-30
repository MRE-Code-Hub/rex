# -*- coding: utf-8 -*-
# pylint: disable=all
"""
WindX Command Line Interface
"""
import click
import logging
import os

from rex.resource_extraction.resource_extraction import WindX, MultiFileWindX
from rex.resource_extraction.resource_cli import box as box_cmd
from rex.resource_extraction.resource_cli import dataset as dataset_grp
from rex.resource_extraction.resource_cli import multi_site as multi_site_cmd
from rex.resource_extraction.resource_cli import _parse_sites
from rex.resource_extraction.resource_cli import region as region_cmd
from rex.resource_extraction.resource_cli import site as site_cmd
from rex.utilities.loggers import init_logger
from rex.utilities.utilities import check_res_file
from rex import __version__

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__)
@click.option('--wind_h5', '-h5', required=True,
              type=click.Path(),
              help=('Path to Resource .h5 file'))
@click.option('--out_dir', '-o', required=True, type=click.Path(),
              help='Directory to dump output files')
@click.option('--log_file', '-log', default=None, type=click.Path(),
              show_default=True,
              help='Path to .log file, if None only log to stdout')
@click.option('-v', '--verbose', is_flag=True,
              help='Flag to turn on debug logging. Default is not verbose.')
@click.pass_context
def main(ctx, wind_h5, out_dir, log_file, verbose):
    """
    WindX Command Line Interface
    """
    ctx.ensure_object(dict)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    ctx.obj['H5'] = wind_h5
    ctx.obj['OUT_DIR'] = out_dir
    ctx.obj['CLS_KWARGS'] = {}

    multi_h5_res, hsds = check_res_file(wind_h5)
    if multi_h5_res and not hsds:
        assert os.path.exists(os.path.dirname(wind_h5))
        ctx.obj['CLS'] = MultiFileWindX
    elif hsds:
        ctx.obj['CLS_KWARGS']['hsds'] = hsds
    else:
        assert os.path.exists(wind_h5)

        ctx.obj['CLS'] = WindX

    if verbose:
        log_level = 'DEBUG'
    else:
        log_level = 'INFO'

    if log_file is not None:
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    init_logger('rex', log_file=log_file, log_level=log_level)

    logger.info('Extracting Wind data from {}'.format(wind_h5))
    logger.info('Outputs to be stored in: {}'.format(out_dir))


@main.command()
@click.option('--hub_height', '-h', type=int, required=True,
              help='Hub height to extract SAM variables at')
@click.option('--lat_lon', '-ll', nargs=2, type=float,
              default=None, show_default=True,
              help='(lat, lon) coordinates of interest')
@click.option('--gid', '-gid', type=int, default=None, show_default=True,
              help='Resource gid of interest')
@click.option('--sites', '-s', type=click.Path(exists=True), default=None,
              show_default=True,
              help=('.csv or .json file with columns "latitude", "longitude" '
                    'OR "gid"'))
@click.pass_context
def sam_datasets(ctx, hub_height, lat_lon, gid, sites):
    """
    Extract all datasets needed for SAM for the nearest pixel(s) to the given
    (lat, lon) coordinates, the given resource gid, or the give sites
    """
    if not lat_lon:
        lat_lon = None

    inputs = set((lat_lon, gid, sites))
    if len(inputs) == 1:
        msg = "Must supply '--lat-lon', '--gid', or '--sites'!"
        click.echo(msg)
        raise click.Abort(msg)
    elif len(inputs) > 2:
        msg = ("You must only supply one of '--lat-lon', '--gid', or "
               "'--sites'!")
        click.echo(msg)
        raise click.Abort(msg)

    if lat_lon or gid:
        logger.info('Saving data to {}'.format(ctx.obj['OUT_DIR']))
        with ctx.obj['CLS'](ctx.obj['H5'], **ctx.obj['CLS_KWARGS']) as f:
            if lat_lon is not None:
                out_path = os.path.join(ctx.obj['OUT_DIR'],
                                        'SAM_{}.csv'.format(lat_lon))
                f.get_SAM_lat_lon(lat_lon, hub_height,
                                  out_path=out_path)
            elif gid is not None:
                out_path = os.path.join(ctx.obj['OUT_DIR'],
                                        'SAM_{}.csv'.format(gid))
                f.get_SAM_gid(gid, hub_height, out_path=out_path)

    else:
        name, gid, lat_lon = _parse_sites(sites)
        with ctx.obj['CLS'](ctx.obj['H5'], **ctx.obj['CLS_KWARGS']) as f:
            meta = f['meta']
            if lat_lon is not None:
                SAM_df = f.get_SAM_lat_lon(lat_lon, hub_height)
            elif gid is not None:
                SAM_df = f.get_SAM_gid(gid, hub_height)

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


@main.group()
@click.option('--dataset', '-d', type=str, required=True,
              help='Dataset to extract')
@click.pass_context
def dataset(ctx, dataset):
    """
    Extract a single dataset
    """
    ctx.invoke(dataset_grp, dataset=dataset)


@dataset.command()
@click.option('--lat_lon', '-ll', nargs=2, type=float,
              default=None, show_default=True,
              help='(lat, lon) coordinates of interest')
@click.option('--gid', '-gid', type=int, default=None, show_default=True,
              help='Resource gid of interest')
@click.pass_context
def site(ctx, lat_lon, gid):
    """
    Extract the nearest pixel to the given (lat, lon) coordinates OR the
    given resource gid
    """

    ctx.invoke(site_cmd, lat_lon=lat_lon, gid=gid)


@dataset.command()
@click.option('--region', '-r', type=str, required=True,
              help='Region to extract')
@click.option('--region_col', '-col', type=str, default='state',
              show_default=True,
              help='Meta column to search for region')
@click.option('--timestep', '-ts', type=str, default=None, show_default=True,
              help='Time-step to extract')
@click.pass_context
def region(ctx, region, region_col, timestep):
    """
    Extract a single dataset for all gids in the given region
    """

    ctx.invoke(region_cmd, region=region, region_col=region_col,
               timestep=timestep)


@dataset.command()
@click.option('--lat_lon_1', '-ll1', nargs=2, type=float,
              required=True,
              help='One corner of the bounding box')
@click.option('--lat_lon_2', '-ll2', nargs=2, type=float,
              required=True,
              help='The other corner of the bounding box')
@click.option('--file_suffix', '-fs', default=None, show_default=True,
              help='Filename suffix')
@click.option('--timestep', '-ts', type=str, default=None, show_default=True,
              help='Timestep to extract')
@click.pass_context
def box(ctx, lat_lon_1, lat_lon_2, file_suffix, timestep):
    """
    Extract all pixels in the given bounding box
    """

    ctx.invoke(box_cmd, lat_lon_1=lat_lon_1, lat_lon_2=lat_lon_2,
               file_suffix=file_suffix, timestep=timestep)


@dataset.command()
@click.option('--sites', '-s', type=click.Path(exists=True), required=True,
              help=('.csv or .json file with columns "latitude", "longitude" '
                    'OR "gid"'))
@click.pass_context
def multi_site(ctx, sites):
    """
    Extract multiple sites given in '--sites' .csv or .json as
    "latitude", "longitude" pairs OR "gid"s

    """
    ctx.invoke(multi_site_cmd, sites=sites)


if __name__ == '__cli__':
    try:
        main(obj={})
    except Exception:
        logger.exception('Error running WindX CLI')
        raise
