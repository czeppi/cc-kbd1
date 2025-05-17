from typing import Iterator

from build123d import export_stl, loft, make_face, extrude, sweep, new_edges, fillet, mirror
from build123d import Box, Part, Pos, Plane, Axis, Sketch, Polyline, Bezier, Curve
from ocp_vscode import show_object

from base import OUTPUT_DPATH, Point
from arc_rect import create_arc_rect2, ArcRectParameters
from klp_lame_data import KlpLameCapBodyData


def main():
    key_cap = LameSaddleKeyCapCreator().create()
    export_stl(key_cap, OUTPUT_DPATH / 'lame-key-cap.stl')
    show_object(key_cap)


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
    FOOT_BOTTOM_FILLET_RADIUS = 0.25  # todo:check
    FOOT_TOP_FILLET_RADIUS = 0.2  # todo:check

    def create(self) -> Part:
        return self._create_cap()

    def _create_cap(self) -> Part:
        cap_body = CapBodyCreator().create()
        sweep_part = self._create_sweep_part()

        sweeped_cap_body = cap_body - sweep_part

        edges = new_edges(cap_body, sweep_part, combined=sweeped_cap_body)
        part = fillet(edges, 1.26)

        edges = part.edges().group_by(Axis.Z)[0]
        part = fillet(edges, 0.25)
        assert isinstance(part, Part)

        return part
        
    def _create_sweep_part(self) -> Part:
        face = Plane.front * self._create_face_to_sweep()
        sweep_path = self._create_sweep_path()
        return sweep(face, path=Plane.right * sweep_path)
    
    def _create_sweep_path(self):
        points = KlpLameCapBodyData.SWEEP_PATH_BEZIER_POINTS
        bezier = Curve() + [Bezier(points[:4]), 
                            Bezier(points[3:7]),
                            Bezier(points[6:10]),
                            Bezier(points[9:])]
        return bezier
    
    def _create_face_to_sweep(self) -> Sketch:
        points = KlpLameCapBodyData.SWEEP_FACE_BEZIER_POINTS
        bezier = Bezier(points[:3]) + Bezier(points[2:])  # quad bezier curves!

        p1 = bezier@0
        p2 = bezier@1

        polyline = Polyline([(p1.X, p1.Y), (p1.X, p1.Y + 3), (p2.X, p2.Y + 3), (p2.X, p2.Y)])
        return make_face(bezier + polyline)

    def _iter_feet(self) -> Iterator[Part]:
        pass

    def _create_foot(self) -> Part:
        return Box()
    

class CapBodyCreator:
    
    def __init__(self):
        self._x_max_bottom = 8.75
        self._x_max_top = 7.0
        self._y_max_bottom = 8.25
        self._y_max_top = 6.5
        self._z_min = 1.3
        self._z_max = 5.8
        self._bottom_arc_rect_params = ArcRectParameters(radius_horizontal=74.836244, radius_vertical=41.30011255, radius_corner=3.46418388)
        self._top_arc_rect_params = ArcRectParameters(radius_horizontal=25.4812902, radius_vertical=17.01983806, radius_corner=3.55100056)
   
    def create(self) -> Part:
        face1 = Pos(Z=1.3) * create_arc_rect2(width=2 * self._x_max_bottom, height=2*self._y_max_bottom, params=self._bottom_arc_rect_params)
        face2 = Pos(Z=3.55) * self._create_middle_arc_rect()
        face3 = Pos(Z=5.8) * create_arc_rect2(width=2*self._x_max_top, height=2*self._y_max_top, params=self._top_arc_rect_params)
        faces = Sketch() + [face1, face2, face3]
        return loft(faces)
    
    def _create_middle_arc_rect(self) -> Sketch:
        scale_x, scale_y = self._create_scale_xy()
        scale_mean = (scale_x + scale_y) / 2
        x_mean = (self._x_max_bottom + self._x_max_top) / 2
        y_mean = (self._y_max_bottom + self._y_max_top) / 2

        radius_horizontal_mean = (self._bottom_arc_rect_params.radius_horizontal + self._top_arc_rect_params.radius_horizontal) / 2
        radius_vertical_mean = (self._bottom_arc_rect_params.radius_vertical + self._top_arc_rect_params.radius_vertical) / 2
        radius_corner_mean = (self._bottom_arc_rect_params.radius_corner + self._top_arc_rect_params.radius_corner) / 2

        arc_rect_params = ArcRectParameters(
            radius_horizontal=radius_horizontal_mean * scale_y,
            radius_vertical=radius_vertical_mean * scale_x,
            radius_corner=radius_corner_mean * scale_mean
        )

        return create_arc_rect2(width=2 * x_mean * scale_x, 
                                height=2 * y_mean * scale_y, 
                                params=arc_rect_params)

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


if __name__ == '__main__':
    main()
