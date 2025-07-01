import logging

import click
import pcbnew

from . import kicad_auto_silkscreen
from . kicad_auto_silkscreen import SilkscreenConfig


@click.command()
@click.option("--board", type=str, required=True)
@click.option("--step-size", type=float, default=0.2)
@click.option("--out", type=str, required=True)
def main(board, step_size, out):
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    config = SilkscreenConfig(
        max_allowed_distance = 5.0,
        step_size = 0.2,
        only_process_selection = False,
        ignore_vias = True,
        deflate_factor = 1.0,
        debug = True
    )

    a = kicad_auto_silkscreen.AutoSilkscreen(pcb=pcbnew.LoadBoard(board), config=config)

    nb_moved, nb_total = a.run()

    a.pcb.Save(out=out)


if __name__ == "__main__":
    main()
