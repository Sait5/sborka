# Мышь: внутренний корпус и отдельные панели поверх него — между панелями настоящие швы.
from math import sin, cos, pi, exp, radians
from mathutils import Vector
from kit import Part


def make_mouse(parent, at):
    m = Part('mouse', at=at, rot=(0, 0, -8), parent=parent)
    Lm, ZB = 126.0, 2.6

    def ends(t, p_rear, p_front):
        s, p = (1 - 2 * t, p_rear) if t < 0.5 else (2 * t - 1, p_front)
        s = min(max(s, 0.0), 0.9995)
        return (1 - s ** p) ** (1 / p)

    def hw(t):
        return (31.5 - 2.9 * exp(-((t - 0.58) / 0.17) ** 2)) * ends(t, 2.6, 5.0)

    def hh(t):
        if t < 0.38:
            u = (0.38 - t) / 0.38
            h = 40.0 * (1 - u ** 2.3) ** (1 / 2.3)
        else:
            h = 40.0 - 23.5 * ((t - 0.38) / 0.62) ** 1.55
        return max(0.6, h * ends(t, 30.0, 9.0))

    def surf(t, a):
        w, h = hw(t), hh(t)
        ca, sa = cos(a), sin(a)
        z = h * abs(sa) ** 0.83
        x = w * (abs(ca) ** 0.66) * (1 if ca >= 0 else -1) * (0.925 + 0.075 * min(1.0, z / (0.34 * h)))
        return Vector((x, -Lm / 2 + Lm * t, ZB + z))

    def normal(t, a):
        e = 1e-3
        da = surf(t, min(pi - 1e-4, a + e)) - surf(t, max(1e-4, a - e))
        dt = surf(min(0.999, t + e), a) - surf(max(0.001, t - e), a)
        n = da.cross(dt)
        if n.length < 1e-9:
            return Vector((0, 0, 1))
        n.normalize()
        p = surf(t, a)
        if n.dot(Vector((p.x, 0, p.z - 8.0))) < 0:
            n = -n
        return n

    def pt(t, a, off):
        return tuple(surf(t, a) + normal(t, a) * off)

    def patch(mat, t0, t1, a0, a1, out=0.0, inn=-1.3, bevel=0.35, res=1.0):
        nt = max(6, int((t1 - t0) * 70 * res))
        na = max(4, int((a1 - a0) * 26 * res))
        rows = []
        for i in range(nt + 1):
            t = t0 + (t1 - t0) * i / nt
            A = [a0 + (a1 - a0) * k / na for k in range(na + 1)]
            rows.append([pt(t, a, out) for a in A] + [pt(t, a, inn) for a in A[::-1]])
        m.grid(mat, rows, close_v=True, cap=True, bevel=bevel)

    # внутренний корпус (виден в швах и в канале колеса)
    ns, na = 44, 30
    rows = []
    for i in range(ns + 1):
        t = 0.004 + 0.992 * (0.5 - 0.5 * cos(pi * i / ns))
        ring = [pt(t, 0.02 + (pi - 0.04) * k / na, -1.0) for k in range(na + 1)]
        w = hw(t) * 0.9
        ring += [(-w, -Lm / 2 + Lm * t, 0.6), (0.0, -Lm / 2 + Lm * t, 0.6), (w, -Lm / 2 + Lm * t, 0.6)]
        rows.append(ring)
    m.grid('plastic_gloss', rows, close_v=True, cap=True)

    AS, G, D = 0.50, 0.017, 0.085
    # спинка, две клавиши, боковые накладки
    patch('mouse_shell', 0.012, 0.512, AS + G, pi - AS - G)
    patch('mouse_shell', 0.530, 0.972, AS + G, pi / 2 - D)
    patch('mouse_shell', 0.530, 0.972, pi / 2 + D, pi - AS - G)
    patch('rubber', 0.028, 0.968, 0.004, AS - G, bevel=0.3)
    patch('rubber', 0.028, 0.968, pi - AS + G, pi - 0.004, bevel=0.3)
    # боковые кнопки слева
    patch('plastic_gloss', 0.36, 0.505, pi - AS + 0.07, pi - AS + 0.25, out=1.7, inn=-0.4, bevel=0.45, res=2.0)
    patch('plastic_gloss', 0.525, 0.67, pi - AS + 0.07, pi - AS + 0.25, out=1.7, inn=-0.4, bevel=0.45, res=2.0)
    # кнопка DPI и окно индикатора в канале
    patch('plastic_gloss', 0.585, 0.635, pi / 2 - 0.05, pi / 2 + 0.05, out=0.1, inn=-1.2, bevel=0.3, res=3.0)
    patch('led_accent', 0.555, 0.567, pi / 2 - 0.035, pi / 2 + 0.035, out=-0.75, inn=-1.2, bevel=0.0, res=3.0)

    # колесо: резина с насечкой на металлической ступице, утоплено в канал
    tw = 0.775
    top = surf(tw, pi / 2).z
    wy, wz = -Lm / 2 + Lm * tw, top - 8.0
    line = [tuple(surf(t, pi / 2) + Vector((0, 0, -0.85))) for t in [tw - 0.115 + 0.23 * k / 18 for k in range(19)]]
    m.pipe('void', line, 4.0, seg=10, flat=0.06, up=(1, 0, 0))
    n = 30
    for k in range(n):
        with m.at((0, wy, wz), (360.0 * k / n, 0, 0)):
            m.box('rubber', (6.6, 1.15, 1.0), at=(0, 0, 11.6), bevel=0.25)
    m.lathe('rubber', [(8.4, -3.5), (11.2, -3.5), (11.2, 3.5), (8.4, 3.5)], at=(0, wy, wz), axis='x', seg=48, closed=True,
            bevel=0.3)
    m.lathe('alu_dark', [(0, -3.9), (8.5, -3.9), (9.1, -3.3), (9.1, 3.3), (8.5, 3.9), (0, 3.9)], at=(0, wy, wz), axis='x',
            seg=40)
    for s in (-1, 1):
        m.lathe('led_accent', [(9.1, s * 3.5), (10.2, s * 3.5), (10.2, s * 3.75), (9.1, s * 3.75)], at=(0, wy, wz), axis='x',
                seg=40, closed=True)

    # основание
    base = [(hw(t) * 0.9, -Lm / 2 + Lm * t) for t in [0.012 + 0.976 * k / 40 for k in range(41)]]
    m.prism('plastic_matte', base + [(-x, y) for x, y in base[::-1]], 0.9, z0=0.0)
    m.build(sharp=radians(42))
    return m
