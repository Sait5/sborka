# Вентилятор: рамка, световые полосы, ротор с лопастями, мотор со стойками.
from math import sin, cos, tau, radians, sqrt, pi
from kit import Part, rrect, circ, bezier


def blade_rows(r0, r1, blades_span, pitch0, pitch1, sweep, ns=14, nc=12, tmax=1.5):
    """Одна лопасть: ряды замкнутых сечений от втулки к краю."""
    rows = []
    for i in range(ns):
        s = i / (ns - 1)
        r = r0 + (r1 - r0) * s
        span = radians(blades_span * (1.0 - 0.18 * s))
        sw = radians(sweep) * s ** 1.4
        ph = pitch0 + (pitch1 - pitch0) * s
        tip = 1.0 - 0.35 * max(0.0, (s - 0.86) / 0.14) ** 2  # скругление у края
        top, bot = [], []
        for j in range(nc + 1):
            u = j / nc
            uu = 0.5 + (u - 0.5) * tip
            th = sw + (uu - 0.5) * span
            z = (uu - 0.5) * ph + 1.6 * sin(pi * uu)
            t = tmax * (0.16 + 0.84 * sin(pi * u) ** 0.55) * (1.0 - 0.3 * s)
            dt, dz = r * span, ph
            L = sqrt(dt * dt + dz * dz)
            nx, nz = -dz / L, dt / L  # нормаль в плоскости (касательная, z)
            x, y = r * cos(th), r * sin(th)
            tx, ty = -sin(th), cos(th)
            top.append((x + tx * nx * t / 2, y + ty * nx * t / 2, z + nz * t / 2))
            bot.append((x - tx * nx * t / 2, y - ty * nx * t / 2, z - nz * t / 2))
        rows.append(top + bot[::-1])
    return rows


