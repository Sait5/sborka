# Монитор: подставка с шарниром, корпус с металлической рамкой, задняя стенка с портами, световая планка сверху.
from math import radians
from kit import Part, rrect, circ, slot, hexagon, screen, anchor, fillet

FRONT = (90, 0, 0)     # местная XY → лицевая плоскость, +z к пользователю
BACK = (-90, 0, 0)     # +z назад, местная +y вниз


def make_monitor(parent, at):
    mon = Part('monitor', at=at, parent=parent)
    A, K = 'alu_dark', 'alu_black'
    # --- основание в два яруса
    mon.prism('rubber', rrect(250, 190, 24, 8), 1.0, z0=-0.2)
    mon.prism(A, rrect(260, 200, 28, 10), 5.0, z0=0.6, bevel=1.4)
    mon.prism(A, rrect(232, 172, 20, 8), 3.0, z0=5.6, bevel=1.0)
    mon.text('print_grey', 'V I V I D', 5.0, at=(0, -68, 8.62), depth=0.06)
    # --- стойка с воротником и окном для кабелей
    mon.prism(K, rrect(88, 36, 11, 6, 0, 55), 9.0, z0=8.6, bevel=1.2)
    mon.prism(A, rrect(72, 22, 8, 6, 0, 55), 314, z0=17.0, bevel=1.2)
    with mon.at((0, 44, 150), FRONT):
        mon.plate('plastic_black', slot(32, 58, 8), [slot(23, 49, 8)], 1.6, bevel=0.4)
        mon.prism('void', slot(23, 49, 8), 0.3, z0=-0.1)
    # --- шарнир
    mon.cyl(K, 17, 98, at=(0, 46, 320), axis='x', seg=48, bevel=1.0)
    for sx in (1, -1):
        mon.lathe(A, [(0, 0), (13, 0), (13, 1.6), (0, 1.6)], at=(sx * 49, 46, 320), axis='x' if sx > 0 else '-x', seg=40)
        mon.prism('void', hexagon(4.0), 0.4, at=(sx * 50.7, 46, 320), rot=(90, 0, 90 * sx))
    mon.box(K, (66, 26, 44), at=(0, 30, 318), bevel=1.2)
    # --- кабели: от портов вниз за стойкой и за край стола
    for sx, col in ((-1, 'sleeve_black'), (1, 'rubber')):
        path = fillet([(sx * 22, 58, 246), (sx * 22, 74, 236), (sx * 13, 76, 30), (sx * 13, 96, 3.2), (sx * 34, 150, 3.2),
                       (sx * 34, 186.5, 3.2), (sx * 34, 186.5, -330)], 16, 8)
        mon.pipe(col, path, 2.7, seg=12, uv=9.0 if sx < 0 else None)
    mon.build()

    hd = Part('monitor_head', at=(0, 14, 300), rot=(-4, 0, 0), parent=mon)
    Wm, Hm = 614.0, 366.0
    vw, vh = 597.0, 336.0
    cy = 9.0
    with hd.at((0, 0, 0), FRONT):
        hd.prism('plastic_black', rrect(Wm, Hm, 5, 5), 9.0, bevel=0.6)
        hd.plate('plastic_black', rrect(Wm, Hm, 5, 5), [rrect(vw + 1.0, vh + 1.0, 1.0, 3, 0, cy)], 1.1, z0=9.0, bevel=0.3)
        hd.prism('plastic_gloss', rrect(vw + 1.0, vh + 1.0, 1.0, 3, 0, cy), 0.3, z0=9.0)
        # металлическая рамка по торцу
        hd.plate(A, rrect(Wm + 2.4, Hm + 2.4, 6.2, 6), [rrect(Wm - 0.1, Hm - 0.1, 5, 5)], 10.9, z0=-0.4, bevel=0.45)
        hd.text('print_grey', 'V I V I D', 4.6, at=(0, -Hm / 2 + 8.5, 10.12), depth=0.06)
        hd.prism('plastic_gloss', slot(15, 3.6, 6), 0.2, at=(-58, -Hm / 2 + 8.5, 10.1))
        hd.cyl('led_white', 0.8, 0.5, at=(Wm / 2 - 16, -Hm / 2 + 8.5, 10.0), seg=12)
        # кнопки и джойстик под нижней кромкой
        for k in range(4):
            hd.box('plastic_black', (9, 3.4, 4), at=(Wm / 2 - 34 - k * 15, -Hm / 2 - 2.6, 4.5), bevel=0.5)
        hd.cyl('plastic_black', 3.4, 4.5, at=(Wm / 2 - 100, -Hm / 2 - 3.0, 4.5), axis='y', seg=20, bevel=0.5)
        # световая планка на верхней кромке
        yb = Hm / 2 + 13
        hd.cyl(K, 10.5, 440, at=(0, yb, 16), axis='x', seg=40, bevel=0.6)
        for sx in (1, -1):
            hd.lathe(A, [(0, 0), (10.5, 0), (10.5, 2.2), (9.4, 3.2), (0, 3.2)], at=(sx * 220, yb, 16), axis='x' if sx > 0 else '-x', seg=40)
        hd.box('led_bar', (410, 5.2, 1.0), at=(0, yb - 8.2, 22.6), rot=(42, 0, 0))
        hd.box(K, (44, 20, 26), at=(0, Hm / 2 + 5, 3), bevel=1.0)
        hd.box(K, (44, 6, 30), at=(0, Hm / 2 - 8, -6), bevel=0.8)
        hd.cyl(A, 12, 48, at=(0, Hm / 2 - 16, -22), axis='x', seg=32, bevel=0.8)
    with hd.at((0, 0, 0), BACK):
        hd.prism('plastic_matte', rrect(404, 244, 34, 8, 0, 6), 24, taper=(0.82, 0.72), bevel=1.0)
        hd.plate('led_accent', rrect(410, 250, 36, 8, 0, 6), [rrect(401, 241, 33, 8, 0, 6)], 1.2, z0=0.1)
        for sx in (-1, 1):
            for k in range(11):
                hd.prism('void', slot(74, 2.4, 4), 0.4, at=(sx * 112, -64 + k * 6.2 + 4, 24.0))
        hd.text('print_grey', 'VIVID', 24.0, at=(0, -52, 24.02), rot=(0, 0, 180), depth=0.25, spacing=1.5)
        # площадка крепления
        hd.prism('plastic_black', rrect(112, 112, 8, 5, 0, 6), 3.0, z0=24.0, bevel=0.6)
        for sx in (1, -1):
            for sy in (1, -1):
                hd.screw(at=(sx * 50, 6 + sy * 50, 27.0), d=6.0, kind='hex')
        # панель портов
        hd.prism('plastic_gloss', rrect(210, 24, 4, 4, 0, 78), 1.0, z0=23.2, bevel=0.3)
        for x, w, h in ((-92, 24, 17), (-58, 15, 5.6), (-38, 15, 5.6), (-18, 16, 5.2), (4, 16, 5.2), (40, 13, 5.8), (58, 13, 5.8), (76, 9, 9)):
            hd.plate('steel_dark', rrect(w + 1.6, h + 1.6, 1.0, 3, x, 78), [rrect(w, h, 0.7, 3, x, 78)], 1.0, z0=24.0, bevel=0.15)
            hd.prism('void', rrect(w, h, 0.7, 3, x, 78), 0.2, z0=24.2)
        hd.lathe('gold', [(1.8, 24.2), (3.2, 24.2), (3.2, 25.4), (1.8, 25.4)], at=(94, 78, 0), seg=20, closed=True)
        for x in (-22, 22):
            hd.box('plastic_black', (19, 11, 24), at=(x if x > 0 else -18, 78, 36), bevel=1.0)
    hd.build()
    screen('screen_monitor', vw, vh, at=(0, -9.4, cy), rot=(90, 0, 0), parent=hd)
    anchor('a_monitor', (0, -9.4, cy), rot=(90, 0, 0), parent=hd)
    anchor('a_bar', (0, -24, Hm / 2 + 8), parent=hd)
    return mon
