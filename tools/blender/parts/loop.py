# Контур охлаждения: радиатор, резервуар с помпой, жёсткие трубки, фитинги. Мировые координаты корпуса.
from math import sin, cos, tau, radians
from kit import Part, rrect, circ, slot, hexagon, fillet, anchor
from layout import *


def fitting(p, at, rot, plug=False):
    """Компрессионный фитинг: основание, накатанная гайка, уплотнение. Ось +Z, z=0 — плоскость порта."""
    with p.at(at, rot):
        p.lathe('nickel', [(6.5, 0), (9.6, 0), (10.2, 0.6), (10.2, 3.4), (9.6, 4.0), (6.5, 4.0)], seg=48, closed=True)
        if plug:
            p.lathe('alu_black', [(0, 4.0), (9.0, 4.0), (9.4, 4.5), (9.4, 6.4), (8.6, 7.2), (0, 7.2)], seg=48)
            p.prism('void', hexagon(3.4), 0.5, z0=6.75)
            return
        n = 44
        pts = []
        for i in range(n * 2):
            rr = 10.9 if i % 2 == 0 else 10.35
            a = tau * i / (n * 2)
            pts.append((rr * cos(a), rr * sin(a)))
        p.plate('alu_black', pts, [circ(TUBE_R + 0.15, 40)], 9.6, z0=5.6)
        p.lathe('alu_black', [(TUBE_R + 0.15, 4.0), (10.3, 4.0), (10.3, 5.6), (TUBE_R + 0.15, 5.6)], seg=48, closed=True)
        p.lathe('alu_black', [(TUBE_R + 0.15, 15.2), (10.3, 15.2), (9.3, 16.6), (TUBE_R + 0.5, 16.6), (TUBE_R + 0.15, 16.2)],
                seg=48, closed=True)
        p.lathe('rubber', [(TUBE_R + 0.05, 16.2), (TUBE_R + 0.9, 16.3), (TUBE_R + 0.9, 16.9), (TUBE_R + 0.05, 17.0)], seg=40,
                closed=True)


def tube(p, pts, name=None):
    path = fillet(pts, 22.0, 12)
    p.pipe('glass_tube', path, TUBE_R, seg=28, caps=False)
    p.pipe('glass_tube', path, TUBE_R - 1.6, seg=24, caps=False)
    p.pipe('coolant', path, TUBE_R - 1.75, seg=20, caps=True)


def make_radiator(pc):
    r = Part('radiator', parent=pc)
    x0, x1, yc, z0 = RAD_X0, RAD_X1, RAD_Y, RAD_Z
    Hh, Wd = 27.0, 120.0
    S = 'steel_black'
    tank = 17.0
    cap_r = 9.0
    cx0, cx1 = x0 + cap_r, x1 - tank       # сердцевина
    # боковины
    for s in (1, -1):
        r.box(S, (x1 - x0, 1.6, Hh), at=((x0 + x1) / 2, yc + s * (Wd / 2 - 0.8), z0 + Hh / 2), bevel=0.3)
    # бачки
    r.box(S, (tank, Wd - 3.2, Hh - 1.0), at=(x1 - tank / 2, yc, z0 + Hh / 2), bevel=1.2)
    r.box(S, (cap_r, Wd - 3.2, Hh - 1.0), at=(x0 + cap_r / 2, yc, z0 + Hh / 2), bevel=1.2)
    r.text('print_grey', 'SBORKA 360', 5.0, at=(x1 - 0.02, yc, z0 + Hh / 2), rot=(90, 0, 90), depth=0.06, spacing=1.4)
    # фланцы с окнами под вентиляторы
    for zz in (z0, z0 + Hh - 1.2):
        holes = [rrect(cx1 - cx0 - 4, Wd - 14, 3, 4, (cx0 + cx1) / 2, yc)]
        for fx in TOP_FANS_X:
            for sx in (1, -1):
                for sy in (1, -1):
                    holes.append(circ(2.0, 10, fx + sx * 52.5, yc + sy * 52.5))
        r.plate(S, rrect(x1 - x0, Wd, 2, 3, (x0 + x1) / 2, yc), [], 0.01, z0=zz) if False else None
        r.plate(S, [(cx0 - 2, yc - Wd / 2), (cx1 + 2, yc - Wd / 2), (cx1 + 2, yc + Wd / 2), (cx0 - 2, yc + Wd / 2)], holes, 1.2,
                z0=zz, bevel=0.2)
    # винты вентиляторов сверху
    for fx in TOP_FANS_X:
        for sx in (1, -1):
            for sy in (1, -1):
                r.screw(at=(fx + sx * 52.5, yc + sy * 52.5, z0 + Hh), d=7.0, mat='steel_dark')
    # плоские трубки и гофрированные рёбра
    nt = 13
    pitch = (Wd - 16) / (nt - 1)
    for i in range(nt):
        y = yc - (Wd - 16) / 2 + i * pitch
        r.box('rad_core', (cx1 - cx0, 1.8, Hh - 5), at=((cx0 + cx1) / 2, y, z0 + Hh / 2))
    npl = int((cx1 - cx0) / 1.25)
    for i in range(nt - 1):
        ya = yc - (Wd - 16) / 2 + i * pitch + 0.9
        yb = ya + pitch - 1.8
        rows = []
        for zz in (z0 + 2.6, z0 + Hh - 2.6):
            rows.append([(cx0 + k * (cx1 - cx0) / npl, ya if k % 2 == 0 else yb, zz) for k in range(npl + 1)])
        r.grid('rad_fin', rows, recalc=False)
    # порты на переднем бачке
    for py in (T2_Y, RES[1]):
        r.lathe(S, [(6.5, 0), (11.5, 0), (11.5, -2.0), (6.5, -2.0)], at=(RES[0], py, z0 - 0.0), seg=40, closed=True)
        fitting(r, (RES[0], py, z0 - 2.0), (180, 0, 0))
    r.build()
    return r


