# Материнская плата, память и водоблок с экраном. Местные оси платы: X вправо, Y вверх, Z от платы.
import random
from math import sin, cos, tau, radians, pi
from kit import Part, rrect, circ, slot, hexagon, screen, anchor, box_uv, dup
from layout import *

UPX = (90, 0, 0)     # профиль в плоскости (x, z), выдавливание по −y
UPY = (90, 0, 90)    # профиль в плоскости (y, z), выдавливание по +x


def pin_header(p, x, y, cols, rows=2, pitch=2.54, shroud=False, skip=()):
    w, d = cols * pitch, rows * pitch
    p.box('slot_plastic', (w, d, 2.5), at=(x, y, 1.25), bevel=0.15)
    if shroud:
        p.plate('slot_plastic', rrect(w + 3, d + 3, 0.4, 2, x, y), [rrect(w + 1.2, d + 1.2, 0.3, 2, x, y)], 9.0, bevel=0.2)
    for i in range(cols):
        for j in range(rows):
            if (i, j) in skip:
                continue
            p.box('gold', (0.64, 0.64, 6.0), at=(x - w / 2 + pitch / 2 + i * pitch, y - d / 2 + pitch / 2 + j * pitch, 5.2))


def atx_conn(p, x, y, cols, rows=2, rot=0, h=12.5):
    """Колодка питания: гнёзда с квадратными и скошенными ячейками."""
    pitch = 4.2
    w, d = cols * pitch + 1.6, rows * pitch + 1.6
    with p.at((x, y, 0), (0, 0, rot)):
        holes = []
        for i in range(cols):
            for j in range(rows):
                cx = -cols * pitch / 2 + pitch / 2 + i * pitch
                cy = -rows * pitch / 2 + pitch / 2 + j * pitch
                if (i + j) % 2:
                    holes.append(rrect(3.4, 3.4, 0.3, 2, cx, cy))
                else:
                    holes.append([(cx - 1.7, cy - 1.7), (cx + 1.7, cy - 1.7), (cx + 1.7, cy + 0.8), (cx + 0.8, cy + 1.7),
                                  (cx - 0.8, cy + 1.7), (cx - 1.7, cy + 0.8)])
                p.box('gold', (0.9, 0.9, h - 4), at=(cx, cy, (h - 4) / 2))
        p.plate('plastic_white' if False else 'slot_plastic', rrect(w, d, 0.5, 2), holes, h - 1.0, z0=1.0, bevel=0.2)
        p.box('slot_plastic', (w, d, 1.0), at=(0, 0, 0.5))
        p.box('slot_plastic', (cols * pitch * 0.3, 1.2, h * 0.7), at=(0, d / 2 + 0.6, h * 0.55), bevel=0.2)


def cap(p, x, y, r=2.5, h=8.0, mat='cap_can'):
    p.lathe(mat, [(0, 0), (r, 0), (r, h - 0.4), (r - 0.4, h), (0, h)], at=(x, y, 0), seg=20)
    p.lathe('print_grey', [(0, h), (r - 0.9, h), (r - 0.9, h + 0.03), (0, h + 0.03)], at=(x, y, 0), seg=16)
    # полукруглая метка полярности
    pts = [(r * 0.75 * cos(a), r * 0.75 * sin(a)) for a in [radians(-70 + 140 * k / 8) for k in range(9)]]
    p.prism('void', pts, 0.03, at=(x, y, h + 0.03))


def choke(p, x, y, s=9.0, h=7.0, label='R15'):
    p.prism('choke', rrect(s, s, 1.0, 3), h, at=(x, y, 0), bevel=0.35)
    p.text('print_grey', label, s * 0.3, at=(x, y, h + 0.02), depth=0.04)
    p.box('solder', (s + 1.2, s * 0.4, 0.5), at=(x, y, 0.25))


