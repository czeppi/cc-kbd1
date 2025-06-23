from typing import Iterator
import copy
import sys
from enum import Enum
from pathlib import Path
import math
from dataclasses import dataclass

sys.path.append(str(Path(__file__).absolute().parent.parent))

from build123d import export_stl, make_face, extrude, offset, mirror
from build123d import Part, Pos, Rot, Curve, Cylinder, Solid, Line, EllipticalCenterArc, AngularDirection, Edge, RadiusArc, Kind, Box, Plane, Sketch, Polyline, CounterBoreHole
from ocp_vscode import show_object

from base import OUTPUT_DPATH
import data


"""
    links:
    - https://www.kailhswitch.com/mechanical-keyboard-switches/box-switches/choc-type-hot-swap-socket.html  # official
    - https://kbd.news/Hot-swap-socket-holders-1669.html  # unprecise
    - https://github.com/daprice/keyswitches.pretty/blob/master/Kailh_socket_PG1350.kicad_mod  # for kicad
    - https://github.com/kiswitch/kiswitch
"""


class kailh_choc_v1_data:
    """ data of github.com/keyboardio/keyswitch_documentation/blob/master/datasheets/Kailh/PG135001D02-Brown-Choc.pdf
    """
    SUB_BODY_SIZE = 13.8  # the size of the squared part, which is penetrated in the case
    SUB_BODY_HEIGHT = 2.1  # (5.0 - 0.8) / 2
    STUBS_HEIGHT = 2.65  # height of the 3 stubs, which stabilized the switch
    CENTER_STUB_RADIUS = 1.7
    OUTER_STUB_RADIUS = 0.95  # radius of the 2 outer stubs, which stabilized the switch
    OUTER_STUB_CX = 5.5  # center of the 2 outer stubs
    PIN1_HOLE_CY = 3.8
    PIN2_HOLE_CY = 5.9  # center of the pin hole, which is on the y-axis


class hot_swap_socket_data:
    """ data of https://www.kailhswitch.com/mechanical-keyboard-switches/box-switches/choc-type-hot-swap-socket.html
    """
    BODY_HEIGHT = 1.8
    BODY_X_LEN = 9.55  # x-axis
    BODY_Y_LEN = 6.85
    SIDE_Y_LEN = 4.65  # the y extension on the left + right side
    CHAMFER_XY = 0.8  # the dx (== dy) value of the chamfers
    FILLET_RADIUS = 0.8
    STUDS_RADIUS = 1.5
    STUDS_HEIGHT = 1.25
    STUDS_DX = 5.0  # x-distance of the 2 studs
    STUDS_DY = 2.2
    TERMINALS_WIDTH = 1.68  # y-extension of the left + right terminal
    Y_OFFSET = -4.75 # 5.85 - studs_dy/2, use 5.85 (not kailh_choc_v1_data.pin_hole_cy), cause pins_dy != studs.dy
    X_OFFSET = -2.5  # studs_dx / 2


class hot_swap_socket_data_old:
    """ data of https://kbd.news/Hot-swap-socket-holders-1669.html

        Y
        |       2 * * * 3
        |       *       a
        1 * * *     O
        b               b
            O     * * * 4
        a       *
     -- 0 * * * 5 ---------------> X
        |      
    """
    Y1 = 4.6  # exact 4.603
    X2 = 4.987
    X34 = 10.154
    Y23 = 7.0  # exact: 7.005
    Y4 = 2.4  # exact: 2.401
    X5 = 4.614
    a = 1.1  # 1.1 + 1.101
    b = 1.2  # exact: 1.201

    BODY_LEN_Z = 2.105
    BODY_RADIUS_X = 1.9  # exact: 1.878 + 1.94
    BODY_RADIUS_Y = 2.4  # exact: 2.401 + 2.402

    STUD_RADIUS = 1.616
    STUD_HEIGHT = 0.695
    STUD1_CX = 2.6  # exact: 2.601
    STUD1_CY = 2.3  # exact: 2.301
    STUD2_CX = 7.7  # exact: 7.703
    STUD2_CY = 4.6  # exact: 4.603


