cut_width = 13.9
left_right_border = 1.0
front_border = 3.0
back_border = 3.2  # 2.7 is minimum
overlap = 1.0
thickness = 2.0
rim_dz = 3.0
rim_dy = 2.0

frame_dy = front_border + cut_width + back_border
frame_dx = left_right_border + cut_width + left_right_border

front_frame = (
    cq.Workplane("XY")
    .box(frame_dx, frame_dy + overlap, thickness)
    .translate((0, (frame_dy + overlap) / 2 - front_border - cut_width/2, -thickness/2))
    .faces(">Z").workplane()
    .rect(cut_width, cut_width).cutThruAll()
    .translate((0, -cut_width/2 - back_border))
)

rim_box = (
    cq.Workplane("XY")
    .box(frame_dx, rim_dy, rim_dz)
    .translate((0, rim_dy/2 - frame_dy, -rim_dz/2 - thickness))
)

front_part = front_frame.union(rim_box)

back_part = (
    front_part
    .rotate((0, 0, 0), (0, 0, 1), 180)
    .rotate((0, 0, 0), (1, 0, 0), 30)
)

result = front_part.union(back_part).union(rim_box)

# Render the solid
show_object(result)
