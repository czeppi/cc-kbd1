from build123d import extrude, Plane, Rectangle, Pos, Box, export_stl
from ocp_vscode import *
import copy


X_LEN = 20.0
Y_LEN = 30.0
Z_LEN = 10.0
SLOT_LEN = 2.0

THICKNESS = 2.0
TOLERANCE = 0.1
CUT_EPS = 0.01


def main():
    part = create_part()
    show_object(part)
    export_stl(part, 'interlock-part.stl')


def create_part():
    u_box = create_u_box()
    slot_box = create_slot_box()

    dy = X_LEN/2 - THICKNESS/2

    slot1 = Pos(Y=dy) * copy.copy(slot_box)
    slot2 = Pos(Y=-dy) * copy.copy(slot_box)

    return u_box - slot1 - slot2


def create_u_box():
    outer_box = Box(length=X_LEN, width=Y_LEN, height=Z_LEN)
    interior_box = Pos(Z=THICKNESS) * Box(length=X_LEN - 2 * THICKNESS, width=Y_LEN + CUT_EPS, height=Z_LEN)
    u_box = outer_box - interior_box 
    return Pos(Z=-Z_LEN/2 + SLOT_LEN) * u_box  # slot begins in the xy-plane


def create_slot_box():
    z_len = SLOT_LEN + CUT_EPS
    y_len = THICKNESS + TOLERANCE
    x_len = X_LEN + CUT_EPS

    slot_box = Box(length=x_len, width=y_len, height=z_len)
    return Pos(Z=z_len/2) * slot_box


main()