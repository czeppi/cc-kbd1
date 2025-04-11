from build123d import BuildPart, Box
from ocp_vscode import show_object

length, width, thickness = 80.0, 60.0, 10.0

with BuildPart() as the_box:
    Box(length, width, thickness)

show_object(the_box)