def main():
    create_switch_pair_holder()


def create_switch_pair_holder():
    holder = SwitchPairHolderCreator().create(OUTPUT_DPATH)
    show_object(holder)


def create_switch_socket():
    socket = SwitchSocketCreator().create()
    export_stl(socket, OUTPUT_DPATH / 'hot-swap-socket.stl')
    show_object(socket)


class SwitchPairHolderCreator:
    TILT_ANGLE = 15  # 15° for each side
    HOLDER_LEFT_RIGHT_BORDER = 1.0
    HOLDER_FRONT_BORDER = 3.2  # s. keys_holder.py#BACK_BORDER
    HOLDER_BACK_BORDER = 1.0
    MIDDLE_PART_HEIGHT_AT_CENTER = 3.0
    CABLE_DIAMETER = 1.3  # AWG26 without tolerance
    CABLE_SLOT_Y = 7.0
    TOLERANCE = 0.1
    CONN_POINT_DX = 4.5

    @property
    def _square_hole_len(self) -> float:
        return kailh_choc_v1_data.SUB_BODY_SIZE + 2 * self.TOLERANCE
    
    @property
    def _square_hole_height(self) -> float:
        return kailh_choc_v1_data.SUB_BODY_HEIGHT - self.TOLERANCE
    
    def create(self, output_dpath: Path|None=None) -> list[Solid]:
        top_part = self.create_top()
        middle_part = self.create_middle_part()

        if output_dpath:
            export_stl(top_part, OUTPUT_DPATH / 'switch-pair-holder-top.stl')
            export_stl(middle_part, OUTPUT_DPATH / 'switch-pair-holder-middle.stl')

        return [top_part, middle_part]

    def create_top(self) -> Solid:
        back_part = self._create_top_back_part()
        back_box = back_part.bounding_box()

        back_part = Rot(X=self.TILT_ANGLE) * Pos(Y=-back_box.min.Y) * back_part
        front_part = Rot(Z=180) * copy.copy(back_part)
        top_part = back_part + front_part

        # => origin: x, y: center, z: bottom

        top_part -= self._create_top_counter_bore_hole()

        top_part.label = 'top'
        return top_part
    
    def _create_top_back_part(self) -> Solid:
        """ 
        origin: x, y: center of hole, z: bottom
        """
        # 
        body = self._create_top_body()

        a = self._square_hole_len
        h = self._square_hole_height
        square_hole = Pos(Z=h/2 + hot_swap_socket_data.STUDS_HEIGHT) * Box(a, a, h)

        holes = list(self._iter_switch_holes())
        hot_swap_socket_studs = list(self._iter_hot_swap_socket_studs())

        neg_parts = [square_hole] + holes + hot_swap_socket_studs
        return body - neg_parts

    def _create_top_body(self) -> Solid:
        face = self._create_top_profile_face()
        width = 2 * self.HOLDER_LEFT_RIGHT_BORDER + self._square_hole_len
        
        return Pos(X=-width/2) * extrude(face, width)

    def _create_top_profile_face(self) -> Sketch:
        """
        order of points:
               z
           2   |    1
          3    +----0-----> y
        """
        # 

        angle_rad = math.radians(self.TILT_ANGLE)

        square_hole_len = self._square_hole_len
        square_hole_height = self._square_hole_height

        y01 = square_hole_len/2 + self.HOLDER_BACK_BORDER 
        y2 = -square_hole_len/2 - self.HOLDER_FRONT_BORDER
        z12 = square_hole_height + hot_swap_socket_data.STUDS_HEIGHT
        y3 = y2 - z12 * math.tan(angle_rad)

        points = [
            (y01, 0),
            (y01, z12),
            (y2, z12),
            (y3, 0),
            (y01, 0),
        ]
        back_half = Polyline(points)
        return make_face(Plane.YZ * back_half)
    
    def _iter_hot_swap_socket_studs(self) -> Iterator[Solid]:
        data = hot_swap_socket_data
        h = data.STUDS_HEIGHT
        r = data.STUDS_RADIUS
        cyl = Pos(Z=h/2) * Cylinder(radius=r, height=h)
        dx = data.STUDS_DX / 2
        dy = data.STUDS_DY / 2

        y0 = hot_swap_socket_data.Y_OFFSET
        x0 = hot_swap_socket_data.X_OFFSET

        yield Pos(X=x0 - dx, Y=y0 + dy) * copy.copy(cyl)
        yield Pos(X=x0 + dx, Y=y0 - dy) * copy.copy(cyl)    
    
    def _create_top_counter_bore_hole(self) -> Part:
        m2 = data.FlatHeadScrewM2

        angle_rad = math.radians(self.TILT_ANGLE)
        h = (hot_swap_socket_data.STUDS_HEIGHT + self._square_hole_height) /  math.cos(angle_rad)
        h_offset =  math.tan(angle_rad) * m2.HEAD_RADIUS
        
        pos = Pos(X=self.CONN_POINT_DX, Z=h+h_offset)
        hole = CounterBoreHole(radius=m2.RADIUS, 
                               counter_bore_radius=m2.HEAD_RADIUS, 
                               counter_bore_depth=m2.HEAD_HEIGHT + h_offset, 
                               depth=1000)

        return Plane.XY * pos * hole
        
    def create_middle_part(self) -> Solid:
        back_part = self._create_middle_back_part()
        front_part = Rot(Z=180) * copy.copy(back_part)
        middle_part = back_part + front_part

        counter_bore_hole = self._create_middle_counter_bore_hole()
        heat_set_insert_hole = self._create_middle_heat_set_insert_hole()
        middle_part -= [counter_bore_hole, heat_set_insert_hole]

        middle_part.label = 'middle'
        return middle_part
    
    def _create_middle_back_part(self) -> Solid:
        body = self._create_middle_body()
        body_box = body.bounding_box()

        angle_rad = math.radians(self.TILT_ANGLE)
        top_height = self._square_hole_height + hot_swap_socket_data.STUDS_HEIGHT
        y_off0 = self._square_hole_len/2 + self.HOLDER_FRONT_BORDER + top_height * math.tan(angle_rad)

        x_off = hot_swap_socket_data.X_OFFSET
        y_off = hot_swap_socket_data.Y_OFFSET + y_off0
        z_off = hot_swap_socket_data.STUDS_HEIGHT
        hot_swap_socket = Rot(X=self.TILT_ANGLE) * Pos(X=x_off, Y=y_off, Z=z_off) * HotSwapSocketCreator3().create()
        #hot_swap_socket_box = hot_swap_socket.bounding_box()

        holes = [Rot(X=self.TILT_ANGLE) * Pos(Y=y_off0) * hole 
                 for hole in self._iter_switch_holes()]
        
        cable_diam = self.CABLE_DIAMETER + self.TOLERANCE
        z_off = cable_diam/2 + body_box.min.Z
        cabel_slot = Pos(Y=self.CABLE_SLOT_Y, Z=z_off) * Box(1000, cable_diam, cable_diam)

        neg_parts = [hot_swap_socket, cabel_slot] + holes
        return body - neg_parts

    def _create_middle_body(self) -> Solid:
        face = self._create_middle_profile_face()
        width = 2 * self.HOLDER_LEFT_RIGHT_BORDER + self._square_hole_len
        
        return Pos(X=width/2) * extrude(face, width)
    
    def _create_middle_profile_face(self) -> Sketch:
        """
        order of points:
               z
               |     1
               0---------> y
               3   2
        """
        angle_rad = math.radians(self.TILT_ANGLE)

        r = self.HOLDER_FRONT_BORDER + self._square_hole_len/2 + kailh_choc_v1_data.CENTER_STUB_RADIUS + 4.0
        y1 = r * math.cos(angle_rad)
        z1 = r * math.sin(angle_rad)
        y2 = y1 - 4.0
        z23 = -self.MIDDLE_PART_HEIGHT_AT_CENTER

        points = [
            (0, 0),
            (y1, z1),
            (y2, z23),
            (0, z23),
            (0, 0),
        ]
        back_half = Polyline(points)
        return make_face(Plane.YZ * back_half)

    def _create_middle_counter_bore_hole(self) -> Part:
        m2 = data.FlatHeadScrewM2

        angle_rad = math.radians(self.TILT_ANGLE)
        h_offset =  math.tan(angle_rad) * m2.HEAD_RADIUS
        
        pos = Pos(X=-self.CONN_POINT_DX, Z=h_offset)
        hole = CounterBoreHole(radius=m2.RADIUS, 
                               counter_bore_radius=m2.HEAD_RADIUS, 
                               counter_bore_depth=m2.HEAD_HEIGHT + h_offset, 
                               depth=1000)

        return Plane.XY * pos * hole
    
    def _create_middle_heat_set_insert_hole(self) -> Solid:
        m2 = data.FlatHeadScrewM2
        angle_rad = math.radians(self.TILT_ANGLE)
        h_offset =  math.tan(angle_rad) * m2.HEAT_SET_INSERT_RADIUS

        pos = Pos(X=self.CONN_POINT_DX, Z=h_offset)
        hole = CounterBoreHole(radius=m2.RADIUS, 
                               counter_bore_radius=m2.HEAT_SET_INSERT_RADIUS, 
                               counter_bore_depth=2.0 + h_offset, 
                               depth=1000)
        
        return Plane.XY * pos * hole

    def create_foot(self) -> Solid:
        pass

    def _iter_switch_holes(self) -> Iterator[Solid]:
        data = kailh_choc_v1_data
        tol = self.TOLERANCE
        height = data.STUBS_HEIGHT + tol
        z_off = hot_swap_socket_data.STUDS_HEIGHT - height/2
        yield Pos(Z=z_off) * Cylinder(radius=data.CENTER_STUB_RADIUS + tol, height=height)
        yield Pos(Z=z_off, X=-data.OUTER_STUB_CX) * Cylinder(radius=data.OUTER_STUB_RADIUS + tol, height=height)
        yield Pos(Z=z_off, X=data.OUTER_STUB_CX) * Cylinder(radius=data.OUTER_STUB_RADIUS + tol, height=height)


