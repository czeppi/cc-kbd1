import math
import copy
from pathlib import Path
from build123d import mirror, extrude, offset, export_stl, make_face
from build123d import Box, Cylinder, Part, Rectangle, Pos, Rot, Kind, Polygon, Polyline, Plane, Wedge, Axis, RigidJoint, Location, Circle, Align, Triangle
from ocp_vscode import show_object


TOLERANCE = 0.1

SUPPORT_BUTTOM_WIDTH = 30.0
SUPPORT_TOP_WIDTH = 8.0
SUPPORT_HEIGHT = 50.0
SUPPORT_THICKNESS = 5.0

STUD_RADIUS = 5.0 / 2 - TOLERANCE
STUD_HEIGHT = 4.0 - TOLERANCE
STUD_DIST = 20.0  # must be smaller than SUPPORT_BUTTOM_WIDTH

HEAD_ANGLE = 15.0
FOOT_ANGLE = 15.0

OUTPUT_DPATH = Path('output')


def main():
    creator = SkeletonSupportCreator()
    support = creator.create()
    
    #export_stl(support, OUTPUT_DPATH / 'skeleton-support.stl')
    show_object(support)


class SkeletonSupportCreator:

    def __init__(self):
        pass

    def create(self) -> Part:
        x1 = SUPPORT_TOP_WIDTH / 2
        x2 = SUPPORT_BUTTOM_WIDTH / 2
        y1 = SUPPORT_HEIGHT

        points = [(0.0, 0.0), (x2, 0.0), (x1, y1), (0.0, y1)]
        poly_line = Polyline(points)
        outer_polygon = poly_line + mirror(poly_line, Plane.YZ)
        inner_polygon = offset(outer_polygon, -SUPPORT_THICKNESS)
        #trapez = make_face(Plane.XZ * (outer_polygon - inner_polygon))
        outer_face = make_face(Plane.XZ * outer_polygon)
        inner_face = make_face(Plane.XZ * inner_polygon)
        result_face = outer_face - inner_face

        rotated_face = Rot(X=30) * result_face
        frame = Pos(Y=-SUPPORT_THICKNESS/2) * extrude(rotated_face, SUPPORT_THICKNESS, dir=(0.0, 1.0, 0.0))

        top_stud = self._create_top_stud(frame)
        buttom1_stud = self._create_buttom_stud(x_offset=STUD_DIST / 2)
        buttom2_stud = self._create_buttom_stud(x_offset=-STUD_DIST / 2)

        return frame + top_stud + buttom1_stud + buttom2_stud
    
    def _create_top_stud(self, frame: Part) -> Part:
        stud = Cylinder(radius=STUD_RADIUS, height=STUD_HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN))

        top_face = frame.faces().sort_by(Axis.Z).last
        top_plane = Plane(origin=top_face.center(), z_dir=top_face.normal_at(top_face.center()))
        
        return top_plane * copy.copy(stud)
    
    def _create_buttom_stud(self, x_offset: float) -> Part:
        return Pos(X=x_offset) * Cylinder(radius=STUD_RADIUS, height=STUD_HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MAX))


if __name__ == '__main__':
    main()