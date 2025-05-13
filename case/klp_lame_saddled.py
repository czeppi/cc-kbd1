from typing import Iterator
import copy
from build123d import offset, export_stl, loft, make_face, extrude, mirror
from build123d import Box, Part, Pos, Line, Bezier, Plane, Curve, Axis, Sketch, GeomType
from ocp_vscode import show_object

from base import TOLERANCE, OUTPUT_DPATH
from trackball_holder import TrackballHolderCreator
from thumb_holder import ThumbMiddlePartCreator
from thumb_base import THICKNESS, SLOT_LEN



def main():
    key_cape = LameSaddleKeyCapCreator().create()
    export_stl(key_cape, OUTPUT_DPATH / 'lame-key-cap.stl')
    show_object(key_cape)


class LameSaddleKeyCapCreator:
    """ 
        origin:
          x, y: center
          z:    top of feet (= bottom of cap without rim)
    """
    CAP_HEIGHT = 0
    CAP_X_LEN = 0  # max width
    CAP_Y_LEN = 0  # max deep

    CAP_TOP_FILLET = 1.26

    CAP_RIM_THICKNESS = 0
    CAP_RIM_HEIGHT = 0
    CAP_RIM_FILLET = 0.25  # inside + outside

    FOOT_HEIGHT = 0
    FOOT_X_LEN = 0
    FOOT_Y_LEN = 0
    FOOT_BOTTOM_CHAMFER_RADIUS = 0.25
    FOOT_TOP_CHAMFER_RADIUS = 0.2

    def create(self) -> Part:
        return self._create_cap()

    def _create_cap(self) -> Part:
        bezier = self._create_bezier7_outside()
        bezier += mirror(bezier, Plane.YZ)
        bezier += mirror(bezier, Plane.XZ)
        face = make_face(bezier)
        return extrude(face, 1)
    
    def _create_bezier7_inside(self) -> Line:
        """ sketch 7 """
        x_max = 7.0
        y_max = 6.5

        # tangent_len = self._tangent_len  # 2.5 * 2.3
        tangent_len_finder = TantgentScaleFinder(x_max=x_max, y_max=y_max, x1=6.0, y1=4.88)  # (x1, y1) taken from AutoDesk
        tangent_len = tangent_len_finder.find_tangent_len()

        x0, y0 = 0, y_max
        x1, y1 = tangent_len, y0
        x2, y2 = x_max, tangent_len
        x3, y3 = x2, 0

        return Bezier([(x0, y0), (x1, y1), (x2, y2), (x3, y3)])
    
    def _create_bezier7_outside(self) -> Line:
        """ sketch 7 """
        x_max = 8.75
        y_max = 8.25

        # tangent_len = self._tangent_len
        tangent_len_finder = TantgentScaleFinder(x_max=x_max, y_max=y_max, x1=8.0, y1=6.32)  # (x1, y1) taken from AutoDesk
        tangent_len = tangent_len_finder.find_tangent_len()

        x0, y0 = 0, y_max
        x1, y1 = tangent_len, y0
        x2, y2 = x_max, tangent_len
        x3, y3 = x2, 0

        return Bezier([(x0, y0), (x1, y1), (x2, y2), (x3, y3)])
    
    def _create_bezier14(self) -> Line:
        """ sketch 14, xz plane """
        z_max = 5.8
        z_min = 4.8
        x_max = 7.0
        tangent_len = 3.6  # center, outside=?

        x0, z0 = 0, z_min
        x1, z1 = tangent_len, z0
        x2, z2 = None  # todo
        x3, z3 = x_max, z_max

        return Bezier([(x0, z0), (x1, z1), (x2, z2), (x3, z3)])

    def _create_bezier10(self) -> Line:
        """ sketch 10, yz plane """
        z_min = 1.3
        z_max = 5.8
        y_max = 8.25
        top_tangent_len = 1.131
        bottom_tangent_len = 0.7

        y0, z0 = y_max, z_min
        y1, z1 = y0, 1.65
        y2, z2 = 6.9, 5.4
        y3, z3 = None, z_max  # todo

        return Bezier([(y0, z0), (y1, z1), (y2, z2), (y3, z3)])
    
    def _iter_feet(self) -> Iterator[Part]:
        pass

    def _create_foot(self) -> Part:
        return Box()
    

class TantgentScaleFinder:
    """ 
        TantgentScaleFinder(x_max=7, y_max=6.5, x1=6.0, y1=4.88)
        => tangent_len=5.552734375
        => tangent_scale = tangent_len / 2.5 = 2.22109375

        TantgentScaleFinder(x_max=8.74, y_max=8.25, x1=8.0, y1=6.32) 
        => tangent_len=8.0224609375
        => tangent_scale = tangent_len / 3.5 = 2.2921316964285716
    """

    def __init__(self, x_max: float, y_max: float, x1: float, y1):
        self._x_max = x_max
        self._y_max = y_max
        self._x1 = x1
        self._y1 = y1
        
    def find_tangent_len(self) -> float:
        tangent_len_a = 1.0
        tangent_len_b = 10.0
        eps = 1e-3

        for i in range(100):
            tangent_len = (tangent_len_a + tangent_len_b) / 2
            y = self._find_y_intersection(tangent_len=tangent_len)
            print(f'{i}: {y}, tangent_len={tangent_len}')
            if abs(y - self._y1) < eps:
                return tangent_len
            elif y < self._y1:
                tangent_len_a = tangent_len
            else:
                tangent_len_b = tangent_len
        else:
            raise Exception('no tangent_len found')

    def _find_y_intersection(self, tangent_len: float) -> float:
        sketch = self._create_sketch(tangent_len=tangent_len)
        edges = sketch.edges().filter_by(GeomType.BEZIER)
        assert len(edges) == 1

        bezier_edge = edges[0]
        intersection_points = bezier_edge.find_intersection_points(Axis.Y)
        assert len(intersection_points) == 1

        y_interseciton = intersection_points[0].Y
        return y_interseciton

    def _create_sketch(self, tangent_len: float) -> Sketch:
        bezier = self._create_bezier(tangent_len=tangent_len)

        lines = Curve() + [Line((0, 0), bezier@0), bezier, Line(bezier@1, (0, 0))]
        face = make_face(lines)
        return Pos(X=-self._x1) * face

    def _create_bezier(self, tangent_len: float) -> Line:
        x_max, y_max = self._x_max, self._y_max

        return Bezier((0, y_max),
                      (tangent_len, y_max),
                      (x_max, tangent_len),
                      (x_max, 0))


if __name__ == '__main__':
    main()
