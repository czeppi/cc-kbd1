import math
from pathlib import Path
from build123d import mirror, extrude, offset, export_stl
from build123d import Box, Cylinder, Part, Rectangle, Pos, Rot, Kind, Polygon, Plane, Wedge, Axis, RigidJoint, Location, Circle, Align
from ocp_vscode import show_object


TOLERANCE = 0.1
DEGREE = math.pi / 180

SKELETON_WIDTH = 18.0
SKELETON_HEIGHT = 10.0
SKELETON_THICKNESS = 2.0

SLOT_HEIGHT = 10.0
FOOT_HEIGHT = 10.0

STUD_RADIUS = 5.0 / 2 - TOLERANCE
STUD_HEIGHT = 4.0 - TOLERANCE

HOLDER_ANGLE = 30.0  # degree

OUTPUT_DPATH = Path('output')


def main():
    creator = SkeletonHolderCreator()
    holder = creator.create()
    export_stl(holder, OUTPUT_DPATH / 'skeleton-holder.stl')

    #holder = extrude(Rectangle(3, 4), 5)
    #holder = Wedge(5, 2, 5, xmin=0, xmax=1, zmin=0, zmax=5)

    #holder = Plane(origin=(0,0,0), z_dir=(0,1,1)) * Cylinder(radius=5, height=2)

    show_object(holder)


class SkeletonHolderCreator:
    """
    view from top:

         x x x x x x x x
         x             x
         x   x x x x   x
         x   x     x   x
         x x x     x x x
    
    """

    def __init__(self):
        pass

    def create(self) -> Part:
        u_shell = self._create_u_shell()
        wedge = self._create_wedge()
        return u_shell + wedge

    def _create_u_shell(self) -> Part:
        """

            x x x     x x x
            x   x     x   x
            x   x x x x   x
            x             x
            x x x x x x x x
        """
        skeleton_rect = Rectangle(width=SKELETON_WIDTH, 
                                  height=SKELETON_HEIGHT)
        
        skeleton_hole = Pos(Y=SKELETON_THICKNESS / 2) * Rectangle(width=SKELETON_WIDTH - 2 * SKELETON_THICKNESS, 
                                                                  height=SKELETON_HEIGHT - SKELETON_THICKNESS)
        skeleton_u = skeleton_rect - skeleton_hole
        skeleton_u_plus = offset(skeleton_u, TOLERANCE, kind=Kind.INTERSECTION)
        skeleton_shell = offset(skeleton_u_plus, SKELETON_THICKNESS, kind=Kind.INTERSECTION) - skeleton_u_plus

        #h = skeleton_shell.bounding_box().size.Y
        return extrude(skeleton_shell, SLOT_HEIGHT)
    
    def _create_wedge_old1(self):
        r = SKELETON_WIDTH + 2 * TOLERANCE + 2 * SKELETON_THICKNESS
        x3 = r * math.cos(HOLDER_ANGLE * DEGREE)
        y3 = r * math.sin(HOLDER_ANGLE * DEGREE)
        points = [(0.0, 0.0), (r, 0.0), (x3, y3)]

        polygon = Polygon(points)
        height = SKELETON_HEIGHT  + 2 * TOLERANCE + 2 * SKELETON_THICKNESS
        wedge = extrude(polygon, height)
        return Plane.YZ * wedge

    def _create_wedge_old1(self):
        length = SKELETON_WIDTH + 2 * TOLERANCE + 2 * SKELETON_THICKNESS
        width = SKELETON_HEIGHT + 2 * TOLERANCE + 2 * SKELETON_THICKNESS
        height = FOOT_HEIGHT

        box = Box(length=length, width=width, height=height)
        cut_height = length * math.tan(math.radians(HOLDER_ANGLE))
        wedge = Box(length=length, width=2 * width, height=cut_height).rotate(Axis.X, 90).translate((0, -width/2, height))
        sloped_body = box - wedge
        return sloped_body

    def _create_wedge(self):
        """
             /
            /     /
           /_____/   
            |__|   <- stud

          HOLDER_ANGLE: angle of holder
          FOOT_HEIGHT:  from top of stud till mid of slope

          rotate =>
           
           y
           |
           | 
           |----   
           |    *
           |     *
           -------*---> x

        """
        y_len = SKELETON_WIDTH + 2 * TOLERANCE + 2 * SKELETON_THICKNESS
        z_len = SKELETON_HEIGHT + 2 * TOLERANCE + 2 * SKELETON_THICKNESS

        angle_rad = math.radians(HOLDER_ANGLE)
        
        x_mid_len = FOOT_HEIGHT / math.cos(angle_rad)
        x_delta = math.tan(angle_rad) * y_len / 2
        x_button = x_mid_len + x_delta
        x_top = x_mid_len - x_delta
         
        wedge = Wedge(x_button, y_len, z_len, xmin=0, xmax=x_top, zmin=0, zmax=z_len)
        wedge_slope_face = wedge.faces().sort_by(Axis.X).last

        wedge_slope_center = wedge_slope_face.center()
        wedge_slope_normal = wedge_slope_face.normal_at(wedge_slope_center)

        slope_plane = Plane(origin=wedge_slope_center, 
                            z_dir=wedge_slope_normal)

        stud = slope_plane * Cylinder(radius=STUD_RADIUS, height=STUD_HEIGHT, align=[Align.CENTER, Align.CENTER, Align.MIN])
        rotated_wedge = Rot(X=-90) * Rot(Z=90) * (wedge + stud)
        box = rotated_wedge.bounding_box()
        return Pos(Z=-box.max.Z) * rotated_wedge

    def old1(self):
        wedge_slope_face = wedge.faces().sort_by(Axis.X)[-1]
        wedge_joint_loc = wedge_slope_face.center()

        stud = Plane.YZ * Cylinder(radius=STUD_RADIUS, height=STUD_HEIGHT)
        stud_top_face = stud.faces().sort_by(Axis.X).last
        stud_joint_loc = stud_top_face.center()

        Location

        wedge_joint = RigidJoint(label="the", to_part=wedge, joint_location=wedge_joint_loc)
        stud_joint = RigidJoint(label="the", to_part=stud, joint_location=stud_joint_loc)
        
        wedge_joint.connect_to(stud_joint)

        wedge.fuse(stud_joint)
        return wedge


    def _create_stud(self) -> Part:
        stud = Cylinder(radius=STUD_RADIUS, height=STUD_HEIGHT)
        return stud


main()
