import copy
from build123d import offset, export_stl, loft, make_face, extrude
from build123d import Box, Cylinder, Part, Pos, Rot, Sphere
from ocp_vscode import show_object

from base import TOLERANCE, OUTPUT_DPATH
from thumb_base import THICKNESS, SLOT_LEN, EPS


def main():
    creator = TrackballHolderCreator()
    holder = creator.create()
    export_stl(holder, OUTPUT_DPATH / 'trackball-holder.stl')
    show_object(holder)


class TrackballHolderCreator:
    SPHERE_INNER_RADIUS = 18.1  # calculated - BEARING_RING_HEIGHT
    BEARING_RADIUS = 3.85
    BEARING_HEIGHT = 4.0
    BEARING_RING_RADIUS = 9.0/2 + TOLERANCE
    BEARING_RING_HEIGHT = 1.0
    SPHERE_BOTTOM_RADIUS = 6.34
    SENSOR_BOX_X_LEN = 19.0
    SENSOR_BOX_Y_LEN = 21.5
    SENSOR_BOX_HEIGHT = 3.5
    BOTTOM_PLATE_X_LEN = 23.0 + 10.0 # SENSOR_BOX_X_LEN + 2 * THICKNESS
    BOTTOM_PLATE_Y_LEN = 33.0
    BOTTOM_PLATE_HEIGHT = 5.5  # orig = 7.0
    FOOT_BOX_DIST_FROM_SPHERE_CENTER = 31.0 - 12.79 - 2.0
    SENSOR_BRACKET_HEIGHT = 4.0
    SLOT_DIST = 22.8  # from center to center

    def create(self) -> Part:
        result = self._create_full_semi_shpere()  # massiv
        result = self._add_bearings(result)
        result += self._create_foot_box_without_sensor_hole()

        result -= self._create_inner_sphere()
        result -= self._create_sensor_hole_box()
        result -= self._create_sphere_bottom_hole()
        return result
    
    def _add_box(self, result: Part) -> None:
        result += Box(20, 30, 40)
        return result
    
    def _create_full_semi_shpere(self) -> Part:
        outer_sphere = Sphere(radius=self.SPHERE_INNER_RADIUS + THICKNESS)
        neg_box = Pos(Z=50) * Box(100, 100, 100)  # cut top half
        return outer_sphere - neg_box
    
    def _create_inner_sphere(self) -> Part:
        return Sphere(radius=self.SPHERE_INNER_RADIUS)
    
    def _add_bearings(self, result: Part) -> Part:
        h = self.BEARING_HEIGHT + self.BEARING_RING_HEIGHT
        loc1 = Rot(X=60) * Pos(Z=-h/2 - self.SPHERE_INNER_RADIUS)
        loc2 = Rot(X=60) * Pos(Z=-self.SPHERE_INNER_RADIUS)
        
        outer_cyl = loc1 * Cylinder(radius=self.BEARING_RADIUS + THICKNESS, height=h) 
        inner_cyl = loc1 * Cylinder(radius=self.BEARING_RADIUS, height=h)
        ring_cyl = loc2 * Cylinder(radius=self.BEARING_RING_RADIUS, height=2 * self.BEARING_RING_HEIGHT)

        for angle in [30, 150, 270]:
            result += Rot(Z=angle) * outer_cyl
            result -= Rot(Z=angle) * inner_cyl
            result -= Rot(Z=angle) * ring_cyl

        return result
    
    def _create_foot_box_without_sensor_hole(self) -> Part:
        # foot_part (bottom, z==0)
        foot_part = Pos(Z=self.BOTTOM_PLATE_HEIGHT/2) * Box(self.BOTTOM_PLATE_X_LEN, self.BOTTOM_PLATE_Y_LEN, self.BOTTOM_PLATE_HEIGHT)
        
        foot_dy = THICKNESS/2 - self.BOTTOM_PLATE_Y_LEN/2
        foot_conn1 = Pos(Y=foot_dy) * self._create_foot_connections()
        foot_conn2 = Pos(Y=-foot_dy) * self._create_foot_connections()

        foot_part += foot_conn1
        foot_part += foot_conn2

        return Pos(Z=-self.BOTTOM_PLATE_HEIGHT - self.FOOT_BOX_DIST_FROM_SPHERE_CENTER) * foot_part
    
    def _create_sensor_hole_box(self) -> Part:
        return Pos(Z=self.SENSOR_BOX_HEIGHT/2 - self.BOTTOM_PLATE_HEIGHT - self.FOOT_BOX_DIST_FROM_SPHERE_CENTER) * \
               Box(self.SENSOR_BOX_X_LEN, self.SENSOR_BOX_Y_LEN, self.SENSOR_BOX_HEIGHT)
    
    def _create_foot_connections(self) -> Part:
        foot_height = self.SENSOR_BRACKET_HEIGHT + 2 * SLOT_LEN
        foot_conn = Pos(Z=foot_height/2) * Box(self.BOTTOM_PLATE_X_LEN, THICKNESS, foot_height)

        slot_width = THICKNESS + 2 * TOLERANCE
        slot_box = Pos(Z=SLOT_LEN/2) * Box(slot_width, 100.0, SLOT_LEN)

        x_off = self.SLOT_DIST / 2
        foot_conn -= Pos(X=x_off) * copy.copy(slot_box)
        foot_conn -= Pos(X=-x_off) * copy.copy(slot_box)

        return Pos(Z=-foot_height) * foot_conn

    def _create_sphere_bottom_hole(self) -> Part:
        return Cylinder(radius=self.SPHERE_BOTTOM_RADIUS, height=100)


if __name__ == '__main__':
    main()
