# Корпус: рама, поддон, кожух БП, верх с сеткой, стёкла, ножки, панель с кнопкой.
from math import sin, cos, tau, radians, sqrt
from kit import Part, rrect, circ, slot, hexagon, screen, anchor
from layout import *

XZ = (90, 0, 0)     # местная плоскость XY → мировая XZ, выдавливание к зрителю (−Y)
YZ = (90, 0, 90)    # местная XY → мировая YZ, выдавливание по +X


def hex_field(x0, x1, y0, y1, flat=4.0, web=1.0, inset=0.0):
    """Соты: список шестиугольных отверстий в прямоугольнике."""
    r = flat / sqrt(3.0)
    px = flat + web
    py = px * sqrt(3.0) / 2
    out = []
    j = 0
    y = y0 + flat / 2 + inset
    while y < y1 - flat / 2 - inset:
        x = x0 + flat / 2 + inset + (px / 2 if j % 2 else 0)
        while x < x1 - flat / 2 - inset:
            out.append(hexagon(r, x, y, radians(30)))
            x += px
        y += py
        j += 1
    return out


def make_case():
    c = Part('case')
    S = 'steel_black'
    H = Z1 - Z0

    # --- ножки: две поперечные опоры с резиновыми накладками
    for x in (-165, 165):
        c.prism('alu_black', rrect(34, W - 24, 6, 6), Z0 - 2.5, at=(x, 0, 2.5), bevel=0.8)
        for y in (-88, 88):
            c.prism('rubber', rrect(30, 34, 5, 5), 2.5, at=(x, y, 0), bevel=0.4)

    # --- дно и верхняя рама
    c.plate(S, rrect(L, W, 3, 4), [], 2.0, at=(0, 0, Z0), bevel=0.3)
    # --- поддон материнской платы с вырезами под кабели и бэкплейт
    tray_holes = [rrect(120, 120, 6, 4, BOARD_X + SOCKET[0] - XR - 0, BOARD_Z + SOCKET[1] - SHROUD)]
    gx = BOARD_X + BOARD_W + 28 - XR
    for zc, hh in ((BOARD_Z + 265 - SHROUD, 62), (BOARD_Z + 175 - SHROUD, 78), (BOARD_Z + 70 - SHROUD, 78)):
        tray_holes.append(rrect(24, hh, 11, 6, gx, zc))
    tray_holes.append(rrect(70, 20, 9, 6, 150, Z1 - SHROUD - 24))
    ssd_holes = [(120.0 - XR, z - 80.0 - SHROUD) for z in (392.0, 255.0)]      # проёмы под накопителями
    for hx, hz in ssd_holes:
        tray_holes.append(rrect(62, 17, 8, 6, hx, hz))
    for i in range(7):
        tray_holes.append(circ(2.2, 10, gx + 34, 40 + i * 48))
        tray_holes.append(circ(2.2, 10, gx + 62, 40 + i * 48))
    with c.at((XR, TRAY + 2, SHROUD), XZ):
        c.plate(S, [(4, 0), (L - 4, 0), (L - 4, Z1 - SHROUD - 2), (4, Z1 - SHROUD - 2)], tray_holes, 2.0, bevel=0.35)
        # резиновые заглушки вырезов
        for zc, hh in ((BOARD_Z + 265 - SHROUD, 62), (BOARD_Z + 175 - SHROUD, 78), (BOARD_Z + 70 - SHROUD, 78)):
            c.plate('rubber', rrect(30, hh + 6, 13, 6, gx, zc), [slot(19, hh - 10, 6, gx, zc)], 1.6, z0=1.4, bevel=0.5)
        for hx, hz in ssd_holes:
            c.plate('rubber', rrect(68, 23, 10, 6, hx, hz), [slot(56, 12, 6, hx, hz)], 1.6, z0=1.4, bevel=0.5)
        c.plate('rubber', rrect(76, 26, 11, 6, 150, Z1 - SHROUD - 24), [slot(62, 13, 6, 150, Z1 - SHROUD - 24)], 1.6,
                z0=1.4, bevel=0.5)
    # латунные стойки платы
    for sx, sy in ((6, 10), (6, 165), (6, 295), (124, 10), (124, 165), (124, 295), (238, 10), (238, 165), (238, 295)):
        c.prism('gold', hexagon(3.0), TRAY - YB - 1.6, at=(BOARD_X + sx, TRAY, BOARD_Z + sy), rot=XZ)

    # --- задняя стенка: решётка вентилятора, окно портов, заглушки слотов
    rear_holes = [h for h in hex_field(REAR_FAN[0] - 60, REAR_FAN[0] + 60, REAR_FAN[1] - 60, REAR_FAN[1] + 60, 6.0, 1.6)
                  if (sum(p[0] for p in h) / 6 - REAR_FAN[0]) ** 2 + (sum(p[1] for p in h) / 6 - REAR_FAN[1]) ** 2 < 57 ** 2
                  and max(p[0] for p in h) < 16]
    rear_holes.append(rrect(46, 160, 2, 3, 42, BOARD_Z + 228))
    with c.at((XR, 0, 0), YZ):
        c.plate(S, [(YG + 5, Z0), (YS, Z0), (YS, Z1), (YG + 5, Z1)], rear_holes, 2.0, bevel=0.3)
        for i in range(7):
            c.box(S, (104, 15.5, 1.0), at=(YB - 58, BOARD_Z + 135 - i * 20.32, 2.4), bevel=0.3)
        # щиток портов платы
        c.box('alu_black', (44, 158, 0.8), at=(42, BOARD_Z + 228, 2.2))

    # --- правая стальная боковина и верх/перед рамы
    c.box(S, (L, 2.0, H), at=(0, YS - 1.0, Z0 + H / 2), bevel=0.5)
    # стойки рамы: задняя у стекла, тонкие полки под стёкла
    c.box(S, (10, 6, H), at=(XR + 5, YG + 7, Z0 + H / 2), bevel=0.5)
    c.box(S, (L - 12, 5, 3), at=(-2, YG + 7.5, Z0 + 1.5), bevel=0.3)
    c.box(S, (5, W - 16, 3), at=(XF - 7.5, 0, Z0 + 1.5), bevel=0.3)
    c.box(S, (8, 40, H), at=(XF - 6, YS - 22, Z0 + H / 2), bevel=0.5)

    # --- кожух блока питания
    sh_holes = hex_field(40, 300, 22, 150, 5.0, 1.5)
    sh_holes += [rrect(26, 66, 10, 6, gx - 8, 172), rrect(58, 22, 9, 6, 150, 176)]
    with c.at((XR, YG + 6, SHROUD - 2.0)):
        c.plate(S, [(2, 0), (L - 6, 0), (L - 6, TRAY - YG - 4), (2, TRAY - YG - 4)], sh_holes, 2.0, bevel=0.35)
        c.plate('rubber', rrect(32, 72, 12, 6, gx - 8, 172), [slot(20, 58, 6, gx - 8, 172)], 1.6, z0=1.2, bevel=0.5)
        c.plate('rubber', rrect(64, 28, 11, 6, 150, 176), [slot(50, 14, 6, 150, 176)], 1.6, z0=1.2, bevel=0.5)
    # лицевая стенка кожуха (видна через стекло): перфорация и шильдик
    side_holes = []
    for i in range(46):
        for j in range(5):
            side_holes.append(slot(1.6, 9.0, 4, 26 + i * 4.2 + (2.1 if j % 2 else 0), 20 + j * 13.0))
    with c.at((XR, YG + 8, Z0), XZ):
        c.plate(S, [(2, 2), (L - 6, 2), (L - 6, SHROUD - Z0), (2, SHROUD - Z0)], side_holes, 2.0, bevel=0.35)
        c.box('alu_dark', (118, 22, 1.2), at=(L - 90, 50, 2.5), bevel=0.4)
        c.text('print_white', 'С Б О Р К А', 9.0, at=(L - 90, 50, 3.15), depth=0.12)
        c.box('led_accent', (118, 1.2, 0.8), at=(L - 90, 36, 2.4))
    # передняя стенка кожуха под передним стеклом
    c.box(S, (2, TRAY - YG - 10, SHROUD - Z0 - 2), at=(XF - 8, (TRAY + YG) / 2 + 2, (SHROUD + Z0) / 2), bevel=0.3)

    # --- блок питания внутри кожуха (виден сквозь перфорацию)
    c.box('steel_dark', (160, 150, 86), at=(XR + 88, 0, Z0 + 46), bevel=1.0)

    # --- верхняя панель с сотами над радиатором
    top_holes = hex_field(RAD_X0 + 4, RAD_X1 - 4, RAD_Y - 58, RAD_Y + 58, 4.2, 1.1)
    io_x = 219.0
    io = [circ(8.6, 40, io_x, -92), circ(3.3, 20, io_x, -70), rrect(5.2, 13.2, 1.0, 3, io_x, -48),
          rrect(5.2, 13.2, 1.0, 3, io_x, -28), slot(3.4, 9.2, 8, io_x, -9)[::1], circ(3.3, 24, io_x, 8),
          circ(0.9, 10, io_x, 20)]
    with c.at((0, 0, Z1 - 2.5)):
        c.plate(S, rrect(L, W, 3.5, 5), top_holes + io, 2.5, bevel=0.5)
    # рамка под сеткой (кромка окна)
    c.plate(S, rrect(RAD_X1 - RAD_X0 + 10, 134, 4, 4, (RAD_X0 + RAD_X1) / 2, RAD_Y),
            [rrect(RAD_X1 - RAD_X0 - 6, 118, 3, 4, (RAD_X0 + RAD_X1) / 2, RAD_Y)], 1.5, at=(0, 0, Z1 - 4.0), bevel=0.3)

    # --- панель портов: гнёзда под отверстиями
    zt = Z1
    # USB-A ×2
    for y in (-48, -28):
        with c.at((io_x, y, zt)):
            c.plate('steel_dark', rrect(5.2, 13.2, 1.0, 3), [rrect(4.4, 12.4, 0.7, 3)], 7.0, z0=-7.2)
            c.box('plastic_black', (1.7, 11.4, 6.0), at=(-0.9, 0, -4.4), bevel=0.2)
            for k in range(4):
                c.box('gold', (0.25, 1.0, 4.2), at=(0.02, -4.2 + k * 2.8, -3.6))
            c.box('void', (4.4, 12.4, 0.5), at=(0, 0, -7.4))
    # USB-C
    with c.at((io_x, -9, zt)):
        c.plate('steel_dark', slot(3.4, 9.2, 8), [slot(2.6, 8.4, 8)], 6.0, z0=-6.2)
        c.prism('plastic_black', slot(0.7, 6.6, 6), 5.0, z0=-5.6)
        c.box('void', (2.6, 8.4, 0.5), at=(0, 0, -6.4))
    # разъём 3,5 мм
    with c.at((io_x, 8, zt)):
        c.lathe('plastic_black', [(3.3, 0.0), (3.3, -8), (1.8, -8), (1.8, -0.6), (2.3, 0.0)], seg=32, closed=True)
        c.cyl('void', 1.8, 0.4, at=(0, 0, -8), seg=16)
        c.lathe('gold', [(1.82, -3), (1.82, -5), (1.7, -5), (1.7, -3)], seg=24, closed=True)
    # кнопка сброса
    with c.at((io_x, -70, zt)):
        c.lathe('alu_dark', [(0, -0.5), (2.6, -0.5), (3.0, -0.9), (3.0, -5), (0, -5)], seg=28)
    # светодиод диска
    c.cyl('led_white', 0.8, 1.5, at=(io_x, 20, zt - 0.9), seg=12)
    # значки над гнёздами
    c.text('print_grey', 'USB', 2.4, at=(io_x - 7.5, -38, zt + 0.02), rot=(0, 0, 90), depth=0.05)
    c.text('print_grey', 'C', 2.4, at=(io_x - 7.5, -9, zt + 0.02), rot=(0, 0, 90), depth=0.05)
    for gxs in (XR + 16, XF - 20):
        for gzs in (Z0 + 16, Z1 - 16):
            c.lathe('rubber', [(2.5, 0), (8.2, 0), (8.2, 1.2), (2.5, 1.2)], at=(gxs, YG - 1.2, gzs), axis='-y', seg=32, closed=True)
            c.thumbscrew(at=(gxs, YG - 1.2, gzs), rot=(90, 0, 0), d=13.5, h=6.5, mat='alu_black')
    c.build(segments=1)

    # --- кнопка питания отдельной деталью (нажимается)
    b = Part('power_button', at=(io_x, -92, Z1), parent=c)
    b.lathe('alu_dark', [(0, 0.6), (6.3, 0.6), (6.9, 0.2), (6.9, -6), (0, -6)], seg=64, bevel=0)
    # значок питания: кольцо с разрывом и черта
    n = 40
    ring = []
    for i in range(n + 1):
        a = radians(35 + 290 * i / n)
        ring.append((2.6 * sin(a), 2.6 * cos(a)))
    pts = [(x * 1.14, y * 1.14) for x, y in ring] + [(x * 0.86, y * 0.86) for x, y in ring[::-1]]
    b.prism('led_power', pts, 0.12, z0=0.56)
    b.prism('led_power', rrect(0.72, 3.0, 0.3, 4, 0, 1.9), 0.12, z0=0.56)
    b.build()
    ringp = Part('power_ring', at=(io_x, -92, Z1), parent=c)
    ringp.lathe('led_power', [(7.1, 0.25), (8.5, 0.25), (8.5, -3), (7.1, -3)], seg=64, closed=True)
    ringp.build()
    anchor('a_power', (io_x, -92, Z1), parent=c)

    # --- стёкла
    g = Part('glass', parent=c)
    gz0, gz1 = Z0 + 1.0, Z1 - 1.0
    # боковое
    with g.at((XR + 1, YG + 4, gz0), XZ):
        g.prism('glass_panel', rrect(L - 3, gz1 - gz0, 2.0, 4, (L - 3) / 2, (gz1 - gz0) / 2), 4.0, bevel=0.6)
        g.plate('glass_frit', rrect(L - 3.4, gz1 - gz0 - 0.4, 2.0, 4, (L - 3) / 2, (gz1 - gz0) / 2),
                [rrect(L - 3 - 30, gz1 - gz0 - 30, 6, 6, (L - 3) / 2, (gz1 - gz0) / 2)], 0.15, z0=-0.2)
    # переднее
    with g.at((XF - 4, YG + 4.2, gz0), YZ):
        g.prism('glass_panel', rrect(W - 6, gz1 - gz0, 2.0, 4, (W - 6) / 2, (gz1 - gz0) / 2), 4.0, bevel=0.6)
        g.plate('glass_frit', rrect(W - 6.4, gz1 - gz0 - 0.4, 2.0, 4, (W - 6) / 2, (gz1 - gz0) / 2),
                [rrect(W - 6 - 30, gz1 - gz0 - 30, 6, 6, (W - 6) / 2, (gz1 - gz0) / 2)], 0.15, z0=-0.2)
    g.build()
    return c
