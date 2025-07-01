import logging
import math
from dataclasses import dataclass
from typing import Any, List, Tuple
import pcbnew
from pcbnew import VECTOR2I
import numpy as np

# --- Config and Utility Classes ---

@dataclass
class SilkscreenConfig:
    max_allowed_distance: float = 5.0   # mm
    step_size: float = 0.1              # mm
    only_process_selection: bool = False
    ignore_vias: bool = True
    deflate_factor: float = 1.0
    debug: bool = True

def is_silkscreen(item) -> bool:
    if item is None:
        return False
    if not (item.IsOnLayer(pcbnew.B_SilkS) or item.IsOnLayer(pcbnew.F_SilkS)):
        return False
    if hasattr(item, "IsVisible") and not item.IsVisible():
        return False
    return True

def distance(a, b) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)

def filter_distance(item_center, max_d, list_items) -> list:
    filtered_items = []
    for i in list_items:
        max_i_size = math.hypot(i.GetBoundingBox().GetHeight(), i.GetBoundingBox().GetWidth())
        if distance(item_center, i.GetBoundingBox().GetCenter()) < max_d + max_i_size:
            filtered_items.append(i)
    return filtered_items

def bb_in_shape_poly_set(bb, poly, all_in=False):
    """Checks if a BOX2I is (entirely or partly) in a SHAPE_POLY_SET."""
    if all_in:
        return (
            poly.Contains(VECTOR2I(bb.GetLeft(), bb.GetTop())) and
            poly.Contains(VECTOR2I(bb.GetRight(), bb.GetTop())) and
            poly.Contains(VECTOR2I(bb.GetLeft(), bb.GetBottom())) and
            poly.Contains(VECTOR2I(bb.GetRight(), bb.GetBottom())) and
            poly.Contains(VECTOR2I(bb.GetCenter().x, bb.GetCenter().y))
        )
    return (
        poly.Contains(VECTOR2I(bb.GetLeft(), bb.GetTop())) or
        poly.Contains(VECTOR2I(bb.GetRight(), bb.GetTop())) or
        poly.Contains(VECTOR2I(bb.GetLeft(), bb.GetBottom())) or
        poly.Contains(VECTOR2I(bb.GetRight(), bb.GetBottom())) or
        poly.Contains(VECTOR2I(bb.GetCenter().x, bb.GetCenter().y))
    )

# --- Main Class ---

