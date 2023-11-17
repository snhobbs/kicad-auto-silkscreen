import logging

import click
import pcbnew

from . import kicad_auto_silkscreen


@click.command()
@click.option("--board", required=True)
@click.option("--out", required=True)
def main(board, out):
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    a = kicad_auto_silkscreen.AutoSilkscreen(pcb=pcbnew.LoadBoard(board))
    a.set_step_size(0.127)
    a.set_max_allowed_distance(100)
    a.set_only_process_selection(False)
    a.set_ignore_vias(True)

    nb_moved, nb_total = a.run()

    a.pcb.Save(out)


if __name__ == "__main__":
    main()
