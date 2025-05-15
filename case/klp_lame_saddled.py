from typing import Iterator
import copy
from build123d import offset, export_stl, loft, make_face, extrude, mirror, sweep, new_edges, fillet, chamfer
from build123d import Box, Part, Pos, Line, Bezier, Plane, Curve, Axis, Sketch, GeomType, Rectangle, Rot, Polyline, RectangleRounded
from ocp_vscode import show_object

from base import TOLERANCE, OUTPUT_DPATH
from trackball_holder import TrackballHolderCreator
from thumb_holder import ThumbMiddlePartCreator
from thumb_base import THICKNESS, SLOT_LEN


type Point = tuple[float, float]


def main():
    #key_cape = Plane.front * Pos(Z=1, Y=1) * Rectangle(1, 1)
    key_cape = LameSaddleKeyCapCreator().create()
    #export_stl(key_cape, OUTPUT_DPATH / 'lame-key-cap.stl')
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
        cap_body = self._create_cap_body()
        sweep_part = self._create_sweep_part()

        sweeped_cap_body = cap_body - sweep_part

        edges = new_edges(cap_body, sweep_part, combined=sweeped_cap_body)
        #edges = sweeped_cap_body.edges().group_by(Axis.Z)[0]

        #r = sweeped_cap_body.max_fillet(edges, tolerance=0.01)
        #print(f'r={r}')
        return fillet(edges, 1.26)
        
    def _create_cap_body(self) -> Part:
        rect_bottom = Pos(Z=1.3) * RectangleRounded(16.5, 15.5, radius=2)  # Rectangle(17.5, 16.5)
        rect_middle = Pos(Z=3.55) * RectangleRounded(15.5, 14.5, radius=2)
        rect_top = Pos(Z=5.8) * RectangleRounded(13, 12, radius=2)  # Rectangle(14, 13)
        return loft(Sketch() + [rect_bottom, rect_middle, rect_top])


        return CapBodyCreator().create()
    
    def _create_sweep_part(self) -> Part:
        face = Plane.front * self._create_face_to_sweep()
        sweep_path = self._create_bezier_sketch19()
        return sweep(face, path=Plane.right * sweep_path)
    
    def _create_face_to_sweep(self) -> Sketch:
        bezier = self._create_bezier_sketch14_shape1()
        p1 = bezier@0
        p2 = bezier@1

        polyline = Polyline([(p1.X, p1.Y), (p1.X, p1.Y + 3), (p2.X, p2.Y + 3), (p2.X, p2.Y)])
        return make_face(bezier + polyline)

    def _create_bezier_sketch10_shape2(self) -> Curve:
        points = [
            (8.25, 1.3),
            (8.205, 2.606),
            (7.985, 4.304),
            (6.5, 5.8),
        ]
        bezier = Bezier(points)
        return bezier

    def _create_bezier_sketch11_shape3(self) -> Curve:
        points = [
            (8.75, -1.3), 
            (8.705, -2.606), 
            (8.485, -4.304), 
            (7.0, -5.8),
        ]
        bezier = Bezier(points)
        return bezier
    
    def _create_bezier_sketch14_shape1(self) -> Curve:
        points = [
            (-7.0, 5.8),    # changed sign of all y values
            (-4.734, 4.827), 
            (0.0, 4.8),  
            (4.734, 4.827), 
            (7.0, 5.8),
        ]
        bezier = Bezier(points[:3]) + Bezier(points[2:])  # quad bezier curves!
        return bezier

    def _create_bezier_sketch15_shape9(self) -> Curve:
        points = [
            (7.9, 0.0), 
            (7.9, 1.632), (7.845, 3.244), (7.668, 4.401), 
            (7.525, 5.336),  (7.296, 5.955), (7.001, 6.332), 
            (6.721, 6.689), (6.363, 6.910), (5.715, 7.078), 
            (4.796, 7.317), (3.308, 7.375), (1.601, 7.393),
            (-0.306, 7.412), (-2.423, 7.423), (-3.983, 7.319), 
            (-5.136, 7.242), (-5.967, 7.070), (-6.461, 6.791), 
            (-6.889, 6.550), (-7.140, 6.253), (-7.363, 5.662), 
            (-7.640, 4.926), (-7.791, 3.713), (-7.856, 2.241), 
            (-7.927, 0.605), (-7.921, -1.307), (-7.823, -2.862), 
            (-7.742, -4.156), (-7.574 -5.181), (-7.305, -5.808),
            (-7.060, -6.376), (-6.791, -6.650), (-6.282, -6.882),
            (-5.698, -7.148), (-4.721, -7.291), (-3.438, -7.349),
            (-1.738, -7.425), (0.4645, -7.418), (2.333, -7.382),
            (3.741, -7.355), (4.935, -7.282), (5.721, -7.076),
            (6.375, -6.906), (6.732, -6.683), (7.013, -6.316),
            (7.316, -5.922), (7.548, -5.259), (7.688, -4.264),
            (7.849, -3.121), (7.9, -1.5696), (7.9, 0.0),
        ]

    def _create_bezier_sketch16_shape20(self) -> Curve:
        points = [
            (7.4, 0.0),
            (7.4, 1.621), (7.343, 3.222), (7.174, 4.325),
            (7.038, 5.214), (6.816, 5.758), (6.608, 6.023),
            (6.394, 6.296), (6.178, 6.441), (5.589, 6.594), 
            (4.778, 6.807), (3.295, 6.875), (1.596, 6.892),
            (-0.309, 6.912), (-2.422, 6.922), (-3.950, 6.820),
            (-5.069, 6.745), (-5.854, 6.560), (-6.216, 6.356),
            (-6.536, 6.175), (-6.667, 6.039), (-6.848, 5.605),
            (-6.864, 5.567), (-6.879, 5.528), (-6.895, 5.485),
            (-7.129, 4.864), (-7.293, 3.669), (-7.356, 2.219),
            (-7.427, 0.602), (-7.420, -1.299), (-7.324, -2.831),
            (-7.244, -4.098), (-7.066, -5.096), (-6.845, -5.609),
            (-6.653, -6.057), (-6.532, -6.190), (-6.203, -6.364),
            (-6.163, -6.385), (-6.121, -6.406), (-6.075, -6.427),
            (-5.621, -6.634), (-4.673, -6.793), (-3.416, -6.849),
            (-1.736, -6.924), (0.461, -6.918), (2.323, -6.882),
            (3.719, -6.855), (4.901, -6.774), (5.594, -6.597),
            (6.154, -6.447), (6.374, -6.306), (6.579, -6.059),
            (6.592, -6.044), (6.604, -6.028), (6.617, -6.012),
            (6.830, -5.734), (7.059, -5.144), (7.193, -4.194),
            (7.347, -3.098), (7.4, -1.558), (7.4, 0.0),
        ]

    def _create_bezier_sketch19(self) -> Curve:  # 
        points = [
            (-14.0, 2.15),
            (-9.710, 2.142),
            (-8.4, 3.309),
            (-7.0, 3.8),
            (-5.617, 4.302),
            (-4.180, 4.793),
            (0.0, 4.8),
            (4.181, 4.793),
            (5.618, 4.300),
            (7.0, 3.799),
            (8.4, 3.307),
            (9.71, 2.14),
            (14.0, 2.147),
        ]
        bezier = Curve() + [Bezier(points[:4]), 
                            Bezier(points[3:7]),
                            Bezier(points[6:10]),
                            Bezier(points[9:])]
        return bezier
    
    def _iter_feet(self) -> Iterator[Part]:
        pass

    def _create_foot(self) -> Part:
        return Box()
    

