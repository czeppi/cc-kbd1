import cadquery as cq
import math

r = 2.5
border = 4
dx = 9
dy = dx * math.sin(60 * math.radians)
x0 = border + r
y0 = border + r
x_offset = dx * math.cos(60 * math.radians)

n = 7
m = 13

box_width = border + r + (m - 1) * dx + r + x_offset + border
box_height = border + r + (n - 1) * dy + r + border
box_thickness = 4
print(box_width, box_height)


box = (
       cq.Workplane("XY").box(box_width, box_height, box_thickness)
       .translate((box_width / 2, box_height / 2, box_thickness / 2))
      )

points = []
for i in range(n):
    for j in range(m):
        x = x0 + j * dx
        y = y0 + i * dy
        if  i % 2 == 1:
            x += x_offset
        points.append((x, y))
        
box = box.faces(">Z").workplane().pushPoints(points).hole(2 * r)
cq.exporters.export(box, 'base-plate.stl')