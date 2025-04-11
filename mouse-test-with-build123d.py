from build123d import Rot, BuildPart, BuildSketch, Rectangle, extrude, offset, ShellKind, shell, Plane, cut_thru_all
from ocp_vscode import show_object

length = 110
width = 65
height = 40
slope_deg = 15

# slopiness as operation
tilt = Rot(0, slope_deg, 0)

with BuildPart() as mouse_body:
    with BuildSketch() as base:
        Rectangle(length, width, radius=12)
    extrude(amount=height, rotation=tilt)
    
    # the inside
    offset(amount=-2)  # thickness = 2mm
    shell(thickness=-2, kind=ShellKind.OUTSIDE)
    
    with BuildSketch(Plane.XY.offset(0.5)) as sensor_hole:
        Rectangle(15, 12)
    cut_thru_all()
    
show_object(mouse_body.part)