import logging
from dataclasses import fields
import click
import pcbnew
from . import kicad_auto_silkscreen
from . kicad_auto_silkscreen import SilkscreenConfig


class DynamicSilkscreenCommand(click.Command):
    def __init__(self, *args, **kwargs):
        # Dynamically add options based on the dataclass fields
        for field in fields(SilkscreenConfig):
            option_name = f'--{field.name.replace("_", "-")}'
            field_type = field.type
            default_value = getattr(SilkscreenConfig, field.name)

            # Handle boolean flags
            if field_type == bool:
                option = click.Option(param_decls=[option_name], is_flag=True, default=dault_value)
            else:
                # For other types, use the appropriate click type (str, int, float, etc.)
                option = click.Option(param_decls=[option_name], default=default_value, type=field_type)

            kwargs.setdefault('params', []).append(option)
        super().__init__(*args, **kwargs)


@click.command(cls=DynamicSilkscreenCommand)
@click.option("--board", type=str, required=True)
@click.option("--out", type=str, required=True)
def main(board, out, **config_options):
    # Instantiate the configuration dataclass
    config = SilkscreenConfig(**config_options)
    a = kicad_auto_silkscreen.AutoSilkscreen(pcb=pcbnew.LoadBoard(board), config=config)
    nb_moved, nb_total = a.run()
    a.pcb.Save(out)
    click.echo(f"Config: {config}")
    click.echo(f"Board: {board}")
    click.echo(f"Output file: {out}")


if __name__ == "__main__":
    main()
