from typing import Iterator
import copy
from enum import Enum

from build123d import export_stl, loft, make_face, sweep, new_edges, fillet
from build123d import Box, Part, Pos, Rot, Plane, Axis, Sketch, Polyline, Bezier, Curve, Cylinder, Solid, BoundBox
from ocp_vscode import show_object

from base import OUTPUT_DPATH
from arc_rect import create_arc_rect, create_arc_rect_variant, ArcRectParameters
import klp_lame_data


class CapKind(Enum):
    ORIG = 1  # original key cap
    INDEX_FINGER_NORMAL_SIZED = 2  # new caps for index finger (outside decreasing)
    INDEX_FINGER_BIG = 3  # new outside caps for index finger (double deep, and rotated stem)


def main():
    #part = create_orig_cap()
    #part = create_index_normal_cap()
    #part = create_index_big_cap()

    part = create_combined_caps()

    show_object(part)


def create_orig_cap() -> None:
    key_cap = LameSaddleKeyCapCreator(cap_kind=CapKind.ORIG, extra_height=0.6).create()
    export_stl(key_cap, OUTPUT_DPATH / 'lame-key-cap-orig.stl')
    return key_cap


def create_index_normal_cap() -> None:
    key_cap = LameSaddleKeyCapCreator(cap_kind=CapKind.INDEX_FINGER_NORMAL_SIZED, extra_height=0.6).create()
    export_stl(key_cap, OUTPUT_DPATH / 'lame-key-cap-index-normal.stl')
    return key_cap


def create_index_big_cap() -> None:
    key_cap = LameSaddleKeyCapCreator(cap_kind=CapKind.INDEX_FINGER_BIG, extra_height=0.6).create()
    export_stl(key_cap, OUTPUT_DPATH / 'lame-key-cap-index-big.stl')
    return key_cap


def create_combined_caps() -> None:
    return LameKeyCapGridCreator(cap_kinds_per_column=[CapKind.ORIG, CapKind.INDEX_FINGER_BIG, CapKind.INDEX_FINGER_NORMAL_SIZED], num_columns=2).create()



