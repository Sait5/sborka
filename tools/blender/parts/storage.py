# Накопители на поддоне: два диска 2,5" на кронштейнах, кабели уходят в проёмы поддона.
from kit import Part, rrect, bezier
from layout import *

SSD_X = 120.0
SSD_Z = (392.0, 255.0)          # центры дисков по высоте
SSD_HOLE = 80.0                 # проём под диском: на столько ниже центра


def make_storage(pc):
    s = Part('storage', parent=pc)
    XZ = (90, 0, 0)
    for zc, name in zip(SSD_Z, ('TRAVELLIAN', 'TEAMLINE')):
        with s.at((SSD_X, TRAY, zc), XZ):
            # кронштейн с ушками и резиновыми втулками
            s.prism('steel_black', rrect(78, 110, 4, 4), 1.2, bevel=0.3)
            for sx in (1, -1):
                for sy in (1, -1):
                    s.prism('steel_black', rrect(12, 12, 3, 3, sx * 43, sy * 44), 1.2, bevel=0.3)
                    s.screw(at=(sx * 44.5, sy * 44, 1.2), d=5.0, kind='hex')
            # корпус диска
            s.prism('alu_black', rrect(70, 100, 3.5, 5), 6.8, z0=1.6, bevel=0.6)
            s.prism('alu_dark', rrect(62, 80, 2.5, 4, 0, 5), 0.25, z0=8.4)
            s.text('print_white', name, 6.6, at=(0, 24, 8.68), depth=0.06, spacing=1.2)
            s.text('print_grey', 'SSD  ·  2 TB  ·  SATA 6 Gb/s', 2.5, at=(0, 13, 8.67), depth=0.05, spacing=1.2)
            s.box('print_accent', (46, 0.6, 0.05), at=(0, 7, 8.67))
            s.text('print_grey', 'SBORKA STORAGE', 2.2, at=(-28, -30, 8.67), depth=0.05, align='LEFT', spacing=1.4)
            for k in range(14):
                s.box('print_grey', (0.5 + (k * 7 % 3) * 0.4, 7, 0.05), at=(8 + k * 1.6, -28, 8.67))
            for sx in (1, -1):
                for sy in (1, -1):
                    s.screw(at=(sx * 30.5, sy * 45, 8.4), d=3.4, kind='hex')
            # разъёмы на нижнем торце и штекеры
            s.box('slot_plastic', (42, 4, 4.4), at=(-6, -51.6, 5.0), bevel=0.2)
            s.box('plastic_black', (15, 11, 6.0), at=(-21, -57, 5.0), bevel=0.6)      # данные
            s.box('plastic_black', (22, 11, 6.0), at=(3, -57, 5.0), bevel=0.6)        # питание
        # кабели: вниз от штекеров и в проём поддона
        zb = zc - 62.5
        zh = zc - SSD_HOLE
        ya = TRAY - 5.0
        s.pipe('sleeve_accent', bezier((SSD_X - 21, ya, zb), (SSD_X - 21, ya - 4, zb - 12), (SSD_X - 21, TRAY - 14, zh + 3),
                                       (SSD_X - 21, TRAY + 6, zh), 16), 4.4, seg=12, flat=0.28, up=(1, 0, 0), uv=7.0)
        for k in range(4):
            x = SSD_X + 3 - 6.6 + k * 4.4
            s.pipe('sleeve_black', bezier((x, ya, zb), (x, ya - 5, zb - 12), (x, TRAY - 15, zh + 3), (x, TRAY + 6, zh), 16),
                   1.7, seg=10, uv=7.0)
    s.build()
    return s
