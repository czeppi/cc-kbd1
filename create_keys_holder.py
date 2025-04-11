import math
from dataclasses import dataclass
from typing import Any, Iterator

import cadquery as cq


CUT_WIDTH = 13.9
LEFT_RIGHT_BORDER = 3.0
FRONT_BORDER = 3.0
BACK_BORDER = 3.2  # 2.7 is minimum
OVERLAP = 1.0
THICKNESS = 2.0
RIM_DZ = 10 - THICKNESS
RIM_DY = 2.0


type Solid = Any  # don't know the correct type


@dataclass
class Vector3D:
    x: float
    y: float
    z: float

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y
        yield self.z
        
    def __repr__(self):
        return f'({self.x, self.y, self.z})'

    def get_list(self) -> list[float]:
        return [self.x, self.y, self.z]


@dataclass
class RelPosition:  # between two fingers
    move: Vector3D  # distances in mm
    rotate: Vector3D  # angles in degree  (rotation order y, x, z)

    # dx: float  # in mm
    # dy: float  # in mm
    # dz: float  # in mm
    # phi_x: float  # in degree
    # phi_y: float  # in degree
    # phi_z: float  # in degree


def calc_index_index_pos() -> RelPosition:
    """ calculate the relative position of the index finger, if I rotate it away from the middle finger"""
    dist_finger_root_key_center = 85  # mm
    key_width = 19.9
    key_height = 20  # mm
    key_gap = 0  # mm

    dx = (key_width + key_gap) / 2
    ry = dist_finger_root_key_center - key_height / 2
    
    phi_z_radian = -2 * math.atan(dx /ry)
    phi_z_degree = phi_z_radian * (180 / math.pi)
    
    dx = -ry * math.sin(phi_z_radian)
    dy = ry * math.cos(phi_z_radian) - ry

    return RelPosition(move=Vector3D(dx, dy, 0),
                       rotate=Vector3D(0, 0, phi_z_degree))


INDEX_INDEX_POS = calc_index_index_pos()
##INDEX_MIDDLE_POS = RelPosition(move=Vector3D(21, 5, 3), rotate=Vector3D(-7, 0, 0))
#INDEX_MIDDLE_POS = RelPosition(move=Vector3D(22, 9, 2.5), rotate=Vector3D(-8, 0, -1))
#MIDDLE_RING_POS = RelPosition(move=Vector3D(21, -8, -3), rotate=Vector3D(0, 0, -5))
#RING_PINKIE_POS = RelPosition(move=Vector3D(31, -20, -17), rotate=Vector3D(-25, 12, -8))
INDEX_MIDDLE_POS = RelPosition(move=Vector3D(22, 9, 2.5), rotate=Vector3D(-8, 0, -1))
MIDDLE_RING_POS = RelPosition(move=Vector3D(25.2, -8.7, -2.4), rotate=Vector3D(2, 0, 0))
RING_PINKIE_POS = RelPosition(move=Vector3D(28, -20, -16), rotate=Vector3D(14, 13, 4))


class KeyPairHolderCreator:

    def __init__(self):
        self._frame_dx = LEFT_RIGHT_BORDER + CUT_WIDTH + LEFT_RIGHT_BORDER
        self._frame_dy = FRONT_BORDER + CUT_WIDTH + BACK_BORDER

    def create(self) -> Solid:
        frame_dy = self._frame_dy
        front_frame = self._create_front_frame()
        rim_box = self._create_rim_box()
        front_part = front_frame.union(rim_box)
        back_part = self._create_back_part(front_part)
        holder = front_part.union(back_part).union(rim_box)
        return holder.translate((0, frame_dy/2, 0))

    def _create_front_frame(self) -> Solid:
        frame_dx = self._frame_dx
        frame_dy = self._frame_dy

        return (
            cq.Workplane("XY")
            .box(frame_dx, frame_dy + OVERLAP, THICKNESS)
            .translate((0, (frame_dy + OVERLAP) / 2 - FRONT_BORDER - CUT_WIDTH / 2, -THICKNESS / 2))
            .faces(">Z").workplane()
            .rect(CUT_WIDTH, CUT_WIDTH).cutThruAll()
            .translate((0, -CUT_WIDTH / 2 - BACK_BORDER))
        )

    def _create_rim_box(self) -> Solid:
        frame_dx = self._frame_dx
        frame_dy = self._frame_dy

        return (
            cq.Workplane("XY")
            .box(frame_dx, RIM_DY, RIM_DZ)
            .translate((0, RIM_DY / 2 - frame_dy, -RIM_DZ / 2 - THICKNESS))
        )

    @staticmethod
    def _create_back_part(front_part: Solid) -> Solid:
        return (
            front_part
            .rotate((0, 0, 0), (0, 0, 1), 180)
            .rotate((0, 0, 0), (1, 0, 0), 30)
        )


