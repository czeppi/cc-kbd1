import copy
from build123d import offset, export_stl, loft, make_face, extrude
from build123d import Box, Part, Pos
from ocp_vscode import show_object

from base import TOLERANCE, OUTPUT_DPATH
from case.trackball_holder_old import TrackballHolderCreator
from thumb_holder import ThumbMiddlePartCreator
from thumb_base import THICKNESS, SLOT_LEN



def main():
    creator = TrackballConnCreator()
    trackball_connector = creator.create()
    export_stl(trackball_connector, OUTPUT_DPATH / 'trackball-connector.stl')
    show_object(trackball_connector)


class TrackballConnCreator:
    MARGIN = 3.0
    EXTRA_TOP_HEIGHT = 0.0
    EXTRA_BOTTOM_HEIGHT = 0.0
    X_TOP_OFFSET = 0.0  # top_center - bottom_center

    def create(self) -> Part:
        """
        view from front (in y+ direction):

        *     *
        *******  <- center: z==0
         *   *

        """
        y_len = max(TrackballHolderCreator.BOTTOM_PLATE_Y_LEN, TrackballHolderCreator.SLOT_DIST) + 2 * self.MARGIN
        slot_width = THICKNESS + 2 * TOLERANCE

        top_comb_height =  2 * SLOT_LEN + self.EXTRA_TOP_HEIGHT
        top_combs_dist = TrackballHolderCreator.SLOT_DIST
        top_comb1_x = -top_combs_dist/2 + self.X_TOP_OFFSET
        top_comb2_x = top_combs_dist/2 + self.X_TOP_OFFSET

        top_comb = Pos(Z=top_comb_height/2 + THICKNESS/2) * Box(THICKNESS, y_len, top_comb_height)
        top_comb1 = Pos(X=top_comb1_x) * copy.copy(top_comb)
        top_comb2 = Pos(X=top_comb2_x) * copy.copy(top_comb)

        top_slots_dist = TrackballHolderCreator.BOTTOM_PLATE_Y_LEN - THICKNESS
        top_slot = Pos(Z=THICKNESS/2 + top_comb_height - SLOT_LEN/2) * Box(100.0, slot_width, SLOT_LEN)
        top_slot1 = Pos(Y=-top_slots_dist/2) * copy.copy(top_slot)
        top_slot2 = Pos(Y=top_slots_dist/2) * copy.copy(top_slot)

        bottom_comb_height =  2 * SLOT_LEN + self.EXTRA_BOTTOM_HEIGHT
        bottom_combs_dist = ThumbMiddlePartCreator.TRACKBALL_SLOTS_DIST  # center to center
        bottom_comb1_x = -bottom_combs_dist/2
        bottom_comb2_x = bottom_combs_dist/2

        bottom_comb = Pos(Z=-THICKNESS/2 - bottom_comb_height/2) * Box(THICKNESS, y_len, bottom_comb_height)
        bottom_comb1 = Pos(X=bottom_comb1_x) * copy.copy(bottom_comb)
        bottom_comb2 = Pos(X=bottom_comb2_x) * copy.copy(bottom_comb)

        bottom_slots_dist = ThumbMiddlePartCreator.Y_LEN - THICKNESS
        bottom_slot = Pos(Z=-THICKNESS/2 - bottom_comb_height + SLOT_LEN/2) * Box(100.0, slot_width, SLOT_LEN)
        bottom_slot1 = Pos(Y=-bottom_slots_dist/2) * copy.copy(bottom_slot)
        bottom_slot2 = Pos(Y=bottom_slots_dist/2) * copy.copy(bottom_slot)

        center_x_left = min(top_comb1_x, bottom_comb1_x) - THICKNESS / 2
        center_x_right = max(top_comb2_x, bottom_comb2_x) + THICKNESS / 2
        center_x_offset = (center_x_left + center_x_right) / 2

        center_x_len = center_x_right - center_x_left
        center_plate = Pos(X=center_x_offset) * Box(center_x_len, y_len, THICKNESS)

        top_right_big_slot_width = y_len - 2 * (self.MARGIN + slot_width + self.MARGIN)
        top_right_big_slot = Pos(X=center_x_right, Z=top_comb_height/2 + THICKNESS/2) * Box(10, top_right_big_slot_width, top_comb_height)
 
        center_slot_left = max(top_comb1_x, bottom_comb1_x) + THICKNESS / 2
        center_slot_right = min(top_comb2_x, bottom_comb2_x) - THICKNESS / 2
        center_slot_offset = (center_slot_left + center_slot_right) / 2
        center_slot = Pos(X=center_slot_offset) * Box(center_slot_right - center_slot_left, y_len - 2 * self.MARGIN, 100)

        return Part() + [center_plate, top_comb1, top_comb2, bottom_comb1, bottom_comb2] \
                      - [top_slot1, top_slot2, bottom_slot1, bottom_slot2, top_right_big_slot, center_slot]


if __name__ == '__main__':
    main()
