import math
from typing import Iterator
from build123d import offset, export_stl, loft, make_face, extrude
from build123d import Box, Cylinder, Part, Rectangle, Pos, Rot, Sphere, PolarLocations
from ocp_vscode import show_object

from base import STUD_HEIGHT, STUD_RADIUS, TOLERANCE, OUTPUT_DPATH


def main():
    creator = TrackballHolder()
    holder = creator.create()
    show_object(holder)


class TrackballHolder:

    def create(self) -> Part:
        # polar_locs = PolarLocations(radius=5, count=3)
        outer_sphere = Sphere(radius=20.0)
        inner_sphere = Sphere(radius=18.0)
        neg_box = Pos(Z=50) * Box(100, 100, 100)
        result = outer_sphere - inner_sphere - neg_box

        loc = Rot(X=-30) * Pos(Y=20) * Rot(X=90)
        
        outer_cyl = loc * Cylinder(radius=3, height=5) 
        inner_cyl = loc * Cylinder(radius=2, height=6)

        for angle in [0, 120, 240]:
            result += Rot(Z=angle) * outer_cyl
            result -= Rot(Z=angle) * inner_cyl

        #foot = Box(30, 30, 5) - Pos(Z=-1) * Box(20, 20, 3)
        result += Pos(Z=-20) * Box(30, 30, 5)
        result -= Pos(Z=-21) * Box(20, 20, 3)

        result -= Cylinder(radius=5, height=100)
        
        return result
    

main()
