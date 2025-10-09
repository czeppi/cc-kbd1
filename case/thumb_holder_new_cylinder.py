import sys
from pathlib import Path
from build123d import export_stl
from build123d import Box, Part, Pos, Rot, Cylinder, CounterBoreHole, Sphere
from ocp_vscode import show

sys.path.append(str(Path(__file__).absolute().parent.parent))

from base import OUTPUT_DPATH
import data


WRITE_ENABLED = True


def main():
    part = MountingPostCreator().create()
    #part = HalfPipeCreator().create()
    show(part)


class MountingPostCreator:
    HEIGHT = 30
    RADIUS = 10
    HEAT_SET_INSERT_DEEP = 10
    BOTTOM_SCREW = data.FLAT_HEAD_SCREW_M5
    CENTER_SCREW = data.FLAT_HEAD_SCREW_M6

    def create(self):
        cylinder = Pos(Z=self.HEIGHT/2) * Cylinder(radius=self.RADIUS, height=self.HEIGHT)
        heat_inserter = self._create_heat_inserter()
        slot = self._create_top_slot()
        part = cylinder - heat_inserter - slot

        if WRITE_ENABLED:
            export_stl(part, OUTPUT_DPATH / 'thumb-mounting-pos.stl')
        return part
    
    def _create_heat_inserter(self) -> Part:
        screw = self.BOTTOM_SCREW
        heat_inserter_deep = self.HEAT_SET_INSERT_DEEP
        hole = CounterBoreHole(radius=screw.hole_radius,
                               counter_bore_radius=screw.head_set_insert_radius,
                               counter_bore_depth=heat_inserter_deep,
                               depth=heat_inserter_deep + 4)
        return Rot(X=180) * hole
    
    def _create_top_slot(self) -> Part:
        h = self.HEIGHT
        r = self.CENTER_SCREW.hole_radius
        box = Pos(Z=h - r/2) * Box(2 * self.RADIUS, 2 * r, r)
        cyl = Pos(Z=h - r) * Rot(Y=90) * Cylinder(radius=r, height=2 * self.RADIUS)
        return box + cyl
    

class HalfPipeCreator:
    SPHERE_RADIUS = 10.0
    SPHERE_COMPLETENESS = 0.75
    SCREW = data.FLAT_HEAD_SCREW_M6
    THICKNESS = 3
    SPHERE_CYLINDER_GAP = 1.0  # between sphere and screw
    HALF_PIPES_GAP = 1.0  # cut a litte more than a half for better tension
    TOLERANCE = 0.1  # make sphere + cylinder a litte bigger

    @property
    def _body_radius(self) -> float:
        sphere_radius = self.SPHERE_RADIUS + self.TOLERANCE
        return max(MountingPostCreator.RADIUS, sphere_radius) + self.THICKNESS
    
    def create(self) -> Part:
        body = self._create_body()
        sphere = self._create_sphere()
        mounting_post = self._create_mounting_post_cylinder()
        screw_node = self._create_screw_nose()
        screw_hole = self._create_screw_hole()
        neg_half_box = Pos(X=-100 + self.HALF_PIPES_GAP) * Box(200, 200, 200)
        part = body + screw_node - sphere - mounting_post - screw_hole - neg_half_box

        if WRITE_ENABLED:
            export_stl(part, OUTPUT_DPATH / 'thumb-half-pipe.stl')
        return part

    def _create_body(self) -> Part:
        sphere_radius = self.SPHERE_RADIUS + self.TOLERANCE
        h = MountingPostCreator.HEIGHT + self.SPHERE_CYLINDER_GAP + 2 * sphere_radius * self.SPHERE_COMPLETENESS
        return Pos(Z=h/2) * Cylinder(radius=self._body_radius, height=h)
    
    def _create_sphere(self) -> Part:
        sphere_radius = self.SPHERE_RADIUS + self.TOLERANCE
        dz = MountingPostCreator.HEIGHT + self.SPHERE_CYLINDER_GAP + sphere_radius
        return Pos(Z=dz) * Sphere(sphere_radius)
    
    def _create_mounting_post_cylinder(self) -> Part:
        h = MountingPostCreator.HEIGHT
        r = MountingPostCreator.RADIUS + self.TOLERANCE
        return Pos(Z=h/2) * Cylinder(radius=r, height=h)
    
    def _create_screw_nose(self) -> Part:
        r = self.SCREW.head_radius
        h = 2 * self._body_radius
        dz = MountingPostCreator.HEIGHT - self.SCREW.hole_radius
        return Pos(Z=dz) * Rot(Y=90) * Cylinder(radius=r, height=h)
    
    def _create_screw_hole(self) -> Part:
        r = self.SCREW.hole_radius
        h = 2 * self._body_radius
        dz = MountingPostCreator.HEIGHT - r
        return Pos(Z=dz) * Rot(Y=90) * Cylinder(radius=r, height=h)


if __name__ == '__main__':
    main()
