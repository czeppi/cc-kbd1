import copy
import math
from dataclasses import dataclass
from typing import Any, Iterator
from build123d import Polyline, mirror, make_face, extrude, Plane, Part, Pos, Rot, Box, Location, Compound, Rectangle, Circle, Sketch, BaseSketchObject, loft
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
HOLDER_HEIGHT = 10.0  # at the crease edge
SKELETON_WIDTH = 20.0
SKELETON_HEIGHT = 10.0
SLOT_LEN = 2.0
DEGREE = math.pi / 180


def main():
    assembly = HolderAssemblyCreator().create()
    #show_object(assembly)

    skeleton = SkeletonCreator().create()
    show_object(assembly + skeleton)


class SkeletonCreator:

    def create(self):
        faces = Sketch() + list(self._iter_u_profiles())
        return loft(faces)

    def _iter_u_profiles(self) -> Iterator[Sketch]:
        loc = KeyPairHolderFingerLocations()
        u_profile = self._create_u_profile()

        holder_dx = LEFT_RIGHT_BORDER + CUT_WIDTH + LEFT_RIGHT_BORDER

        yield loc.index_to_index2 * Pos(X=-holder_dx/2 - 5, Y=-5) * copy.copy(u_profile)
        yield Pos(Y=0) * copy.copy(u_profile)
        yield loc.index_to_middle * Pos(Y=0) * copy.copy(u_profile)
        yield loc.index_to_middle * loc.middle_to_ring * Pos(X=holder_dx/2, Y=-5) * copy.copy(u_profile)
        yield loc.index_to_middle * loc.middle_to_ring * loc.ring_to_pinkie * Pos(X=-holder_dx/2, Y=5) * copy.copy(u_profile)
        yield loc.index_to_middle * loc.middle_to_ring * loc.ring_to_pinkie * Pos(X=holder_dx/2, Y=-5) * copy.copy(u_profile)

    def _create_u_profile(self) -> BaseSketchObject:
        outer_rect = Rectangle(SKELETON_WIDTH, SKELETON_HEIGHT)
        inner_rect = Pos(0, THICKNESS) * Rectangle(SKELETON_WIDTH - 2 * THICKNESS, SKELETON_HEIGHT)

        u_profile = Plane.YZ * (outer_rect - inner_rect)
        dz = -SKELETON_HEIGHT / 2 - HOLDER_HEIGHT + 2 * SLOT_LEN
        return Pos(Z=dz) * u_profile
    

class HolderAssemblyCreator:

    def create(self):
        assembly = Compound(label="assembly", children=list(self._iter_key_holders()))
        return assembly
    
    def _iter_key_holders(self) -> Iterator[Part]:
        loc = KeyPairHolderFingerLocations()

        index_holder = KeyPairHolderCreator().create()
        index2_holder = loc.index_to_index2 * copy.copy(index_holder)
        middle_holder = loc.index_to_middle * copy.copy(index_holder)
        ring_holder = loc.index_to_middle * loc.middle_to_ring * copy.copy(index_holder)
        pinkie_holder = loc.index_to_middle * loc.middle_to_ring * loc.ring_to_pinkie * copy.copy(index_holder)

        index_holder.label = 'index'
        index2_holder.label = 'index2'
        middle_holder.label = 'middle'
        ring_holder.label = 'ring'
        pinkie_holder.label = 'pinkie'

        yield index_holder
        yield index2_holder
        yield middle_holder
        yield ring_holder
        yield pinkie_holder


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
            (y1, -HOLDER_HEIGHT),
            (0, -HOLDER_HEIGHT),
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
        y4, z4 = y3, -HOLDER_HEIGHT
        y5, z5 = 0.0, -HOLDER_HEIGHT

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
        self._index_to_index2 = self._calc_index_index2_pos()
        self._index_to_middle = self._create_location(move=(22, 7, 2.5), rotate=(-8, 0, -1))
        self._middle_to_ring = self._create_location(move=(25.2, -6.7, -2.4), rotate=(2, 0, 0))
        self._ring_to_pinkie = self._create_location(move=(33, -20, -16), rotate=(14, 30, 4))

    @property
    def index_to_index2(self) -> Location:
        return self._index_to_index2
    
    @property
    def index_to_middle(self) -> Location:
        return self._index_to_middle
    
    @property
    def middle_to_ring(self) -> Location:
        return self._middle_to_ring
    
    @property
    def ring_to_pinkie(self) -> Location:
        return self._ring_to_pinkie

    def _calc_index_index2_pos(self) -> Location:
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

        swinger = KeyPairHolderSwinger()
        return swinger.front_centered_to_normal * Pos(X=-dx, Y=dy) * Rot(Z=-phi_z_degree) * swinger.normal_to_front_centered

    def _create_location(self, move: tuple[float, float, float], rotate: tuple[float, float, float]) -> Location:
        """ rotation order: y-axis, x-axis, z-axis
        """
        dx, dy, dz = move 
        rotx, roty, rotz = rotate

        swinger = KeyPairHolderSwinger()
        return swinger.front_centered_to_normal * Pos(X=dx, Y=dy, Z=dz) * Rot(Z=rotz) * Rot(X=rotx) * Rot(Y=roty) * swinger.normal_to_front_centered


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


main()