class SwitchSocketCreator:

    def __init__(self):
        self._holder_left_right_border = 1.0
        self._holder_front_border = 3.2  # s. keys_holder.py#BACK_BORDER
        self._holder_back_border = 1.0
        self._tolerance = 0.1

    def create(self) -> Solid:
        square_hole_box = self._create_switch_square_hole_box()
        square_hole_bounding_box = square_hole_box.bounding_box()
        square_hole_height = square_hole_bounding_box.max.Z - square_hole_bounding_box.min.Z

        hot_swap_socket = Pos(X=hot_swap_socket_data.X_OFFSET, Y=hot_swap_socket_data.Y_OFFSET) * HotSwapSocketCreator3().create()
        hot_swap_socket_box = hot_swap_socket.bounding_box()

        body_z_max = square_hole_height
        body_z_min = hot_swap_socket_box.min.Z
        body = self._create_body(z_min=body_z_min, z_max=body_z_max)

        holes = list(self._iter_holes())
        neg_parts = [hot_swap_socket, square_hole_box] + holes
        result = body - neg_parts

        return result
    
    def _create_switch_square_hole_box(self) -> Solid:
        square_hole_len = kailh_choc_v1_data.SUB_BODY_SIZE + 2 * self._tolerance
        height = kailh_choc_v1_data.SUB_BODY_HEIGHT - self._tolerance
        return Pos(Z=height/2) * Box(square_hole_len, square_hole_len, height)
    
    def _create_body(self, z_min: float, z_max: float) -> Solid:
        square_hole_len = kailh_choc_v1_data.SUB_BODY_SIZE + 2 * self._tolerance
        x_len = square_hole_len + 2 * self._holder_left_right_border
        y_len = square_hole_len + self._holder_back_border + self._holder_front_border
        height = z_max - z_min
        y_offset = y_len/2 - self._holder_front_border - square_hole_len/2
        z_offset = -height/2 + z_max
        return Pos(Y=y_offset, Z=z_offset) * Box(x_len, y_len, height)
    
    def _iter_holes(self) -> Iterator[Solid]:
        data = kailh_choc_v1_data
        tol = self._tolerance
        height = data.STUBS_HEIGHT + tol
        yield Pos(Z=-height/2) * Cylinder(radius=data.CENTER_STUB_RADIUS + tol, height=height)
        yield Pos(Z=-height/2, X=-data.OUTER_STUB_CX) * Cylinder(radius=data.OUTER_STUB_RADIUS + tol, height=height)
        yield Pos(Z=-height/2, X=data.OUTER_STUB_CX) * Cylinder(radius=data.OUTER_STUB_RADIUS + tol, height=height)


