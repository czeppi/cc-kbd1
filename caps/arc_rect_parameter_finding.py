""" Find the best parameters for the arc rectangulars

    Problem: the original KLP caps has bezier curves as cap body sketch. OCP cannot fillet this bezier curve edges.
    Solution: use an arc-rectangular (or biarc-rect) instead. An arc rectangular has 8 arcs: big arcs at the sides and small arcs in the corners.

    This program tries to find the best parameters for the arc rectangular, to make they as simular as possible with the bezier edges.
"""

from typing import Iterator
from enum import Enum
import math

import scipy
import shapely
import numpy as np

from build123d import fillet, mirror, make_face
from build123d import Pos, Bezier, Curve, Axis, Sketch, GeomType, Rectangle, Rot, Edge, Plane
from ocp_vscode import show_object
import scipy.optimize

from base import Point
import klp_lame_data
from arc_rect import ArcRectParameters, create_arc_rect



class SearchMethod(Enum):
    COMPARE_POINTS_OF_BEZIER_CURVES = 1  # take some x-values and compare the y-values of the arc rect with the orig. bezier curve (=> not good)
    AREA_DIFF_OF_POLYGONS = 2  # convert arc rect and bezier curves in polygons. Compare the area (=> OK)
    MAX_DIST_OF_POLYGONS = 3  # convert arc rect and bezier curves in polygons. Compare the max. distance between the points and edges of the other polygon (=> OK, but has convergence problems)
    SUM_OF_SQUARES_OF_DIST_OF_POLYGONS = 4  # convert arc rect and bezier curves in polygons. Calc the square of the distance between the points and edges of the other polygon (=> good) 



def main():
    find_arc_rect_parameters(SearchMethod.SUM_OF_SQUARES_OF_DIST_OF_POLYGONS)
    #show_top_results()


def find_arc_rect_parameters(search_method: SearchMethod) -> ArcRectParameters:
    # points = klp_lame_data.saddle.BOTTOM_BEZIER_POINTS
    points = klp_lame_data.saddle.TOP_BEZIER_POINTS
    bezier = Bezier(points[:4]) + Bezier(points[3:])

    param_finder = ArcRectParametersFinder(bezier_curve=bezier, search_method=search_method)
    best_params = param_finder.find_parameters()
    print(f'best_params = {best_params}')
    return best_params


def show_bottom_results():
    bezier_bottom = create_bezier_face(klp_lame_data.saddle.BOTTOM_BEZIER_POINTS)
    show_object(bezier_bottom, name='bezier_bottom')

    rh, rv, rc = 70, 38, 3.2
    rect = create_arc_rect(width=17.5, height=16.5, radius_front_back=rh, radius_left_right=rv, radius_corner=rc)
    show_object(rect, name="arc-rect-manu")

    #rh, rv, rc = 127.77364364, 49.05397903, 3.95642961  # curve dist

    rh, rv, rc = 82.17270862, 42.35694325, 3.49574271  # area diff of poly
    rect = create_arc_rect(width=17.5, height=16.5, radius_front_back=rh, radius_left_right=rv, radius_corner=rc)
    show_object(rect, name="arc-rect-area-poly")

    rh, rv, rc = 70.02322301, 39.20389013, 3.39182747  # max dist of poly
    rect = create_arc_rect(width=17.5, height=16.5, radius_front_back=rh, radius_left_right=rv, radius_corner=rc)
    show_object(rect, name="arc-rect-max-dist-poly")

    rh, rv, rc = 74.836244, 41.30011255, 3.46418388  # sum of poly square dist
    rect = create_arc_rect(width=17.5, height=16.5, radius_front_back=rh, radius_left_right=rv, radius_corner=rc)
    show_object(rect, name="arc-rect-sum-of-square-poly")


def show_top_results():
    bezier_bottom = create_bezier_face(klp_lame_data.saddle.TOP_BEZIER_POINTS)
    show_object(bezier_bottom, name='bezier_bottom')

    rh, rv, rc = 25.4812902, 17.01983806, 3.55100056
    rect = create_arc_rect(width=14.0, height=13.0, radius_front_back=rh, radius_left_right=rv, radius_corner=rc)
    show_object(rect, name="arc-rect-sum-of-square-poly")
     