class LameKeyCapGridCreator:

    
    def __init__(self, cap_kinds_per_column: list[CapKind], num_columns: int):
        self._cap_kinds_per_column = cap_kinds_per_column
        self._num_columns = num_columns
        self._cap_map: dict[CapKind, Solid] = {}
        self._cap_box_map: dict[CapKind, BoundBox] = {}
        self._column_width: float = -1.0

    def create(self) -> Part:
        cap_kindes = set(self._cap_kinds_per_column)
        self._cap_map = {cap_kind: LameSaddleKeyCapCreator(cap_kind=cap_kind, extra_height=0.6).create()
                         for cap_kind in cap_kindes}
        self._cap_box_map = {cap_kind: cap.bounding_box() 
                             for cap_kind, cap in self._cap_map.items()}
        self._column_width = max(box.max.X - box.min.X for box in self._cap_box_map.values())

        return Part() + list(self._iter_column_solids())
    
    def _iter_column_solids(self) -> Iterator[Solid]:
        grid_data = klp_lame_data.grid
        dist = grid_data.CAP_DISTANCE
        cap_kinds = self._cap_kinds_per_column
        column_dist = self._column_width + dist
        conn_cyl = self._create_column_cylinder()
         
        yield Part() + list(self._iter_row_solids(0))
        #yield copy.copy(self._cap_map[cap_kinds[0]])

        prev_box = self._cap_box_map[cap_kinds[0]]
        prev_y = 0.0

        num_rows = len(self._cap_kinds_per_column)
        for i in range(1, num_rows):
            cur_cap_kind = self._cap_kinds_per_column[i]
            for j in range(self._num_columns):
                yield Pos(X=j * column_dist, Y=prev_y + prev_box.max.Y + dist/2) * copy.copy(conn_cyl)

            cur_box = self._cap_box_map[cur_cap_kind]
            cur_y = prev_y + prev_box.max.Y + dist + abs(cur_box.min.Y)
            row_solid = Part() + list(self._iter_row_solids(i))
            yield Pos(Y=cur_y) * copy.copy(row_solid)

            prev_box = cur_box
            prev_y = cur_y
    
    def _iter_row_solids(self, i: int) -> Iterator[Solid]:
        cap_kind = self._cap_kinds_per_column[i]
        cap_box = self._cap_box_map[cap_kind]
        cap_width = cap_box.max.X - cap_box.min.X
        cap = self._cap_map[cap_kind]

        grid_data = klp_lame_data.grid
        dist = grid_data.CAP_DISTANCE
        column_dist = self._column_width + dist

        conn_cyl_len = column_dist - cap_width + 2 * klp_lame_data.saddle.RIM_THICKNESS
        if cap_kind == CapKind.INDEX_FINGER_NORMAL_SIZED:
            conn_cyl_len += 1.3  # cause of the concave form

        conn_cyl = self._create_row_cylinder(height=conn_cyl_len)

        yield copy.copy(cap)

        for j in range(1, self._num_columns):
            x = (j - 0.5) * column_dist
            yield Pos(X=x) * copy.copy(conn_cyl)

            x = j * column_dist
            yield Pos(X=x) * copy.copy(cap)

    def _create_row_cylinder(self, height: float) -> Solid:
        grid_data = klp_lame_data.grid
        conn_cyl_radius = grid_data.CONN_CYLINDER_RADIUS
        conn_cyl_overlap = grid_data.CONN_CYLINDER_OVERLAP_WITH_CAP

        return Pos(Z=-conn_cyl_radius + 1.3 + conn_cyl_overlap) * Rot(Y=90) * Cylinder(radius=conn_cyl_radius, height=height)

    def _create_column_cylinder(self) -> Solid:
        grid_data = klp_lame_data.grid
        conn_cyl_radius = grid_data.CONN_CYLINDER_RADIUS
        conn_cyl_overlap = grid_data.CONN_CYLINDER_OVERLAP_WITH_CAP
        conn_cyl_height = grid_data.CAP_DISTANCE + 2 * klp_lame_data.saddle.RIM_THICKNESS

        return Pos(Z=-conn_cyl_radius + 1.3 + conn_cyl_overlap) * Rot(X=90) * Cylinder(radius=conn_cyl_radius, height=conn_cyl_height)
    

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

    def __init__(self, cap_kind: CapKind = CapKind.ORIG, extra_height: float = 0.0):
        self._cap_kind = cap_kind
        self._extra_height = extra_height  # to avoid holes in index finger caps (there will be holes with extra_height <= 0.2)
        self._y_factor = 2.0 if self._cap_kind == CapKind.INDEX_FINGER_BIG else 1.0

    def create(self) -> Part:
        return self._create_cap()
    
    def _create_cap(self) -> Part:
        body_creator = CapBodyCreator(extra_height=self._extra_height, y_factor=self._y_factor, cap_kind=self._cap_kind)
        cap_body_without_rim = body_creator.create_body()
        neg_rim = body_creator.create_neg_rim()
        cap_body_with_rim = cap_body_without_rim - neg_rim
        edges = new_edges(cap_body_without_rim, combined=cap_body_with_rim)
        cap = fillet(edges, radius=0.2)  # at a fillet at the inside of the rim, cause the thickness is very thin at back/left with cap_kind=INDEX_FINGER_NORMAL_SIZED
  
        sweep_part = self._create_sweep_part()
        sweeped_cap_body = cap - sweep_part #- Pos(X=-10, Y=-10) * Box(20, 20, 20)

        edges = new_edges(cap, sweep_part, combined=sweeped_cap_body)
        cap = fillet(edges, klp_lame_data.saddle.SWEEP_FILLET_RADIUS)

        edges = cap.edges().group_by(Axis.Z)[0]
        cap_without_stems = fillet(edges, radius=klp_lame_data.saddle.RIM_FILLET_RADIUS)

        stems = Part() + list(self._iter_stems())
        cap_with_stems = cap_without_stems + stems
        edges = new_edges(cap_without_stems, stems, combined=cap_with_stems)

        cap = fillet(edges, radius=klp_lame_data.choc_stem.TOP_FILLET_RADIUS)
        # cap -= Pos(X=-10, Y=-5) * Box(20, 20, 20)
        return cap

    def _create_sweep_part(self) -> Part:
        face = Plane.front * self._create_face_to_sweep()
        sweep_path = self._create_sweep_path()
        return sweep(face, path=Plane.right * sweep_path)
    
    def _create_sweep_path(self):
        return Curve() + [Bezier([(y * self._y_factor, z + self._extra_height) for y, z in points]) for 
                          points in klp_lame_data.saddle.SWEEP_PATH_BEZIER_POINT_LISTS]
    
    def _create_face_to_sweep(self) -> Sketch:
        point_lists = klp_lame_data.saddle.SWEEP_FACE_BEZIER_POINT_LISTS if self._cap_kind == CapKind.ORIG \
                      else klp_lame_data.saddle.SWEEP_FACE_BEZIER_POINT_LISTS2

        bezier = Curve() + [Bezier([(x, z + self._extra_height) for x, z in points]) 
                            for points in point_lists]
        p1 = bezier@0
        p2 = bezier@1

        polyline = Polyline([(p1.X, p1.Y), (p1.X, p1.Y + 3), (p2.X, p2.Y + 3), (p2.X, p2.Y)])
        return make_face(bezier + polyline)

    def _iter_stems(self) -> Iterator[Part]:
        stem_data = klp_lame_data.choc_stem

        x_len = stem_data.X_MAX - stem_data.X_MIN
        y_len = stem_data.Y_MAX - stem_data.Y_MIN
        z_len = stem_data.Z_MAX - stem_data.Z_MIN
        
        stem_box = Pos(Z=z_len / 2 + stem_data.Z_MIN) * Box(x_len, y_len, z_len)
        edges = stem_box.edges().group_by(Axis.Z)[:2]
        stem_box = fillet(edges, radius=klp_lame_data.choc_stem.BOTTOM_FILLET_RADIUS)
    
        rot = Rot(Z=90) if self._cap_kind == CapKind.INDEX_FINGER_BIG else Rot(Z=0)
        x_off = x_len / 2 + stem_data.X_MIN
        yield rot * Pos(X=-x_off) * copy.copy(stem_box)
        yield rot * Pos(X=x_off) * copy.copy(stem_box)


