from typing import Iterator
import copy
from enum import Enum
import math

from build123d import export_stl, loft, make_face, sweep, new_edges, fillet, mirror, extrude
from build123d import Box, Part, Pos, Rot, Plane, Axis, Sketch, Polyline, Bezier, Curve, Cylinder, Solid, BoundBox, Line, EllipticalCenterArc, AngularDirection
from ocp_vscode import show_object

from base import OUTPUT_DPATH


class how_swap_socket_data:
    """
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
    hot_swap_socket = HotSwapSocketCreator().create()
    # export_stl(hot_swap_socket, OUTPUT_DPATH / 'hot-swap-socket.stl')
    show_object(hot_swap_socket)


class HotSwapSocketCreator:

    def __init__(self):
        self._left_right_terminal_len = 5.0

    def create(self):
        body = self._create_body()
        studs = list(self._iter_studs())
        return body + studs
    
    def _create_body(self) -> Solid:
        data = how_swap_socket_data

        lines = Curve() + list(self._iter_profile_items())
        face = make_face(lines)
        return extrude(face, data.BODY_LEN_Z)

    def _iter_profile_items(self):
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
        data = how_swap_socket_data
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
        data = how_swap_socket_data
        yield Pos(X=data.STUD1_CX, Y=data.STUD1_CY, Z=-data.STUD_HEIGHT/2) * Cylinder(radius=data.STUD_RADIUS, height=data.STUD_HEIGHT)
        yield Pos(X=data.STUD2_CX, Y=data.STUD2_CY, Z=-data.STUD_HEIGHT/2) * Cylinder(radius=data.STUD_RADIUS, height=data.STUD_HEIGHT)


if __name__ == '__main__':
    main()
