from dataclasses import dataclass
from build123d import fillet, mirror, make_face
from build123d import Pos, Sketch, Circle
from ocp_vscode import show_object


@dataclass
class ArcRectParameters:
    radius_horizontal: float
    radius_vertical: float
    radius_corner: float


def create_arc_rect(width: float, height: float, radius_horziontal: float, radius_vertical: float, radius_corner: float) -> Sketch:
    w2 = width / 2
    h2 = height / 2
    rh = radius_horziontal
    rv = radius_vertical

    rect = Pos(Y=h2 - rh) * Circle(rh) & Pos(Y=rh - h2) * Circle(rh) & Pos(X=w2 - rv) * Circle(rv) & Pos(X=rv - w2) * Circle(rv)
    return fillet(rect.vertices(), radius_corner)


def create_arc_rect2(width: float, height: float, params: ArcRectParameters) -> Sketch:
    return create_arc_rect(width=width, 
                           height=height, 
                           radius_horziontal=params.radius_horizontal, 
                           radius_vertical=params.radius_vertical,
                           radius_corner=params.radius_corner)
