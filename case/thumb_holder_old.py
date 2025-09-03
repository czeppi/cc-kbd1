import math
from typing import Iterator
from build123d import offset, export_stl, loft, make_face, extrude, chamfer, fillet
from build123d import Box, Cylinder, Part, Rectangle, Pos, Rot, Sketch, Plane, Align, Polyline, Axis, GeomType
from ocp_vscode import show_object

from base import STUD_HEIGHT, STUD_RADIUS, STUD_DISTANCE, STUD_CHAMFER_LEN, TOLERANCE, OUTPUT_DPATH
from thumb_base import SLOT_LEN, EPS, THICKNESS


STUD_DISTANCE_X = STUD_DISTANCE
STUD_DISTANCE_Y = math.sin(math.radians(60)) * STUD_DISTANCE * 2


def main():
    foot_creator = ThumbFootCreator()
    foot = foot_creator.create()
    export_stl(foot, OUTPUT_DPATH / 'thumb-foot.stl')

    middle_creator = ThumbMiddlePartCreator()
    middle_part = middle_creator.create()
    export_stl(middle_part, OUTPUT_DPATH / 'thumb-middle-part.stl')

    show_object(middle_part)


class ThumbFootCreator:
    STUD_DIST = 2 * STUD_DISTANCE_Y  # from center to center
    PLATE_X_LEN = 10.0
    PLATE_HEIGHT = 2.0
    Y_MARGIN = 5.0
    COMB_HEIGHT = 2 * SLOT_LEN
    COMB_X_OFFSET = 2.0  # from center
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
        stud = Pos(Y=y, Z=z) * Cylinder(radius=stud_radius, height=stud_height)

        bottom_edge = stud.edges().sort_by(Axis.Z).first
        return chamfer(bottom_edge, length=STUD_CHAMFER_LEN)
    
    def _create_comb(self) -> Part:
        x_len = THICKNESS
        y_len = self._base_plate_y_len
        h = self.COMB_HEIGHT
        comb = Pos(X=self.COMB_X_OFFSET, Z=h/2) * Box(x_len, y_len, h)

        slots_dist = ThumbMiddlePartCreator.Y_LEN - THICKNESS

        slot_y1 = -slots_dist / 2 + self.COMB_SLOT_Y_OFFSET
        slot_y2 = slots_dist / 2 + self.COMB_SLOT_Y_OFFSET
        slot_width = THICKNESS + 2 * TOLERANCE
        slot_height = SLOT_LEN + TOLERANCE
        slot_z = slot_height/2 + self.COMB_HEIGHT - SLOT_LEN

        slot1 = Pos(Y=slot_y1, Z=slot_z) * Box(100.0, slot_width, slot_height)
        slot2 = Pos(Y=slot_y2, Z=slot_z) * Box(100.0, slot_width, slot_height)
        return comb - slot1 - slot2


