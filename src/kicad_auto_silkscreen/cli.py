import logging

import click
import pcbnew

from . import kicad_auto_silkscreen
from . kicad_auto_silkscreen import SilkscreenConfig


@click.command()
@click.option("--board", type=str, required=True)
@click.option("--step-size", type=float, default=0.2)
@click.option("--method", type=str, default="anneal")
@click.option("--deflate_factor", type=float, default=0.9)
@click.option("--max-distance", type=float, default=2.5)
@click.option("--maxiter", type=int, default=10)
@click.option("--out", type=str, required=True)
def main(board, step_size, method, deflate_factor, max_distance, maxiter, out):
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    config = SilkscreenConfig(
        max_allowed_distance = max_distance,
        step_size = step_size,
        only_process_selection = False,
        ignore_vias = True,
        maxiter = maxiter,
        deflate_factor = deflate_factor,
        method=method,
        debug = True
    )

    a = kicad_auto_silkscreen.AutoSilkscreen(pcb=pcbnew.LoadBoard(board), config=config)

    nb_moved, nb_total = a.run()

    a.pcb.Save(out)


if __name__ == "__main__":
    main()
