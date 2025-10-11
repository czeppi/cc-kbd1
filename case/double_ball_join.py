from build123d import export_stl
from build123d import Box, Part, Pos, Rot, Cylinder, Sphere, Circle, revolve, Axis, Plane, RegularPolygon, extrude, Compound
from ocp_vscode import show

from base import OUTPUT_DPATH, mm, Degree
import data



WRITE_ENABLED = True


def main():
    #part = ThumbDoubleBallJoinCreator().create()
    part = ThumbHolderWingCreator().create()
    show(part)


class DoubleBallJoinCreator:
    BELT_FACTOR = 0.8  # = belt_radius / sphere_radius
    SPHERE_COMPLETENESS = 0.77
    SCREW = data.HEXAGON_SCREW_M6
    THICKNESS = 3
    HALVES_GAP = 2.0  # cut a litte more than a half for better tension
    TOLERANCE = 0.1  # make sphere + cylinder a litte bigger    

    def __init__(self, name_prefix: str, sphere_radius: mm, sphere_dist: mm, handle_radius: mm):
        self._name_prefix = name_prefix
        self._sphere_radius = sphere_radius
        self._sphere_dist = sphere_dist
        self._handle_radius = handle_radius
    
    def create(self) -> Compound:
        holder = self._create_holder()

        holder_half1 = holder - Pos(50 - self.HALVES_GAP / 2, 0, 0) * Box(100, 100, 100)
        holder_half2 = holder - Pos(-50 + self.HALVES_GAP / 2, 0, 0) * Box(100, 100, 100)

        holder_half1.label = 'half1'
        holder_half2.label = 'half2'

        if WRITE_ENABLED:
            export_stl(holder_half1, OUTPUT_DPATH / f'{self._name_prefix}-double-ball-holder1.stl')
            export_stl(holder_half2, OUTPUT_DPATH / f'{self._name_prefix}-double-ball-holder2.stl')

        return Compound(label="double-ball-join", children=[holder_half1, holder_half2])
    
    def _create_holder(self) -> Part:
        r1 = self._sphere_radius + self.THICKNESS  # outer sphere radius
        d_2 = self._sphere_dist / 2
        torus_minor_radius = self._calc_torus_minor_radius()
        belt_radius = self.BELT_FACTOR * r1
        cyl_radius = self._calc_vertical_cylinder_radius(torus_minor_radius)

        upper_outer_sphere = Pos(0, 0, d_2) * Sphere(r1)
        upper_inner_sphere = Pos(0, 0, d_2) * Sphere(self._sphere_radius)
        lower_outer_sphere = Pos(0, 0, -d_2) * Sphere(r1)
        lower_inner_sphere = Pos(0, 0, -d_2) * Sphere(self._sphere_radius)

        z3 = d_2 + 3
        holder_r = self._handle_radius + 0.5  # add some tolerance
        upper_sphere_holder_neg_cylinder = Pos(0, 0, z3) * Rot(X=90) * Cylinder(holder_r, height=2 * r1)
        lower_sphere_holder_neg_cylinder = Pos(0, 0, -z3) * Rot(X=90) * Cylinder(holder_r, height=2 * r1)
        upper_sphere_holder_neg_box = Pos(0, 0, 50 + z3) * Box(2 * holder_r, 100, 100)
        lower_sphere_holder_neg_box = Pos(0, 0, -50 + -z3) * Box(2 * holder_r, 100, 100)

        h = (d_2 - r1) + (self.SPHERE_COMPLETENESS * 2 * r1)
        upper_neg_box = Pos(0, 0, h + 50) * Box(100, 100, 100)
        lower_neg_box = Pos(0, 0, -h - 50) * Box(100, 100, 100)

        conn_cylinder = Cylinder(radius=cyl_radius, height=self._sphere_dist)
        torus = revolve(Plane.XZ * Pos(belt_radius + torus_minor_radius, 0) * Circle(torus_minor_radius), Axis.Z)

        screw = self.SCREW
        screw_head_radius = screw.head_radius + self.TOLERANCE
        screw_radius = screw.radius + self.TOLERANCE
        screw_cylinder = Rot(Y=90) * Cylinder(radius=screw_head_radius + self.THICKNESS, height=2 * r1)
        screw_hole = Rot(Y=90) * Cylinder(radius=screw_radius, height=2 * r1)
        screw_head = Pos(r1 - screw.head_height, 0, 0) * extrude(Plane.YZ * RegularPolygon(radius=screw_head_radius, side_count=6), amount=screw.head_height)

        part = upper_outer_sphere + conn_cylinder + lower_outer_sphere - torus - upper_neg_box - lower_neg_box \
               - upper_sphere_holder_neg_cylinder - upper_sphere_holder_neg_box - lower_sphere_holder_neg_cylinder - lower_sphere_holder_neg_box \
               + screw_cylinder - screw_hole - upper_inner_sphere - lower_inner_sphere - screw_head
        #part -= Pos(-50, 0, 0) * Box(100, 100, 100)
        return part

    def _calc_vertical_cylinder_radius(self, torus_radius: mm) -> mm:
        """
            x--r1 
                 -|--
                  |  ----
                  |      ----
            x--b--|-------r2-----x
        """
        r1 = self._sphere_radius + self.THICKNESS
        b = self.BELT_FACTOR * r1
        r2 = torus_radius

        return r1 / (r1 + r2)  * (b + r2)
    
    def _calc_torus_minor_radius(self) -> mm:
        """
          (   )
           )x(----R----x
          (   )
        
          d: distance between center of spheres
          r: radius of spheres
          b: radius at belt (= BELT_FACTOR * r)
        
          (d/2)^2 + (b + R)^2 = (r + R)^2
        
        =>
              d^2 + 4 (b^2 - r^2)
          R = -------------------
                 8 (r - b)
        """
        d = self._sphere_dist
        r = self._sphere_radius + self.THICKNESS
        b = self.BELT_FACTOR * r
        
        return (d**2 + 4 * (b**2 - r**2)) / (8 * (r - b))    
    

