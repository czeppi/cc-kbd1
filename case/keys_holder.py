import copy
import math
from dataclasses import dataclass
from typing import Iterator
from pathlib import Path

from build123d import mirror, make_face, extrude, loft, export_stl, sweep
from build123d import Polyline, Plane, Part, Pos, Rot, Box, Location, Compound, Rectangle, Circle, Sketch, BaseSketchObject, Cylinder, Edge, Vector, Face, Sphere
from ocp_vscode import show_object
from hot_swap_socket import SwitchPairHolderCreator

#
# all length values in this file are in mm
#

CUT_WIDTH = 13.9
LEFT_RIGHT_BORDER = 3.0
FRONT_BORDER = 3.0
BACK_BORDER = 3.2  # 2.7 is minimum
THICKNESS = 2.0
RIM_DY = 2.0
TILT_ANGLE = 15.0  # => the knick is 30 degree
HOLDER_HEIGHT = 10.0  # at the crease edge

HOT_SWAP_SOCKET_PIN_SLOT_Y_START = 1.5
HOT_SWAP_SOCKET_PIN_SLOT_Y_END = 4.5
HOT_SWAP_SOCKET_PIN_SLOT_Z_LEN = 6.0

SKELETON_WIDTH = 18.0
SKELETON_HEIGHT = 10.0
SLOT_LEN = 2.0

TOLERANCE = 0.1  # for slots
DEGREE = math.pi / 180

OUTPUT_DPATH = Path('output')


def main():
    SkeletonSplineFinder().find_path()
    return

    creator = FinalAssemblyCreator()
    assembly = creator.create_with_slots()

    creator.save(OUTPUT_DPATH)   
    export_stl(assembly, OUTPUT_DPATH / 'assembly.stl')

    show_object(assembly)


class FinalAssemblyCreator:

    def __init__(self):
        self._skeleton: Part | None = None
        self._holder_map: dict[str, Part] = {}

    def create_with_slots(self) -> Compound:
        self._holder_map = self._create_holder_with_slots_map()
        self._skeleton = self._create_skeleton_with_slots()

        key_holders = Compound(label='holders', children=list(self._holder_map.values()))
        return Compound(label="assembly", children=[key_holders, self._skeleton])

    def _create_holder_with_slots_map(self) -> Compound:
        holder_without_slots_map = HolderAssemblyCreator().create_map()
        skeleton_without_slots = SkeletonCreator(tolerance=TOLERANCE, height_offset=-SLOT_LEN).create()
        return {name: holder - skeleton_without_slots 
                for name, holder in holder_without_slots_map.items()}

    def _create_skeleton_with_slots(self) -> Part:
        holder_without_slots_map = HolderAssemblyCreator(tolerance=TOLERANCE).create_map()
        holders_without_slots = Compound(label='holders', children=list(holder_without_slots_map.values()))
        skeleton_without_slots = SkeletonCreator(tolerance=TOLERANCE, height_offset=-SLOT_LEN).create()

        holders_with_slots = holders_without_slots - skeleton_without_slots
        return SkeletonCreator().create() - holders_with_slots
    
    def save(self, output_dpath: Path) -> None:
        if self._skeleton:
            export_stl(self._skeleton, output_dpath / 'skeleton.stl')
            
        for name, holder in self._holder_map.items():
            export_stl(holder, output_dpath / f'{name}.stl')