class CapBodyCreator:
    _BOTTOM_BEZIER_POINTS = [  # XY plane
            (0.0, 8.25),
            (3.352, 8.219),
            (6.150, 8.317),
            (7.335, 7.211),
            (8.605, 6.203),
            (8.726, 3.431),
            (8.75, 0.0),
        ]
    _TOP_BEZIER_POINTS = [  # XY plane
            (0.0, 6.5),
            (2.368, 6.484),
            (4.452, 6.355),
            (5.527, 5.395),
            (6.649, 4.495),
            (6.991, 2.441),
            (7.0, 0.0),
        ]
    _RIGHT_BEZIER_POINTS = [  # XZ plane
            (8.75, 1.3), 
            (8.705, 2.606), 
            (8.485, 4.304), 
            (7.0, 5.8),
        ]
    _BACK_BEZIER_POINTS = [  # YZ plane
            (8.25, 1.3),
            (8.205, 2.606),
            (7.985, 4.304),
            (6.5, 5.8),
        ]
    
    def __init__(self):
        self._x_max_bottom = 8.75
        self._x_max_top = 7.0
        self._y_max_bottom = 8.25
        self._y_max_top = 6.5
        self._z_min = 1.3
        self._z_max = 5.8
   
    def create(self) -> Part:
        z_min = self._z_min
        z_max = self._z_max
        z_center = (self._z_min + self._z_max) / 2

        bezier_bottom = Pos(Z=z_min) * self._create_bezier_face(self._BOTTOM_BEZIER_POINTS)
        bezier_top = Pos(Z=z_max) * self._create_bezier_face(self._TOP_BEZIER_POINTS)
        bezier_middle = Pos(Z=z_center) * self._create_bezier_face(list(self._iter_z_centered_bezier_points()))

        return loft(Sketch() + [bezier_bottom, bezier_middle, bezier_top])

    def _create_bezier_face(self, points: list[Point]) -> Sketch:
        assert len(points) == 7
        bezier = Bezier(points[:4]) + Bezier(points[3:])
        bezier += mirror(bezier, Plane.XZ)
        bezier += mirror(bezier, Plane.YZ)
        return make_face(bezier)
         
    def _iter_z_centered_bezier_points(self) -> Iterator[Point]:
        scale_x, scale_y = self._create_scale_xy()
        for (x1, y1), (x2, y2) in zip(self._BOTTOM_BEZIER_POINTS, self._TOP_BEZIER_POINTS):
            x = scale_x * (x1 + x2) / 2
            y = scale_y * (y1 + y2) / 2
            yield x, y 

    def _create_scale_xy(self) -> tuple[float, float]:
        x_mean = (self._x_max_bottom + self._x_max_top) / 2
        y_mean = (self._y_max_bottom + self._y_max_top) / 2
        z_center = (self._z_min + self._z_max) / 2

        right_bezier = Bezier(self._RIGHT_BEZIER_POINTS)
        back_bezier = Bezier(self._BACK_BEZIER_POINTS)

        x_curve = self._find_curve_x_at_y(curve=right_bezier, y_target=z_center)
        y_curve = self._find_curve_x_at_y(curve=back_bezier, y_target=z_center)

        scale_x = x_curve / x_mean
        scale_y = y_curve / y_mean

        return scale_x, scale_y

    @staticmethod
    def _find_curve_x_at_y(curve: Curve, y_target: float) -> float:  # curve must monoton increase
        eps = 1e-6
        assert (curve@0).Y <= y_target <= (curve@1).Y

        t1 = 0.0
        t2 = 1.0

        for i in range(100):
            t = (t1 + t2) / 2
            p = curve@t
            if (p.Y - y_target) < eps:
                return p.X
            elif p.Y < y_target:
                t1 = t
            else:
                t2 = t
        else:
            raise Exception('y value not found')


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