class ArcRectParametersFinder:
    _BIG_RADIUS_MIN = 15.0
    _BIG_RADIUS_MAX = 200.0
    _SMALL_RADIUS_MIN = 0.1
    _SMALL_RADIUS_MAX = 5.0

    def __init__(self, bezier_curve: Curve, search_method: SearchMethod):  # bezier_curve should only defined in the x+/y+ quarter
        self._bezier_curve = bezier_curve
        self._search_method = search_method

    def find_parameters(self) -> ArcRectParameters:
        big_r_min = self._BIG_RADIUS_MIN
        big_r_max = self._BIG_RADIUS_MAX
        small_r_min = self._SMALL_RADIUS_MIN
        small_r_max = self._SMALL_RADIUS_MAX

        #start_values = [70, 38, 3.2]  # radius_front_back, radius_left_right, radius_corner
        start_values = [60, 40, 2.5]  # radius_front_back, radius_left_right, radius_corner

        result = scipy.optimize.minimize(
            fun=self._calc_error_with_polygon_distances,
            x0=start_values, 
            bounds=[(big_r_min, big_r_max), (big_r_min, big_r_max), (small_r_min, small_r_max)])
        
        if not result.success:
            raise Exception('no best parameters found')
        
        print(f'success: {result.success}, best_parameters: {result.x}')
        
        rh, rv, rc = result.x
        return ArcRectParameters(radius_front_back=rh,
                                 radius_left_right=rv,
                                 radius_corner=rc)
    
    def _calc_error_with_curve_diff(self, params: tuple[float, float, float]) -> float:
        rh, rv, rc = params
        arc_rect_params = ArcRectParameters(radius_front_back=rh, radius_left_right=rv, radius_corner=rc)

        diff_calc = CurveDiffCalculator(bezier_curve=self._bezier_curve, 
                                        arc_rect_params=arc_rect_params)
        return diff_calc.calc_diff_value()
    
    def _calc_error_with_polygon_distances(self, params: tuple[float, float, float]) -> float:
        rh, rv, rc = params
        arc_rect_params = ArcRectParameters(radius_front_back=rh, radius_left_right=rv, radius_corner=rc)

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
                                   radius_front_back=arc_rect_params.radius_front_back, 
                                   radius_left_right=arc_rect_params.radius_left_right, 
                                   radius_corner=arc_rect_params.radius_corner)
        arc_rect -= Pos(X=-50) * Rectangle(100, 100)
        arc_rect -= Pos(Y=-50) * Rectangle(100, 100)
        rect_edges: list[Edge] = arc_rect.edges().filter_by(GeomType.CIRCLE)
        assert len(rect_edges) == 3

        yield 0.0, height / 2

        for i in range(1, num_points - 1):
            angle = 90 * i / (num_points - 1)

            for edge in rect_edges:
                rotated_edge = Rot(Z=angle) * edge
                assert isinstance(rotated_edge, Edge)

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

        match self._search_method:
            case SearchMethod.AREA_DIFF_OF_POLYGONS:
                return self._calc_area_diff_of_polygons(poly1, poly2)
            case SearchMethod.MAX_DIST_OF_POLYGONS:
                return self._calc_max_distance_of_polygons(poly1, poly2)
            case SearchMethod.SUM_OF_SQUARES_OF_DIST_OF_POLYGONS:
                return self._calc_square_distance_of_polygons(poly1, poly2)
            
        raise Exception('invalid search method')

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
        rh = self._arc_rect_params.radius_front_back
        rv = self._arc_rect_params.radius_left_right
        rc = self._arc_rect_params.radius_corner
        bezier = self._bezier_curve

        p1 = bezier@0
        p2 = bezier@1

        width = 2 * max(p1.X, p2.X)
        height = 2 * max(p1.Y, p2.Y)

        n = 16
        bezier_points = [bezier@(i / n) for i in range(n + 1)]

        arc_rect = create_arc_rect(width=width, height=height, radius_front_back=rh, radius_left_right=rv, radius_corner=rc)
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
                moved_edge = Pos(X=-x) * edge
                assert isinstance(moved_edge, Edge)
                intersection_points = moved_edge.find_intersection_points(Axis.Y)
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


def create_bezier_face(points: list[Point]) -> Sketch:
    assert len(points) == 7

    bezier = Bezier(points[:4]) + Bezier(points[3:])
    bezier += mirror(bezier, Plane.XZ)
    bezier += mirror(bezier, Plane.YZ)

    return make_face(bezier)


if __name__ == '__main__':
    main()
