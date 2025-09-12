import copy
from build123d import offset, export_stl, loft, make_face, extrude
from build123d import Box, Part, Pos, Axis
from ocp_vscode import show_object

from base import TOLERANCE, OUTPUT_DPATH
from case.thumb_holder_old import ThumbMiddlePartCreator
from thumb_base import THICKNESS, SLOT_LEN
from finger_parts_old import SwitchPairHolderCreator


def main():
    creator = ThumbKeysHolderCreator()
    holder = creator.create()
    export_stl(holder, OUTPUT_DPATH / 'thumb-switches-holder.stl')
    show_object(holder)


class ThumbKeysHolderCreator:
    FEET_WIDT = 5.0
    CENTER_HEIGHT = 5.0
    FEET_EXTRA_WIDTH = 2.0  # next to slot

    def create(self):
        eps = 1E-6
        slot_width = THICKNESS + 2 * TOLERANCE

        holder = SwitchPairHolderCreator(with_hot_swap_slots=False).create()
        box = holder.bounding_box()
        assert abs(box.min.Y + box.max.Y) < eps  # part should be symmetric
        box_y_len = box.max.Y - box.min.Y

        feet_width = (box_y_len - ThumbMiddlePartCreator.Y_LEN) / 2 - TOLERANCE + slot_width + self.FEET_EXTRA_WIDTH
      
        # cut left + right side
        right_face = holder.faces().sort_by(Axis.X).first
        neg_form = extrude(offset(right_face, -THICKNESS), -30)
        neg_form -= Pos(Y=50 + box_y_len/2 - feet_width) * Box(100, 100, 100)
        neg_form -= Pos(Y=-50 - box_y_len/2 + feet_width) * Box(100, 100, 100)
        holder -= neg_form

        # cut bottom
        holder -= Pos(Z=-50 - self.CENTER_HEIGHT) * Box(100, 100, 100)

        # cut slots
        slot = Pos(Z=SLOT_LEN / 2 - self.CENTER_HEIGHT) * Box(100, THICKNESS + 2 * TOLERANCE, SLOT_LEN)
        slots_dist = ThumbMiddlePartCreator.Y_LEN - THICKNESS
        slot1 = Pos(Y=-slots_dist/2) * copy.copy(slot)
        slot2 = Pos(Y=slots_dist/2) * copy.copy(slot)

        holder -= [slot1, slot2]
        return holder
    

if __name__ == '__main__':
    main()