class SkeletonCreator:

    def __init__(self, tolerance: float = 0.0, height_offset: float = 0.0):
        self._tolerance = tolerance
        self._height_offset = height_offset

    def create(self) -> Part:
        loc = KeyPairHolderFingerLocations()
        u_profile = self._create_u_profile()

        holder_dx = LEFT_RIGHT_BORDER + CUT_WIDTH + LEFT_RIGHT_BORDER

        loc1 = loc.index2 * Pos(X=-holder_dx/2 - 5, Y=-5)
        loc2 = loc.middle * Pos(Y=0)
        loc3 = loc.ring  * Pos(Y=-2) * Rot(Z=-20)
        loc4 = loc.pinkie * Pos(X=-holder_dx/2, Y=8) * Rot(Z=-25)
        loc5 = loc.pinkie * Pos(X=holder_dx/2+5, Y=-7) * Rot(Z=-30)
        loc6 = loc.pinkie * Pos(X=holder_dx/2+25, Y=-12) * Rot(Z=-30)
        loc7 = loc.pinkie * Pos(X=holder_dx/2+19, Y=-12) * Rot(Y=15)

        u1 = loc1 * copy.copy(u_profile)
        u2 = loc2 * copy.copy(u_profile)
        u3 = loc3 * copy.copy(u_profile)
        u4 = loc4 * copy.copy(u_profile)
        u5 = loc5 * copy.copy(u_profile)
        u6 = loc6 * copy.copy(u_profile)

        loft1 = loft(Sketch() + list([u1, u2, u3]))
        loft2 = loft(Sketch() + list([u3, u4, u5]))
        loft3 = loft(Sketch() + list([u5, u6]))

        # bottom wholes
        cylinder = Cylinder(radius=2.5, height=50)
        cylinder1 = loc.index2 * copy.copy(cylinder)
        cylinder2 = loc2 * copy.copy(cylinder)
        cylinder3 = loc3 * copy.copy(cylinder)

        neg_foot_box = loc7 * Pos(X=15, Z=-10) * Box(30, 30, 30)
        dummy_box = loc7 * Pos(X=1, Z=0) * Box(2, 20, 20)

        skeleton = loft1 + loft2 + loft3 - cylinder1 - cylinder2 - cylinder3 - neg_foot_box + dummy_box
        skeleton.label = 'skeleton'
        return skeleton

    def _create_u_profile(self) -> BaseSketchObject:
        width = SKELETON_WIDTH + 2 * self._tolerance
        height = SKELETON_HEIGHT + self._height_offset
        thickness = THICKNESS + 2 * self._tolerance
        dz = -height / 2 - HOLDER_HEIGHT + 2 * SLOT_LEN + self._height_offset

        outer_rect = Rectangle(width, height)
        inner_rect = Pos(0, thickness) * Rectangle(width - 2 * thickness, height)

        u_profile = Plane.YZ * (outer_rect - inner_rect)
        return Pos(Z=dz) * u_profile
    

class HolderAssemblyCreator:

    def __init__(self, tolerance: float = 0.0):
        self._creator = KeyPairHolderCreator(tolerance=tolerance)

    def create_map(self) -> dict[str, Part]:
        return {
            'index': self.create_index_holder(),
            'middle': self.create_middle_holder(),
            'ring': self.create_ring_holder(),
            'pinkie': self.create_pinkie_holder(),
        }
    
    def create_index_holder(self) -> Compound:
        loc = KeyPairHolderFingerLocations()
        creator = self._creator

        index1_holder = creator.create(front_left_bevel=-9, front_right_bevel=-14, back_left_bevel=-3, back_right_bevel=0, 
                                       extra_left_height=1.0, extra_right_height=1.0)
        index1_holder.label = 'normal'

        index2_holder = loc.index2 * creator.create(front_left_bevel=-3, front_right_bevel=-8, back_left_bevel=-10, back_right_bevel=-5)
        index2_holder.label = 'outside'

        return Compound(label="index-holder", children=[index1_holder, index2_holder])

    def create_middle_holder(self) -> Part:
        loc = KeyPairHolderFingerLocations()
        creator = self._creator
        middle_holder = loc.middle * creator.create(front_left_bevel=-9, front_right_bevel=-5, back_left_bevel=-5, back_right_bevel=-8)
        middle_holder.label = 'middle'
        return middle_holder

    def create_ring_holder(self) -> Part:
        loc = KeyPairHolderFingerLocations()
        creator = self._creator
        ring_holder = loc.ring * creator.create(front_left_bevel=-9, front_right_bevel=-1, back_left_bevel=-2, back_right_bevel=-10,
                                                extra_left_height=1.0)
        ring_holder.label = 'ring'
        return ring_holder

    def create_pinkie_holder(self) -> Part:
        loc = KeyPairHolderFingerLocations()
        creator = self._creator
        pinkie_holder = loc.pinkie * creator.create(front_left_bevel=-14, front_right_bevel=-2, back_left_bevel=2, back_right_bevel=-7,  
                                                    extra_left_height=1.0)
        pinkie_holder.label = 'pinkie'
        return pinkie_holder
    

