# Кабели питания в оплётке: 24-pin, питание процессора, питание видеокарты. Мировые координаты корпуса.
from kit import Part, bezier, rrect
from layout import *

WIRE = 1.85


def wire(p, a, b, c, d, accent=False, n=30):
    p.pipe('sleeve_accent' if accent else 'sleeve_black', bezier(a, b, c, d, n), WIRE, seg=10, uv=7.0)


def comb(p, pts_a, pts_b, t, n=12, rows=2):
    """Гребёнка: планка, охватывающая пучок в точке t."""
    pass


def make_cables(pc):
    c = Part('cables', parent=pc)
    gx = BOARD_X + BOARD_W + 28          # ось вырезов поддона

    # --- 24-pin
    cx, cz = BOARD_X + 235.5, BOARD_Z + 218
    ytop = YB - 12.5
    c.box('plastic_black', (11.4, 17.0, 53.0), at=(cx, ytop - 8.2, cz), bevel=0.6)
    c.box('plastic_black', (2.2, 13.0, 9.0), at=(cx + 6.6, ytop - 5.5, cz), bevel=0.4)
    gz = BOARD_Z + 175
    for i in range(12):
        z = cz - 23.1 + i * 4.2
        ze = gz - 27.5 + i * 5.0
        acc = i in (2, 3, 8, 9)
        wire(c, (cx + 2.1, ytop - 16, z), (cx + 2.1, ytop - 58, z), (gx - 2.4, TRAY - 62, ze), (gx - 2.4, TRAY + 4, ze), acc)
        wire(c, (cx - 2.1, ytop - 16, z), (cx - 2.1, ytop - 68, z), (gx + 2.4, TRAY - 72, ze), (gx + 2.4, TRAY + 4, ze), acc)
    # гребёнки
    for t_y, xs in ((ytop - 30, (cx - 2.1, cx + 2.1)),):
        c.plate('plastic_gloss', rrect(11.5, 54.5, 1.5, 3, cx, cz), [], 0.01) if False else None
        c.box('plastic_gloss', (10.6, 3.0, 54.0), at=(cx, t_y, cz), bevel=0.4)
    c.box('plastic_gloss', (10.6, 3.0, 62.0), at=(gx, TRAY - 22, gz + 0.0), bevel=0.4)

    # --- питание процессора 8+4
    ez = BOARD_Z + 298.5
    tx, tz = XR + 150, Z1 - 24
    k = 0
    for x0, cols in ((BOARD_X + 44, 4), (BOARD_X + 62.5, 2)):
        w = cols * 4.2 + 1.8
        c.box('plastic_black', (w, 16.0, 10.6), at=(x0, ytop - 7.8, ez), bevel=0.5)
        for i in range(cols):
            x = x0 - (cols - 1) * 2.1 + i * 4.2
            for j, dz in enumerate((2.1, -2.1)):
                xe = tx - 26 + k * 4.6
                wire(c, (x, ytop - 15, ez + dz), (x, ytop - 37 - j * 5, ez + dz + 10), (xe, 44 - j * 5, tz - 22 + dz),
                     (xe, TRAY + 4, tz + dz), accent=(i == 1 and cols == 4))
            k += 1

    # --- питание видеокарты 2×8
    gx0, gy, gz0 = GPU_AT
    ztop = gz0 + GPU_H
    yrow = gy - 22
    ex, ey = gx - 8, TRAY - 20      # вырез в кожухе
    k = 0
    for cxg in (gx0 + 212, gx0 + 240):
        c.box('plastic_black', (18.6, 10.6, 16.0), at=(cxg, yrow, ztop + 8.4), bevel=0.5)
        for i in range(4):
            x = cxg - 6.3 + i * 4.2
            for j, dy in enumerate((-2.1, 2.1)):
                xe = ex - 7 + (k % 4) * 4.6
                ye = ey - 16 + (k // 4) * 4.6 + j * 18
                wire(c, (x, yrow + dy, ztop + 15.5), (x, yrow + dy, ztop + 60 + j * 9), (xe, ye - 6, SHROUD + 96 + j * 9),
                     (xe, ye, SHROUD - 4), accent=(i in (1, 2)), n=34)
            k += 1
    c.build()
    return c
