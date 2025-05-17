from dataclasses import dataclass
from build123d import fillet, mirror, make_face
from build123d import Pos, Sketch, Circle
from ocp_vscode import show_object


@dataclass
class ArcRectParameters:
    radius_front_back: float
    radius_left_right: float
    radius_corner: float


def create_arc_rect(width: float, height: float, params: ArcRectParameters) -> Sketch:
    w2 = width / 2
    h2 = height / 2
    rh = params.radius_front_back
    rv = params.radius_left_right

    rect = Pos(Y=h2 - rh) * Circle(rh) & Pos(Y=rh - h2) * Circle(rh) & Pos(X=w2 - rv) * Circle(rv) & Pos(X=rv - w2) * Circle(rv)
    return fillet(rect.vertices(), params.radius_corner)