def make_fan(name='fan', size=120.0, thick=25.0, blades=9, hub_r=21.0, light=True):
    half = size / 2
    duct = half - 3.2
    f = Part(name)
    hole_o = half - 7.5
    corner = [(sx * hole_o, sy * hole_o) for sx in (1, -1) for sy in (1, -1)]
    # рамка: две плиты-фланца и кольцевой канал
    fl = 4.2
    holes = [circ(duct, 96)] + [circ(2.2, 16, cx, cy) for cx, cy in corner]
    f.plate('plastic_black', rrect(size, size, 7.5, 8), holes, fl, z0=-thick / 2, bevel=0.5)
    f.plate('plastic_black', rrect(size, size, 7.5, 8), holes, fl, z0=thick / 2 - fl, bevel=0.5)
    f.lathe('plastic_black', [(duct, -thick / 2 + fl), (duct + 2.2, -thick / 2 + fl), (duct + 2.2, thick / 2 - fl),
                              (duct, thick / 2 - fl)], seg=96, closed=True)
    # угловые стойки между фланцами
    for cx, cy in corner:
        f.lathe('plastic_black', [(4.6, -thick / 2 + fl), (4.6, thick / 2 - fl)], at=(cx, cy, 0), seg=20)
        for z, rz in ((thick / 2, 0), (-thick / 2, 180)):
            f.lathe('rubber', [(2.4, 0), (6.2, 0), (6.2, 0.9), (5.6, 1.3), (2.4, 1.3)], at=(cx, cy, z - (1.3 if rz else 0)),
                    seg=24, closed=True)
    # боковые стенки-накладки со световой полосой
    side_h = thick - 2 * fl
    for k in range(4):
        with f.at(rot=(0, 0, 90 * k)):
            f.box('plastic_black', (size - 22, 1.6, side_h), at=(0, half - 0.8 - 0.3, 0), bevel=0.3)
            if light and k % 2 == 0:
                f.box('led_accent', (size - 30, 1.2, 3.2), at=(0, half - 0.25, 0), bevel=0.4)
                f.box('alu_dark', (size - 26, 0.8, 2.6), at=(0, half - 0.35, 5.6), bevel=0.25)
                f.box('alu_dark', (size - 26, 0.8, 2.6), at=(0, half - 0.35, -5.6), bevel=0.25)
    if light:
        # световое кольцо на входе канала
        f.lathe('led_accent', [(duct - 0.2, thick / 2 - 0.2), (duct + 1.6, thick / 2 - 0.2), (duct + 1.6, thick / 2 + 0.5),
                               (duct - 0.2, thick / 2 + 0.5)], seg=96, closed=True)
    # мотор и стойки сзади
    zb = -thick / 2
    f.lathe('plastic_black', [(0, zb + 0.4), (hub_r - 1.0, zb + 0.4), (hub_r - 0.2, zb + 1.2), (hub_r - 0.2, zb + 5.0),
                              (hub_r - 3.0, zb + 5.6), (0, zb + 5.6)], seg=64)
    f.lathe('print_grey', [(0, zb + 0.3), (hub_r - 4.0, zb + 0.3), (hub_r - 4.0, zb + 0.42), (0, zb + 0.42)], seg=48)
    f.text('print_white', 'DC 12V  0.28A', 2.2, at=(0, 5.5, zb + 0.28), rot=(180, 0, 0), depth=0.06)
    f.text('print_white', 'SBORKA 120', 3.0, at=(0, -1.0, zb + 0.28), rot=(180, 0, 0), depth=0.06)
    f.text('print_white', 'PWM · FDB', 2.0, at=(0, -6.5, zb + 0.28), rot=(180, 0, 0), depth=0.06)
    for k in range(4):
        a0 = radians(45 + 90 * k)
        a1 = a0 + radians(26)
        p0 = (hub_r * 0.9 * cos(a0), hub_r * 0.9 * sin(a0), zb + 2.6)
        p3 = ((duct + 1.0) * cos(a1), (duct + 1.0) * sin(a1), zb + 2.6)
        pm = (hub_r * 1.9 * cos(a0 + 0.05), hub_r * 1.9 * sin(a0 + 0.05), zb + 2.6)
        pn = (duct * 0.8 * cos(a1 - 0.1), duct * 0.8 * sin(a1 - 0.1), zb + 2.6)
        path = bezier(p0, pm, pn, p3, 14)
        f.pipe('plastic_black', path, lambda t: 2.3 - 0.6 * t, seg=10, flat=0.55, up=(0, 0, 1))
    # провод вдоль одной стойки
    a1 = radians(45 + 26)
    f.pipe('sleeve_black', bezier((hub_r * 0.8 * cos(radians(45)), hub_r * 0.8 * sin(radians(45)), zb + 4.2),
                                  (hub_r * 1.9 * cos(radians(48)), hub_r * 1.9 * sin(radians(48)), zb + 4.4),
                                  (duct * 0.8 * cos(a1 - 0.1), duct * 0.8 * sin(a1 - 0.1), zb + 4.4),
                                  ((duct + 1.5) * cos(a1), (duct + 1.5) * sin(a1), zb + 4.2), 14), 1.1, seg=8)
    f.build()

    # ротор
    r = Part('rotor', parent=f)
    zt = thick / 2 - 2.2
    zl = -thick / 2 + 6.4
    r.lathe('fan_hub', [(0, zt), (hub_r - 3.2, zt), (hub_r - 1.2, zt - 0.6), (hub_r, zt - 2.4), (hub_r, zl),
                          (hub_r - 1.6, zl), (hub_r - 1.6, zt - 3.0), (0, zt - 3.0)], seg=72)
    # наклейка втулки
    r.lathe('alu_dark', [(0, zt), (hub_r - 4.4, zt), (hub_r - 4.4, zt + 0.25), (0, zt + 0.25)], seg=64)
    r.lathe('print_accent', [(hub_r - 7.2, zt + 0.25), (hub_r - 6.2, zt + 0.25), (hub_r - 6.2, zt + 0.32),
                             (hub_r - 7.2, zt + 0.32)], seg=64, closed=True)
    r.text('print_white', 'S', 13.0, at=(0, 0.3, zt + 0.3), depth=0.08)
    rows = blade_rows(hub_r - 0.6, duct - 1.4, blades_span=360.0 / blades * 0.98, pitch0=thick - 12.0,
                      pitch1=thick - 15.5, sweep=34.0)
    zc = (zt - 2.4 + zl) / 2
    for k in range(blades):
        r.grid('fan_blade', rows, at=(0, 0, zc), rot=(0, 0, 360.0 * k / blades), close_v=True, cap=True)
    r.build()
    return f