@dataclass
class PathItem:  # names from SVG

    def create_edge(self, x0: float, y0: float) -> Edge:
        raise NotImplementedError()
    
    @property
    def dx(self) -> float:
        raise NotImplementedError()

    @property
    def dy(self) -> float:
        raise NotImplementedError()


@dataclass
class L(PathItem):  # line to 
    dx: float = 0.0
    dy: float = 0.0

    def create_edge(self, x0: float, y0: float) -> Edge:
        return Line((x0, y0), (x0 + self.dx, y0 + self.dy))
    

@dataclass
class A(PathItem):  # arc
    r: float
    dx: float = 0.0
    dy: float = 0.0
    #sf: bool = 

    def create_edge(self, x0: float, y0: float) -> Edge:
        eps = 1E-6
        print(f'RadiusArc(start_point({x0}, {y0}), end_point=({x0 + self.dx}, {y0 + self.dy}), radius={self.r})')
        return RadiusArc(start_point=(x0, y0), end_point=(x0 + self.dx, y0 + self.dy), radius=self.r + eps)


class HotSwapSocketCreator1:
    """ https://kbd.news/Hot-swap-socket-holders-1669.html
    """

    def __init__(self):
        self._left_right_terminal_len = 5.0

    def create(self):
        body = self._create_body()
        studs = list(self._iter_studs())
        return body + studs
    
    def _create_body(self) -> Solid:
        data = hot_swap_socket_data_old

        lines = Curve() + list(self._iter_profile_items())
        face = make_face(lines)
        return extrude(face, data.BODY_LEN_Z)

    def _iter_profile_items(self) -> Iterator[Edge]:
        """ 
            Y
            |       7 * * * 8
            |       *       9 * 10
            5 * * 6     O       *
        3 * 4              12 * 11
        *       O    14 * *13
        2 * 1       *
            0 * * *15 ---------------> X
            |      
        """
        data = hot_swap_socket_data_old
        term_len = self._left_right_terminal_len

        x1, y1 = 0.0, data.a
        x2, y2 = -term_len, y1
        x3, y3 = x2, data.Y1 - data.b
        x4, y4 = 0.0, y3
        x5, y5 = 0.0, data.Y1
        x6, y6 = data.X2 - data.BODY_RADIUS_X, y5
        x7, y7 = data.X2, data.Y23
        x8, y8 = data.X34, data.Y23
        x9, y9 = x8, y8 - data.a
        x10, y10 = x9 + term_len, y9
        x11, y11 = x10, data.Y4 + data.b
        x12, y12 = x8, y11
        x13, y13 = x8, data.Y4
        x14, y14 = data.X5 + data.BODY_RADIUS_X, y13
        x15, y15 = data.X5, 0.0

        yield Line((0, 0), (x1, y1))
        yield Line((x1, y1), (x2, y2))
        yield Line((x2, y2), (x3, y3))
        yield Line((x3, y3), (x4, y4))
        yield Line((x4, y4), (x5, y5))
        yield Line((x5, y5), (x6, y6))
        yield EllipticalCenterArc(center=(x6, y7), x_radius=data.BODY_RADIUS_X, y_radius=data.BODY_RADIUS_Y, 
                                  start_angle=-90, end_angle=0, angular_direction=AngularDirection.COUNTER_CLOCKWISE)
        yield Line((x7, y7), (x8, y8))
        yield Line((x8, y8), (x9, y9))
        yield Line((x9, y9), (x10, y10))
        yield Line((x10, y10), (x11, y11))
        yield Line((x11, y11), (x12, y12))
        yield Line((x12, y12), (x13, y13))
        yield Line((x13, y13), (x14, y14))
        yield EllipticalCenterArc(center=(x14, y15), x_radius=data.BODY_RADIUS_X, y_radius=data.BODY_RADIUS_Y, 
                                  start_angle=90, end_angle=180, angular_direction=AngularDirection.COUNTER_CLOCKWISE)
        yield Line((x15, y15), (0, 0))

    def _iter_studs(self) -> Iterator[Solid]:
        data = hot_swap_socket_data_old
        yield Pos(X=data.STUD1_CX, Y=data.STUD1_CY, Z=-data.STUD_HEIGHT/2) * Cylinder(radius=data.STUD_RADIUS, height=data.STUD_HEIGHT)
        yield Pos(X=data.STUD2_CX, Y=data.STUD2_CY, Z=-data.STUD_HEIGHT/2) * Cylinder(radius=data.STUD_RADIUS, height=data.STUD_HEIGHT)