class AutoSilkscreen:
    def __init__(self, pcb: pcbnew.BOARD, config: SilkscreenConfig = SilkscreenConfig()):
        self.pcb = pcb
        self.config = config
        self.max_allowed_distance = pcbnew.FromMM(config.max_allowed_distance)
        self.step_size = pcbnew.FromMM(config.step_size)
        self.only_process_selection = config.only_process_selection
        self.ignore_via = config.ignore_vias
        self.__deflate_factor__ = config.deflate_factor
        self.logger = logging.getLogger("kicad_auto_silkscreen")
        if config.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    def run(self) -> Tuple[int, int]:
        """Main entry point: optimize all eligible silkscreen reference/value positions."""
        vias_all = [trk for trk in self.pcb.Tracks()
                    if not self.ignore_via
                    and isinstance(trk, pcbnew.PCB_VIA)
                    and (trk.TopLayer() == pcbnew.F_Cu or trk.BottomLayer() == pcbnew.B_Cu)]
        tht_pads_all = [pad for pad in self.pcb.GetPads() if pad.HasHole()]
        dwgs_all = [dwg for dwg in self.pcb.GetDrawings() if is_silkscreen(dwg)]
        mask_all = [dwg for dwg in self.pcb.GetDrawings()
                    if dwg.IsOnLayer(pcbnew.F_Mask) or dwg.IsOnLayer(pcbnew.B_Mask)]
        fp_all = list(self.pcb.GetFootprints())
        board_edge = pcbnew.SHAPE_POLY_SET()
        self.pcb.GetBoardPolygonOutlines(board_edge)

        import timeit
        starttime = timeit.default_timer()

        nb_total = 0
        nb_moved = 0

        for fp in fp_all:
            if self.only_process_selection and not fp.IsSelected():
                continue

            value = fp.Value()
            ref = fp.Reference()
            if not is_silkscreen(ref) and not is_silkscreen(value):
                continue

            fp_bb = fp.GetBoundingBox(False, False)
            ref_bb = ref.GetBoundingBox()
            value_bb = value.GetBoundingBox()
            max_fp_size = (
                math.hypot(fp_bb.GetWidth(), fp_bb.GetHeight()) / 2
                + self.max_allowed_distance
            )
            if is_silkscreen(ref) and is_silkscreen(value):
                max_fp_size += (
                    max(
                        math.hypot(ref_bb.GetWidth(), ref_bb.GetHeight()),
                        math.hypot(value_bb.GetWidth(), value_bb.GetHeight()),
                    ) / 2
                )
            elif is_silkscreen(ref):
                max_fp_size += math.hypot(ref_bb.GetWidth(), ref_bb.GetHeight()) / 2
            elif is_silkscreen(value):
                max_fp_size += math.hypot(value_bb.GetWidth(), value_bb.GetHeight()) / 2

            # Filter for local collisions
            vias = filter_distance(fp_bb.GetCenter(), max_fp_size, vias_all)
            modules = filter_distance(fp_bb.GetCenter(), max_fp_size, fp_all)
            tht_pads = filter_distance(fp_bb.GetCenter(), max_fp_size, tht_pads_all)
            masks = filter_distance(fp_bb.GetCenter(), max_fp_size, mask_all)
            dwgs = filter_distance(fp_bb.GetCenter(), max_fp_size, dwgs_all)

            if is_silkscreen(ref):
                nb_total += 1
                if self.place_field(True, fp, modules, board_edge, vias, tht_pads, masks, dwgs):
                    nb_moved += 1
            if is_silkscreen(value):
                nb_total += 1
                if self.place_field(False, fp, modules, board_edge, vias, tht_pads, masks, dwgs):
                    nb_moved += 1

        self.logger.info(f"Execution time is {timeit.default_timer() - starttime:.2f}s")
        self.logger.info(f"Finished ({nb_moved}/{nb_total} moved)")
        return nb_moved, nb_total

    def place_field(self, is_reference: bool, fp, modules, board_edge, vias, tht_pads, masks, dwgs) -> bool:
        """
        Try to find a valid position for the field (reference or value) using a spiral-out grid search.
        Returns True if a valid position is found and set, else False (restores original position).
        """
        item = fp.Reference() if is_reference else fp.Value()
        initial_pos = item.GetPosition()
        fp_bb = fp.GetBoundingBox(False, False)

        # Center and step sizes in mm
        center_x_mm = pcbnew.ToMM(fp_bb.GetCenter().x)
        center_y_mm = pcbnew.ToMM(fp_bb.GetCenter().y)
        max_dist_mm = self.config.max_allowed_distance
        step_mm = self.config.step_size
        max_width_mm = pcbnew.ToMM(fp_bb.GetWidth())

        found = False
        best_pos = None

        for i in np.arange(0, max_dist_mm + step_mm, step_mm):
            max_j = max_width_mm / 2 + i
            for j in np.arange(0, max_j + step_mm, step_mm):
                for dx_mm, dy_mm in [
                    (-j, -i), (j, -i), (-j, i), (j, i),
                    (-i, -j), (i, -j), (-i, j), (i, j)
                ]:
                    candidate_x = pcbnew.FromMM(center_x_mm + dx_mm)
                    candidate_y = pcbnew.FromMM(center_y_mm + dy_mm)
                    item.SetPosition(VECTOR2I(candidate_x, candidate_y))
                    if self.is_position_valid(
                        item, fp, modules, board_edge, vias, tht_pads, masks, dwgs, is_reference
                    ):
                        found = True
                        best_pos = VECTOR2I(candidate_x, candidate_y)
                        break
                if found:
                    break
            if found:
                break

        if best_pos is not None:
            item.SetPosition(best_pos)
            self.logger.debug(f"{fp.GetReference()} moved to ({pcbnew.ToMM(best_pos.x):.2f},{pcbnew.ToMM(best_pos.y):.2f})")
            return True
        else:
            item.SetPosition(initial_pos)
            self.logger.debug(f"{fp.GetReference()} couldn't be moved")
            return False

    def is_position_valid(self, item, fp, modules, board_edge, vias, tht_pads, masks, drawings, is_reference=True) -> bool:
        """Collision and containment logic for a field at its current position."""
        bb_item = item.GetBoundingBox()
        bb_item.SetSize(
            int(bb_item.GetWidth() * self.__deflate_factor__),
            int(bb_item.GetHeight() * self.__deflate_factor__),
        )
        item_shape = item.GetEffectiveShape()

        if not bb_in_shape_poly_set(bb_item, board_edge, all_in=True):
            return False

        for fp2 in modules:
            fp_shape = fp2.GetCourtyard(item.GetLayer())
            if fp_shape.Collide(item_shape):
                return False
            ref_fp = fp2.Reference()
            if ((is_reference and fp != fp2) or not is_reference) and is_silkscreen(ref_fp) \
                and ref_fp.IsOnLayer(item.GetLayer()) and bb_item.Intersects(ref_fp.GetBoundingBox()):
                return False
            value_fp = fp2.Value()
            if is_silkscreen(value_fp) \
                and ((not is_reference and fp != fp2) or is_reference) \
                and value_fp.IsOnLayer(item.GetLayer()) \
                and bb_item.Intersects(value_fp.GetBoundingBox()):
                return False

        for via in vias:
            if (via.TopLayer() == pcbnew.F_Cu and item.IsOnLayer(pcbnew.F_SilkS)) or \
               (via.BottomLayer() == pcbnew.B_Cu and item.IsOnLayer(pcbnew.B_SilkS)):
                if bb_item.Intersects(via.GetBoundingBox()):
                    return False

        for pad in tht_pads:
            if bb_item.Intersects(pad.GetBoundingBox()):
                return False

        for mask in masks:
            if ((mask.IsOnLayer(pcbnew.F_Mask) and item.IsOnLayer(pcbnew.F_SilkS)) or
                (mask.IsOnLayer(pcbnew.B_Mask) and item.IsOnLayer(pcbnew.B_SilkS))) and \
               mask.GetEffectiveShape().Collide(item_shape):
                return False

        for drawing in drawings:
            if drawing.IsOnLayer(item.GetLayer()) and drawing.GetEffectiveShape(item.GetLayer()).Collide(item_shape):
                return False

        return True