class ThumbDoubleBallJoinCreator(DoubleBallJoinCreator):
    NAME_PREFIX = 'thumb'
    SPHERE_RADIUS = 10
    HANDLE_RADIUS = 6

    def __init__(self):
        super().__init__(name_prefix=self.NAME_PREFIX, sphere_radius=self.SPHERE_RADIUS, handle_radius=self.HANDLE_RADIUS)


class FingerDoubleBallJoinCreator(DoubleBallJoinCreator):
    NAME_PREFIX = 'finger'
    SPHERE_RADIUS = 12
    HANDLE_RADIUS = 7

    def __init__(self):
        super().__init__(name_prefix=self.NAME_PREFIX, sphere_radius=self.SPHERE_RADIUS, handle_radius=self.HANDLE_RADIUS)


class HolderWingCreator:
    TOLERANCE = 0.1

    def _create(self, name_prefix: str, wing_length: mm, wing_width: mm, wing_height: mm, screw: data.HexagonScrew, 
                heat_set_length: mm, screw_hole_length: mm, hole_cylinder_thickness: mm) -> Part:
        r1 = screw.head_set_insert_radius
        r2 = screw.radius + self.TOLERANCE
        r3 = r1 + hole_cylinder_thickness
        dz = wing_width / 2
        hole_outer_cylinder = Pos(Z=dz) * Cylinder(r3, wing_width)
        heat_set_hole = Pos(Z=heat_set_length / 2) * Cylinder(r1, heat_set_length)
        screw_hole = Pos(Z=screw_hole_length / 2) * Cylinder(r2, screw_hole_length)
        wing_box = Pos(Z=dz) * Box(2 * (wing_length + r3), wing_height, wing_width)
        part = wing_box + hole_outer_cylinder - screw_hole - heat_set_hole

        if WRITE_ENABLED:
            export_stl(part, OUTPUT_DPATH / f'{name_prefix}-double-ball-wing.stl')

        return part
    

class ThumbHolderWingCreator(HolderWingCreator):
    WING_LENGTH = 10  # x-dir
    WING_WIDTH = 10  # z-dir
    WING_HEIGHT = 4  # y-dir
    SCREW = data.HEXAGON_SCREW_M6
    HEAT_SET_LENGTH = 8
    SCREW_HOLE_LENGTH = 9
    HOLE_CYLINDER_THICKNESS = 3

    def create(self) -> Part:
        return self._create(name_prefix='thumb',
                            wing_length=self.WING_LENGTH, 
                            wing_width=self.WING_WIDTH,
                            wing_height=self.WING_HEIGHT,
                            screw=self.SCREW,
                            heat_set_length=self.HEAT_SET_LENGTH,
                            screw_hole_length=self.SCREW_HOLE_LENGTH,
                            hole_cylinder_thickness=self.HOLE_CYLINDER_THICKNESS)


if __name__ == '__main__':
    main()