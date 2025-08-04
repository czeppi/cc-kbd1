from finger_parts_common import LEFT_RIGHT_BORDER, CUT_WIDTH, SwitchPairHolderFingerLocations
from hot_swap_socket import SwitchPairHolderCreator


from build123d import Box, Circle, Compound, Cylinder, Edge, Part, Plane, Pos, Solid, Sphere, Vector, sweep
from ocp_vscode import show_object


import copy
from pathlib import Path
from typing import Iterator


def main():
    creator = CaseAssemblyCreator()
    case_assembly = creator.create()
    show_object(case_assembly)


class CaseAssemblyCreator:

    def __init__(self):
        self._skeleton: Part | None = None
        self._holders: list[Solid] = None

    def create(self) -> Compound:
        self._skeleton = SkeletonCreator2().create()
        children = [self._skeleton] + list(self._iter_switch_holders())
        return Compound(label="case_assembly", children=children)

    def _iter_switch_holders(self) -> Iterator[Compound]:
        loc = SwitchPairHolderFingerLocations()

        # y2 = 11.36  # SwitchPairHolderCreator._create_middle_profile_face()#y2
        # holder = Box(14, 2 * y2, 5)

        holder_parts = SwitchPairHolderCreator().create()

        yield loc.index * Pos(X=-14) * Compound(label='index2', children=copy.copy(holder_parts))
        yield loc.index * Compound(label='index', children=copy.copy(holder_parts))
        yield loc.middle * Compound(label='middle', children=copy.copy(holder_parts))
        yield loc.ring * Compound(label='ring', children=copy.copy(holder_parts))
        yield loc.pinkie * Compound(label='pinkie', children=copy.copy(holder_parts))

    def save(self, output_path: Path) -> None:
        raise NotImplementedError()


class SkeletonCreator2:
    TUBE_OUTER_RADIUS = 8
    TUBE_INNER_RADIUS = 5
    BASE_HOLDER_DISTANCE = 4
    BASE_OFFSET = 0.5  # make base position a little bit above the tube

    def __init__(self):
        self._dz = SwitchPairHolderCreator.MIDDLE_PART_HEIGHT_AT_CENTER + self.BASE_HOLDER_DISTANCE + self.BASE_OFFSET + self.TUBE_OUTER_RADIUS

    def create(self) -> Part:
        spline_edge = self._create_spline_edge()
        outer_tube = self._create_tube(r=self.TUBE_OUTER_RADIUS, spline_edge=spline_edge)
        inner_tube = self._create_tube(r=self.TUBE_INNER_RADIUS, spline_edge=spline_edge)

        switch_bases = list(self._iter_switch_bases())
        sphere = self._create_sphere()
        sphere_handle = self._create_sphere_handle()

        skeleton_with_sphere = (outer_tube + switch_bases + sphere_handle + sphere) - inner_tube
        skeleton_with_sphere.label = 'skeleton'
        return skeleton_with_sphere

    def _create_spline_edge(self) -> Edge:
        loc = SwitchPairHolderFingerLocations()
        dz = self._dz
        holder_dx = LEFT_RIGHT_BORDER + CUT_WIDTH + LEFT_RIGHT_BORDER
        skeleton_start = loc.index * Pos(X=-3/2*holder_dx, Y=-5)
        skeleton_end = loc.pinkie * Pos(X=holder_dx/2+5, Y=-5)

        points = [#Vector(-30, -15, -dz), 
                  (skeleton_start * Pos(Z=-dz)).position,
                  (loc.index * Pos(X=-holder_dx/2, Z=-dz)).position,
                  (loc.middle * Pos(Z=-dz)).position,
                  (loc.ring * Pos(Z=-dz)).position,
                  (loc.pinkie * Pos(Z=-dz)).position,
                  (skeleton_end * Pos(Z=-dz)).position]

        return Edge.make_spline_approx(points=points, tol=0.01, max_deg=3)

    def _create_tube(self, r: float, spline_edge: Edge) -> Part:
        profile_template = Circle(1.0 * r)  # Circle(0.9 * r)
        profile_template2 = Circle(1.0 * r)  # Circle(1.1 * r)

        start_tangent = spline_edge%0
        x_dir = start_tangent.cross(Vector(0, 0, 1)).normalized()
        plane0 = Plane(origin=spline_edge@0, z_dir=start_tangent, x_dir=x_dir)
        profile0 = plane0 * profile_template

        end_tangent = spline_edge%1
        x_dir = end_tangent.cross(Vector(0, 0, 1)).normalized()
        plane1 = Plane(origin=spline_edge@1, z_dir=end_tangent, x_dir=x_dir)
        profile1 = plane1 * profile_template2

        return sweep([profile0, profile1], path=spline_edge, multisection=True)

    def _iter_switch_bases(self) -> Iterator[Part]:
        loc = SwitchPairHolderFingerLocations()

        base_height = 3
        base_len = 18
        index_base_width = 2 * base_len
        z_dist = SwitchPairHolderCreator.MIDDLE_PART_HEIGHT_AT_CENTER + self.BASE_HOLDER_DISTANCE + base_height / 2

        yield loc.index * Pos(X=(base_len - index_base_width) / 2, Z=-z_dist) * Box(index_base_width, base_len, base_height)
        yield loc.middle * Pos(Z=-z_dist) * Box(base_len, base_len, base_height)
        yield loc.ring * Pos(Z=-z_dist) * Box(base_len, base_len, base_height)
        yield loc.pinkie * Pos(Z=-z_dist) * Box(base_len, base_len, base_height)

    def _create_sphere(self) -> Part:
        loc = SwitchPairHolderFingerLocations()
        sphere_radius = 12
        dz = self._dz + self.TUBE_OUTER_RADIUS + sphere_radius + 1
        return loc.middle * Pos(Z=-dz) * Sphere(radius=sphere_radius)

    def _create_sphere_handle(self) -> Part:
        loc = SwitchPairHolderFingerLocations()
        handle_radius = 7
        dz = self._dz + self.TUBE_OUTER_RADIUS
        return loc.middle * Pos(Z=-dz) * Cylinder(radius=handle_radius, height=10)

    # def _find_t_in_spline(self, x0: float, spline: Edge) -> float:
    #     """ not used in the moment"""
    #     eps = 1e-3
    #     t1 = 0.0
    #     t2 = 1.0

    #     for i in range(100):
    #         t = (t1 + t2) / 2
    #         p = spline@t
    #         if abs(p.X - x0) < eps:
    #             return t
    #         if p.X < x0:
    #             t2 = t
    #         else:
    #             t1 = t
    #     else: 
    #         raise Exception('t not found in spline')


if __name__ == '__main__':
    main()
