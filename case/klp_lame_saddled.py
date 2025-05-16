from typing import Iterator
from dataclasses import dataclass
import copy
import math

import scipy
import shapely
import numpy as np

from build123d import offset, export_stl, loft, make_face, extrude, mirror, sweep, new_edges, fillet, chamfer
from build123d import Box, Part, Pos, Line, Bezier, Plane, Curve, Axis, Sketch, GeomType, Rectangle, Rot, Polyline, RectangleRounded, Spline, JernArc, Circle, Edge
from ocp_vscode import show_object
import scipy.optimize

from base import TOLERANCE, OUTPUT_DPATH
from trackball_holder import TrackballHolderCreator
from thumb_holder import ThumbMiddlePartCreator
from thumb_base import THICKNESS, SLOT_LEN


type Point = tuple[float, float]


def main():
    _find_arc_rect_parameters()
    #_find_arc_rect_parameters_manual()


def show_cap():
    key_cap = LameSaddleKeyCapCreator().create()
    export_stl(key_cap, OUTPUT_DPATH / 'lame-key-cap.stl')
    show_object(key_cap)


def _find_arc_rect_parameters():
    points = CapBodyCreator._BOTTOM_BEZIER_POINTS
    bezier = Bezier(points[:4]) + Bezier(points[3:])

    param_finder = ArcRectParametersFinder(bezier_curve=bezier)
    best_params = param_finder.find_parameters()
    print(f'best_params = {best_params}')

def _find_arc_rect_parameters_manual():
    body_createor = CapBodyCreator()
    bezier_bottom = body_createor._create_bezier_face(body_createor._BOTTOM_BEZIER_POINTS)
    show_object(bezier_bottom, name='bezier_bottom')

    rh, rv, rc = 70, 38, 3.2
    rect = create_arc_rect(width=17.5, height=16.5, radius_horziontal=rh, radius_vertical=rv, radius_corner=rc)
    show_object(rect, name="arc-rect-manu")

    #rh, rv, rc = 127.77364364, 49.05397903, 3.95642961  # curve dist

    rh, rv, rc = 82.17270862, 42.35694325, 3.49574271  # area diff of poly
    rect = create_arc_rect(width=17.5, height=16.5, radius_horziontal=rh, radius_vertical=rv, radius_corner=rc)
    show_object(rect, name="arc-rect-area-poly")

    rh, rv, rc = 70.02322301, 39.20389013, 3.39182747  # max dist of poly
    rect = create_arc_rect(width=17.5, height=16.5, radius_horziontal=rh, radius_vertical=rv, radius_corner=rc)
    show_object(rect, name="arc-rect-max-dist-poly")

    rh, rv, rc = 74.836244, 41.30011255, 3.46418388  # sum of poly square dist
    rect = create_arc_rect(width=17.5, height=16.5, radius_horziontal=rh, radius_vertical=rv, radius_corner=rc)
    show_object(rect, name="arc-rect-sum-of-square-poly")


def main_test():
    face1 = Pos(Z=0) * create_birect(4, r=5)
    face2 = Pos(Z=1) * create_birect(3.5, r=4.8)
    face3 = Pos(Z=2) * create_birect(3, r=4)
    part = loft(Sketch() + [face1, face2, face3])

    part = fillet(part.edges().group_by(Axis.Z)[0], 0.5)
    part = fillet(part.edges().group_by(Axis.Z)[-1], 0.5)


    show_object(part)
    return

    x1 = 8.0
    x2 = 4.0
    r1 = 20.0
    r2 = 1.0
    key_cap = JernArc(start=(0, 2), tangent=(1, 0), radius=5, arc_size=-30)


def create_birect(a: float, r: float):
    a2 = a / 2
    rect = Pos(Y=a2 - r) * Circle(r) & Pos(Y=r - a2) * Circle(r) & Pos(X=a2 - r) * Circle(r) & Pos(X=r - a2) * Circle(r)
    return fillet(rect.vertices(), 1)