def make_reservoir(pc):
    rx, ry = RES
    v = Part('reservoir', at=(rx, ry, 0), parent=pc)
    zb = SHROUD
    # основание
    v.prism('alu_black', rrect(84, 84, 8, 6), 4.0, z0=zb, bevel=0.6)
    for sx in (1, -1):
        for sy in (1, -1):
            v.screw(at=(sx * 34, sy * 34, zb + 4), d=6.0, kind='hex')
    v.lathe('rubber', [(0, zb + 4), (27, zb + 4), (27, zb + 7), (0, zb + 7)], seg=48)
    # мотор помпы с охлаждающими кольцами
    prof = [(0, zb + 7), (28, zb + 7)]
    z = zb + 7.0
    while z < zb + 44:
        prof += [(28, z + 1.0), (30.5, z + 1.6), (30.5, z + 3.4), (28, z + 4.0)]
        z += 5.0
    prof += [(28, zb + 47), (0, zb + 47)]
    v.lathe('alu_dark', prof, seg=64)
    v.text('print_grey', 'VIVID  D5  ·  PWM', 3.0, at=(0, -30.6, zb + 30), rot=(90, 0, 0), depth=0.05)
    # улитка помпы
    zt = zb + 47
    v.lathe('plastic_gloss', [(0, zt), (33, zt), (34, zt + 1), (34, RES_Z0 - 5), (32.5, RES_Z0 - 3.5), (0, RES_Z0 - 3.5)], seg=72)
    for k in range(4):
        a = radians(45 + 90 * k)
        v.screw(at=(27.5 * cos(a), 27.5 * sin(a), RES_Z0 - 3.5), d=5.0, kind='hex')
    # порт выхода (к водоблоку) и порт слива
    dy = T1_Y - ry
    px = -(34 ** 2 - dy ** 2) ** 0.5
    v.lathe('plastic_gloss', [(6.5, 0), (11, 0), (11, 3.5), (6.5, 3.5)], at=(px + 1.0, dy, PUMP_Z), axis='-x', seg=40, closed=True)
    fitting(v, (px - 2.4, dy, PUMP_Z), (0, -90, 0))
    v.lathe('plastic_gloss', [(6.5, 0), (11, 0), (11, 3.5), (6.5, 3.5)], at=(0, -33.0, PUMP_Z), axis='-y', seg=40, closed=True)
    fitting(v, (0, -36.4, PUMP_Z), (90, 0, 0), plug=True)
    # переходное кольцо со светом
    v.lathe('alu_black', [(27, RES_Z0 - 3.5), (32.5, RES_Z0 - 3.5), (32.5, RES_Z0 + 5), (31.4, RES_Z0 + 6), (30.2, RES_Z0 + 6),
                          (30.2, RES_Z0), (27, RES_Z0)], seg=72, closed=True)
    v.lathe('led_white', [(20, RES_Z0 - 0.6), (27, RES_Z0 - 0.6), (27, RES_Z0), (20, RES_Z0)], seg=64, closed=True)
    # колба
    v.lathe('glass_tube', [(30, RES_Z0), (30, RES_Z1)], seg=72, closed=False) if False else None
    v.pipe('glass_tube', [(0, 0, RES_Z0), (0, 0, RES_Z1)], 30.0, seg=72, caps=False)
    v.pipe('glass_tube', [(0, 0, RES_Z0), (0, 0, RES_Z1)], 27.4, seg=72, caps=False)
    # жидкость с мениском
    lvl = RES_Z1 - 30
    v.lathe('coolant', [(0, RES_Z0 + 0.2), (27.2, RES_Z0 + 0.2), (27.2, lvl), (25.5, lvl - 1.4), (18, lvl - 2.0), (0, lvl - 2.0)], seg=64)
    # возвратная трубка внутри
    v.pipe('glass_tube', [(0, 0, lvl - 34), (0, 0, RES_Z1)], 6.0, seg=28, caps=False)
    # верхняя крышка
    zc = RES_Z1
    n = 60
    v.lathe('alu_black', [(27, zc - 4), (30.2, zc - 4), (30.2, zc), (32.5, zc), (32.5, zc + 3)], seg=72, closed=False) if False else None
    v.lathe('alu_black', [(0, zc - 5), (27.2, zc - 5), (27.2, zc), (32.5, zc), (32.5, zc + 3.0), (0, zc + 3.0)], seg=72)
    pts = []
    for i in range(n * 2):
        rr = 33.0 if i % 2 == 0 else 32.3
        a = tau * i / (n * 2)
        pts.append((rr * cos(a), rr * sin(a)))
    v.prism('alu_black', pts, 8.5, z0=zc + 3.0)
    v.lathe('alu_black', [(0, zc + 11.5), (32.2, zc + 11.5), (31.0, zc + 13.4), (0, zc + 13.4)], seg=72)
    ztop = zc + 13.4
    v.lathe('nickel', [(6.5, ztop), (11.2, ztop), (11.2, ztop + 0.6), (6.5, ztop + 0.6)], seg=40, closed=True)
    fitting(v, (0, 0, ztop + 0.6), (0, 0, 0))
    for a in (135, 225):
        fitting(v, (20 * cos(radians(a)), 20 * sin(radians(a)), ztop), (0, 0, 0), plug=True)
    v.text('print_grey', 'VIVID', 4.0, at=(17, 0, ztop + 0.02), rot=(0, 0, -90), depth=0.05, spacing=1.6)
    # хомуты крепления к поддону
    for zz in (RES_Z0 + 36, RES_Z1 - 44):
        v.lathe('alu_black', [(30.1, zz - 5), (33.2, zz - 5), (33.2, zz + 5), (30.1, zz + 5)], seg=72, closed=True)
        v.box('alu_black', (14, TRAY - ry - 31, 6), at=(0, (TRAY - ry + 31) / 2, zz), bevel=0.6)
        v.box('alu_black', (30, 3, 18), at=(0, TRAY - ry - 1.5, zz), bevel=0.5)
        for sx in (1, -1):
            v.screw(at=(sx * 10, TRAY - ry - 3, zz), rot=(90, 0, 0), d=5.0, kind='hex')
        v.screw(at=(0, -33.2, zz), rot=(90, 0, 0), d=4.6, kind='hex')
    v.build()
    anchor('a_res', (0, -30, (RES_Z0 + RES_Z1) / 2), parent=v)
    return v