class KeyPairHolderCreator:

    def __init__(self, with_hot_swap_slots: bool = True, tolerance: float = 0.0):
        self._width = LEFT_RIGHT_BORDER + CUT_WIDTH + LEFT_RIGHT_BORDER + 2 * tolerance
        self._height = HOLDER_HEIGHT
        self._deep = BACK_BORDER + CUT_WIDTH + FRONT_BORDER
        self._with_hot_swap_slots = with_hot_swap_slots
        self._thickness = THICKNESS + 2 * tolerance

    def create(self, front_left_bevel: float=0.0, 
               front_right_bevel: float=0.0, 
               back_left_bevel: float=0.0, 
               back_right_bevel: float=0.0, 
               extra_left_height: float=0.0,
               extra_right_height: float=0.0) -> Part:
        block = self._create_block(front_left_bevel=front_left_bevel, 
                                   front_right_bevel=front_right_bevel,
                                   back_left_bevel=back_left_bevel,
                                   back_right_bevel=back_right_bevel,
                                   extra_left_height=extra_left_height,
                                   extra_right_height=extra_right_height)
        hole = self._create_interior(extra_height=max(extra_left_height, extra_right_height))
        holder = block - hole
        holder = Pos(X=-self._width/2) * holder  # center on x axis
        holder = self._cut(holder)

        return holder
    
    def _create_block(self, front_left_bevel: float, 
                      front_right_bevel: float, 
                      back_left_bevel: float, 
                      back_right_bevel: float, 
                      extra_left_height: float,
                      extra_right_height) -> Part:
        left_profile_face = self._create_block_profile_face(front_bevel=front_left_bevel, 
                                                            back_bevel=back_left_bevel, 
                                                            extra_height=extra_left_height)
        right_profile_face = Pos(X=self._width) * self._create_block_profile_face(front_bevel=front_right_bevel, 
                                                                                  back_bevel=back_right_bevel, 
                                                                                  extra_height=extra_right_height)

        return loft(Sketch() + list([left_profile_face, right_profile_face]))
    
    def _create_block_profile_face(self, front_bevel: float, back_bevel: float, extra_height: float) -> Sketch:
        """
        order of points:
               z
          6    |    1
          5    0 ---2--------> y
           4       3

        """
        r = self._deep
        y1 = r * math.cos(TILT_ANGLE * DEGREE)
        z1 = r * math.sin(TILT_ANGLE * DEGREE)
        z2 = z1 - self._thickness - RIM_DY
        y3 = y1 + back_bevel
        y4 = -y1 - front_bevel
        h = self._height + extra_height

        points = [
            (0, 0),
            (y1, z1),
            (y1, z2),
            (y3, -h),
            (y4, -h),
            (-y1, z2),
            (-y1, z1),
            (0, 0),
        ]
        right_half = Polyline(points)
        profile_line = right_half

        return make_face(Plane.YZ * profile_line)
    
    def _create_interior(self, extra_height: float) -> Part:
        """
        order of points:
              z
              |     * 
              *   1
              0---2-3---> y
               
              5     4

        *: block point
        """
        r = self._deep
        sin_tilt = math.sin(TILT_ANGLE * DEGREE)
        cos_tilt = math.cos(TILT_ANGLE * DEGREE)
        thickness = self._thickness
        h = self._height + extra_height

        y0, z0 = 0.0, -thickness / cos_tilt

        y1 = r * cos_tilt - thickness
        z1 = z0 + y1 * sin_tilt / cos_tilt

        y2, z2 = y1, z1 - RIM_DY
        y3, z3 = 100, z2
        y4, z4 = 100, -h
        y5, z5 = 0.0, -h

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

        dx = self._width - 2 * thickness

        hole = extrude(profile_face, -dx).clean()
        return Pos(X=thickness) * hole      

    def _cut(self, holder: Part) -> Part:
        thickness = self._thickness
        swinger = KeyPairHolderSwinger()
        cut_box = Pos(Z=-thickness/2) * Box(CUT_WIDTH, CUT_WIDTH, 1.1 * thickness)
        

        holder = swinger.normal_to_front_centered * holder  # move front cut in origin
        holder -= cut_box
        if self._with_hot_swap_slots:
            front_hot_swap_box = self._create_hot_swap_slot_box(front=True)
            holder -= front_hot_swap_box
        holder = swinger.front_centered_to_normal * holder  # move back

        holder = swinger.normal_to_back_centered * holder  # move back cut in origin
        holder -= cut_box
        if self._with_hot_swap_slots:
            back_hot_swap_box = self._create_hot_swap_slot_box(front=False)
            holder -= back_hot_swap_box
        holder = swinger.back_centered_to_normal * holder  # move back

        return holder
    
    def _create_hot_swap_slot_box(self, front: bool) -> Part:
        cut_eps = 0.1

        # box
        x_len = LEFT_RIGHT_BORDER + cut_eps
        y_len = HOT_SWAP_SOCKET_PIN_SLOT_Y_END - HOT_SWAP_SOCKET_PIN_SLOT_Y_START
        z_len = HOT_SWAP_SOCKET_PIN_SLOT_Z_LEN + cut_eps

        box = Box(x_len, y_len, z_len)

        # pos
        dx = CUT_WIDTH/2 + LEFT_RIGHT_BORDER/2
        dy = CUT_WIDTH/2 - y_len/2 - HOT_SWAP_SOCKET_PIN_SLOT_Y_START
        dz = z_len/2 - HOT_SWAP_SOCKET_PIN_SLOT_Z_LEN

        if not front:
            dx = -dx
            dy = -dy

        pos = Pos(X=dx, Y=dy, Z=dz) 
        
        return pos * box


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

        self._ring_move_correction = self._create_location(move=(2, -2, 0), rotate=(0, 0, 0))
        self._ring_rotate_correction = self._create_location(move=(2, -2, 0), rotate=(0, 5, 0))
        self._pinkie_rotate_correction = self._create_location(move=(0, 0, 0), rotate=(0, 0, -10))

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

    @property
    def index(self) -> Location:
        return Pos(0, 0, 0)
    
    @property
    def index2(self) -> Location:
        return self._index_to_index2
    
    @property
    def middle(self) -> Location:
        return self._index_to_middle
    
    @property
    def ring(self) -> Location:
        return self._ring_move_correction * self._index_to_middle * self._middle_to_ring * self._ring_rotate_correction
    
    @property
    def pinkie(self) -> Location:
        return self._index_to_middle * self._middle_to_ring * self._ring_to_pinkie * self._pinkie_rotate_correction