def create_arc_rect(width: float, height: float, radius_horziontal: float, radius_vertical: float, radius_corner: float) -> Sketch:
    w2 = width / 2
    h2 = height / 2
    rh = radius_horziontal
    rv = radius_vertical

    rect = Pos(Y=h2 - rh) * Circle(rh) & Pos(Y=rh - h2) * Circle(rh) & Pos(X=w2 - rv) * Circle(rv) & Pos(X=rv - w2) * Circle(rv)
    return fillet(rect.vertices(), radius_corner)

@dataclass
class ArcRectParameters:
    radius_horizontal: float
    radius_vertical: float
    radius_corner: float


class ArcRectParametersFinder:
    _BIG_RADIUS_MIN = 15.0
    _BIG_RADIUS_MAX = 200.0
    _SMALL_RADIUS_MIN = 0.1
    _SMALL_RADIUS_MAX = 5.0

    def __init__(self, bezier_curve: Curve):  # bezier_curve should only defined in the x+/y+ quarter
        self._bezier_curve = bezier_curve

    def find_parameters(self) -> ArcRectParameters:
        big_r_min = self._BIG_RADIUS_MIN
        big_r_max = self._BIG_RADIUS_MAX
        small_r_min = self._SMALL_RADIUS_MIN
        small_r_max = self._SMALL_RADIUS_MAX

        #start_values = [70, 38, 3.2]  # radius_horizontal, radius_vertical, radius_corner
        start_values = [60, 40, 2.5]  # radius_horizontal, radius_vertical, radius_corner

        result = scipy.optimize.minimize(
            fun=self._calc_error_with_polygon_distances,
            x0=start_values, 
            #bounds=[(big_r_min, big_r_min, small_r_min), (big_r_max, big_r_max, small_r_max)])
            bounds=[(big_r_min, big_r_max), (big_r_min, big_r_max), (small_r_min, small_r_max)])
        
        if not result.success:
            raise Exception('no best parameters found')
        
        print(f'{result.success}, {result.x}')
        
        rh, rv, rc = result.x
        return ArcRectParameters(radius_horizontal=rh,
                                 radius_vertical=rv,
                                 radius_corner=rc)
    
    def _calc_error_with_curve_diff(self, params: tuple[float, float, float]) -> float:
        rh, rv, rc = params
        arc_rect_params = ArcRectParameters(radius_horizontal=rh, radius_vertical=rv, radius_corner=rc)

        diff_calc = CurveDiffCalculator(bezier_curve=self._bezier_curve, 
                                        arc_rect_params=arc_rect_params)
        return diff_calc.calc_diff_value()
    
    def _calc_error_with_polygon_distances(self, params: tuple[float, float, float]) -> float:
        rh, rv, rc = params
        arc_rect_params = ArcRectParameters(radius_horizontal=rh, radius_vertical=rv, radius_corner=rc)

        n = 17
        bezier = self._bezier_curve
        bezier_pts = [bezier@(i / (n - 1)) for i in range(n)]
        bezier_points = [(p.X, p.Y) for p in bezier_pts]
        arc_rect_points = list(self._iter_arc_rect_points(arc_rect_params=arc_rect_params, num_points=n))
        assert len(arc_rect_points) == n

        err = self._calc_error_of_polygons(bezier_points, arc_rect_points)
        print(f'  err: {err}, params: {rh, rv, rc}')
        return err

    def _iter_arc_rect_points(self, arc_rect_params: ArcRectParameters, num_points: int) -> Iterator[Point]:
        bezier = self._bezier_curve
        p1 = bezier@0
        p2 = bezier@1
        width = 2 * max(p1.X, p2.X)
        height = 2 * max(p1.Y, p2.Y)

        arc_rect = create_arc_rect(width=width, height=height,
                                   radius_horziontal=arc_rect_params.radius_horizontal, 
                                   radius_vertical=arc_rect_params.radius_vertical, 
                                   radius_corner=arc_rect_params.radius_corner)
        arc_rect -= Pos(X=-50) * Rectangle(100, 100)
        arc_rect -= Pos(Y=-50) * Rectangle(100, 100)
        rect_edges = arc_rect.edges().filter_by(GeomType.CIRCLE)
        assert len(rect_edges) == 3

        yield 0.0, height / 2

        for i in range(1, num_points - 1):
            angle = 90 * i / (num_points - 1)

            for edge in rect_edges:
                rotated_edge = Rot(Z=angle) * edge

                intersection_points = rotated_edge.find_intersection_points(Axis.Y)
                if len(intersection_points) == 1:
                    r = intersection_points[0].Y
                    phi = math.radians(angle)
                    x = r * math.sin(phi)
                    y = r * math.cos(phi)
                    yield x, y
                    break
            else:
                raise Exception('no intersecion point found')
            
        yield width / 2, 0.0

    def _calc_error_of_polygons(self, bezier_points: list[Point], arc_rect_points: list[Point]) -> float:
        origin = 0.0, 0.0
        poly1 = shapely.Polygon(np.array([origin] + bezier_points))
        poly2 = shapely.Polygon(np.array([origin] + arc_rect_points))

        #eturn self._calc_max_distance_of_polygons(poly1, poly2)
        #return self._calc_area_diff_of_polygons(poly1, poly2)
        return self._calc_square_distance_of_polygons(poly1, poly2)
    
    def _calc_max_distance_of_polygons(self, poly1: shapely.Polygon, poly2: shapely.Polygon) -> float:  # converged slowly
        line1 = shapely.LineString(poly1.exterior.coords)
        line2 = shapely.LineString(poly2.exterior.coords)

        max1 = max(shapely.Point(pt).distance(line2)
                   for pt in poly1.exterior.coords)
        
        max2 = max(shapely.Point(pt).distance(line1)
                   for pt in poly2.exterior.coords)

        return max(max1, max2)
    
    def _calc_square_distance_of_polygons(self, poly1: shapely.Polygon, poly2: shapely.Polygon) -> float:
        line1 = shapely.LineString(poly1.exterior.coords)
        line2 = shapely.LineString(poly2.exterior.coords)

        sum1 = sum(shapely.Point(pt).distance(line2)**2
                   for pt in poly1.exterior.coords)
        
        sum2 = sum(shapely.Point(pt).distance(line1)**2
                   for pt in poly2.exterior.coords)

        return sum1 + sum2

    def _calc_area_diff_of_polygons(self, poly1: shapely.Polygon, poly2: shapely.Polygon) -> float:
        intersection_area = poly1.intersection(poly2).area
        union_area = poly1.union(poly2).area
        return union_area - intersection_area


