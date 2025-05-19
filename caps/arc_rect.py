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
    ry = params.radius_front_back
    rx = params.radius_left_right

    rect = Pos(Y=h2 - ry) * Circle(ry) & Pos(Y=ry - h2) * Circle(ry) & Pos(X=w2 - rx) * Circle(rx) & Pos(X=rx - w2) * Circle(rx)
    return fillet(rect.vertices(), params.radius_corner)


def create_arc_rect_variant(width: float, height: float, params: ArcRectParameters) -> Sketch:
    """
        * * * 
      *       *
       *       *
        *      *
         *     *
         *    *
         *  *

    """
    w2 = width / 2
    h2 = height / 2
    ry = params.radius_front_back
    rx = params.radius_left_right

    rect = Pos(Y=h2 - ry) * Circle(ry) & Pos(Y=ry - h2) * Circle(ry) & Pos(X=w2 - rx) * Circle(rx) - Pos(X=-2 * rx - w2, Y=-h2) * Circle(2 * rx)
    return fillet(rect.vertices(), params.radius_corner)