def translate_rel_keys_holder(start_keys_holder: Solid, rel_pos: RelPosition) -> Solid:
    return (
        start_keys_holder
        .rotate((0, 0, 0), (0, 1, 0), rel_pos.rotate.y)
        .rotate((0, 0, 0), (1, 0, 0), rel_pos.rotate.x)
        .rotate((0, 0, 0), (0, 0, 1), rel_pos.rotate.z)
        .translate(rel_pos.move.get_list())
    )

def create_loft_between_two_holders(left_holder: Solid, right_holder: Solid) -> Solid:
    return (
        left_holder
        .faces(">X")
        .wires().toPending()
        .add(right_holder)
        .faces("<X")
        .wires().toPending()
        .loft(combine=True)
    )

def create_key_holders_without_loft(index_finger_keys_holder: Solid, rel_positions: list[RelPosition]) -> Solid:
    cur_part = index_finger_keys_holder
    for rel_pos in reversed(rel_positions):
        moved_part = translate_rel_keys_holder(cur_part, rel_pos=rel_pos)
        cur_part = moved_part.union(index_finger_keys_holder)
    return cur_part

def create_whole_key_holder_with_loft(index_finger_keys_holder: Solid, rel_positions: list[RelPosition]) -> Solid:
    cur_part = index_finger_keys_holder
    for rel_pos in reversed(rel_positions):
        moved_part = translate_rel_keys_holder(cur_part, rel_pos=rel_pos)
        part_with_loft = create_loft_between_two_holders(index_finger_keys_holder, moved_part)
        cur_part = part_with_loft.union(index_finger_keys_holder)
    return cur_part

index_finger_keys_holder = KeyPairHolderCreator().create()

whole_key_holder = create_whole_key_holder_with_loft(index_finger_keys_holder, 
                                                     [INDEX_INDEX_POS, INDEX_MIDDLE_POS, MIDDLE_RING_POS, RING_PINKIE_POS])



#holder4 = index_finger_keys_holder

#holder4_moved = translate_rel_keys_holder(holder4, rel_pos=RING_PINKIE_POS)
#ring_pinkie_loft = create_loft_between_two_holders(index_finger_keys_holder, holder4_moved)
#holder34 = ring_pinkie_loft.union(index_finger_keys_holder)

#holder34_moved = translate_rel_keys_holder(holder34, rel_pos=MIDDLE_RING_POS)
#middle_ring_loft = create_loft_between_two_holders(index_finger_keys_holder, holder34_moved)
#holder234 = middle_ring_loft.union(index_finger_keys_holder)

#holder234_moved = translate_rel_keys_holder(holder234, rel_pos=INDEX_MIDDLE_POS)
#index_middle_loft = create_loft_between_two_holders(index_finger_keys_holder, holder234_moved)
#holder1234 = index_middle_loft.union(index_finger_keys_holder)

#holder1234_moved = translate_rel_keys_holder(holder1234, rel_pos=INDEX_INDEX_POS)
#index_index_loft = create_loft_between_two_holders(index_finger_keys_holder, holder1234_moved)
#holder01234 = index_index_loft.union(index_finger_keys_holder)

#index_middle_loft = create_loft_between_two_holders(index_finger_keys_holder, middle_finger_keys_holder)

cq.exporters.export(whole_key_holder, 'key-holder.stl')
show_object(whole_key_holder)