class HotSwapSocketCreator2:
    """ https://github.com/daprice/keyswitches.pretty/blob/master/Kailh_socket_PG1350.kicad_mod
    """

    def create(self) -> Solid:
        raise NotImplementedError()

    def _iter_profile1_items(self) -> Iterator[Edge]:
        """
            große Quadrat: 13.8 x 13.8

            drei Kreis in Mitte (auf X-Achse)
            großer Kreis in der Mitte: radius: 3.429/2
            kleinen Kreise links und rechts:
                radius: 1.7018/2
                x: +-5.5
                y: 0.0

            Socket
            left_circle:
                cx: -5.0
                cy:  3.75
                r:   1.5
            right_circle:
                cx: 0.0
                cy: 5.95
                r:  1.5 
            outline: 
                start_point: -7.0, 1.5
                hline: 4.5  # right
                vline: 0.7  # down
                arc: 
                r: 1.5
                end_point: -1.0, 3.7
                hline: 2.5
                line: 
                end_point: 2.0, 4.2
                vline: 3.45  # down  => 2.0, 7.7
                line:
                end_point: 1.5, 8.2
                hline: 3.0  => -1.5, 8.2
                line:
                end_point: -2.0, 7.7
                vline: 1.0  # up  => -2.0, 6.7
                arc:
                r: 0.5
                end_point: -2.5, 6.2
                hline: -4.5  => -7.0, 6.2
                vline: 0.6 => -7.0, 5.6  # up
                vline: 3.6 => -7.2, 2.0  # up
                vline: 0.5 => -7.0, 1.5  # up
        """
    pass


