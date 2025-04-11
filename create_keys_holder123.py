import copy
import math
from dataclasses import dataclass
from typing import Any, Iterator
from build123d import Polyline, mirror, make_face, extrude, Plane, Part, Pos, Rot, Box, Location, Compound
from ocp_vscode import show_object

#
# all values in this file are in mm
#


CUT_WIDTH = 13.9
LEFT_RIGHT_BORDER = 3.0
FRONT_BORDER = 3.0
BACK_BORDER = 3.2  # 2.7 is minimum
THICKNESS = 2.0
RIM_DY = 2.0
TILT_ANGLE = 15.0  # => the knick is 30 degree
HEIGHT = 10.0  # at the crease edge
DEGREE = math.pi / 180


def main():
    swinger = KeyPairHolderSwinger()
    loc = KeyPairHolderFingerLocations()

    index2_holder = swinger.normal_to_front_centered * KeyPairHolderCreator().create()
    index_holder = loc.index2_to_index * copy.copy(index2_holder)
    middle_holder = loc.index2_to_index * loc.index_to_middle * copy.copy(index2_holder)
    ring_holder = loc.index2_to_index * loc.index_to_middle * loc.middle_to_ring * copy.copy(index2_holder)
    pinkie_holder = loc.index2_to_index * loc.index_to_middle * loc.middle_to_ring * loc.ring_to_pinkie * copy.copy(index2_holder)

    index2_holder.label = 'index2'
    index_holder.label = 'index'
    middle_holder.label = 'middle'
    ring_holder.label = 'ring'
    pinkie_holder.label = 'pinkie'

    assembly = Compound(label="assembly", children=[index2_holder, index_holder, middle_holder, ring_holder, pinkie_holder])

    show_object(assembly)


class KeyPairHolderSwinger:
    """ create locations for a holder of a pair of keys

        the normal position is, when the crease edge is on the x axis
        and the middle of the crease edge coincident the origin

        the front/bach centered position is, when the center of the cut from the front/back key holder coincident the origin.
    """

    def __init__(self):
        self._dy = BACK_BORDER + CUT_WIDTH / 2

    @property
    def normal_to_front_centered(self) -> Location:
        return Pos(Y=self._dy) * Rot(X=TILT_ANGLE)
    
    @property
    def front_centered_to_normal(self) -> Location:
        return Rot(X=-TILT_ANGLE) * Pos(Y=-self._dy)

    @property
    def normal_to_back_centered(self) -> Location:
        return Pos(Y=-self._dy) * Rot(X=-TILT_ANGLE)
    
    @property
    def back_centered_to_normal(self) -> Location:
        return Rot(X=TILT_ANGLE) * Pos(Y=self._dy)


