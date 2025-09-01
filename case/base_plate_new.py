import sys
import math
from pathlib import Path
from typing import Iterator

sys.path.append(str(Path(__file__).absolute().parent.parent))

from case.base import OUTPUT_DPATH
import data

from build123d import Box, Circle, Compound, CounterBoreHole, Hole, Cylinder, Edge, Part, Plane, Polyline, Pos, Rot, Sketch, Solid, Sphere, Vector, export_stl, extrude, make_face, sweep
from ocp_vscode import show_object


WRITE_ENABLED = True


type XY = tuple[float, float]


def main():
    #_create_assembly()
    _create_finger_sphere()


def _create_finger_sphere():
    part = FingerSphereCreator().create()
    show_object(part)


def _create_assembly():
    creator = BaseAssemblyCreator()
    assembly = creator.create()
    show_object(assembly)


class BaseAssemblyCreator:

    def __init__(self):
        self._base_plate: Part | None = None
        self._stumps: list[Part] = []
        self._half_pipes: list[Part] = []

    def create(self) -> Compound:
        self._base_plate = BasePlateCreator().create()
        self._stumps = list(self._iter_stumps())
        self._half_pipes = list(self._iter_half_pipes())
        
        children = [self._base_plate] + self._stumps + self._half_pipes
        return Compound(label="base_assembly", children=children)
    
    def _iter_stumps(self) -> Iterator[Part]:
        x1, y1 = BasePlateCreator.FINGER_SLOT_POSITION
        x2, y2 = BasePlateCreator.THUMB_SLOT_POSITION
        z = BasePlateCreator.THICKNESS + BasePlateCreator.SCREW_HEAD_HEIGHT

        mounting_post1 = Pos(X=x1, Y=y1, Z=z) * MountingPostCreator().create()
        mounting_post2 = Pos(X=x2, Y=y2, Z=z) * MountingPostCreator().create()

        mounting_post1.label = 'mounting-post1'
        mounting_post2.label = 'mounting-post2'

        yield mounting_post1
        yield mounting_post2

    def _iter_half_pipes(self) -> Iterator[Part]:
        x1, y1 = BasePlateCreator.FINGER_SLOT_POSITION
        x2, y2 = BasePlateCreator.THUMB_SLOT_POSITION
        z = BasePlateCreator.THICKNESS + BasePlateCreator.SCREW_HEAD_HEIGHT + 10

        creator = HalfPipeCreator()
        half_pipe_1a = Pos(X=x1, Y=y1, Z=z) * creator.create_with_counter_hole()
        half_pipe_1b = Pos(X=x1, Y=y1, Z=z) * Rot(Z=180) * creator.create_with_heat_inserter_set()
        half_pipe_2a = Pos(X=x2, Y=y2, Z=z) * creator.create_with_counter_hole()
        half_pipe_2b = Pos(X=x2, Y=y2, Z=z) * Rot(Z=180) * creator.create_with_heat_inserter_set()

        half_pipe_1a.label = 'half-pipe-1a'
        half_pipe_1b.label = 'half-pipe-1b'
        half_pipe_2a.label = 'half-pipe-2a'
        half_pipe_2b.label = 'half-pipe-2b'

        yield half_pipe_1a
        yield half_pipe_1b
        yield half_pipe_2a
        yield half_pipe_2b


class BasePlateCreator:
    THICKNESS = 4
    SLOTS_LEN = 25
    SLOTS_WIDTH = 5 
    SCREW_HEAD_HEIGHT = 3
    SCREW_HEAD_WIDTH = 10
    FINGER_SLOT_POSITION = 0, 30
    THUMB_SLOT_POSITION = -20, -20

    def create(self) -> Part:
        """ origin: z=0 => bottom of plate
        """
        x1, y1 = self.FINGER_SLOT_POSITION
        x2, y2 = self.THUMB_SLOT_POSITION

        body = self._create_body()
        body_with_one_slot = self._add_slot(body, x=x1, y=y1, angle=90)
        base_plate = self._add_slot(body_with_one_slot, x=x2, y=y2, angle=0)
        base_plate.label = 'base-plate'
        return base_plate

    def _create_body(self) -> Part:
        points = list(self._iter_points())
        face = make_face(Plane.XY * Polyline(points))
        height = self.THICKNESS
        return Pos(Z=0) * extrude(face, height)

    def _iter_points(self) -> Iterator[XY]:
        a = 60
        b = 40
        yield -a, -b
        yield a, -b
        yield a, b
        yield 30, b + 20
        yield -30, b + 20
        yield -a, b
        yield -a, -b

    def _add_slot(self, plate: Part, x: float, y: float, angle: float) -> Part:
        loc = Pos(X=x, Y=y) * Rot(Z=angle)

        bounding_box = loc * self._create_bounding_box_for_slot()
        slot_box = loc * self._create_slot_box()
        screw_head_box = loc * self._create_screw_head_box_for_slot()

        return plate + bounding_box - slot_box - screw_head_box
    
    def _create_bounding_box_for_slot(self) -> Part:
        h = self.SCREW_HEAD_HEIGHT + self.THICKNESS
        dx = self.SCREW_HEAD_WIDTH - self.SLOTS_WIDTH
        box = Box(self.SLOTS_LEN + dx + 2 * self.THICKNESS, 
                  self.SCREW_HEAD_WIDTH + 2 * self.THICKNESS, 
                  h)
        return Pos(Z=h/2) * box
    
    def _create_slot_box(self) -> Part:
        h = self.SCREW_HEAD_HEIGHT + self.THICKNESS
        box = Box(self.SLOTS_LEN, self.SLOTS_WIDTH, h)
        return Pos(Z=h/2) * box
    
    def _create_screw_head_box_for_slot(self) -> Part:
        h = self.SCREW_HEAD_HEIGHT
        dx = self.SCREW_HEAD_WIDTH - self.SLOTS_WIDTH
        box = Box(self.SLOTS_LEN + dx, self.SCREW_HEAD_WIDTH, h)
        return Pos(Z=h/2) * box
    

