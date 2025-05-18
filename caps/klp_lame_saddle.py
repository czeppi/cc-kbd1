from typing import Iterator
import copy

from build123d import export_stl, loft, make_face, sweep, new_edges, fillet
from build123d import Box, Part, Pos, Rot, Plane, Axis, Sketch, Polyline, Bezier, Curve, Rectangle
from ocp_vscode import show_object

from base import OUTPUT_DPATH
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
        cap_body = CapBodyCreator().create_body() #- CapBodyCreator().create_neg_rim()
    
        sweep_part = self._create_sweep_part()
        sweeped_cap_body = cap_body - sweep_part
        #return sweeped_cap_body

        edges = new_edges(cap_body, sweep_part, combined=sweeped_cap_body)
        cap = fillet(edges, klp_lame_data.saddle.SWEEP_FILLET_RADIUS)

        edges = cap.edges().group_by(Axis.Z)[0]
        cap_without_stems = fillet(edges, radius=klp_lame_data.saddle.RIM_FILLET_RADIUS)

        stems = Part() + list(self._iter_stems())
        cap_with_stems = cap_without_stems + stems
        edges = new_edges(cap_without_stems, stems, combined=cap_with_stems)

        return fillet(edges, radius=klp_lame_data.choc_stem.TOP_FILLET_RADIUS)

    def _create_cap_test(self) -> Part:
        cap_body = CapBodyCreator().create_body() - CapBodyCreator().create_neg_rim()
    
        sweep_part = self._create_sweep_part2()
        #return sweep_part
        sweep_part2 = Rot(Z=90) * copy.copy(sweep_part) - Pos(X=50) * Box(100, 100, 100)
        sweeped_cap_body = cap_body - sweep_part - sweep_part2
        return sweeped_cap_body

        edges = new_edges(cap_body, sweep_part, combined=sweeped_cap_body)
        cap = fillet(edges, klp_lame_data.saddle.SWEEP_FILLET_RADIUS)

        edges = cap.edges().group_by(Axis.Z)[0]
        cap_without_stems = fillet(edges, radius=klp_lame_data.saddle.RIM_FILLET_RADIUS)

        stems = Part() + list(self._iter_stems())
        cap_with_stems = cap_without_stems + stems
        edges = new_edges(cap_without_stems, stems, combined=cap_with_stems)

        return fillet(edges, radius=klp_lame_data.choc_stem.TOP_FILLET_RADIUS)
    
    def _create_sweep_part(self) -> Part:
        face = Plane.front * self._create_face_to_sweep()
        sweep_path = self._create_sweep_path()
        return sweep(face, path=Plane.right * sweep_path)
    
    def _create_sweep_part2(self) -> Part:
        face = Plane.front * Pos(Y=5.8 + 5) * Rectangle(20, 10)
        sweep_path = self._create_sweep_path()
        return sweep(face, path=Plane.right * sweep_path)
    
    def _create_sweep_path(self):
        return Curve() + [Bezier(points) for points in klp_lame_data.saddle.SWEEP_PATH_BEZIER_POINT_LISTS]
    
    def _create_face_to_sweep(self) -> Sketch:
        bezier = Curve() + [Bezier(points) for points in klp_lame_data.saddle.SWEEP_FACE_BEZIER_POINT_LISTS2]
        p1 = bezier@0
        p2 = bezier@1

        polyline = Polyline([(p1.X, p1.Y), (p1.X, p1.Y + 3), (p2.X, p2.Y + 3), (p2.X, p2.Y)])
        return make_face(bezier + polyline)

    def _iter_stems(self) -> Iterator[Part]:
        stem_data = klp_lame_data.choc_stem

        x_len = stem_data.X_MAX - stem_data.X_MIN
        y_len = stem_data.Y_MAX - stem_data.Y_MIN
        z_len = stem_data.Z_MAX - stem_data.Z_MIN + 1.0  # increase high to support top fillet later
        
        stem_box = Pos(Z=z_len / 2 + stem_data.Z_MIN) * Box(x_len, y_len, z_len)
        edges = stem_box.edges().group_by(Axis.Z)[:2]
        stem_box = fillet(edges, radius=klp_lame_data.choc_stem.BOTTOM_FILLET_RADIUS)
    
        x_off = x_len / 2 + stem_data.X_MIN
        yield Pos(X=-x_off) * copy.copy(stem_box)
        yield Pos(X=x_off) * copy.copy(stem_box)


