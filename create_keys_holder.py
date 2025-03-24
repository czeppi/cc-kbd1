from typing import Any

import cadquery as cq

CUT_WIDTH = 13.9
LEFT_RIGHT_BORDER = 1.0
FRONT_BORDER = 3.0
BACK_BORDER = 3.2  # 2.7 is minimum
OVERLAP = 1.0
THICKNESS = 2.0
RIM_DZ = 3.0
RIM_DY = 2.0


type Solid = Any  # don't know the correct type


class KeyPairHolderCreator:

    def __init__(self):
        self._frame_dx = LEFT_RIGHT_BORDER + CUT_WIDTH + LEFT_RIGHT_BORDER
        self._frame_dy = FRONT_BORDER + CUT_WIDTH + BACK_BORDER

    def create(self) -> Solid:
        front_frame = self._create_front_frame()
        rim_box = self._create_rim_box()
        front_part = front_frame.union(rim_box)
        back_part = self._create_back_part(front_part)
        return front_part.union(back_part).union(rim_box)

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


holder = KeyPairHolderCreator().create()
show_object(holder)