class MountingPostCreator:
    HEIGHT = 50
    RADIUS = 12
    HEAT_SET_INSERT_RADIUS = 3.1
    HEAT_SET_INSERT_DEEP = 10
    SCREW_DIAMETER = 5

    def create(self):
        cylinder = Pos(Z=self.HEIGHT/2) * Cylinder(radius=self.RADIUS, height=self.HEIGHT)

        hole = CounterBoreHole(radius=self.SCREW_DIAMETER/2,
                               counter_bore_radius=self.HEAT_SET_INSERT_RADIUS,
                               counter_bore_depth=self.HEAT_SET_INSERT_DEEP,
                               depth=self.HEAT_SET_INSERT_DEEP + 4)
        return cylinder - Rot(X=180) * hole
    

class HalfPipeCreator:
    MOUNTING_POST_RADIUS = 12
    MOUNTING_POST_HEIGHT = 50
    SPHERE_RADIUS = 12
    SPHERE_COMPLETENESS = 0.75
    HEAT_SET_INSERT_RADIUS = 3.1
    HEAT_SET_INSERT_DEEP = 10
    HEAT_SET_HEIGHT = 10
    SCREW_DIAMETER = 5
    THICKNESS = 3

    def create_with_heat_inserter_set(self) -> Part:
        half_pipe = self._create_half_pipe()
        return half_pipe

    def create_with_counter_hole(self) -> Part:
        half_pipe = self._create_half_pipe()
        return half_pipe

    def _create_half_pipe(self) -> Part:
        body = self._create_body()
        sphere = self._create_sphere()
        mounting_post = self._create_mounting_post_cylinder()
        neg_half_box = Pos(X=-100) * Box(200, 200, 200)
        return body - sphere - mounting_post - neg_half_box

    def _create_body(self) -> Part:
        h = self.MOUNTING_POST_HEIGHT + self.HEAT_SET_HEIGHT + 2 * self.SPHERE_RADIUS * self.SPHERE_COMPLETENESS
        r = max(self.MOUNTING_POST_RADIUS, self.SPHERE_RADIUS) + self.THICKNESS
        return Pos(Z=h/2) * Cylinder(radius=r, height=h)
    
    def _create_sphere(self) -> Part:
        dz = self.MOUNTING_POST_HEIGHT + self.HEAT_SET_HEIGHT + self.SPHERE_RADIUS
        return Pos(Z=dz) * Sphere(self.SPHERE_RADIUS)
    
    def _create_mounting_post_cylinder(self) -> Part:
        h = self.MOUNTING_POST_HEIGHT
        r = self.MOUNTING_POST_RADIUS
        return Pos(Z=h/2) * Cylinder(radius=r, height=h)


class FingerSphereCreator:
    SPHERE_RADIUS = 12
    CYLINDER_RADIUS = 7
    CYLINDER_EXTRA_HEIGHT = 5  # len beyond sphere
    SCREW = data.FLAT_HEAD_SCREW_M5
    HEAT_INSERTER_HEIGHT = 12
    HOLE_EXTRA_DEPTH = 5

    def create(self) -> Part:
        sphere_dz = self.SPHERE_RADIUS + self.CYLINDER_EXTRA_HEIGHT
        sphere = Pos(Z=sphere_dz) * Sphere(self.SPHERE_RADIUS)

        cyl_height = self.SPHERE_RADIUS + self.CYLINDER_EXTRA_HEIGHT
        cylinder = Pos(Z=cyl_height / 2) * Cylinder(radius=self.CYLINDER_RADIUS, height=cyl_height)

        hole_deep = self.HEAT_INSERTER_HEIGHT + self.HOLE_EXTRA_DEPTH
        hole = Rot(X=180) * CounterBoreHole(radius=self.SCREW.hole_radius,
                                            counter_bore_radius=self.SCREW.head_set_insert_radius,
                                            counter_bore_depth=self.HEAT_INSERTER_HEIGHT,
                                            depth=hole_deep)
        
        part = sphere + cylinder - hole  # - Pos(X=50) * Box(100, 100, 100)

        if WRITE_ENABLED:
            export_stl(part, OUTPUT_DPATH / 'finger-base-sphere.stl')

        return part
    

if __name__ == '__main__':
    main()