class CapBodyCreator:
    
    def __init__(self):
        self._x_max_bottom = 8.75
        self._x_max_top = 7.0
        self._y_max_bottom = 8.25
        self._y_max_top = 6.5
        self._z_min = 1.3
        self._z_max = 5.8
        self._bottom_arc_rect_params = ArcRectParameters(radius_front_back=74.836, radius_left_right=41.300, radius_corner=3.464)  # parameters from arc_rect_paramter_finder
        self._top_arc_rect_params = ArcRectParameters(radius_front_back=25.481, radius_left_right=17.020, radius_corner=3.551)  # parameters from arc_rect_paramter_finder
   
    def create_body(self) -> Part:
        width_bottom, width_top = 2 * self._x_max_bottom, 2 * self._x_max_top
        deep_bottom, deep_top = 2 * self._y_max_bottom, 2 * self._y_max_top

        z_min, z_max = self._z_min, self._z_max
        z_centered = (z_min + z_max) / 2

        face1 = Pos(Z=z_min) * create_arc_rect(width=width_bottom, height=deep_bottom, params=self._bottom_arc_rect_params)
        face2 = Pos(Z=z_centered) * self._create_center_arc_rect(z=z_centered)
        face3 = Pos(Z=z_max) * create_arc_rect(width=width_top, height=deep_top, params=self._top_arc_rect_params)
        faces = Sketch() + [face1, face2, face3]
        return loft(faces)
    
    def create_neg_rim(self) -> Part:
        thickness = klp_lame_data.saddle.RIM_THICKNESS

        width_bottom = 2 * (self._x_max_bottom - thickness)
        deep_bottom = 2 * (self._y_max_bottom - thickness)
        bottom_arc_params = ArcRectParameters(radius_front_back=self._bottom_arc_rect_params.radius_front_back - thickness, 
                                              radius_left_right=self._bottom_arc_rect_params.radius_left_right - thickness, 
                                              radius_corner=self._bottom_arc_rect_params.radius_corner - thickness)
        face1 = Pos(Z=self._z_min) * create_arc_rect(width=width_bottom, height=deep_bottom, params=bottom_arc_params)

        z_rim_top = klp_lame_data.choc_stem.Z_MAX
        face2 = Pos(Z=z_rim_top) * self._create_center_arc_rect(z=z_rim_top, offset=thickness)

        faces = Sketch() + [face1, face2]
        return loft(faces)

    def _create_center_arc_rect(self, z: float, offset: float = 0.0) -> Sketch:
        right_bezier = Bezier(klp_lame_data.saddle.RIGHT_BEZIER_POINTS)
        back_bezier = Bezier(klp_lame_data.saddle.BACK_BEZIER_POINTS)

        right_side_helper = CapSideHelper(bezier=right_bezier)
        back_side_helper = CapSideHelper(bezier=back_bezier)

        bottom_params = self._bottom_arc_rect_params
        top_params = self._top_arc_rect_params

        rx_bottom, rx_top = bottom_params.radius_left_right, top_params.radius_left_right
        rx = right_side_helper.calc_value_at_z(z=z, value_bottom=rx_bottom, value_top=rx_top) - offset

        ry_bottom, ry_top = bottom_params.radius_front_back, top_params.radius_front_back
        ry = back_side_helper.calc_value_at_z(z=z, value_bottom=ry_bottom, value_top=ry_top) - offset

        rc_bottom, rc_top = bottom_params.radius_corner, top_params.radius_corner
        rc1 = right_side_helper.calc_value_at_z(z=z, value_bottom=rc_bottom, value_top=rc_top)
        rc2 = back_side_helper.calc_value_at_z(z=z, value_bottom=rc_bottom, value_top=rc_top)
        rc = (rc1 + rc2) / 2 - offset

        width_bottom, width_top = 2 * self._x_max_bottom, 2 * self._x_max_top
        width = right_side_helper.calc_value_at_z(z=z, value_bottom=width_bottom, value_top=width_top) - 2 * offset

        deep_bottom, deep_top = 2 * self._y_max_bottom, 2 * self._y_max_top
        deep = back_side_helper.calc_value_at_z(z=z, value_bottom=deep_bottom, value_top=deep_top) - 2 * offset
        
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
