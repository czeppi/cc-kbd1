import math
from typing import Iterator
from build123d import offset, export_stl, loft, make_face, extrude
from build123d import Box, Cylinder, Part, Rectangle, Pos, Rot, Sketch, Plane, Align, Polyline
from ocp_vscode import show_object

from base import STUD_HEIGHT, STUD_RADIUS, TOLERANCE, OUTPUT_DPATH


SLOT_LEN = 3.0
EPS = 0.01


def main():
    #creator = ThumbFootCreator()
    creator = ThumbMiddlePartCreator()
    foot = creator.create()
    show_object(foot)


class ThumbFootCreator:
    STUD_DIST = 30.0  # from center to center
    PLATE_X_LEN = 10.0
    PLATE_HEIGHT = 2.0
    Y_MARGIN = 5.0
    COMB_THICKNESS = 2.0
    COMB_HEIGHT = 6.0
    COMB_X_OFFSET = 0.0  # from center
    COMB_SLOT_Y_OFFSET = 0.0  # from center

    def __init__(self):
        margin = self.Y_MARGIN + STUD_RADIUS
        self._base_plate_y_len = margin + self.STUD_DIST + margin

    def create(self) -> Part:
        base_plate = self._create_base_plate()
        stud1 = self._create_stud(y=-self.STUD_DIST/2)
        stud2 = self._create_stud(y=self.STUD_DIST/2)
        comb = self._create_comb()
        foot = base_plate + stud1 + stud2 + comb
        #export_stl(foot, OUTPUT_DPATH / 'thumb-foot.stl')
        return foot

    def _create_base_plate(self) -> Part:
        """ z == 0 at top of plate
        """
        x_len = self.PLATE_X_LEN
        y_len = self._base_plate_y_len
        z_len = self.PLATE_HEIGHT
        return Pos(Z=-z_len/2) * Box(x_len, y_len, z_len)
    
    def _create_stud(self, y: float) -> Part:
        stud_radius = STUD_RADIUS - TOLERANCE
        stud_height = STUD_HEIGHT - TOLERANCE
        z = -stud_height/2 - self.PLATE_HEIGHT
        return Pos(Y=y, Z=z) * Cylinder(radius=stud_radius, height=stud_height)
    
    def _create_comb(self) -> Part:
        x_len = self.COMB_THICKNESS
        y_len = self._base_plate_y_len
        h = self.COMB_HEIGHT
        comb = Pos(X=self.COMB_X_OFFSET, Z=h/2) * Box(x_len, y_len, h)

        slots_dist = ThumbMiddlePartCreator.y_LEN - ThumbMiddlePartCreator.THICKNESS

        slot_y1 = -slots_dist / 2 + self.COMB_SLOT_Y_OFFSET
        slot_y2 = slots_dist / 2 + self.COMB_SLOT_Y_OFFSET
        slot_width = ThumbMiddlePartCreator.THICKNESS + 2 * TOLERANCE
        slot_height = SLOT_LEN + TOLERANCE
        slot_z = slot_height/2 + self.COMB_HEIGHT - SLOT_LEN

        slot1 = Pos(Y=slot_y1, Z=slot_z) * Box(100.0, slot_width, slot_height)
        slot2 = Pos(Y=slot_y2, Z=slot_z) * Box(100.0, slot_width, slot_height)
        return comb - slot1 - slot2


