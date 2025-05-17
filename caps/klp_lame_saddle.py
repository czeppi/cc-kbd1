from typing import Iterator

from build123d import export_stl, loft, make_face, extrude, sweep, new_edges, fillet, mirror
from build123d import Box, Part, Pos, Plane, Axis, Sketch, Polyline, Bezier, Curve
from ocp_vscode import show_object

from base import OUTPUT_DPATH, Point
from arc_rect import create_arc_rect, ArcRectParameters
import klp_lame_data


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
    
    def _create_rim_neg_part(self, cap_body: Part) -> Part:
        pass
        
    def _create_sweep_part(self) -> Part:
        face = Plane.front * self._create_face_to_sweep()
        sweep_path = self._create_sweep_path()
        return sweep(face, path=Plane.right * sweep_path)
    
    def _create_sweep_path(self):
        return Curve() + [Bezier(points) for points in klp_lame_data.saddle.SWEEP_PATH_BEZIER_POINT_LISTS]
    
    def _create_face_to_sweep(self) -> Sketch:
        bezier = Curve() + [Bezier(points) for points in klp_lame_data.saddle.SWEEP_FACE_BEZIER_POINT_LISTS]
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
        self._bottom_arc_rect_params = ArcRectParameters(radius_front_back=74.836, radius_left_right=41.300, radius_corner=3.464)
        self._top_arc_rect_params = ArcRectParameters(radius_front_back=25.481, radius_left_right=17.020, radius_corner=3.551)
   
    def create(self) -> Part:
        width_bottom, width_top = 2 * self._x_max_bottom, 2 * self._x_max_top
        deep_bottom, deep_top = 2 * self._y_max_bottom, 2 * self._y_max_top

        face1 = Pos(Z=1.3) * create_arc_rect(width=width_bottom, height=deep_bottom, params=self._bottom_arc_rect_params)
        face2 = Pos(Z=3.55) * self._create_center_arc_rect()
        face3 = Pos(Z=5.8) * create_arc_rect(width=width_top, height=deep_top, params=self._top_arc_rect_params)
        faces = Sketch() + [face1, face2, face3]
        return loft(faces)

    def _create_center_arc_rect(self) -> Sketch:
        right_bezier = Bezier(klp_lame_data.saddle.RIGHT_BEZIER_POINTS)
        back_bezier = Bezier(klp_lame_data.saddle.BACK_BEZIER_POINTS)

        z_center = (self._z_min + self._z_max) / 2

        right_side_helper = CapSideHelper(bezier=right_bezier)
        back_side_helper = CapSideHelper(bezier=back_bezier)

        bottom_params = self._bottom_arc_rect_params
        top_params = self._top_arc_rect_params

        rx_bottom, rx_top = bottom_params.radius_left_right, top_params.radius_left_right
        rx = right_side_helper.calc_value_at_z(z=z_center, value_bottom=rx_bottom, value_top=rx_top)

        ry_bottom, ry_top = bottom_params.radius_front_back, top_params.radius_front_back
        ry = back_side_helper.calc_value_at_z(z=z_center, value_bottom=ry_bottom, value_top=ry_top)

        rc_bottom, rc_top = bottom_params.radius_corner, top_params.radius_corner
        rc1 = right_side_helper.calc_value_at_z(z=z_center, value_bottom=rc_bottom, value_top=rc_top)
        rc2 = back_side_helper.calc_value_at_z(z=z_center, value_bottom=rc_bottom, value_top=rc_top)
        rc = (rc1 + rc2) / 2

        width_bottom, width_top = 2 * self._x_max_bottom, 2 * self._x_max_top
        width = right_side_helper.calc_value_at_z(z=z_center, value_bottom=width_bottom, value_top=width_top)

        deep_bottom, deep_top = 2 * self._y_max_bottom, 2 * self._y_max_top
        deep = back_side_helper.calc_value_at_z(z=z_center, value_bottom=deep_bottom, value_top=deep_top)
        
        return create_arc_rect(width=width, 
                                height=deep, 
                                params=ArcRectParameters(radius_front_back=ry, 
                                                         radius_left_right=rx, 
                                                         radius_corner=rc)
                                )


class CapSideHelper:
    """ Helper for side bezier curves
    
    The sides of the caps are bezier curves. 
    This class help to calculate values in the middle, if only the top and bottom values is known.

    top    *      bezier@1
             *    <- calculate value in the middle
              * 
    bottom    *   bezier@0
    """

    def __init__(self, bezier: Curve):
        """ bezier: (sketch: XY plane, real world: XZ or YZ plane)
        """
        assert 0.0 <= (bezier@0).Y < (bezier@1).Y  # bezier must go from bottom -> top
        assert (bezier@0).X > (bezier@1).X >= 0.0  # bezier must go from right -> left

        self._bezier = bezier
       
    def calc_value_at_z(self, z: float, value_top: float, value_bottom: float) -> float:
        bezier = self._bezier

        xy_bottom = (bezier@0).X
        xy_top = (bezier@1).X
        xy = self._find_curve_x_at_y(y_target=z)

        k = (xy - xy_top) / (xy_bottom - xy_top)  # top => k=0, bottom => k=1
        return (1.0 - k) * value_top + k * value_bottom

    def _find_curve_x_at_y(self, y_target: float) -> float:  # curve must monoton increase
        eps = 1e-6
        curve = self._bezier
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
