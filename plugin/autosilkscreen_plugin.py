import os
import pcbnew
import gettext
import wx, math

from pcbnew import VECTOR2I

from . import auto_silkscreen_dialog
from kicad_auto_silkscreen import isSilkscreen, log, BB_in_SHAPE_POLY_SET, distance, filter_distance, AutoSilkscreen

class AutoSilkscreenPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = u"AutoSilkscreen"
        self.category = u"Modify PCB"
        self.description = u"Automatically moves the silkscreen reference designators to prevent overlap"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'logo.png')

    def Run(self):
        dialog = auto_silkscreen_dialog.AutoSilkscreenDialog(pcb=pcbnew.GetBoard())
        modal_result = dialog.ShowModal()
        if modal_result == wx.ID_OK:
            try:
                a = AutoSilkscreen()
                a.set_step_size(float(dialog.m_stepSize.GetValue().replace(',', '.')))
                a.set_max_allowed_distance(float(dialog.m_maxDistance.GetValue().replace(',', '.')))
                a.set_only_process_selection(dialog.m_onlyProcessSelection.IsChecked())
                a.set_ignore_vias(dialog.m_silkscreenOnVia.IsChecked())

                nb_moved, nb_total = a.run()
                wx.MessageBox('Successfully moved {}/{} items!'.format(nb_moved,nb_total), 'AutoSilkscreen completed', wx.OK)
            except ValueError:
                wx.MessageBox("Invalid value entered.",'AutoSilkscreen error',wx.ICON_ERROR | wx.OK)
        dialog.Destroy()

