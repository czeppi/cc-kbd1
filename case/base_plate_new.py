import math
import copy
from typing import Iterator
from ocp_vscode import show
from build123d import Part, Compound, Pos, Rot, Cylinder, Box, export_stl, make_face, Polyline, extrude, Plane, CounterBoreHole, Sphere

import data
from base import OUTPUT_DPATH, mm, Degree
from double_ball_join import FingerDoubleBallJoinCreator, ThumbDoubleBallJoinCreator

WRITE_ENABLED = True


type XY = tuple[float, float]


def main():
    assembly = create_assembly()
    show(assembly)


def create_assembly() -> Compound:
    plate = CircleBasePlateCreator().create_plate()
    cover = CircleBasePlateCreator().create_cover()
    return Compound(label="base", children=[plate, cover])


class CircleBasePlateCreator:
    RADIUS = 50
    # REL_HEIGHT = 0.75
    THICKNESS_TOP = 3 
    INTERIOR_HEIGHT = 6.2
    THICKNESS_RIM = 3

    FINGER_POST_SPHERE_RADIUS = FingerDoubleBallJoinCreator.SPHERE_RADIUS
    FINGER_POST_HANDLE_RADIUS = FingerDoubleBallJoinCreator.HANDLE_RADIUS
    FINGER_POST_HANDLE_LEN = 4
    FINGER_POST_POS_ANGLE = 150  # math. in degree
    FINGER_POST_POS_DIST_FROM_CENTER = 25

    THUMB_POST_SPHERE_RADIUS = ThumbDoubleBallJoinCreator.SPHERE_RADIUS
    THUMB_POST_HANDLE_RADIUS = ThumbDoubleBallJoinCreator.HANDLE_RADIUS
    THUMB_POST_HANDLE_LEN = 4
    THUMB_POST_POS_ANGLE = -60  # math. in degree
    THUMB_POST_POS_DIST_FROM_CENTER = 25

    TRRS_SOCKET_POS_ANGLE = 180  # math. in degree
    TRRS_SOCKET_RIM = 2

    CONTROLLER_POS_ANGLE = 45  # math. in degree
    CONTROLLER_POS_DIST_FROM_CENTER = 25
    CONTROLLER_ROT_ANGLE = 45
    CONTROLLER_RIM = 2

    THUMB_CABEL_HOLE_POS_ANGLE = -60  # math. in degree
    THUMB_CABEL_HOLE_POS_DIST_FROM_CENTER = 10
    THUMB_CABEL_HOLE_RADIUS = 5

    FINGER_CABEL_HOLE_POS_ANGLE = -45  # math. in degree

    COVER_HEIGHT = 2
    COVER_STEP_LEN = 1
    COVER_SCREW = data.FLAT_HEAD_SCREW_M3
    COVER_SCREW_HEAD_HEIGHT_TOLERANCE = 0.5  # should not touch the ground
    COVER_SCREW_HEAT_INSERT_LEN = 4
    COVER_SCREW_RIM = 2  # rim in all directions

    TOLERANCE = 0.1

    def create_plate(self) -> Part:
        """ origin: z=0 => bottom of plate
        """
        body = self._create_body_with_rim()
        cover_holder_neg_part = self._create_cover_holder_neg_part()
        cover_holder = self._create_cover_holder()
        finger_post = self._create_finger_post()
        thumb_post = self._create_thumb_post()
        trrs_socket_body = self._create_trrs_socket_body()
        trrs_socket_neg_part = self._create_trrs_socket_neg_part()
        controller_neg_part = self._create_controller_neg_part()
        controller_holder = self._create_controller_holder()
        thumb_cabel_hole = self._create_thumb_cabel_hole()
        finger_cabel_hole = self._create_finger_cabel_hole()

        part = body - cover_holder_neg_part + cover_holder \
            + finger_post + thumb_post \
            + trrs_socket_body - trrs_socket_neg_part \
            - controller_neg_part + controller_holder \
            - thumb_cabel_hole - finger_cabel_hole
        part.label = 'plate'

        if WRITE_ENABLED:
            export_stl(part, OUTPUT_DPATH / 'circle-base-plate.stl')

        return part
    
    def _create_body_with_rim(self) -> Part:
        body = self._create_cut_circle(r=self.RADIUS, h=self.THICKNESS_TOP + self.INTERIOR_HEIGHT + self.COVER_HEIGHT)
        neg_part = self._create_cut_circle(r=self.RADIUS - self.THICKNESS_RIM, h=self.INTERIOR_HEIGHT + self.COVER_HEIGHT)
        cover_step = self._create_cover_step_for_plate()
        return body - neg_part - cover_step

    def _create_cut_circle(self, r: float, h: float) -> Part:
        cyl = Pos(Z=h / 2) * Cylinder(radius=r, height=h)

        # a = 2 * r
        # dy = self.REL_HEIGHT * r
        # neg_box = Pos(Y=-a/2 - dy) * Box(a, a, a)
        # return cyl - neg_box
        return cyl
    
    def _create_cover_step_for_plate(self) -> Part:
        r = self.RADIUS - (self.THICKNESS_RIM - self.COVER_STEP_LEN)
        h = self.COVER_HEIGHT / 2
        return Pos(Z=h/2) * Cylinder(radius=r, height=h)
    
    def _create_cover_holder_neg_part(self) -> Part:
        return Cylinder(radius=self.COVER_SCREW.head_set_insert_radius, height=100)
    
    def _create_cover_holder(self) -> Part:
        body_height = self.THICKNESS_TOP + self.INTERIOR_HEIGHT + self.COVER_HEIGHT
        screw_head_height = self.COVER_SCREW.head_height + self.COVER_SCREW_HEAD_HEIGHT_TOLERANCE  # s. create_cover
        screw_hole_radius = self.COVER_SCREW.radius + self.TOLERANCE  # s. create_cover
        z0 = screw_head_height + self.COVER_SCREW_RIM

        heat_insert_radius = self.COVER_SCREW.head_set_insert_radius
        heat_insert_len = self.COVER_SCREW_HEAT_INSERT_LEN
        holder_radius = heat_insert_radius + self.COVER_SCREW_RIM
        holder_height = body_height - z0
        screw_hole_len = holder_height - 1
        assert screw_hole_len >= heat_insert_len

        holder_body = Pos(Z=z0 + holder_height/2) * Cylinder(radius=holder_radius, height=holder_height)
        screw_hole = Pos(Z=z0 + screw_hole_len/2) * Cylinder(radius=screw_hole_radius, height=screw_hole_len)
        heat_insert_hole = Pos(Z=z0 + heat_insert_len/2) * Cylinder(radius=heat_insert_radius, height=heat_insert_len)

        return holder_body - screw_hole - heat_insert_hole
    
    def _create_finger_post(self) -> Part:
        return self._create_post(pos_angle=self.FINGER_POST_POS_ANGLE, pos_radius=self.FINGER_POST_POS_DIST_FROM_CENTER,
                                 sphere_radius=self.FINGER_POST_SPHERE_RADIUS,
                                 handle_radius=self.FINGER_POST_HANDLE_RADIUS, handle_len=self.FINGER_POST_HANDLE_LEN)

    def _create_thumb_post(self) -> Part:
        return self._create_post(pos_angle=self.THUMB_POST_POS_ANGLE, pos_radius=self.THUMB_POST_POS_DIST_FROM_CENTER,
                                 sphere_radius=self.THUMB_POST_SPHERE_RADIUS,
                                 handle_radius=self.THUMB_POST_HANDLE_RADIUS, handle_len=self.THUMB_POST_HANDLE_LEN)

    def _create_post(self, pos_angle: Degree, pos_radius: mm, sphere_radius: mm, handle_radius: mm, handle_len: mm) -> Part:
        angle_rad = math.radians(pos_angle)
        x = pos_radius * math.cos(angle_rad)
        y = pos_radius * math.sin(angle_rad)
        z = self.THICKNESS_TOP + self.INTERIOR_HEIGHT + self.COVER_HEIGHT

        z_sphere = z + handle_len + sphere_radius

        cyl_len = handle_len + sphere_radius
        handle = Pos(x, y, z + cyl_len/2) * Cylinder(radius=handle_radius, height=cyl_len)
        sphere = Pos(x, y, z_sphere) * Sphere(radius=sphere_radius)
        return handle + sphere

    def _create_trrs_socket_body(self) -> Part:
        z0 = self.COVER_HEIGHT
        cyl_len = data.TRRS_SOCKET.cylinder_length
        box_x_len = data.TRRS_SOCKET.box_length + 3 * self.TOLERANCE
        box_y_len = data.TRRS_SOCKET.box_width + self.TOLERANCE
        box_height = data.TRRS_SOCKET.box_height + self.TOLERANCE
        x_off = 1  # reduce a litte cause the plate is round

        body_x_len = cyl_len + box_x_len + self.TRRS_SOCKET_RIM - x_off
        body_y_len = box_y_len + 2 * self.TRRS_SOCKET_RIM
        body_height = box_height
        body_x_pos = self.RADIUS - x_off - body_x_len/2

        return Rot(Z=self.TRRS_SOCKET_POS_ANGLE) * Pos(X=body_x_pos, Z=z0 + body_height/2) * Box(body_x_len, body_y_len, body_height)

    def _create_trrs_socket_neg_part(self) -> Part:
        z0 = self.COVER_HEIGHT

        cyl_radius = data.TRRS_SOCKET.cylinder_radius + self.TOLERANCE
        cyl_len = data.TRRS_SOCKET.cylinder_length
        cyl_x_pos = self.RADIUS - cyl_len/2

        box_x_len = data.TRRS_SOCKET.box_length + 3 * self.TOLERANCE
        box_y_len = data.TRRS_SOCKET.box_width + self.TOLERANCE
        box_height = data.TRRS_SOCKET.box_height + self.TOLERANCE
        box_x_pos = self.RADIUS - cyl_len - box_x_len / 2

        box = Pos(X=box_x_pos, Z=z0 + box_height/2) * Box(box_x_len, box_y_len, box_height)
        cyl = Pos(X=cyl_x_pos, Z=z0 + box_height/2) * Rot(Y=90) * Cylinder(radius=cyl_radius, height=cyl_len)

        lower_cabel_box_x_len = box_x_len - 2
        lower_cabel_box_height = data.TRRS_SOCKET.cable_space
        lower_cabel_box_y_len = box_y_len + self.TRRS_SOCKET_RIM
        lower_cabel_box_x_pos = self.RADIUS - cyl_len - box_x_len + lower_cabel_box_x_len/2
        lower_cabel_box = Pos(lower_cabel_box_x_pos, lower_cabel_box_y_len/2, z0 + lower_cabel_box_height/2) * Box(lower_cabel_box_x_len, lower_cabel_box_y_len, lower_cabel_box_height)

        end_cabel_box_x_len = data.TRRS_SOCKET.cable_space
        end_cabel_box_y_len = box_y_len + self.TRRS_SOCKET_RIM
        end_cabel_box_x_pos = self.RADIUS - cyl_len - box_x_len + end_cabel_box_x_len/2
        end_cabel_box = Pos(end_cabel_box_x_pos, end_cabel_box_y_len/2, z0 + box_height/2) * Box(end_cabel_box_x_len, end_cabel_box_y_len, box_height)

        return Rot(Z=self.TRRS_SOCKET_POS_ANGLE) * (cyl + box + lower_cabel_box + end_cabel_box)

    def _create_controller_neg_part(self) -> Part:
        angle_radians = math.radians(self.CONTROLLER_POS_ANGLE)
        pos_radius = self.CONTROLLER_POS_DIST_FROM_CENTER
        x0 = pos_radius * math.cos(angle_radians)
        y0 = pos_radius * math.sin(angle_radians)
        z0 = self.COVER_HEIGHT + self.INTERIOR_HEIGHT
        rim = self.CONTROLLER_RIM
        box_len = data.PICO_BOARD.length + data.PICO_BOARD.usb_len_over_board + 2 * self.TOLERANCE + 2 * rim
        box_width = data.PICO_BOARD.pcb_terminal_width + 2 * self.TOLERANCE + 2 * rim
        box_height = self.THICKNESS_TOP

        box = Pos(x0, y0, z0 + box_height/2) * Rot(Z=self.CONTROLLER_ROT_ANGLE) * Box(box_width, box_len, box_height)
        return box

    def _create_controller_holder(self) -> Part:
        angle_radians = math.radians(self.CONTROLLER_POS_ANGLE)
        pos_radius = self.CONTROLLER_POS_DIST_FROM_CENTER
        x0 = pos_radius * math.cos(angle_radians)
        y0 = pos_radius * math.sin(angle_radians)
        z0 = self.COVER_HEIGHT + self.INTERIOR_HEIGHT
        rim = self.CONTROLLER_RIM
        inner_len = data.PICO_BOARD.length + data.PICO_BOARD.usb_len_over_board + 2 * self.TOLERANCE
        inner_width = data.PICO_BOARD.pcb_terminal_width + 2 * self.TOLERANCE
        ctrl_height = data.PICO_BOARD.get_total_height_with_feet()
        inner_height = ctrl_height - self.INTERIOR_HEIGHT + 2 * self.TOLERANCE

        outer_len = inner_len + 2 * rim
        outer_width = inner_width + 2 * rim
        outher_height = inner_height + rim

        body = Pos(Z=outher_height/2) * Box(outer_width, outer_len, outher_height)
        interior = Pos(Z=inner_height/2) * Box(inner_width, inner_len, inner_height)

        dist_holder_len = max(data.PICO_BOARD.pins_height, data.PICO_BOARD.usb_height) + self.TOLERANCE
        dist_holder_z = inner_height - dist_holder_len/2
        dist_holders = [
             Pos(dx, dy, dist_holder_z) * Cylinder(radius=1.5, height=dist_holder_len)
             for dx, dy in self._iter_controller_dist_holder_positions()]
        
        top_holder_x_len = 8
        top_holder_y_len = 3
        top_holder_height = 2
        top_holder_y = inner_len / 2 - top_holder_y_len / 2
        top_holder_z = inner_height - dist_holder_len - data.PICO_BOARD.height - top_holder_height/2 - self.TOLERANCE
        top_holder = Pos(Y=top_holder_y, Z=top_holder_z) * Box(top_holder_x_len, top_holder_y_len, top_holder_height)
        
        part = body - interior + dist_holders + top_holder
        return Pos(x0, y0, z0) * Rot(Z=self.CONTROLLER_ROT_ANGLE) * part
    
    def _iter_controller_dist_holder_positions(self) -> Iterator[tuple[mm, mm]]:
        y_len = data.PICO_BOARD.length
        x_len = data.PICO_BOARD.width
        y1 = data.PICO_BOARD.hole_distance_top
        y2 = data.PICO_BOARD.hole_distance_bottom
        x1 = data.PICO_BOARD.hole_distance_left
        x2 = data.PICO_BOARD.hole_distance_right

        yield -x_len/2 + x1, y_len/2 - y1
        yield  x_len/2 - x2, y_len/2 - y1
        yield -x_len/2 + x1, -y_len/2 + y2
        yield  x_len/2 - x2, -y_len/2 + y2
    
    def _create_thumb_cabel_hole(self) -> Part:
        angle_radians = math.radians(self.THUMB_CABEL_HOLE_POS_ANGLE)
        pos_radius = self.THUMB_CABEL_HOLE_POS_DIST_FROM_CENTER
        x0 = pos_radius * math.cos(angle_radians)
        y0 = pos_radius * math.sin(angle_radians)
        z0 = self.COVER_HEIGHT + self.INTERIOR_HEIGHT
        height = self.THICKNESS_TOP
        return Pos(x0, y0, z0 + height/2) * Cylinder(radius=self.THUMB_CABEL_HOLE_RADIUS, height=height)
    
    def _create_finger_cabel_hole(self) -> Part:
        # cabel_radius = self.INTERIOR_HEIGHT / 2
        # height = 10
        # z = self.COVER_HEIGHT + self.INTERIOR_HEIGHT / 2
        # return Rot(Z=self.FINGER_CABEL_HOLE_POS_ANGLE) * Pos(X=self.RADIUS, Z=z) * Rot(Y=90) * Cylinder(radius=cabel_radius, height=height)

        hole_heigh = self.INTERIOR_HEIGHT
        hole_x_len = 10
        hole_y_len = 10
        z = self.COVER_HEIGHT + self.INTERIOR_HEIGHT / 2
        return Rot(Z=self.FINGER_CABEL_HOLE_POS_ANGLE) * Pos(X=self.RADIUS, Z=z) * Box(hole_x_len, hole_y_len, hole_heigh)

    def create_cover(self) -> Part:
        upper_slice_radius = self.RADIUS - self.THICKNESS_RIM - self.TOLERANCE
        lower_slice_radius = upper_slice_radius + self.COVER_STEP_LEN
        slice_height = self.COVER_HEIGHT / 2
        upper_slice = Pos(Z=3/2 * slice_height) * Cylinder(radius=upper_slice_radius, height=slice_height)
        lower_slice = Pos(Z=slice_height/2) * Cylinder(radius=lower_slice_radius, height=slice_height)

        screw_head_height = self.COVER_SCREW.head_height + self.COVER_SCREW_HEAD_HEIGHT_TOLERANCE
        screw_head_radius = self.COVER_SCREW.head_radius + self.TOLERANCE
        screw_head_neg_cyl = Pos(Z=screw_head_height/2) * Cylinder(radius=screw_head_radius, height=screw_head_height)

        screw_hole_radius = self.COVER_SCREW.radius + self.TOLERANCE
        screw_hole_len = 100
        screw_hole = Pos(Z=screw_hole_len/2) * Cylinder(radius=screw_hole_radius, height=screw_hole_len)

        screw_post_radius = screw_head_radius + self.COVER_SCREW_RIM
        screw_post_height = screw_head_height + self.COVER_SCREW_RIM - 2 * slice_height
        screw_post = Pos(Z=2 * slice_height + screw_post_height/2) * Cylinder(radius=screw_post_radius, height=screw_post_height)

        part = upper_slice + lower_slice + screw_post - screw_head_neg_cyl - screw_hole
        part.label = 'cover'

        if WRITE_ENABLED:
            export_stl(part, OUTPUT_DPATH / 'circle-base-cover.stl')
        
        return part
    

if __name__ == '__main__':
    main()