class HotSwapSocketCreator3:
    """ www.kailhswitch.com/mechanical-keyboard-switches/box-switches/choc-type-hot-swap-socket.html

                       * * * * 
                    *          * * *
                   *      O        *
          * * * *              * * *
    * * S            * * * * *   
    *         O     *
    * * *           *
          * * * * *

    S = start point
    """
    def __init__(self):
        self._left_right_terminal_len = 10.0
        self._tolerance = 0.1

    def create(self) -> Solid:
        body = self._create_body()

        studs = list(self._iter_studs())
        part = Part() + ([body] + studs)
        part = mirror(part, Plane.XZ)
        part = offset(part, amount=self._tolerance, kind=Kind.INTERSECTION)
        return part

    def _iter_studs(self) -> Iterator[Solid]:
        data = hot_swap_socket_data
        h = data.STUDS_HEIGHT
        r = data.STUDS_RADIUS
        cyl = Pos(Z=-h/2) * Cylinder(radius=r, height=h)
        dx = data.STUDS_DX / 2
        dy = data.STUDS_DY / 2
        yield Pos(X=-dx, Y=-dy) * copy.copy(cyl)
        yield Pos(X=dx, Y=dy) * copy.copy(cyl)

    def _create_body(self) -> Solid:
        lines = Curve() + list(self._iter_profile_edges())
        cx, cy = self._calc_center()

        face = make_face(lines)
        data = hot_swap_socket_data
        height = data.BODY_HEIGHT
        return Pos(X=-cx, Y=-cy, Z=-height - data.STUDS_HEIGHT) * extrude(face, height)

    def _calc_center(self) -> tuple[float, float]:
        items = list(self._iter_path_items())

        x_values = []
        y_values = []
        
        x0, y0 = 0.0, 0.0
        for item in items:
            x0 += item.dx
            y0 += item.dy
            x_values.append(x0)
            y_values.append(y0)

        x_min = min(x_values)
        x_max = max(x_values)
        y_min = min(y_values)
        y_max = max(y_values)

        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        return cx, cy

    def _iter_profile_edges(self) -> Iterator[Edge]:
        x0, y0 = 0.0, 0.0
        for item in self._iter_path_items():
            yield item.create_edge(x0=x0, y0=y0)
            x0 += item.dx
            y0 += item.dy

    def _iter_path_items(self) -> Iterator[PathItem]:
        chamfer_xy = hot_swap_socket_data.CHAMFER_XY
        fillet_radius = hot_swap_socket_data.FILLET_RADIUS
        term_len = self._left_right_terminal_len
        term_width = hot_swap_socket_data.TERMINALS_WIDTH
        x_infl, y_infl = self._calc_inflection_point()
        side_height = hot_swap_socket_data.SIDE_Y_LEN

        a = (side_height - 2 * chamfer_xy - term_width) / 2  # length of rim next to terminal

        yield L(dy=a)
        yield L(dx=chamfer_xy, dy=chamfer_xy)
        yield L(dx=1.95)
        yield A(r=-2.0, dx=x_infl, dy=y_infl)
        yield A(r=fillet_radius, dx=2.75 - x_infl, dy=2.2 - y_infl)
        yield L(dx=4.05)
        yield L(dy=-chamfer_xy - a)

        yield L(dx=term_len)
        yield L(dy=-term_width)
        yield L(dx=-term_len)

        yield L(dy=-a)
        yield A(r=fillet_radius, dx=-fillet_radius, dy=-fillet_radius)
        yield L(dx=-2.9)
        yield A(r=-1.1, dx=-1.1, dy=-1.1)
        yield L(dy=-0.3)
        yield L(dx=-chamfer_xy, dy=-chamfer_xy)
        yield L(dx=-3.15)
        yield L(dx=-chamfer_xy, dy=chamfer_xy)
        yield L(dy=a)

        yield L(dx=-term_len)
        yield L(dy=term_width)
        yield L(dx=term_len)

    def _calc_inflection_point(self):
        """
           C1
           .               * * *
           .           * *     .
           .         X         .
           .     * *           . 
           * * *               .
                               C2
 
          X:  inflection point (must lie on the connection line between C1 and C2)
          C1: center of left circle (position fixed by radius)
          C2: center of right circle (position fixed by radius)

          set C1 = (0, 0)
            =>  x**2 + y**2 = r1**2

          dx = width, dy = r1 + r2 - height
            =>  y = m * x,  with m = dy / dx

          => x**2 + m**2 * x**2 == r1**2
          => x**2 = r1**2 / (1 + m**2)
        """
        r1 = 2.0  # left radius
        r2 = 0.8  # right radius
        width = 2.75  # total width
        height = 2.2  # total height

        m = (r1 + r2 - height) / width
        x = math.sqrt(r1**2 / (1 + m**2))
        y = m * x

        print(f'inflection point: ({x}, {y})')

        return x, r1 - y


if __name__ == '__main__':
    main()
