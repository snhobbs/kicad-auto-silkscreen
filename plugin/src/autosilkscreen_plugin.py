import os
import sys
from pathlib import Path

import pcbnew
import wx

if __name__ == "__main__":
    # Circumvent the "scripts can't do relative imports because they are not
    # packages" restriction by asserting dominance and making it a package!
    dirname = os.path.dirname(os.path.abspath(__file__))
    __package__ = os.path.basename(dirname)
    sys.path.insert(0, os.path.dirname(dirname))
    __import__(__package__)

from . import auto_silkscreen_dialog
from .kicad_auto_silkscreen import AutoSilkscreen

_board = None


def get_board():
    global _board
    if _board is None:
        _board = pcbnew.GetBoard()
    return _board


class Meta:
    title = "AutoSilkscreen"
    toolname = "AutoSilkscreen"
    category = "Modify PCB"
    body = "Automatically moves the silkscreen reference designators to prevent overlap"


class AutoSilkscreenPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.show_toolbar_button = True
        self.name = Meta.title
        self.category = Meta.category
        self.show_toolbar_button = True
        self.pcbnew_icon_support = hasattr(self, "show_toolbar_button")
        icon_dir = Path(__file__).parent
        self.icon_file_name_path = icon_dir / "icon-24x24.png"
        self.icon_file_name = self.icon_file_name_path.as_posix()
        print(icon_dir, str(self.icon_file_name))
        assert self.icon_file_name_path.exists()
        self.description = Meta.body

    def Run(self):
        dialog = auto_silkscreen_dialog.AutoSilkscreenDialog(parent=None)
        modal_result = dialog.ShowModal()
        if modal_result == wx.ID_OK:
            try:
                a = AutoSilkscreen(pcb=get_board())
                a.set_step_size(float(dialog.m_stepSize.GetValue().replace(",", ".")))
                a.set_max_allowed_distance(
                    float(dialog.m_maxDistance.GetValue().replace(",", "."))
                )
                a.set_only_process_selection(dialog.m_onlyProcessSelection.IsChecked())
                a.set_ignore_vias(dialog.m_silkscreenOnVia.IsChecked())

                nb_moved, nb_total = a.run()
                wx.MessageBox(
                    f"Successfully moved {nb_moved}/{nb_total} items!",
                    "AutoSilkscreen completed",
                    wx.OK,
                )
            except ValueError:
                wx.MessageBox(
                    "Invalid value entered.",
                    "AutoSilkscreen error",
                    wx.ICON_ERROR | wx.OK,
                )
        dialog.Destroy()


if __name__ == "__main__":
    try:
        _board = pcbnew.LoadBoard(sys.argv[1])
    except IndexError:
        pass
    # run_with_dialog()

    app = wx.App()
    p = AutoSilkscreenPlugin()
    p.Run()
