import copy
import sys
from pathlib import Path
from build123d import offset, export_stl, loft, make_face, extrude
from build123d import Box, Cylinder, Part, Pos, Rot, Sphere, CounterBoreHole
from ocp_vscode import show_object

sys.path.append(str(Path(__file__).absolute().parent.parent))

from base import TOLERANCE, OUTPUT_DPATH
from thumb_base import THICKNESS
import data


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
    SENSOR_BOX_X_LEN = 21.5
    SENSOR_BOX_Y_LEN = 19.0
    SENSOR_BOX_HEIGHT = 3.5
    SENSOR_SREW_HOLES_DIST = 24.0
    BOTTOM_PLATE_X_LEN = 29.0
    BOTTOM_PLATE_Y_LEN = 21.5 # SENSOR_BOX_X_LEN
    BOTTOM_PLATE_HEIGHT = 5.5  # orig = 7.0
    FOOT_BOX_DIST_FROM_SPHERE_CENTER = 31.0 - 12.79 - 2.0
    SENSOR_BRACKET_HEIGHT = 4.0
    SWITCH_HOLDER_X_LEN = 22.0  # size from outer sphere (includes distance to sphere and offset cause of angle)
    SWITCH_HOLDER_Y_LEN = 18.0  # s. SkeletonCreator.BASE_LEN
    SWITCH_HOLDER_HEIGHT = 3.0
    SWITCH_HOLDER_Z_OFFSET = 8.0  # distance between top of switch holder plate to sphere center
    CONN_SPHERE_RADIUS = 9
    CONN_SPHERE_HANDLE_RADIUS = 5 
    CONN_SPHERE_HANDLE_LEN = 4  # from outer sphere
    CONN_SPHERE_HANDLE_ANGLE = 45
    CONN_SPHERE_HANDLE_X_OFF = 2

    def create(self) -> Part:
        result = self._create_full_semi_shpere()  # massiv
        result = self._add_bearings(result)
        result += self._create_foot_box_without_sensor_hole()
        result += self._create_switch_holder_plate()
        result += self._create_handle()

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
        dz1 = -self.BOTTOM_PLATE_HEIGHT / 2 - self.FOOT_BOX_DIST_FROM_SPHERE_CENTER
        box = Pos(Z=dz1) * Box(self.BOTTOM_PLATE_X_LEN, self.BOTTOM_PLATE_Y_LEN, self.BOTTOM_PLATE_HEIGHT)

        screw = data.FLAT_HEAD_SCREW_M2

        # no place for heat inserter!
        # screw_hole = CounterBoreHole(radius=screw.hole_radius,
        #                              counter_bore_radius=screw.head_set_insert_radius,
        #                              counter_bore_depth=2,
        #                              depth=4)
        # dz = -self.BOTTOM_PLATE_HEIGHT - self.FOOT_BOX_DIST_FROM_SPHERE_CENTER
        # screw_hole = Pos(Z=dz) * Rot(Y=180) * screw_hole

        hole_radius = 1.0  # only a small hole
        hole_deep = 4.0
        dz2 = hole_deep / 2 - self.FOOT_BOX_DIST_FROM_SPHERE_CENTER - self.BOTTOM_PLATE_HEIGHT
        screw_hole = Pos(Z=dz2) * Cylinder(radius=hole_radius, height=hole_deep)

        dx = self.SENSOR_SREW_HOLES_DIST / 2
        screw_hole1 = Pos(X=dx) * copy.copy(screw_hole)
        screw_hole2 = Pos(X=-dx) * copy.copy(screw_hole)

        return box - screw_hole1 - screw_hole2
    
    def _create_sensor_hole_box(self) -> Part:
        dz = self.SENSOR_BOX_HEIGHT/2 - self.BOTTOM_PLATE_HEIGHT - self.FOOT_BOX_DIST_FROM_SPHERE_CENTER
        return Pos(Z=dz) * Box(self.SENSOR_BOX_X_LEN, self.SENSOR_BOX_Y_LEN, self.SENSOR_BOX_HEIGHT)
    
    def _create_sphere_bottom_hole(self) -> Part:
        return Cylinder(radius=self.SPHERE_BOTTOM_RADIUS, height=100)
    
    def _create_switch_holder_plate(self) -> Part:
        x_len = self.SWITCH_HOLDER_X_LEN + self.SPHERE_INNER_RADIUS + THICKNESS 
        dx = -x_len / 2
        dz = -self.SWITCH_HOLDER_HEIGHT / 2 - self.SWITCH_HOLDER_Z_OFFSET
        return Pos(X=dx, Z=dz) * Box(x_len, self.SWITCH_HOLDER_Y_LEN, self.SWITCH_HOLDER_HEIGHT)
    
    def _create_handle(self) -> Part:
        h = self.SPHERE_INNER_RADIUS + THICKNESS + self.CONN_SPHERE_HANDLE_LEN + self.CONN_SPHERE_RADIUS
        cyl = Pos(Z=-h/2) * Cylinder(radius=self.CONN_SPHERE_HANDLE_RADIUS, height=h)

        r = self.CONN_SPHERE_RADIUS
        sphere = Pos(Z=-h) * Sphere(radius=r)
        return Pos(X=-self.CONN_SPHERE_HANDLE_X_OFF) * Rot(Y=self.CONN_SPHERE_HANDLE_ANGLE) * (cyl + sphere)


if __name__ == '__main__':
    main()
