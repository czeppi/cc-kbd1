from dataclasses import dataclass


@dataclass
class FlatHeadScrew:
    head_radius: float
    head_height: float
    radius: float
    head_set_insert_radius: float

    @property
    def hole_radius(self) -> float:
        return self.radius + 0.2


FLAT_HEAD_SCREW_M2 = FlatHeadScrew(
    head_radius = 2.0,  # measured 1.9
    head_height = 1.0,  # measured: 0.87
    radius = 1.0,  # measured: 0.96
    head_set_insert_radius = 1.5
)


FLAT_HEAD_SCREW_M2_5 = FlatHeadScrew(
    head_radius = 2.25,  # measured 2.13
    head_height = 1.0,  # measured: 0.87
    radius = 1.25,
    head_set_insert_radius = 1.65
)


FLAT_HEAD_SCREW_M5 = FlatHeadScrew(
    head_radius = 10.0,  # measured 9.8
    head_height = 2.6,  # measured: 2.55
    radius = 2.5,  # measured: 4.92
    head_set_insert_radius = 3.2  # 3.05 < x < 3.5
)
