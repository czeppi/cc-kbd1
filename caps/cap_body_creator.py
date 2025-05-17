from typing import Iterator

from build123d import loft, make_face, mirror
from build123d import Part, Pos, Bezier, Plane, Curve, Sketch

from base import Point
from klp_lame_data import KlpLameCapBodyData


class CapBodyCreator:
    
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

        bezier_bottom = Pos(Z=z_min) * self.create_bezier_face(KlpLameCapBodyData.BOTTOM_BEZIER_POINTS)
        bezier_top = Pos(Z=z_max) * self.create_bezier_face(KlpLameCapBodyData.TOP_BEZIER_POINTS)
        bezier_middle = Pos(Z=z_center) * self.create_bezier_face(list(self._iter_z_centered_bezier_points()))

        return loft(Sketch() + [bezier_bottom, bezier_top])

    def create_bezier_face(self, points: list[Point]) -> Sketch:
        assert len(points) == 7

        bezier = Bezier(points[:4]) + Bezier(points[3:])
        bezier += mirror(bezier, Plane.XZ)
        bezier += mirror(bezier, Plane.YZ)

        return make_face(bezier)
         
    def _iter_z_centered_bezier_points(self) -> Iterator[Point]:
        scale_x, scale_y = self._create_scale_xy()
        for (x1, y1), (x2, y2) in zip(KlpLameCapBodyData.BOTTOM_BEZIER_POINTS, KlpLameCapBodyData.TOP_BEZIER_POINTS):
            x = scale_x * (x1 + x2) / 2
            y = scale_y * (y1 + y2) / 2
            yield x, y 

    def _create_scale_xy(self) -> tuple[float, float]:
        x_mean = (self._x_max_bottom + self._x_max_top) / 2
        y_mean = (self._y_max_bottom + self._y_max_top) / 2
        z_center = (self._z_min + self._z_max) / 2

        right_bezier = Bezier(KlpLameCapBodyData.RIGHT_BEZIER_POINTS)
        back_bezier = Bezier(KlpLameCapBodyData.BACK_BEZIER_POINTS)

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
