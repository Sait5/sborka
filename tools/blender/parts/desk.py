# Стол и всё, что на нём: монитор, клавиатура, мышь, коврик, стена. Координаты стола: пользователь со стороны −Y.
from math import sin, cos, tau, radians, pi
from kit import Part, rrect, circ, slot, screen, anchor, box_uv, bezier
from layout import *
from mouse import make_mouse
from monitor import make_monitor
from kit import fillet

PC_AT = (620.0, 60.0)        # где на столе стоит корпус
U = 19.05

ROWS = [
    [('Esc', 1, 0)] + [('F%d' % (i + 1), 1, 2 + i) for i in range(4)] + [('F%d' % (i + 5), 1, 6.5 + i) for i in range(4)] +
    [('F%d' % (i + 9), 1, 11 + i) for i in range(4)] + [('PrtSc', 1, 15.25), ('ScrLk', 1, 16.25), ('Pause', 1, 17.25)],
    [(k, 1, i) for i, k in enumerate(['`|Ё', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='])] +
    [('Backspace', 2, 13), ('Ins', 1, 15.25), ('Home', 1, 16.25), ('PgUp', 1, 17.25)],
    [('Tab', 1.5, 0)] + [(k, 1, 1.5 + i) for i, k in enumerate(
        ['Q|Й', 'W|Ц', 'E|У', 'R|К', 'T|Е', 'Y|Н', 'U|Г', 'I|Ш', 'O|Щ', 'P|З', '[|Х', ']|Ъ'])] +
    [('\\', 1.5, 13.5), ('Del', 1, 15.25), ('End', 1, 16.25), ('PgDn', 1, 17.25)],
    [('Caps', 1.75, 0)] + [(k, 1, 1.75 + i) for i, k in enumerate(
        ['A|Ф', 'S|Ы', 'D|В', 'F|А', 'G|П', 'H|Р', 'J|О', 'K|Л', 'L|Д', ';|Ж', "'|Э"])] + [('Enter', 2.25, 12.75)],
    [('Shift', 2.25, 0)] + [(k, 1, 2.25 + i) for i, k in enumerate(
        ['Z|Я', 'X|Ч', 'C|С', 'V|М', 'B|И', 'N|Т', 'M|Ь', ',|Б', '.|Ю', '/'])] + [('Shift', 2.75, 12.25), ('↑', 1, 16.25)],
    [('Ctrl', 1.25, 0), ('Win', 1.25, 1.25), ('Alt', 1.25, 2.5), ('', 6.25, 3.75), ('Alt', 1.25, 10), ('Fn', 1.25, 11.25),
     ('Menu', 1.25, 12.5), ('Ctrl', 1.25, 13.75), ('←', 1, 15.25), ('↓', 1, 16.25), ('→', 1, 17.25)],
]
ROW_Y = [0, 1.4, 2.4, 3.4, 4.4, 5.4]
ROW_TILT = [7, 7, 3, 0, -4, -6]
ROW_H = [8.6, 8.6, 7.6, 7.2, 7.6, 8.2]


def make_keyboard(parent, at):
    kb = Part('keyboard', at=at, rot=(4, 0, 0), parent=parent)
    Wk, Dk = 18.25 * U + 12, 6.4 * U + 12
    x0, y0 = -18.25 * U / 2, 6.4 * U / 2
    kb.plate('alu_dark', rrect(Wk, Dk, 7, 6), [rrect(Wk - 10.5, Dk - 10.5, 2.5, 4)], 8.5, z0=9.5, bevel=0.6)
    kb.prism('alu_dark', rrect(Wk, Dk, 7, 6), 9.5, bevel=0.6)
    kb.prism('led_kbd', rrect(Wk - 11, Dk - 11, 2.4, 4), 0.3, z0=9.5)
    for sx in (1, -1):
        for sy in (1, -1):
            kb.prism('rubber', rrect(34, 8, 3, 4, sx * (Wk / 2 - 40), sy * (Dk / 2 - 12)), 1.2, z0=-1.2)
    # гнездо и шнур
    kb.box('void', (9.4, 1.0, 3.6), at=(-Wk / 2 + 60, Dk / 2 + 0.02, 5.5))
    kb.prism('plastic_black', slot(12, 6.4, 6), 22, at=(-Wk / 2 + 60, Dk / 2 + 0.5, 5.5), rot=(-90, 0, 0), bevel=0.5)
    for ri, row in enumerate(ROWS):
        for label, w, cx in row:
            kx = x0 + (cx + w / 2) * U
            ky = y0 - (ROW_Y[ri] + 0.5) * U
            kw, kd, kh = w * U - 1.1, U - 1.1, ROW_H[ri]
            accent = label in ('Esc', 'Enter')
            mat = 'keycap_accent' if accent else 'keycap'
            with kb.at((kx, ky, 11.2), (ROW_TILT[ri], 0, 0)):
                kb.prism(mat, rrect(kw, kd, 1.7, 3), kh, taper=((kw - 5.6) / kw, (kd - 5.6) / kd), bevel=0.75)
                kb.box('plastic_black', (5.5, 5.5, 3.0), at=(0, 0, -1.4))
                if not label:
                    continue
                lat, _, cyr = label.partition('|')
                zt = kh + 0.02
                if cyr:
                    kb.text('legend', lat, 4.4, at=(-3.0, 2.4, zt), depth=0.04)
                    kb.text('legend', cyr, 3.8, at=(3.0, -2.6, zt), depth=0.04)
                elif len(lat) == 1:
                    kb.text('legend', lat, 4.6, at=(0, 0.2, zt), depth=0.04)
                else:
                    kb.text('legend', lat, 2.7 if len(lat) > 5 else 3.0, at=(0, 0, zt), depth=0.04)
    kb.build()
    return kb


def make_desk(pc):
    d = Part('desk', at=(PC_AT[1], -PC_AT[0], 0), rot=(0, 0, 90), parent=None)
    Wd, Dd, Td = 1800.0, 820.0, 30.0
    top = Part('desk_slab', parent=d)
    top.prism('desk_top', rrect(Wd, Dd, 10, 6, 0, 20), Td, z0=-Td, bevel=2.0)
    top.build()
    box_uv(top.objects[0], 400.0)
    # опоры
    for sx in (1, -1):
        d.box('desk_leg', (60, 700, 40), at=(sx * 800, 20, -730), bevel=2.0)
        d.box('desk_leg', (60, 80, 690), at=(sx * 800, 20, -Td - 345), bevel=2.0)
    d.box('desk_leg', (1540, 40, 70), at=(0, 20, -Td - 60), bevel=1.5)
    # стена и пол
    room = Part('room', parent=d)
    room.box('wall', (7000, 30, 3600), at=(0, Dd / 2 + 20 + 28, 700))
    room.box('floor', (7000, 5000, 20), at=(0, -1500, -770))
    room.build()
    for o in room.objects:
        box_uv(o, 1000.0)
    # световая лента за столом
    d.box('led_wall', (1500, 4, 8), at=(0, Dd / 2 + 20 - 6, -Td - 6))
    # коврик со строчкой по краю
    pad = Part('pad', parent=d)
    pad.prism('fabric', rrect(900, 400, 5, 5, -20, -170), 3.0, bevel=0.8)
    pad.pipe('stitch', [(x - 20, y - 170, 2.7) for x, y in rrect(894, 394, 4, 5)], 0.75, seg=6, closed=True)
    pad.build()
    box_uv(pad.objects[0], 60.0)
    d.pipe('sleeve_black', fillet([(-190, -84, 15.2), (-190, -58, 5.4), (-202, -8, 5.0), (-214, 34, 4.6), (-232, 60, 2.0),
                                   (-262, 300, 2.0), (-262, 436.6, 2.0), (-262, 436.6, -330)], 14, 8), 1.9, seg=10, uv=7.0)
    d.build()

    make_monitor(d, (0, 250, 0))
    make_keyboard(d, (-70, -170, 4.2))
    make_mouse(d, (255, -160, 3.0))
    anchor('a_desk', (0, -400, 420), parent=d)
    return d
