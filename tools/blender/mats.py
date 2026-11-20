# Материалы сцены. На сайте часть из них подменяется по имени (стекло, экраны, подсветка).
from kit import MAT_SPECS

ACCENT = (1.0, 0.16, 0.05)  # коралловый

MAT_SPECS.update({
    # металл
    'steel_black': dict(color=(0.012, 0.012, 0.013), metal=0.0, rough=0.48),
    'steel_dark': dict(color=(0.09, 0.09, 0.095), metal=1.0, rough=0.34),
    'alu_black': dict(color=(0.018, 0.018, 0.02), metal=1.0, rough=0.36),
    'alu_dark': dict(color=(0.1, 0.1, 0.108), metal=1.0, rough=0.34),
    'alu_silver': dict(color=(0.78, 0.78, 0.8), metal=1.0, rough=0.3),
    'chrome': dict(color=(0.9, 0.9, 0.92), metal=1.0, rough=0.06),
    'nickel': dict(color=(0.72, 0.7, 0.66), metal=1.0, rough=0.14),
    'copper': dict(color=(0.93, 0.45, 0.26), metal=1.0, rough=0.24),
    'gold': dict(color=(1.0, 0.72, 0.28), metal=1.0, rough=0.22),
    'solder': dict(color=(0.7, 0.7, 0.72), metal=1.0, rough=0.4),
    'rad_core': dict(color=(0.02, 0.02, 0.022), metal=1.0, rough=0.5),
    'rad_fin': dict(color=(0.03, 0.03, 0.032), metal=1.0, rough=0.5, double=True),
    # пластик, резина
    'plastic_black': dict(color=(0.014, 0.014, 0.015), rough=0.42),
    'plastic_matte': dict(color=(0.02, 0.02, 0.022), rough=0.8),
    'plastic_gloss': dict(color=(0.008, 0.008, 0.009), rough=0.08),
    'plastic_grey': dict(color=(0.07, 0.07, 0.075), rough=0.5),
    'plastic_white': dict(color=(0.75, 0.75, 0.74), rough=0.45),
    'fan_blade': dict(color=(0.03, 0.03, 0.033), rough=0.3),
    'fan_hub': dict(color=(0.03, 0.03, 0.033), rough=0.3),
    'rubber': dict(color=(0.01, 0.01, 0.01), rough=0.92),
    'void': dict(color=(0.0, 0.0, 0.0), rough=1.0),
    # электроника
    'pcb': dict(color=(0.006, 0.008, 0.008), rough=0.55),
    'pcb_edge': dict(color=(0.05, 0.045, 0.02), rough=0.7),
    'chip': dict(color=(0.012, 0.012, 0.013), rough=0.38),
    'cap_can': dict(color=(0.08, 0.08, 0.085), metal=1.0, rough=0.3),
    'choke': dict(color=(0.03, 0.03, 0.032), rough=0.55),
    'slot_plastic': dict(color=(0.02, 0.02, 0.022), rough=0.35),
    'print_white': dict(color=(0.62, 0.62, 0.62), rough=0.6),
    'print_grey': dict(color=(0.16, 0.16, 0.17), rough=0.6),
    'print_accent': dict(color=ACCENT, rough=0.5),
    # свет
    'led_accent': dict(color=(0.9, 0.9, 0.9), rough=0.5, emit=ACCENT, emit_strength=6.0),
    'led_white': dict(color=(0.9, 0.9, 0.9), rough=0.5, emit=(0.85, 0.9, 1.0), emit_strength=5.0),
    'led_ram': dict(color=(0.9, 0.9, 0.9), rough=0.45, emit=(0.85, 0.9, 1.0), emit_strength=4.0),
    'led_gpu': dict(color=(0.9, 0.9, 0.9), rough=0.45, emit=(0.85, 0.9, 1.0), emit_strength=4.0),
    'led_kbd': dict(color=(0.5, 0.5, 0.5), rough=0.6, emit=(0.85, 0.9, 1.0), emit_strength=0.6),
    'led_wall': dict(color=(0.9, 0.9, 0.9), rough=0.5, emit=(1.0, 0.16, 0.05), emit_strength=8.0),
    'led_bar': dict(color=(0.9, 0.9, 0.9), rough=0.5, emit=(1.0, 0.93, 0.85), emit_strength=6.0),
    'led_power': dict(color=(0.9, 0.9, 0.9), rough=0.4, emit=(0.85, 0.9, 1.0), emit_strength=4.0),
    'legend': dict(color=(0.8, 0.8, 0.8), rough=0.5, emit=(0.9, 0.93, 1.0), emit_strength=1.2),
    # стекло и жидкость
    'glass_panel': dict(color=(0.02, 0.02, 0.022), rough=0.02, transmission=1.0, ior=1.5, double=True),
    'glass_frit': dict(color=(0.004, 0.004, 0.004), rough=0.1),
    'glass_tube': dict(color=(1, 1, 1), rough=0.0, transmission=1.0, ior=1.47, double=True),
    'acrylic': dict(color=(1, 1, 1), rough=0.03, transmission=1.0, ior=1.49, double=True),
    'coolant': dict(color=(1.0, 0.35, 0.2), rough=0.1, emit=ACCENT, emit_strength=1.5),
    # экраны
    'screen_pump': dict(color=(0, 0, 0), rough=0.1, emit=(0.5, 0.6, 0.8), emit_strength=2.0),
    'screen_monitor': dict(color=(0, 0, 0), rough=0.12, emit=(0.4, 0.45, 0.6), emit_strength=2.0),
    'screen_debug': dict(color=(0, 0, 0), rough=0.2, emit=ACCENT, emit_strength=3.0),
    'screen_off': dict(color=(0.004, 0.004, 0.005), rough=0.08),
    # кабели
    'sleeve_black': dict(color=(0.012, 0.012, 0.013), rough=0.85),
    'sleeve_accent': dict(color=(0.75, 0.12, 0.04), rough=0.8),
    'sleeve_white': dict(color=(0.6, 0.6, 0.6), rough=0.8),
    # стол и комната
    'desk_top': dict(color=(0.02, 0.018, 0.017), rough=0.42),
    'desk_leg': dict(color=(0.012, 0.012, 0.013), rough=0.5),
    'wall': dict(color=(0.03, 0.03, 0.033), rough=0.92),
    'floor': dict(color=(0.02, 0.02, 0.02), rough=0.8),
    'fabric': dict(color=(0.011, 0.011, 0.012), rough=0.97),
    'stitch': dict(color=(0.5, 0.08, 0.03), rough=0.9),
    'keycap': dict(color=(0.022, 0.022, 0.024), rough=0.62),
    'keycap_accent': dict(color=(0.8, 0.13, 0.04), rough=0.6),
    'mouse_shell': dict(color=(0.016, 0.016, 0.017), rough=0.55),
})
