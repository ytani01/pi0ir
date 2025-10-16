#
# (c) 2025 Yoichi Tanibayashi
#
"""__main__.py"""

import click
import pigpio

from . import __version__
from .cmd_iranalyze import CmdIrAnalyze
from .utils.clickutils import click_common_opts
from .utils.mylogger import errmsg, get_logger

DEF_PIN = 24


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


@cli.command()
@click.option(
    "--pin",
    "-p",
    type=int,
    default=DEF_PIN,
    show_default=True,
    help="GPIO pin number",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="verbose mode",
)
@click_common_opts(__version__)
def analyze(ctx, pin, verbose, debug):
    """Ir Analyze."""
    __log = get_logger(__name__, debug)
    __log.debug("cmd_name=%s", ctx.command.name)
    __log.debug("pin=%s, verbose=%s", pin, verbose)

    pi = None
    app = None
    try:
        pi = get_pi(debug)
        print("AAA")
        app = CmdIrAnalyze(pin, verbose=verbose, debug=debug)
        print("BBB")
        app.main()
        print("CCC")

    except Exception as _e:
        __log.error(errmsg(_e))

    finally:
        if app:
            app.end()
        if pi:
            pi.stop()