def chip(p, x, y, w, d, h=1.2, legs=0, rot=0, dot=True):
    with p.at((x, y, 0), (0, 0, rot)):
        p.box('chip', (w, d, h), at=(0, 0, h / 2 + 0.15), bevel=0.12)
        if dot:
            p.cyl('print_grey', min(w, d) * 0.06, 0.03, at=(-w / 2 + min(w, d) * 0.16, -d / 2 + min(w, d) * 0.16, h + 0.16), seg=10)
        if legs:
            n = legs
            for i in range(n):
                t = (i + 0.5) / n - 0.5
                for s in (1, -1):
                    p.box('solder', (w * 0.6 / n, 1.1, 0.35), at=(t * w * 0.88, s * (d / 2 + 0.4), 0.3))
                    if legs > 5:
                        p.box('solder', (1.1, d * 0.6 / n, 0.35), at=(s * (w / 2 + 0.4), t * d * 0.88, 0.3))


def spring(p, at, r=3.0, h=6.0, turns=4.5, wire=0.45, mat='steel_dark'):
    n = int(turns * 14)
    pts = [(r * cos(tau * turns * i / n), r * sin(tau * turns * i / n), h * i / n) for i in range(n + 1)]
    p.pipe(mat, pts, wire, at=at, seg=6)


def make_ram(parent):
    r = Part('ram1', parent=parent)
    Lr = 133.0
    # текстолит и контакты
    r.box('pcb', (1.2, Lr, 30), at=(0, 0, 15), bevel=0.1)
    # радиатор: две пластины с ломаным верхом
    prof = [(-Lr / 2, 4), (Lr / 2, 4), (Lr / 2, 34), (Lr / 2 - 8, 39.5), (Lr / 2 - 34, 39.5), (Lr / 2 - 40, 35),
            (-Lr / 2 + 40, 35), (-Lr / 2 + 34, 39.5), (-Lr / 2 + 8, 39.5), (-Lr / 2, 34)]
    for s in (1, -1):
        with r.at((s * 1.5 - 0.9 if s > 0 else -2.4, 0, 0), UPY):
            r.prism('alu_black', prof, 1.8, bevel=0.3)
        xs = s * 3.35
        # фрезерованные канавки и вставка
        with r.at((xs, 0, 0), UPY):
            for k in range(5):
                r.box('alu_dark', (22 - k * 3, 0.8, 0.25), at=(-Lr / 2 + 16 + k * 1.2, 9 + k * 4.2, 0 if s > 0 else -0.0))
            r.box('alu_dark', (52, 9, 0.3), at=(14, 21, 0), bevel=0.1)
        r.text('print_white', 'RESONANCE', 4.6, at=(xs + s * 0.18, 14, 21), rot=(90, 0, 90 if s > 0 else -90),
               depth=0.06, spacing=1.25)
        r.text('print_grey', 'DDR5 · 32GB · 6400', 2.2, at=(xs + s * 0.03, -34, 9), rot=(90, 0, 90 if s > 0 else -90),
               depth=0.05)
    # световая планка сверху: гранёный профиль
    with r.at((-3.6, 0, 0), UPY):
        pass
    bar = [(-3.4, 35.2), (3.4, 35.2), (3.4, 41.5), (1.6, 44.2), (-1.6, 44.2), (-3.4, 41.5)]
    with r.at((0, Lr / 2 - 9, 0), UPX):
        r.prism('led_ram', bar, Lr - 18, bevel=0.25)
    r.build()
    return r