class CapBodyCreator:
    
    def __init__(self, y_factor: float = 1.0, extra_height: float = 0.0, cap_kind: CapKind = CapKind.ORIG):
        self._y_factor = y_factor
        self._extra_height = extra_height  # necessary for new cap variant to avoid holes
        self._cap_kind = cap_kind
        self._x_max_bottom = 8.75
        self._x_max_top = 7.0
        self._y_max_bottom = 8.25 * y_factor
        self._y_max_top = 6.5 * y_factor
        self._z_min = 1.3
        self._z_max = 5.8
        self._bottom_arc_rect_params = ArcRectParameters(radius_front_back=74.836, 
                                                         radius_left_right=41.300 * y_factor, 
                                                         radius_corner=3.464)  # parameters from arc_rect_paramter_finder
        self._top_arc_rect_params = ArcRectParameters(radius_front_back=25.481, 
                                                      radius_left_right=17.020 * y_factor, 
                                                      radius_corner=3.551)  # parameters from arc_rect_paramter_finder
   
    def create_body(self) -> Part:
        width_bottom, width_top = 2 * self._x_max_bottom, 2 * self._x_max_top
        deep_bottom, deep_top = 2 * self._y_max_bottom, 2 * self._y_max_top

        z_min, z_max = self._z_min, self._z_max + self._extra_height
        z_centered = (z_min + z_max) / 2

        face1 = Pos(Z=z_min) * self._create_arc_rect(width=width_bottom, height=deep_bottom, params=self._bottom_arc_rect_params)
        face2 = Pos(Z=z_centered) * self._create_center_arc_rect(z=z_centered)
        face3 = Pos(Z=z_max) * self._create_arc_rect(width=width_top, height=deep_top, params=self._top_arc_rect_params)
        faces = Sketch() + [face1, face2, face3]
        return loft(faces)
    
    def create_neg_rim(self) -> Part:
        thickness = klp_lame_data.saddle.RIM_THICKNESS

        width_bottom = 2 * (self._x_max_bottom - thickness)
        deep_bottom = 2 * (self._y_max_bottom - thickness)
        bottom_arc_params = ArcRectParameters(radius_front_back=self._bottom_arc_rect_params.radius_front_back - thickness, 
                                              radius_left_right=self._bottom_arc_rect_params.radius_left_right - thickness, 
                                              radius_corner=self._bottom_arc_rect_params.radius_corner - thickness)
        face1 = Pos(Z=self._z_min) * self._create_arc_rect(width=width_bottom, height=deep_bottom, params=bottom_arc_params)

        z_rim_top = klp_lame_data.choc_stem.Z_MAX - 0.3
        face2 = Pos(Z=z_rim_top) * self._create_center_arc_rect(z=z_rim_top, offset=thickness)

        faces = Sketch() + [face1, face2]
        return loft(faces)

    def _create_center_arc_rect(self, z: float, offset: float = 0.0) -> Sketch:
        right_bezier = Bezier([(x, self._calc_adapted_z_value(z)) 
                               for x, z in klp_lame_data.saddle.RIGHT_BEZIER_POINTS])
        back_bezier = Bezier([(y, self._calc_adapted_z_value(z)) 
                              for y, z in klp_lame_data.saddle.BACK_BEZIER_POINTS])

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
        
        return self._create_arc_rect(width=width, 
                                     height=deep, 
                                     params=ArcRectParameters(radius_front_back=ry, 
                                                              radius_left_right=rx, 
                                                              radius_corner=rc)
                                    )
    
    def _calc_adapted_z_value(self, z_orig: float) -> float:
        z_min, z_max = self._z_min, self._z_max
        z_extra = self._extra_height

        if z_orig <= z_min:
            return z_orig
        elif z_orig >= z_max:
            return z_orig + z_extra
        
        dz = z_max - z_min
        s = (dz + z_extra) / dz  # stretch factor for side bezier curves
        
        return z_min + s * (z_orig - z_min)
    
    def _create_arc_rect(self, width: float, height: float, params: ArcRectParameters) -> Sketch:
        if self._cap_kind == CapKind.INDEX_FINGER_NORMAL_SIZED:
            return create_arc_rect_variant(width=width, height=height, params=params)
        else:
            return create_arc_rect(width=width, height=height, params=params)


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
