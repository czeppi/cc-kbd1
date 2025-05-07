import copy
from build123d import offset, export_stl, loft, make_face, extrude
from build123d import Box, Part, Pos
from ocp_vscode import show_object

from base import TOLERANCE, OUTPUT_DPATH
from trackball_holder import TrackballHolderCreator
from thumb_holder import ThumbMiddlePartCreator
from thumb_holder import SLOT_LEN as THUMB_HOLDER_SLOT_LEN


EPS = 1E-3


def main():
    creator = TrackballConnCreator()
    trackball_connector = creator.create()
    export_stl(trackball_connector, OUTPUT_DPATH / 'trackball-connector.stl')
    show_object(trackball_connector)


class TrackballConnCreator:
    MARGIN = 1.0
    EXTRA_HEIGHT = 2.0

    def create(self) -> Part:
        thickness = TrackballHolderCreator.THICKNESS
        margin = self.MARGIN

        box_x_len = TrackballHolderCreator.SLOT_DIST + thickness
        box_y_len = max(ThumbMiddlePartCreator.Y_LEN, TrackballHolderCreator.BOTTOM_PLATE_Y_LEN) + 2 * (margin + thickness)
        box_height = 2 * TrackballHolderCreator.SLOT_LEN + 2 * THUMB_HOLDER_SLOT_LEN + self.EXTRA_HEIGHT
        frame = Box(box_x_len, box_y_len, box_height) - Box(box_x_len - 2 * thickness, box_y_len - 2 * thickness, 100.0)

        frame = Pos(Z=-box_height/2) * frame
        frame = self._cut_top_slots(frame)

        frame = Pos(Z=box_height) * frame
        frame = self._cut_bottom_slots(frame)
        
        return frame
    
    def _cut_top_slots(self, frame: Part) -> Part:
        slot = self._create_top_slot()

        y_off = (TrackballHolderCreator.BOTTOM_PLATE_Y_LEN - TrackballHolderCreator.THICKNESS) / 2
        frame -= Pos(Y=y_off) * copy.copy(slot)
        frame -= Pos(Y=-y_off) * copy.copy(slot)
        return frame

    def _create_top_slot(self) -> Part:
        slot_len = TrackballHolderCreator.SLOT_LEN
        slot_width = TrackballHolderCreator.THICKNESS + 2 * TOLERANCE

        slot_box = Pos(Z=-slot_len/2) * Box(100.0, slot_width, slot_len)
        return slot_box
    
    def _cut_bottom_slots(self, frame: Part) -> Part:
        slot = self._create_bottom_slot()

        y_off = (ThumbMiddlePartCreator.Y_LEN - ThumbMiddlePartCreator.THICKNESS) / 2
        frame -= Pos(Y=y_off) * copy.copy(slot)
        frame -= Pos(Y=-y_off) * copy.copy(slot)
        return frame
    
    def _create_bottom_slot(self) -> Part:
        slot_len = THUMB_HOLDER_SLOT_LEN
        slot_width = ThumbMiddlePartCreator.THICKNESS + 2 * TOLERANCE
        
        slot_box = Pos(Z=slot_len/2) * Box(100.0, slot_width, slot_len)
        return slot_box


if __name__ == '__main__':
    main()