class CurveDiffCalculator:

    def __init__(self, bezier_curve: Curve, arc_rect_params: ArcRectParameters):
        self._bezier_curve = bezier_curve
        self._arc_rect_params = arc_rect_params

    def calc_diff_value(self) -> float:
        rh = self._arc_rect_params.radius_horizontal
        rv = self._arc_rect_params.radius_vertical
        rc = self._arc_rect_params.radius_corner
        bezier = self._bezier_curve

        p1 = bezier@0
        p2 = bezier@1

        width = 2 * max(p1.X, p2.X)
        height = 2 * max(p1.Y, p2.Y)

        n = 16
        bezier_points = [bezier@(i / n) for i in range(n + 1)]

        arc_rect = create_arc_rect(width=width, height=height, radius_horziontal=rh, radius_vertical=rv, radius_corner=rc)
        arc_rect -= Pos(X=-50) * Rectangle(100, 100)
        arc_rect -= Pos(Y=-50) * Rectangle(100, 100)
        rect_edges = arc_rect.edges().filter_by(GeomType.CIRCLE)
        assert len(rect_edges) == 3

        return sum(self._calc_error_at_p(p, rect_edges=rect_edges)
                   for p in bezier_points)
    
    def _calc_error_at_p(self, bezier_point, rect_edges: list[Edge]) -> float:
        eps = 1e-4
        x, y_bezier = bezier_point.X, bezier_point.Y
        #print(f'bezier: {x}, {y_bezier}')

        y_rect = None
        for edge in rect_edges:
            p1 = edge.start_point()
            p2 = edge.end_point()
            x_min = min(p1.X, p2.X) - eps
            x_max = max(p1.X, p2.X) + eps

            if x_min <= x <= x_max:
                intersection_points = (Pos(X=-x) * edge).find_intersection_points(Axis.Y)
                assert len(intersection_points) == 1
                y_rect = intersection_points[0].Y
                break
        else:
            raise Exception('no edge found')

        #y_rect = self._calc_monoton_curve_value(x, curve=curve)

        return (y_rect - y_bezier)**2

    def _calc_monoton_curve_value(self, x_target: float, curve: Curve) -> float:
        eps = 1e-4
        t1, t2 = 0.0, 1.0
        for i in range(100):
            t = (t1 + t2) / 2
            p = curve@t
            if abs(p.X - x_target) < eps:
                return p.Y
            elif p.X < x_target:
                t1 = t
            else:
                t2 = t
        else:
            raise Exception(f'value not found')








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
        #return sweeped_cap_body

        edges = new_edges(cap_body, sweep_part, combined=sweeped_cap_body)
        part = fillet(edges, 1.26)

        edges = part.edges().group_by(Axis.Z)[0]
        part = fillet(edges, 0.25)

        #r = sweeped_cap_body.max_fillet(edges, tolerance=0.01)
        #print(f'r={r}')
        return part
        
    def _create_cap_body(self) -> Part:
        #return CapBodyCreator().create()
    
        radius_corner = 3
        radius_side = 30
        face1 = Pos(Z=1.3) * create_arc_rect(width=17.5, height=16.5, radius_horziontal=radius_side, radius_vertical=radius_side, radius_corner=radius_corner)
        face2 = Pos(Z=3.55) * create_arc_rect(width=16.5, height=15.5, radius_horziontal=radius_side, radius_vertical=radius_side, radius_corner=radius_corner)
        face3 = Pos(Z=5.8) * create_arc_rect(width=14, height=13, radius_horziontal=radius_side, radius_vertical=radius_side, radius_corner=radius_corner)
        part = loft(Sketch() + [face1, face2, face3])

        #part = fillet(part.edges().group_by(Axis.Z)[0], 0.5)
        #part = fillet(part.edges().group_by(Axis.Z)[-1], 0.5)
        return part


        rect_bottom = Pos(Z=1.3) * RectangleRounded(16.5, 15.5, radius=2)  # Rectangle(17.5, 16.5)
        rect_middle = Pos(Z=3.55) * RectangleRounded(15.5, 14.5, radius=2)
        rect_top = Pos(Z=5.8) * RectangleRounded(13, 12, radius=2)  # Rectangle(14, 13)
        #return loft(Sketch() + [rect_bottom, rect_middle, rect_top])

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
    

