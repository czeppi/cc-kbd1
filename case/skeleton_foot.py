
import math
import copy
from typing import Iterator
from pathlib import Path
from build123d import offset, export_stl, loft, chamfer
from build123d import Box, Cylinder, Part, Rectangle, Pos, Rot, Kind, Sketch, Plane, Axis
from ocp_vscode import show_object

from base import STUD_DISTANCE, STUD_HEIGHT, STUD_RADIUS, STUD_CHAMFER_LEN, OUTPUT_DPATH


STUD_TOLERANCE = 0.1


# Y
# |
# O     O     O
# |  O     O
# O     O     O
# |  O     O
# O     O     O
# |  O     O
# O-----O-----O---> X
BASE_MARGIN = 1.0
BASE_ROWS = 4
BASE_COLUMNS = 3
BASE_HEIGHT = 3.0

SKELETON_WIDTH = 18.0
SKELETON_HEIGHT = 10.0
SKELETON_THICKNESS = 2.0

FOOT_TOLERANCE = 0.1
SLOT_LEN = 6.0

SLOT_ANGLE_X = -15.0  # s. create_keys_holder.py#loc7
SLOT_ANGLE_Y = 30.0  # s. create_keys_holder.py#loc6
SLOT_ANGLE_Z = -45.0


def main():
    creator = SkeletonFootCreator()
    foot = creator.create()

    export_stl(foot, OUTPUT_DPATH / 'skeleton-foot.stl')
    show_object(foot)


class SkeletonFootCreator:

    def __init__(self):
        pass

    def create(self) -> Part:
        base_plate = self._create_base_plate_with_studs()
        slot = self._create_slot()
        return base_plate + slot

    
    def _create_base_plate_with_studs(self) -> Part:
        """ z == 0 at top of plate
        """
        margin = BASE_MARGIN + STUD_RADIUS
        x_len = margin + (BASE_COLUMNS - 1) * STUD_DISTANCE * 2 * math.sin(math.radians(60)) + margin
        y_len = margin + (BASE_ROWS - 1) * STUD_DISTANCE + margin
        z_len = BASE_HEIGHT

        plate = Pos(Z=-z_len/2) * Box(x_len, y_len, z_len)

        stud_height = STUD_HEIGHT - STUD_TOLERANCE
        studs = [Pos(Z=-z_len - stud_height/2) * stud 
                 for stud in self._iter_studs(x_len=x_len, y_len=y_len)]
                      
        return Pos(X=x_len/2, Y=y_len/2) * (plate + studs)

    def _iter_studs(self, x_len: float, y_len: float) -> Iterator[Part]:
        dx = x_len / 2 - BASE_MARGIN - STUD_RADIUS
        dy = y_len / 2 - BASE_MARGIN - STUD_RADIUS

        stud_radius = STUD_RADIUS - STUD_TOLERANCE
        stud_height = STUD_HEIGHT - STUD_TOLERANCE
        
        stud_template = Cylinder(radius=stud_radius, height=stud_height)
        bottom_edge = stud_template.edges().sort_by(Axis.Z).first
        stud_template = chamfer(bottom_edge, length=STUD_CHAMFER_LEN)

        for y in (-dy, dy):
            for x in (-dx, dx):
                yield Pos(x, y, 0) * copy.copy(stud_template)

    def _create_slot(self) -> Part:
        """ !! loft-function does not work with u_profile with hole !!
        """
        skeleton_u = self._create_skeleton_u_profile()
        inner_u_profile = offset(skeleton_u, FOOT_TOLERANCE, kind=Kind.INTERSECTION)
        outer_u_profile = offset(inner_u_profile, SKELETON_THICKNESS, kind=Kind.INTERSECTION)

        inner_u_face = Plane.YZ * inner_u_profile
        outer_u_face = Plane.YZ * outer_u_profile

        inner_loft = self._create_slot_loft(inner_u_face)
        outer_loft = self._create_slot_loft(outer_u_face)

        slot_height = self._calc_slot_height()
        slot = outer_loft - inner_loft
        slot -= Pos(X=-50) * Box(100.0, 100.0, 100.0)  # cut left
        slot -= Pos(X=50 + slot_height) * Box(100.0, 100.0, 100.0)  # cut right
        slot = Rot(Z=-90) * Rot(Y=90) * slot
        slot = Rot(Z=SLOT_ANGLE_Z) * slot

        box = slot.bounding_box()
        min_x = box.min.X
        min_y = box.min.Y
        min_z = box.min.Z
        return Pos(X=-min_x, Y=-min_y, Z=-min_z) * slot  # move slot in x+/y+ quadrant

    def _create_skeleton_u_profile(self) -> Sketch:
        """
            x x x     x x x
            x   x     x   x
            x   x x x x   x
            x             x
            x x x x x x x x
        """
        skeleton_rect = Rectangle(width=SKELETON_WIDTH, 
                                  height=SKELETON_HEIGHT)
        
        skeleton_hole = Pos(Y=SKELETON_THICKNESS) * Rectangle(width=SKELETON_WIDTH - 2 * SKELETON_THICKNESS, 
                                                              height=SKELETON_HEIGHT)
        skeleton_u = skeleton_rect - skeleton_hole
        return skeleton_u

    def _create_slot_loft(self, slot_profile) -> Part:
        # s. create_keys_holder123.py#SkeletonCreator.create()

        shift_x = 20  # s. create_keys_hoolder
        shift_y = -5  # s. create_keys_hoolder
        shift_factor = shift_y / shift_x  

        x_min = -20
        x_max = 20
        dx = x_max - x_min
        dy = shift_factor * dx

        loc5 = Rot(Y=SLOT_ANGLE_X) * Pos(X=x_min, Y=0) * Rot(Z=-SLOT_ANGLE_Y)
        loc6 = Rot(Y=SLOT_ANGLE_X) * Pos(X=x_max, Y=dy) * Rot(Z=-SLOT_ANGLE_Y)  

        u5 = loc5 * copy.copy(slot_profile)
        u6 = loc6 * copy.copy(slot_profile)
        return loft([u5, u6])
 
    def _calc_slot_height(self) -> float:
        x_rad = math.radians(SLOT_ANGLE_X)
        y_rad = math.radians(SLOT_ANGLE_Y)
        return SLOT_LEN * math.cos(x_rad) * math.cos(y_rad)
   

if __name__ == '__main__':
    main()