def make_block(parent, at):
    b = Part('block', at=at, parent=parent)
    b.prism('nickel', rrect(78, 78, 4, 5), 5.0, bevel=0.6)
    b.prism('alu_black', rrect(80, 80, 7, 6), 19.0, z0=5.0, bevel=0.9)
    # световой пояс
    b.plate('led_accent', rrect(80.5, 80.5, 7.2, 6), [rrect(78, 78, 6, 6)], 1.3, z0=13.5)
    b.prism('alu_dark', rrect(76, 76, 6, 6), 1.6, z0=24.0, bevel=0.4)
    # модуль экрана
    b.lathe('alu_black', [(27.0, 25.6), (27.0, 30.4), (26.0, 31.4), (24.6, 31.4), (24.2, 30.6), (24.2, 25.6)], seg=96,
            closed=True)
    b.lathe('plastic_gloss', [(0, 29.6), (24.2, 29.6), (24.2, 25.6), (0, 25.6)], seg=64)
    for k in range(60):
        a = tau * k / 60
        b.box('print_grey', (0.25, 1.1 if k % 5 else 2.0, 0.05), at=(25.3 * sin(a), 25.3 * cos(a), 31.42),
              rot=(0, 0, -360.0 * k / 60))
    b.text('print_grey', 'SBORKA  LIQUID', 2.4, at=(-22, -33.5, 25.62), depth=0.05, align='LEFT', spacing=1.3)
    # посадки штуцеров
    for py in (BLOCK_PORT, -BLOCK_PORT):
        b.lathe('alu_black', [(10.6, 25.6), (10.6, 27.4), (9.8, 28.0), (6.0, 28.0), (6.0, 25.6)], at=(BLOCK_PORT, py, 0),
                seg=40, closed=True)
    b.text('print_grey', 'IN', 2.2, at=(BLOCK_PORT - 14, -BLOCK_PORT, 25.62), depth=0.05)
    b.text('print_grey', 'OUT', 2.2, at=(BLOCK_PORT - 15, BLOCK_PORT, 25.62), depth=0.05)
    # крепление: планка, пружины, винты с накаткой
    b.plate('steel_dark', rrect(70, 104, 8, 6), [circ(2.0, 12, sx * 27, sy * 45) for sx in (1, -1) for sy in (1, -1)],
            2.2, z0=3.2, bevel=0.3)
    for sx in (1, -1):
        for sy in (1, -1):
            spring(b, (sx * 27, sy * 45, 5.4), r=3.0, h=5.2)
            b.thumbscrew(at=(sx * 27, sy * 45, 10.6), d=9.5, h=6.5, mat='alu_dark')
            b.cyl('steel_dark', 1.6, 12, at=(sx * 27, sy * 45, 4), seg=12)
    b.build()
    sc = screen('screen_pump', 47.6, 47.6, at=(0, 0, 29.75), parent=b, corner=23.79)
    anchor('a_pump', (0, 0, 30), parent=b)
    return b