def make_loop(pc):
    make_radiator(pc)
    v = make_reservoir(pc)
    t = Part('tubes', parent=pc)
    bx = BOARD_X + SOCKET[0] + BLOCK_PORT
    zin = BOARD_Z + SOCKET[1] - BLOCK_PORT
    zout = BOARD_Z + SOCKET[1] + BLOCK_PORT
    yport = YB - 8.0 - 28.0            # плоскость посадки штуцера на водоблоке
    dy = T1_Y - RES[1]
    ppx = RES[0] - (34 ** 2 - dy ** 2) ** 0.5 - 2.4
    fitting(t, (bx, yport, zin), (90, 0, 0))
    fitting(t, (bx, yport, zout), (90, 0, 0))
    # Т1: помпа → водоблок
    tube(t, [(bx, yport - 6, zin), (bx, T1_Y, zin), (125, T1_Y, zin), (125, T1_Y, PUMP_Z), (ppx - 6, T1_Y, PUMP_Z)])
    # Т2: водоблок → радиатор
    tube(t, [(bx, yport - 6, zout), (bx, T2_Y, zout), (RES[0], T2_Y, zout), (RES[0], T2_Y, RAD_Z - 8)])
    # Т3: радиатор → резервуар
    tube(t, [(RES[0], RES[1], RAD_Z - 8), (RES[0], RES[1], RES_Z1 + 13.4 + 0.6 + 6)])
    t.build()
    anchor('a_tube', (20, T1_Y, zin), parent=pc)