class KeyPairHolderCreator:

    def __init__(self):
        self._width = LEFT_RIGHT_BORDER + CUT_WIDTH + LEFT_RIGHT_BORDER
        self._deep = BACK_BORDER + CUT_WIDTH + FRONT_BORDER

    def create(self) -> Part:
        block = self._create_block()
        hole = self._create_hole()
        holder = block - hole
        holder = Pos(X=-self._width/2) * holder  # center on x axis
        holder = self._cut(holder)

        return holder
    
    def _create_block(self) -> Part:
        """
        order of points:

                    1
               0
               3    2
        """
        r = self._deep
        y1 = r * math.cos(TILT_ANGLE * DEGREE)
        z1 = r * math.sin(TILT_ANGLE * DEGREE)

        points = [
            (0, 0),
            (y1, z1),
            (y1, -HEIGHT),
            (0, -HEIGHT),
        ]
        right_half = Polyline(points)
        profile_line = right_half + mirror(right_half, Plane.YZ)

        profile_face = make_face(Plane.YZ * profile_line)
        return extrude(profile_face, -self._width).clean()
    
    def _create_hole(self) -> Part:
        """
        order of points:

                    * 
              *   1
              0   2 3
               
              5     4

        *: block point
        """
        r = BACK_BORDER + CUT_WIDTH + FRONT_BORDER
        sin_tilt = math.sin(TILT_ANGLE * DEGREE)
        cos_tilt = math.cos(TILT_ANGLE * DEGREE)

        y0, z0 = 0.0, -THICKNESS / cos_tilt

        y1 = r * cos_tilt - THICKNESS
        z1 = z0 + y1 * sin_tilt / cos_tilt

        y2, z2 = y1, z1 - RIM_DY
        y3, z3 = r * cos_tilt, z2
        y4, z4 = y3, -HEIGHT
        y5, z5 = 0.0, -HEIGHT

        points = [
            (y0, z0),
            (y1, z1),
            (y2, z2),
            (y3, z3),
            (y4, z4),
            (y5, z5),
        ]
        right_half = Polyline(points)
        profile_line = right_half + mirror(right_half, Plane.YZ)

        profile_face = make_face(Plane.YZ * profile_line)

        dx = self._width - 2 * THICKNESS

        hole = extrude(profile_face, -dx).clean()
        return Pos(X=THICKNESS) * hole      

    def _cut(self, holder: Part) -> Part:
        loc = KeyPairHolderSwinger()
        cut_box = Pos(Z=-THICKNESS/2) * Box(CUT_WIDTH, CUT_WIDTH, 1.1 * THICKNESS)

        holder = loc.normal_to_front_centered * holder  # move front cut in origin
        holder = holder - cut_box
        holder = loc.front_centered_to_normal * holder  # move back

        holder = loc.normal_to_back_centered * holder  # move back cut in origin
        holder = holder - cut_box
        holder = loc.back_centered_to_normal * holder  # move back

        return holder


class KeyPairHolderFingerLocations:
    """ create location of key pair holder between the different fingers

    the names of the positions:

        index2: index finger turned outside
        index:  normal position of the index finger 
        middle: position of the middle finger
        ring:   position of the ring finger
        pinkie: position of the pinkie
    """

    def __init__(self):
        self._index2_to_index = self._calc_index2_index_pos()
        self._index_to_middle = self._create_location(move=(22, 9, 2.5), rotate=(-8, 0, -1))
        self._middle_to_ring = self._create_location(move=(25.2, -8.7, -2.4), rotate=(2, 0, 0))
        self._ring_to_pinkie = self._create_location(move=(28, -20, -16), rotate=(14, 13, 4))

    @property
    def index2_to_index(self) -> Location:
        return self._index2_to_index
    
    @property
    def index_to_middle(self) -> Location:
        return self._index_to_middle
    
    @property
    def middle_to_ring(self) -> Location:
        return self._middle_to_ring
    
    @property
    def ring_to_pinkie(self) -> Location:
        return self._ring_to_pinkie

    def _calc_index2_index_pos(self) -> Location:
        """ calculate the relative position of the index finger, if I rotate it away from the middle finger
        """
        dist_finger_root_key_center = 85  # mm
        key_width = 19.9
        key_height = 20  # mm
        key_gap = 0  # mm

        dx = (key_width + key_gap) / 2
        ry = dist_finger_root_key_center - key_height / 2
        
        phi_z_radian = -2 * math.atan(dx /ry)
        phi_z_degree = phi_z_radian * (180 / math.pi)
        
        dx = -ry * math.sin(phi_z_radian)
        dy = ry * math.cos(phi_z_radian) - ry

        print(f'index2: dx={dx}, dy={dy}, phi_z_degree={phi_z_degree}')

        #return self._create_location(move=(dx, dy, 0), rotate=(0, 0, phi_z_degree))
        return Pos(X=dx, Y=dy) * Rot(Z=phi_z_degree)

    def _create_location(self, move: tuple[float, float, float], rotate: tuple[float, float, float]) -> Location:
        """ rotation order: y-axis, x-axis, z-axis
        """
        dx, dy, dz = move 
        rotx, roty, rotz = rotate
        return Pos(X=dx, Y=dy, Z=dz) * Rot(Z=rotz) * Rot(X=rotx) * Rot(Y=roty)


main()