def make_board(pc):
    bd = Part('board', at=(BOARD_X, YB, BOARD_Z), rot=(90, 0, 0), parent=pc)
    W_, H_ = BOARD_W, BOARD_H
    sx, sy = SOCKET
    rnd = random.Random(7)

    # --- текстолит отдельной деталью (на сайте получает рисунок дорожек)
    pcb = Part('pcb', parent=bd)
    mounts = [(6, 10), (6, 165), (6, 295), (124, 10), (124, 165), (124, 295), (238, 10), (238, 165), (238, 295)]
    pcb.plate('pcb', rrect(W_, H_, 2.5, 4, W_ / 2, H_ / 2), [circ(2.0, 14, x, y) for x, y in mounts], 1.6, z0=-1.6,
              bevel=0.15)
    pcb.build()
    box_uv(pcb.objects[0], 305.0)

    p = bd
    for x, y in mounts:
        p.lathe('solder', [(2.1, 0.0), (4.6, 0.0), (4.6, 0.04), (2.1, 0.04)], at=(x, y, 0), seg=24, closed=True)
        p.screw(at=(x, y, 0.04), d=6.4, mat='steel_dark')

    # --- кожух портов
    prof = [(0, 0), (30, 0), (30, 20), (24, 33), (5, 37), (0, 37)]
    with p.at((0, 305, 0), UPX):
        p.prism('plastic_matte', prof, 152, bevel=0.7)
    with p.at((14, 229, 36.2), (0, -12, 0)):
        p.box('alu_dark', (15, 118, 1.2), at=(0, 0, 0), bevel=0.3)
        p.text('print_white', 'HORIZON', 6.4, at=(0, 0, 0.62), rot=(0, 0, 90), depth=0.08, spacing=1.5)
    with p.at((27.3, 229, 26.5), (0, 65.2, 0)):
        p.box('led_accent', (1.4, 132, 1.0), at=(0, 0, 0.4))
        for k in range(9):
            p.box('plastic_gloss', (6.5, 1.2, 0.5), at=(-5.6, -56 + k * 14, 0.2))

    # --- радиаторы питания
    p.box('alu_dark', (18, 104, 7), at=(45, 236, 3.5), bevel=0.4)
    for k in range(26):
        p.prism('alu_dark', [(-9, 0), (9, 0), (9, 14), (6, 19), (-9, 19)], 2.2, at=(45, 186 + k * 4.0 + 2.2, 7), rot=UPX,
                bevel=0.25)
    p.box('alu_dark', (88, 20, 6), at=(106, 288, 3.0), bevel=0.4)
    for k in range(22):
        p.prism('alu_dark', [(-10, 0), (10, 0), (10, 16), (-6, 16), (-10, 12)], 2.2, at=(63.5 + k * 4.0, 288, 6),
                rot=UPY, bevel=0.25)
    # тепловая трубка между радиаторами
    from kit import fillet
    p.pipe('nickel', fillet([(45, 190, 4.2), (45, 300, 4.2), (150, 300, 4.2)], 9, 8), 2.6, seg=14)

    # --- дроссели и конденсаторы вокруг сокета
    for k in range(8):
        choke(p, 60.5, 196 + k * 10.0)
    for k in range(4):
        choke(p, 82 + k * 10.0, 273.2, 8.2, 6.5)
    for k in range(7):
        cap(p, 68.5, 192 + k * 11.5, 2.4, 7.5)
    for k in range(5):
        cap(p, 146.5, 196 + k * 12.0, 2.6, 8.5)
        chip(p, 153, 196 + k * 12.0, 5, 6, 0.9, legs=3, rot=90)
    for k in range(4):
        choke(p, 162.5, 176 + k * 10.5, 7.5, 5.5, 'R22')

    # --- питание процессора (8+4), вентиляторные колодки
    atx_conn(p, 44, 298.5, 4, 2)
    atx_conn(p, 62.5, 298.5, 2, 2)
    for x in (158, 170, 222):
        pin_header(p, x, 301, 4, 1)
        p.box('slot_plastic', (10.2, 1.2, 5.5), at=(x, 302.6, 2.75))
    p.text('print_white', 'CPU_FAN', 1.5, at=(164, 296.4, 0.02), depth=0.03)

    # --- слоты памяти с защёлками
    for i in range(4):
        x = 178 + i * 9.5
        hole = [rrect(1.6, 62, 0.3, 2, 0, -34.5), rrect(1.6, 69, 0.3, 2, 0, 34)]
        with p.at((x, 230, 0)):
            p.plate('slot_plastic' if i % 2 else 'plastic_grey', rrect(7.4, 141, 0.6, 2), hole, 6.2, bevel=0.2)
            for s in (1, -1):
                p.prism('plastic_grey' if i % 2 else 'slot_plastic', [(-3.2, 0), (3.2, 0), (3.2, 9), (2, 11.5), (-2, 11.5), (-3.2, 9)],
                        5.2, at=(-0.0, s * 71.5 + (2.6 if s > 0 else 2.6), 0), rot=UPX, bevel=0.3)
    p.text('print_white', 'DIMM_A1  A2  B1  B2', 1.7, at=(192, 156, 0.02), depth=0.03)

    # --- 24-контактная колодка и USB
    atx_conn(p, 235.5, 218, 12, 2, rot=90)
    pin_header(p, 236, 172, 10, 2, 2.0, shroud=True)
    pin_header(p, 236, 150, 5, 2, 2.0, shroud=True)

    # --- индикатор POST-кодов
    p.box('plastic_gloss', (20, 13.5, 6.5), at=(226, 270, 3.25), bevel=0.3)
    p.text('print_white', 'DEBUG', 1.5, at=(226, 279, 0.02), depth=0.03)

    # --- M.2 и слоты расширения
    def m2(y0, y1, label):
        yc, hh = (y0 + y1) / 2, y1 - y0
        p.prism('alu_dark', rrect(90, hh, 2.0, 3, 106, yc), 5.0, bevel=0.5)
        for k in range(int(hh / 3.2) - 1):
            p.box('alu_black', (58, 1.1, 0.6), at=(92, y0 + 3.2 + k * 3.2, 5.0), rot=(0, 0, 0))
        p.text('print_white', label, 3.6, at=(138, yc, 5.02), depth=0.06, rot=(0, 0, 90))
        for x in (64.5, 147.5):
            p.screw(at=(x, yc, 5.0), d=4.0, mat='steel_dark', kind='hex')

    m2(152, 176, 'M.2_1')
    m2(92, 120, 'M.2_2')
    m2(38, 64, 'M.2_3')
    p.text('print_white', 'HORIZON  ·  REV 1.0  ·  SAIT5', 3.0, at=(104, 181.5, 0.02), depth=0.03, spacing=1.3)

    def pcie(y, length, armor=True):
        x0 = 60.0
        with p.at((x0 + length / 2, y, 0)):
            p.plate('slot_plastic', rrect(length, 7.6, 0.5, 2), [rrect(length - 14, 1.7, 0.3, 2, -3, 0), rrect(8, 1.7, 0.3, 2, length / 2 - 6.5, 0)]
                    if length > 40 else [rrect(length - 5, 1.7, 0.3, 2)], 11.0, bevel=0.2)
            if armor:
                p.plate('steel_dark', rrect(length + 1.2, 8.8, 0.6, 2), [rrect(length - 0.4, 7.7, 0.5, 2)], 10.0, z0=0.4, bevel=0.15)
                for k in range(6):
                    p.box('steel_dark', (2.0, 1.2, 0.6), at=(-length / 2 + 8 + k * (length - 16) / 5, 4.9, 0.3))
            p.prism('plastic_grey', [(-2.5, 0), (2.5, 0), (2.5, 9), (0, 13), (-2.5, 12)], 3.4, at=(length / 2 + 4.5, 1.7, 0), rot=UPX,
                    bevel=0.3)

    pcie(136, 90)
    pcie(76, 90)
    pcie(24, 26, armor=False)

    # --- радиатор чипсета
    with p.at((194, 80, 0)):
        p.prism('alu_dark', [(-42, -50), (42, -50), (42, 36), (30, 48), (-42, 48)], 9.0, bevel=0.7)
        p.prism('alu_black', [(-36, -44), (36, -44), (36, 10), (-10, 10), (-36, -16)], 0.8, z0=9.0, bevel=0.2)
        for k in range(9):
            p.box('alu_dark', (40, 0.9, 0.5), at=(-14 + k * 1.2, 16 + k * 3.2, 9.0), rot=(0, 0, 45))
        p.text('print_white', 'HORIZON', 7.0, at=(2, -20, 9.82), depth=0.08, spacing=1.4)
        p.text('print_grey', 'X-SERIES', 2.6, at=(2, -30, 9.82), depth=0.05, spacing=2.2)
        p.box('led_accent', (1.2, 52, 0.8), at=(-38.5, -18, 9.2))
        for x, y in ((-37, 43), (37, -45), (-37, -45)):
            p.screw(at=(x, y, 9.0), d=4.0, mat='steel_dark', kind='hex')

    # --- SATA
    for k in range(4):
        with p.at((238, 58 + k * 16.5, 0)):
            p.plate('slot_plastic', rrect(11, 15, 0.5, 2), [[(-4, -6), (4, -6), (4, 6), (2.6, 6), (2.6, -4.6), (-4, -4.6)]],
                    7.5, bevel=0.2)

    # --- батарейка
    p.lathe('chrome', [(0, 1.2), (9.4, 1.2), (10, 1.8), (10, 4.0), (9.2, 4.4), (0, 4.4)], at=(190, 144, 0), seg=48)
    p.lathe('slot_plastic', [(10.3, 0), (11.6, 0), (11.6, 3.4), (10.3, 3.4)], at=(190, 144, 0), seg=48, closed=True)
    p.text('print_grey', 'CR2032  3V', 2.0, at=(190, 144, 4.42), depth=0.04)
    p.box('steel_dark', (5, 3, 1.0), at=(190, 155.5, 4.2), bevel=0.2)

    # --- звук: позолоченные конденсаторы, экран кодека
    for k in range(6):
        cap(p, 9 + (k % 3) * 8.5, 14 + (k // 3) * 9.5, 3.0, 10.0, 'gold')
    p.box('steel_dark', (22, 14, 3.5), at=(20, 44, 1.75), bevel=0.4)
    p.text('print_grey', 'AUDIO', 2.4, at=(20, 44, 3.52), depth=0.04, spacing=1.6)
    p.box('print_accent', (0.5, 70, 0.03), at=(46, 38, 0.015))

    # --- нижние колодки
    xs = 30
    for cols, lab in ((5, 'AUDIO'), (2, 'RGB'), (4, 'FAN4'), (5, 'USB_E1'), (5, 'USB_E2'), (4, 'FAN5'), (3, 'ARGB'), (7, 'TPM'),
                      (5, 'F_PANEL')):
        rows = 1 if cols < 5 and lab != 'RGB' else 2
        w = cols * 2.54
        pin_header(p, xs + w / 2, 4.5, cols, rows)
        p.text('print_white', lab, 1.4, at=(xs + w / 2, 10.2 if rows == 2 else 8.6, 0.02), depth=0.03)
        xs += w + 9

    # --- микросхемы
    chip(p, 30, 90, 14, 14, 1.4, legs=12)
    chip(p, 38, 125, 8, 8, 1.2, legs=8)
    chip(p, 170, 150, 5.3, 8, 1.6, legs=4)
    chip(p, 214, 140, 6, 6, 1.0, legs=6)
    chip(p, 222, 288, 5, 4, 0.9, legs=4)
    for k in range(8):
        chip(p, 54.5, 198 + k * 10.0, 3.4, 5.0, 0.8, legs=0, dot=False)
    # --- россыпь мелких деталей в свободных местах
    busy = [(0, 150, 32, 305), (34, 180, 72, 305), (55, 185, 140, 275), (60, 276, 152, 305), (172, 155, 212, 305),
            (226, 185, 244, 250), (58, 30, 152, 180), (150, 28, 240, 130), (0, 0, 244, 14), (212, 255, 244, 285),
            (0, 8, 44, 62), (176, 130, 204, 158), (226, 140, 244, 182), (228, 48, 244, 116), (22, 82, 40, 98),
            (140, 185, 170, 260)]

    def free(x, y, m=2.0):
        if not (3 < x < W_ - 3 and 3 < y < H_ - 3):
            return False
        for mx, my in mounts:
            if abs(x - mx) < 7 and abs(y - my) < 7:
                return False
        return not any(a - m < x < c + m and b - m < y < d + m for a, b, c, d in busy)

    n = 0
    while n < 620:
        x, y = rnd.uniform(3, W_ - 3), rnd.uniform(3, H_ - 3)
        if not free(x, y):
            continue
        n += 1
        k = rnd.random()
        rot = rnd.choice((0, 90))
        if k < 0.5:      # резистор
            p.box('chip', (1.6, 0.8, 0.45), at=(x, y, 0.23), rot=(0, 0, rot))
            p.box('solder', (0.35, 0.82, 0.47), at=(x + (0.7 if rot == 0 else 0), y + (0.7 if rot else 0), 0.235), rot=(0, 0, rot))
            p.box('solder', (0.35, 0.82, 0.47), at=(x - (0.7 if rot == 0 else 0), y - (0.7 if rot else 0), 0.235), rot=(0, 0, rot))
        elif k < 0.86:   # керамический конденсатор
            p.box('pcb_edge', (1.5, 0.8, 0.8), at=(x, y, 0.4), rot=(0, 0, rot))
            p.box('solder', (0.35, 0.84, 0.82), at=(x + (0.62 if rot == 0 else 0), y + (0.62 if rot else 0), 0.41), rot=(0, 0, rot))
            p.box('solder', (0.35, 0.84, 0.82), at=(x - (0.62 if rot == 0 else 0), y - (0.62 if rot else 0), 0.41), rot=(0, 0, rot))
        elif k < 0.95:   # транзистор
            p.box('chip', (2.9, 1.5, 1.0), at=(x, y, 0.55), rot=(0, 0, rot), bevel=0.1)
        else:            # контрольная площадка
            p.cyl('solder', 0.7, 0.04, at=(x, y, 0.02), seg=10)
    p.build()

    # --- экран POST-кодов
    screen('screen_debug', 17.0, 10.5, at=(226, 270, 6.52), parent=bd)

    # --- память
    r1 = make_ram(bd)
    r1.root.location = (178 * 0.001, 230 * 0.001, 6.4 * 0.001)
    for i in range(1, 4):
        dup(r1, 'ram%d' % (i + 1), (178 + i * 9.5, 230, 6.4), (0, 0, 0), bd)

    make_block(bd, (sx, sy, 8.0))
    return bd