class ThumbMiddlePartCreator:
    Y_LEN = 32.0
    X_LEN2 = 48.0
    ANGLE1 = 40.0  # from point 1 -> point 2
    ANGLE2 = 10.0  # from point 3 -> point 4
    PROFILE_Z12 = 45.0
    PROFILE_Z34 = 25.0
    SWITCH_HOLDER_THICKNESS = 2.0  # s. keysholder.py
    SWITCH_HOLDER_WIDTH = 20.0  # s. keysholder.py
    TRACKBALL_SLOTS_DIST = 18.0  # from center to center
    THUMB_FOOT_DIST = 5 * STUD_DISTANCE_X  # from center to center of comb for slots

    @property
    def X_LEN1(self) -> float:
        right_margin = 2.0
        sin1 = math.sin(math.radians(self.ANGLE1))
        cos1 = math.cos(math.radians(self.ANGLE1))
        return THICKNESS + (self.SWITCH_HOLDER_WIDTH + 2 * TOLERANCE) * cos1 + SLOT_LEN * sin1 + right_margin        

    @property
    def PROFILE_Z1(self) -> float:
        dx = self.X_LEN1
        tan1 = math.tan(math.radians(self.ANGLE1))

        return self.PROFILE_Z12 - dx / 2 * tan1

    @property
    def PROFILE_Z2(self) -> float:
        dx = self.X_LEN1
        tan1 = math.tan(math.radians(self.ANGLE1))
        
        return self.PROFILE_Z12 + dx / 2 * tan1

    @property
    def PROFILE_Z3(self) -> float:
        dx = self.X_LEN2
        tan2 = math.tan(math.radians(self.ANGLE2))

        return self.PROFILE_Z34 - dx / 2 * tan2

    @property
    def PROFILE_Z4(self) -> float:
        dx = self.X_LEN2
        tan2 = math.tan(math.radians(self.ANGLE2))
        
        return self.PROFILE_Z34 + dx / 2 * tan2
    
    def create(self) -> Part:
        body = self._create_body()
        for slot in self._iter_create_bottom_slots():
            body -= slot
        for slot in self._iter_thumb_switch_slots():
            body -= slot
        for slot in self._iter_trackball_slots():
            body -= slot
        return body
    
    def _create_body(self) -> Part:
        profile = self._create_profile()
        body = extrude(profile, self.Y_LEN)

        print(f'x_len={self.X_LEN1}')
        dx1 = self.X_LEN1 - THICKNESS
        dx2 = self.X_LEN2 - 2 * THICKNESS
        dy = self.Y_LEN - 2 * THICKNESS
        dz = 200.0

        x01 = THICKNESS + dx1/2
        x02 = self.X_LEN1 + THICKNESS + dx2/2
        y0 = THICKNESS + dy/2
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
        feet_dist = self.THUMB_FOOT_DIST  # from center of comb to center of comb

        x0 = (self.X_LEN1 + self.X_LEN2 - feet_dist) / 2
        dx = THICKNESS + 2 * TOLERANCE

        yield Pos(X=x0) * Box(dx, 100.0, 2 + SLOT_LEN)
        yield Pos(X=x0 + feet_dist) * Box(dx, 100.0, 2 + SLOT_LEN)

    def _iter_thumb_switch_slots(self) -> Iterator[Part]:
        cos1 = math.cos(math.radians(self.ANGLE1))
        tan1 = math.tan(math.radians(self.ANGLE1))

        slots_dist = self.SWITCH_HOLDER_WIDTH - self.SWITCH_HOLDER_THICKNESS  # from center to center

        dx = self.SWITCH_HOLDER_THICKNESS + 2 * TOLERANCE
        y_angle = self._calc_y_angle_in_degree(dx=self.X_LEN1, dz=self.PROFILE_Z2 - self.PROFILE_Z1)

        x_off = THICKNESS + (self.SWITCH_HOLDER_WIDTH / 2 + TOLERANCE) * cos1
        z_off = self.PROFILE_Z1 + x_off * tan1

        for slot_x in [-slots_dist/2, slots_dist/2]:

            yield Pos(X=x_off, Z=z_off) \
                * Rot(Y=-y_angle) \
                * Pos(X=slot_x) \
                * Box(dx, 100.0, 2 * SLOT_LEN)

    def _iter_trackball_slots(self) -> Iterator[Part]:
        slots_dist = self.TRACKBALL_SLOTS_DIST  # from center to center
        slot_x1 = (self.X_LEN2 - slots_dist) / 2
        slot_x2 = slot_x1 + slots_dist

        dx = THICKNESS + 2 * TOLERANCE
        z_mean = (self.PROFILE_Z3 + self.PROFILE_Z4) / 2

        y_angle = self._calc_y_angle_in_degree(dx=self.X_LEN2, dz=self.PROFILE_Z4 - self.PROFILE_Z3)

        for slot_x in [slot_x1, slot_x2]:
            yield Pos(X=self.X_LEN1 + self.X_LEN2/2, Z=z_mean) \
                * Rot(Y=-y_angle) \
                * Pos(X=slot_x - self.X_LEN2/2) \
                * Box(dx, 100.0, 2 * SLOT_LEN)


    def _calc_y_angle_in_degree(self, dx: float, dz: float) -> float:
        return math.degrees(math.atan(dz / dx))


if __name__ == '__main__':
    main()