class ThumbMiddlePartCreator:
    THICKNESS = 2.0
    y_LEN = 20.0
    X_LEN1 = 30.0
    X_LEN2 = 30.0
    PROFILE_Z1 = 30.0
    PROFILE_Z2 = 40.0
    PROFILE_Z3 = 20.0
    PROFILE_Z4 = 30.0

    def create(self) -> Part:
        body = self._create_body()
        for slot in self._iter_create_bottom_slots():
            body -= slot
        for slot in self._iter_thumb_keys_slots():
            body -= slot
        for slot in self._iter_trackball_slots():
            body -= slot
        return body
    
    def _create_body(self) -> Part:
        profile = self._create_profile()
        body = extrude(profile, self.y_LEN)

        dx1 = self.X_LEN1 - 2 * self.THICKNESS
        dx2 = self.X_LEN2 - self.THICKNESS
        dy = self.y_LEN - 2 * self.THICKNESS
        dz = 100.0

        x01 = self.THICKNESS + dx1/2
        x02 = self.X_LEN1 + dx2/2
        y0 = self.THICKNESS + dy/2
        body -= Pos(X=x01, Y=y0) * Box(dx1, dy, dz)
        body -= Pos(X=x02, Y=y0) * Box(dx2, dy, dz)
        return body

    def _create_profile(self) -> Sketch:
        """
                 2
            1         4
                 3    
            0         5
        """
        x23 = self.X_LEN1
        x45 = self.X_LEN1 + self.X_LEN2
        z1 = self.PROFILE_Z1
        z2 = self.PROFILE_Z2
        z3 = self.PROFILE_Z3
        z4 = self.PROFILE_Z4

        points = [
            (0.0, 0.0),
            (0.0, z1),
            (x23, z2),
            (x23, z3),
            (x45, z4),
            (x45, 0.0),
            (0.0, 0.0),
        ]

        profile_line = Polyline(points)
        return make_face(Plane.XZ * profile_line)
    
    def _iter_create_bottom_slots(self) -> Iterator[Part]:
        feet_dist = 50  # from center of comb to center of comb

        x0 = (self.X_LEN1 + self.X_LEN2 - feet_dist) / 2
        dx = ThumbFootCreator.COMB_THICKNESS + 2 * TOLERANCE
        dz = SLOT_LEN + EPS

        yield Pos(X=x0, Z=-dz/2 + SLOT_LEN) * Box(dx, 100.0, dz)
        yield Pos(X=x0 + feet_dist, Z=-dz/2 + SLOT_LEN) * Box(dx, 100.0, dz)

    def _iter_thumb_keys_slots(self) -> Iterator[Part]:
        key_holder_width = 20.0
        key_holder_thickness = 2.0

        slots_dist = key_holder_width - key_holder_thickness  # from center to center
        slot_x1 = (self.X_LEN1 - slots_dist) / 2
        slot_x2 = slot_x1 + slots_dist

        dx = key_holder_thickness + 2 * TOLERANCE
        dz = SLOT_LEN + EPS
        z_mean = (self.PROFILE_Z1 + self.PROFILE_Z2) / 2

        y_angle = self._calc_y_angle_in_degree(dx=self.X_LEN1, dz=self.PROFILE_Z2 - self.PROFILE_Z1)

        for slot_x in [slot_x1, slot_x2]:
            yield Pos(X=self.X_LEN1/2, Z=z_mean) \
                * Rot(Y=y_angle) \
                * Pos(X=slot_x - self.X_LEN1/2, Z=-dz/2) \
                * Box(dx, 100.0, dz)

    def _iter_trackball_slots(self) -> Iterator[Part]:
        trackball_width = 20.0
        trackball_holder_thickness = 2.0

        slots_dist = trackball_width - trackball_holder_thickness  # from center to center
        slot_x1 = (self.X_LEN2 - slots_dist) / 2
        slot_x2 = slot_x1 + slots_dist

        dx = trackball_holder_thickness + 2 * TOLERANCE
        dz = SLOT_LEN + EPS
        z_mean = (self.PROFILE_Z3 + self.PROFILE_Z4) / 2

        y_angle = self._calc_y_angle_in_degree(dx=self.X_LEN2, dz=self.PROFILE_Z4 - self.PROFILE_Z3)

        for slot_x in [slot_x1, slot_x2]:
            yield Pos(X=self.X_LEN1 + self.X_LEN2/2, Z=z_mean) \
                * Rot(Y=y_angle) \
                * Pos(X=slot_x - self.X_LEN2/2, Z=-dz/2) \
                * Box(dx, 100.0, dz)


    def _calc_y_angle_in_degree(self, dx: float, dz: float) -> float:
        return math.degrees(math.atan(-dz / dx))



main()