class KeyPairHolderSwinger:
    """ create locations for a holder of a pair of keys

        the normal position is, when the crease edge is on the x axis
        and the middle of the crease edge coincident the origin

        the front/bach centered position is, when the center of the cut from the front/back key holder coincidents the origin.
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
    

class SkeletonSplineFinder:

    def __init__(self):
        self._tube_outer_radius = 8
        self._tube_inner_radius = 5
        self._base_holder_distance = 4
        self._base_offset = 0.5  # make base position a little bit above the tube
        self._dz = SwitchPairHolderCreator.MIDDLE_PART_HEIGHT_AT_CENTER + self._base_holder_distance + self._base_offset + self._tube_outer_radius

    def find_path(self):
        spline_edge = self._create_spline_edge()
        #show_object(spline_edge, name='spline')

        outer_tube = self._create_tube(r=self._tube_outer_radius, spline_edge=spline_edge)
        inner_tube = self._create_tube(r=self._tube_inner_radius, spline_edge=spline_edge)
        key_bases = list(self._iter_key_bases())
        sphere = self._create_sphere()
        sphere_handle = self._create_sphere_handle()
        sweeped_part = (outer_tube + key_bases + sphere_handle + sphere) - inner_tube
        show_object(sweeped_part, name='sweeped')

        self._show_switch_holder()
  
        #profile_template = Rectangle(16, 8) - Circle(3)
        #profile_template = Circle(8) + Rectangle(4,12)

        return spline_edge
    
    def _create_spline_edge(self) -> Edge:
        loc = KeyPairHolderFingerLocations()
        dz = self._dz
        holder_dx = LEFT_RIGHT_BORDER + CUT_WIDTH + LEFT_RIGHT_BORDER
        skeleton_start = loc.index * Pos(X=-3/2*holder_dx, Y=-5)
        skeleton_end = loc.pinkie * Pos(X=holder_dx/2+5, Y=-5)

        points = [#Vector(-30, -15, -dz), 
                  (skeleton_start * Pos(Z=-dz)).position,
                  (loc.index * Pos(X=-holder_dx/2, Z=-dz)).position,
                  (loc.middle * Pos(Z=-dz)).position, 
                  (loc.ring * Pos(Z=-dz)).position, 
                  (loc.pinkie * Pos(Z=-dz)).position,
                  (skeleton_end * Pos(Z=-dz)).position]
        
        return Edge.make_spline_approx(points=points, tol=0.01, max_deg=3)
    
    def _create_tube(self, r: float, spline_edge: Edge) -> Part:
        profile_template = Circle(1.0 * r)  # Circle(0.9 * r)
        profile_template2 = Circle(1.0 * r)  # Circle(1.1 * r)

        start_tangent = spline_edge%0
        x_dir = start_tangent.cross(Vector(0, 0, 1)).normalized()
        plane0 = Plane(origin=spline_edge@0, z_dir=start_tangent, x_dir=x_dir)
        profile0 = plane0 * profile_template

        end_tangent = spline_edge%1
        x_dir = end_tangent.cross(Vector(0, 0, 1)).normalized()
        plane1 = Plane(origin=spline_edge@1, z_dir=end_tangent, x_dir=x_dir)
        profile1 = plane1 * profile_template2

        return sweep([profile0, profile1], path=spline_edge, multisection=True)
    
    def _iter_key_bases(self) -> Iterator[Part]:
        loc = KeyPairHolderFingerLocations()
        dz = self._dz

        base_height = 3
        base_len = 18
        z_dist = SwitchPairHolderCreator.MIDDLE_PART_HEIGHT_AT_CENTER + self._base_holder_distance + base_height / 2

        yield loc.index * Pos(Z=-z_dist) * Box(base_len, base_len, base_height)
        yield loc.middle * Pos(Z=-z_dist) * Box(base_len, base_len, base_height)
        yield loc.ring * Pos(Z=-z_dist) * Box(base_len, base_len, base_height)
        yield loc.pinkie * Pos(Z=-z_dist) * Box(base_len, base_len, base_height)

    def _create_sphere(self) -> Part:
        loc = KeyPairHolderFingerLocations()
        sphere_radius = 12
        dz = self._dz + self._tube_outer_radius + sphere_radius + 1
        return loc.middle * Pos(Z=-dz) * Sphere(radius=sphere_radius)

    def _create_sphere_handle(self) -> Part:
        loc = KeyPairHolderFingerLocations()
        handle_radius = 7
        dz = self._dz + self._tube_outer_radius
        return loc.middle * Pos(Z=-dz) * Cylinder(radius=handle_radius, height=10)

    def _show_switch_holder(self):
        loc = KeyPairHolderFingerLocations()
        y2 = 11.36  # SwitchPairHolderCreator._create_middle_profile_face()#y2
        
        holder = Box(14, 2 * y2, 5)
        holder_parts = SwitchPairHolderCreator().create()

        index2_box = loc.index * Pos(X=-14) * Compound(label='index2', children=copy.copy(holder_parts))
        show_object(index2_box)

        index_box = loc.index * Compound(label='index', children=copy.copy(holder_parts))
        show_object(index_box)

        middle_box = loc.middle * Compound(label='middle', children=copy.copy(holder_parts))
        show_object(middle_box)

        ring_box = loc.ring * Compound(label='ring', children=copy.copy(holder_parts))
        show_object(ring_box)

        pinkie_box = loc.pinkie * Compound(label='pinkie', children=copy.copy(holder_parts))
        show_object(pinkie_box)
    
    def _find_t_in_spline(self, x0: float, spline: Edge) -> float:
        eps = 1e-3
        t1 = 0.0
        t2 = 1.0

        for i in range(100):
            t = (t1 + t2) / 2
            p = spline@t
            if abs(p.X - x0) < eps:
                return t
            if p.X < x0:
                t2 = t
            else:
                t1 = t
        else: 
            raise Exception('t not found in spline')


if __name__ == '__main__':
    main()