class FourArcClosedCurve:

    def __init__(self, width: float, height: float, r: float, angle: float): 
        assert width == height  # simplified in the moment
        assert 2 * r > width
        assert 0 < angle < 90

        self._width = width
        self._height = height
        self._r = r
        self._angle = angle

    def create(self) -> Curve:
        return JernArc(start=(0, self._height / 2), tangent=(0, 1), radius=self._r, arc_size=self._angle)




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

        return loft(Sketch() + [bezier_bottom, bezier_top])

    def _create_bezier_face(self, points: list[Point]) -> Sketch:
        assert len(points) == 7

        bezier = Bezier(points[:4]) + Bezier(points[3:])
        #bezier_points = [bezier@t for t in [0.0, 0.5, 1.0]]
        #bezier = Spline(bezier_points)
        #bezier += mirror(bezier, Plane.XZ)
        #bezier += mirror(bezier, Plane.YZ)

        #n = 8
        #spline = Spline([bezier@(i / n) for i in range(n + 1)], tangents=[(1, 0), (1, 0)])

        n = 2
        #spline = Spline([bezier@(i / n) for i in range(n + 1)], tangents=[(1, 0), (1, 0)])
        spline = Spline([bezier@0, bezier@0.5, bezier@1], tangents=[bezier%0, bezier%1])
        spline += mirror(spline, Plane.XZ)
        spline += mirror(spline, Plane.YZ)

        return make_face(spline)
         
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


if __name__ == '__main__':
    main()
