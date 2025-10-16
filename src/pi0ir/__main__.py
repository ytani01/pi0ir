#
# (c) 2025 Yoichi Tanibayashi
#
"""__main__.py"""
import os

import click
import pigpio

form . import __version__
from .utils.clickutils import click_common_opts
from .utils.mylogger import errmsg, get_logger


def get_pi(debug=False) -> pigpio.pi:
    """Initialize and return a pigpio.pi instance.
    If connection fails, log an error and return None.
    """
    __log = get_logger(__name__, debug)

    pi = pigpio.pi()
    if not pi.connected:
        __log.error("pigpio daemon not connected.")
        raise ConnectionError("pigpio daemon not connected.")
    return pi


def print_pins_error(ctx):
    """Print error message and help."""
    click.echo()
    click.echo(click.style("Error: Please specify GPIO pins.", fg="red"))
    click.echo()
    click.echo(f"{ctx.get_help()}")


@click.group()
@click_common_opts(__version__)
def cli(ctx, debug):
    """pi0servo CLI top."""
    cmd_name = ctx.info_name
    subcmd_name = ctx.invoked_subcommand

    ___log = get_logger(cmd_name, debug)

    ___log.debug("cmd_name=%s, subcmd_name=%s", cmd_name, subcmd_name)

    if subcmd_name is None:
        click.echo(ctx.get_help())


cli.command()
@click.argument("pin", type=int, nargs=1)
@click_common_opts(__version__)
def analyze(ctx, pin, debug):
    """Ir Analyze."""
    __log = get_logger(__name__, debug)
    __log.debug("cmd_name=%s", ctx.command.name)
    __log.debug("pin=%s", pin)

    pi = None
    app = None
    try:
        print(pi)
        print(app)

    except Exception as _e:
        __log.error(errmsg(_e))

    finally:
        if app:
            app.end()
        if pi:
            pi.stop()
