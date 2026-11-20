# Видеокарта, стоит вертикально вентиляторами к стеклу. Местные оси: X длина, Y высота (от разъёма к верхней кромке), Z толщина.
from math import sin, cos, tau, radians
import bpy
from kit import Part, rrect, circ, slot, bezier, anchor
from layout import *
from fan import blade_rows
from board import atx_conn, UPX, UPY

FANS_X = (54.0, 150.0, 246.0)
FAN_Y = 62.5
FAN_R = 45.0


def make_gpu(pc):
    g = Part('gpu', at=GPU_AT, rot=(90, 0, 0), parent=pc)
    Lg, Hg, Tg = GPU_L, GPU_H, GPU_T

    # --- задняя пластина
    bp_holes = [slot(46, 3.2, 5, 60 + i * 9, 30 + j * 9) for i in range(0, 1) for j in range(0)]
    for j in range(6):
        bp_holes.append(rrect(70 - j * 6, 2.6, 1.2, 3, 228 + j * 3, 22 + j * 7.5))
    bp_holes.append(rrect(46, 46, 4, 4, 112, 62))
    g.plate('alu_black', [(0, 0), (Lg, 0), (Lg, Hg - 10), (Lg - 10, Hg), (0, Hg)], bp_holes, 1.8, bevel=0.3)
    g.text('print_white', 'VELOCITY', 11.0, at=(64, 98, -0.04), rot=(180, 0, 0), depth=0.08, spacing=1.5, align='LEFT')
    g.text('print_grey', 'ATELIER  ·  16 GB', 3.4, at=(64, 84, -0.03), rot=(180, 0, 0), depth=0.06, spacing=1.6, align='LEFT')
    g.box('steel_dark', (44, 44, 1.2), at=(112, 62, 2.2), bevel=0.3)   # крестовина за чипом
    for x, y in ((6, 6), (6, Hg - 6), (Lg - 8, 6), (150, 6), (150, Hg - 6), (Lg - 14, Hg - 6)):
        g.screw(at=(x, y, 0), rot=(180, 0, 0), d=4.2, kind='hex')

    # --- плата и контакты
    g.box('pcb', (Lg - 12, Hg - 14, 1.6), at=(Lg / 2 - 4, Hg / 2 - 5, 4.8), bevel=0.1)
    g.box('pcb', (86, 9, 1.6), at=(86, -3.5, 4.8))
    for k in range(40):
        g.box('gold', (1.2, 7.0, 1.7), at=(46 + k * 2.0 + (4 if k > 6 else 0), -4.0, 4.8))

    # --- рёбра радиатора и тепловые трубки
    n = int((Lg - 26) / 2.1)
    for k in range(n):
        g.box('alu_silver', (0.4, Hg - 16, 31), at=(14 + k * 2.1, Hg / 2 - 1, 24.5))
    for j, y in enumerate((20, 38, 56, 74, 92, 108)):
        g.pipe('nickel', [(10, y, 12), (Lg - 10, y, 12)], 3.0, seg=14)
    for y0, y1 in ((20, 38), (56, 74), (92, 108)):
        pts = [(Lg - 10 + 8 * sin(radians(a)), (y0 + y1) / 2 - (y1 - y0) / 2 * cos(radians(a)), 12) for a in range(0, 181, 15)]
        g.pipe('nickel', pts, 3.0, seg=14)
    g.box('copper', (60, 60, 4), at=(112, 62, 8.0), bevel=0.4)

    # --- кожух: лицевая панель с тремя окнами
    outline = [(4, 0), (Lg - 16, 0), (Lg, 14), (Lg, Hg - 22), (Lg - 20, Hg), (22, Hg), (4, Hg - 16)]
    holes = [circ(FAN_R, 96, x, FAN_Y) for x in FANS_X]
    g.plate('plastic_black', outline, holes, 5.0, z0=Tg - 9.0, bevel=0.7)
    # кольца-воздуховоды
    for x in FANS_X:
        g.lathe('plastic_black', [(FAN_R, Tg - 4.0), (FAN_R + 2.2, Tg - 4.0), (FAN_R + 2.2, Tg - 16), (FAN_R, Tg - 16)],
                at=(x, FAN_Y, 0), seg=96, closed=True)
        g.lathe('alu_dark', [(FAN_R + 0.3, Tg - 4.0), (FAN_R + 2.6, Tg - 4.0), (FAN_R + 2.2, Tg - 3.3), (FAN_R + 0.6, Tg - 3.3)],
                at=(x, FAN_Y, 0), seg=96, closed=True)
    # накладки между окнами: гранёные вставки и световые шевроны
    for xm in (102.0, 198.0):
        for s in (1, -1):
            yc = FAN_Y + s * 44
            pts = [(-24, s * 12), (24, s * 12), (10, -s * 9), (-10, -s * 9)]
            g.prism('alu_dark', pts if s > 0 else pts[::-1], 1.6, at=(xm, yc, Tg - 4.0), bevel=0.4)
            g.prism('led_accent', [(-7, 0), (0, -s * 5), (7, 0), (7, s * 1.6), (0, -s * 3.4), (-7, s * 1.6)][::s],
                    0.8, at=(xm, yc - s * 13, Tg - 4.0))
    for k in range(7):
        g.box('plastic_gloss', (1.0, 15, 0.6), at=(12 + k * 2.6, Hg - 34 + k * 2.2, Tg - 3.9), rot=(0, 0, 0))
    g.text('print_grey', 'VELOCITY', 5.0, at=(Lg - 46, 9, Tg - 3.96), depth=0.06, spacing=1.6)
    # стенки кожуха
    g.box('plastic_black', (Lg - 24, 2.4, Tg - 15), at=(Lg / 2 - 4, 1.2, (Tg - 9 + 6) / 2), bevel=0.4)
    g.prism('plastic_black', [(0, 6), (0, Tg - 9), (-2.4, Tg - 9), (-2.4, 6)], Lg - 44, at=(22, Hg, 0), rot=UPY, bevel=0.4)
    g.box('plastic_black', (2.4, Hg - 24, Tg - 15), at=(Lg - 1.2, Hg / 2 - 4, (Tg - 9 + 6) / 2), bevel=0.4)
    # верхняя кромка: световая полоса и надпись
    with g.at((0, Hg, 0)):
        g.box('alu_dark', (150, 1.0, 16), at=(96, 0.5, 26), bevel=0.3)
        g.box('led_gpu', (120, 0.8, 1.4), at=(96, 1.0, 20.5))
        g.text('led_gpu', 'VELOCITY', 8.2, at=(96, 1.02, 28.5), rot=(-90, 0, 0), depth=0.3, spacing=1.6)
    # питание: два разъёма 8-pin на верхней кромке
    for x in (212.0, 240.0):
        with g.at((x, Hg - 12.6, 22), (-90, 0, 0)):
            atx_conn(g, 0, 0, 4, 2, h=12.5)
    # стойки моторов
    for x in FANS_X:
        g.lathe('plastic_black', [(0, Tg - 17.5), (14, Tg - 17.5), (14, Tg - 13.5), (0, Tg - 13.5)], at=(x, FAN_Y, 0), seg=40)
        for k in range(3):
            a = radians(90 + 120 * k)
            g.pipe('plastic_black', [(x + 12 * cos(a), FAN_Y + 12 * sin(a), Tg - 15.5),
                                     (x + (FAN_R + 1) * cos(a + 0.3), FAN_Y + (FAN_R + 1) * sin(a + 0.3), Tg - 15.5)], 1.8, seg=8, flat=0.6)

    # --- планка крепления (у задней стенки корпуса)
    with g.at((0, 0, 0), UPY):
        g.plate('steel_dark', [(-12, -2), (Hg + 8, -2), (Hg + 8, 40), (-12, 40)],
                [slot(18, 3, 5, 24 + i * 24, 30) for i in range(4)] + [rrect(16, 6, 1, 3, 30 + i * 22, 12) for i in range(4)],
                1.0, z0=-1.0, bevel=0.2)
    g.build()

    # --- роторы
    rows = blade_rows(13.6, FAN_R - 2.6, blades_span=360.0 / 11 * 0.94, pitch0=9.0, pitch1=6.5, sweep=30.0, ns=12, nc=10,
                      tmax=1.1)
    first = None
    for i, x in enumerate(FANS_X):
        r = Part('rotor_gpu%d' % (i + 1), at=(x, FAN_Y, Tg - 9.0), parent=g)
        if first is None:
            r.lathe('fan_hub', [(0, 4.2), (12.2, 4.2), (14, 3.2), (14, -3.6), (0, -3.6)], seg=56)
            r.lathe('alu_dark', [(0, 4.2), (10.5, 4.2), (10.5, 4.4), (0, 4.4)], seg=48)
            r.lathe('print_accent', [(8.2, 4.4), (9.0, 4.4), (9.0, 4.46), (8.2, 4.46)], seg=48, closed=True)
            r.text('print_white', 'V', 8.5, at=(0, 0.2, 4.44), depth=0.06)
            for k in range(11):
                r.grid('fan_blade', rows, rot=(0, 0, 360.0 * k / 11), close_v=True, cap=True)
            r.lathe('fan_blade', [(FAN_R - 2.9, -3.2), (FAN_R - 1.6, -3.2), (FAN_R - 1.6, 2.6), (FAN_R - 2.9, 2.6)], seg=96,
                    closed=True)
            r.build()
            first = r
        else:
            for o in first.objects:
                c = o.copy()
                bpy.context.scene.collection.objects.link(c)
                c.parent = r.root
    anchor('a_gpu', (150, FAN_Y, Tg), parent=g)

    # --- подставка и шлейф к слоту платы (мировые координаты)
    m = Part('gpu_mount', parent=pc)
    gx0, gy, gz = GPU_AT
    m.box('steel_black', (250, 46, 3), at=(gx0 + 135, gy - 18, SHROUD + 1.5), bevel=0.5)
    m.box('steel_black', (250, 3, 12), at=(gx0 + 135, gy + 4.5, SHROUD + 6), bevel=0.4)
    m.box('slot_plastic', (92, 9, 11), at=(gx0 + 88, gy - 4.8, SHROUD + 8.5), bevel=0.3)
    for sx in (40, 230):
        m.screw(at=(gx0 + sx, gy - 34, SHROUD + 3), d=6.5)
    slot_z = BOARD_Z + 136
    path = bezier((gx0 + 88, gy + 8, SHROUD + 5), (gx0 + 88, gy + 60, SHROUD + 3), (gx0 + 88, YB - 26, SHROUD + 30),
                  (gx0 + 88, YB - 22, slot_z - 40), 18) + [(gx0 + 88, YB - 20, slot_z - 8)]
    m.pipe('rubber', path, 42.0, seg=16, flat=0.02, up=(1, 0, 0))
    m.box('slot_plastic', (90, 8, 14), at=(BOARD_X + 105, YB - 17, slot_z), bevel=0.3)
    m.build()
    return g
