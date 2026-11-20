# Набор для процедурного моделирования: всё задаётся в миллиметрах,
# в сцену попадает в метрах. Одна деталь (Part) = пустышка-корень + по одному
# мешу на каждую пару «материал, фаска».
import bpy, bmesh, math
from math import sin, cos, pi, tau, radians, sqrt
from mathutils import Vector, Matrix, Euler

MM = 0.001
SHARP = radians(32)
_FONTS = {}
_MATS = {}
MAT_SPECS = {}


def XF(at=(0, 0, 0), rot=(0, 0, 0), scale=None):
    m = Matrix.Translation(Vector(at)) @ Euler(
        (radians(rot[0]), radians(rot[1]), radians(rot[2])), 'XYZ').to_matrix().to_4x4()
    if scale is not None:
        if isinstance(scale, (int, float)):
            scale = (scale, scale, scale)
        m = m @ Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))
    return m


AXIS = {'z': (0, 0, 0), 'x': (0, 90, 0), 'y': (-90, 0, 0), '-z': (180, 0, 0), '-x': (0, -90, 0), '-y': (90, 0, 0)}


def rrect(w, h, r, seg=6, cx=0.0, cy=0.0):
    r = max(1e-4, min(r, w / 2 - 1e-4, h / 2 - 1e-4))
    pts = []
    for sx, sy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox = cx + sx * (w / 2 - r)
        oy = cy + sy * (h / 2 - r)
        for i in range(seg + 1):
            a = radians(a0 + 90 * i / seg)
            pts.append((ox + r * cos(a), oy + r * sin(a)))
    return pts


def circ(r, n=32, cx=0.0, cy=0.0, a0=0.0):
    return [(cx + r * cos(a0 + tau * i / n), cy + r * sin(a0 + tau * i / n)) for i in range(n)]


def slot(w, h, n=8, cx=0.0, cy=0.0):
    """Овальная прорезь (стадион) вдоль X."""
    return rrect(w, h, h / 2 - 1e-3, n, cx, cy)


def hexagon(r, cx=0.0, cy=0.0, a0=0.0):
    return circ(r, 6, cx, cy, a0)


def fillet(pts, r, seg=8):
    """Ломаная в 3D со скруглёнными углами."""
    P = [Vector(p) for p in pts]
    out = [P[0]]
    for i in range(1, len(P) - 1):
        a, b, c = P[i - 1], P[i], P[i + 1]
        d1 = a - b
        d2 = c - b
        l1, l2 = d1.length, d2.length
        d1.normalize()
        d2.normalize()
        ang = d1.angle(d2)
        if ang > pi - 1e-3 or ang < 1e-3:
            out.append(b)
            continue
        t = min(r / math.tan(ang / 2), l1 * 0.49, l2 * 0.49)
        rr = t * math.tan(ang / 2)
        p1 = b + d1 * t
        cen = b + (d1 + d2).normalized() * (rr / math.sin(ang / 2))
        v1 = p1 - cen
        v2 = (b + d2 * t) - cen
        tot = v1.angle(v2)
        axis = v1.cross(v2).normalized()
        for k in range(seg + 1):
            out.append(cen + Matrix.Rotation(tot * k / seg, 3, axis) @ v1)
    out.append(P[-1])
    return out


def bezier(p0, p1, p2, p3, n=16):
    P = [Vector(p) for p in (p0, p1, p2, p3)]
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append(P[0] * u ** 3 + P[1] * 3 * u * u * t + P[2] * 3 * u * t * t + P[3] * t ** 3)
    return out


def font(name='bahnschrift'):
    if name not in _FONTS:
        _FONTS[name] = bpy.data.fonts.load(r'C:\Windows\Fonts\%s.ttf' % name)
    return _FONTS[name]


def MAT(name):
    if name in _MATS:
        return _MATS[name]
    spec = MAT_SPECS.get(name)
    if spec is None:
        raise KeyError('нет материала ' + name)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    c = spec.get('color', (0.8, 0.8, 0.8))
    b.inputs['Base Color'].default_value = (c[0], c[1], c[2], 1)
    b.inputs['Metallic'].default_value = spec.get('metal', 0.0)
    b.inputs['Roughness'].default_value = spec.get('rough', 0.5)
    if 'emit' in spec:
        e = spec['emit']
        b.inputs['Emission Color'].default_value = (e[0], e[1], e[2], 1)
        b.inputs['Emission Strength'].default_value = spec.get('emit_strength', 1.0)
    if 'transmission' in spec:
        b.inputs['Transmission Weight'].default_value = spec['transmission']
        b.inputs['IOR'].default_value = spec.get('ior', 1.5)
    if 'alpha' in spec:
        b.inputs['Alpha'].default_value = spec['alpha']
        m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else m.blend_method
    if 'coat' in spec:
        b.inputs['Coat Weight'].default_value = spec['coat']
        b.inputs['Coat Roughness'].default_value = spec.get('coat_rough', 0.05)
    if 'spec' in spec:
        b.inputs['Specular IOR Level'].default_value = spec['spec']
    m.use_backface_culling = not spec.get('double', False)
    _MATS[name] = m
    return m


class _Ctx:
    def __init__(self, part, m):
        self.part, self.m = part, m

    def __enter__(self):
        self.part._stack.append(self.part.cur)
        self.part.cur = self.part.cur @ self.m
        return self.part

    def __exit__(self, *a):
        self.part.cur = self.part._stack.pop()


class Part:
    def __init__(self, name, at=(0, 0, 0), rot=(0, 0, 0), parent=None):
        self.name = name
        self.root = bpy.data.objects.new(name, None)
        self.root.empty_display_size = 0.01
        bpy.context.scene.collection.objects.link(self.root)
        self.root.location = Vector(at) * MM
        self.root.rotation_euler = Euler([radians(a) for a in rot], 'XYZ')
        if parent is not None:
            self.root.parent = parent.root if isinstance(parent, Part) else parent
        self.groups = {}
        self.cur = Matrix.Identity(4)
        self._stack = []
        self.objects = []

    # --- служебное
    def at(self, at=(0, 0, 0), rot=(0, 0, 0), scale=None):
        return _Ctx(self, XF(at, rot, scale))

    def g(self, mat, bevel=0.0):
        key = (mat, round(bevel, 3))
        if key not in self.groups:
            self.groups[key] = bmesh.new()
        return self.groups[key]

    def _fin(self, bm, verts, at, rot, faces=None, scale=None):
        if faces:
            bmesh.ops.recalc_face_normals(bm, faces=faces)
        bmesh.ops.transform(bm, matrix=self.cur @ XF(at, rot, scale), verts=verts)
        return self

    # --- примитивы
    def box(self, mat, size, at=(0, 0, 0), rot=(0, 0, 0), bevel=0.0):
        bm = self.g(mat, bevel)
        r = bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((size[0], size[1], size[2], 1.0)))
        return self._fin(bm, r['verts'], at, rot)

    def cyl(self, mat, r, h, at=(0, 0, 0), rot=(0, 0, 0), seg=32, r2=None, bevel=0.0, axis=None):
        bm = self.g(mat, bevel)
        res = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r,
                                    radius2=r if r2 is None else r2, depth=h)
        if axis:
            m = XF(at) @ XF(rot=AXIS[axis]) @ XF(rot=rot)
            bmesh.ops.transform(bm, matrix=self.cur @ m, verts=res['verts'])
            return self
        return self._fin(bm, res['verts'], at, rot)

    def sphere(self, mat, r, at=(0, 0, 0), rot=(0, 0, 0), seg=24, scale=None):
        bm = self.g(mat, 0)
        res = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(8, seg // 2), radius=r)
        return self._fin(bm, res['verts'], at, rot, scale=scale)

    def prism(self, mat, pts, h, at=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, z0=0.0, taper=None):
        """Выдавленный контур. taper=(sx, sy) — масштаб верхней грани."""
        bm = self.g(mat, bevel)
        n = len(pts)
        vb = [bm.verts.new((x, y, z0)) for x, y in pts]
        if taper:
            vt = [bm.verts.new((x * taper[0], y * taper[1], z0 + h)) for x, y in pts]
        else:
            vt = [bm.verts.new((x, y, z0 + h)) for x, y in pts]
        f = [bm.faces.new(vb[::-1]), bm.faces.new(vt)]
        for i in range(n):
            j = (i + 1) % n
            f.append(bm.faces.new((vb[i], vb[j], vt[j], vt[i])))
        return self._fin(bm, vb + vt, at, rot, f)

    def plate(self, mat, outline, holes, h, at=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, z0=0.0):
        """Пластина с отверстиями."""
        bm = self.g(mat, bevel)
        loops, edges = [], []
        for pts in [outline] + list(holes):
            vs = [bm.verts.new((x, y, z0)) for x, y in pts]
            edges += [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
            loops.append(vs)
        res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges, normal=(0, 0, 1))
        bot = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]
        d = bmesh.ops.duplicate(bm, geom=bot)
        vmap = d['vert_map']
        top = [g for g in d['geom'] if isinstance(g, bmesh.types.BMFace)]
        nv = [g for g in d['geom'] if isinstance(g, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=nv, vec=(0, 0, h))
        faces = bot + top
        allv = list(nv)
        for vs in loops:
            allv += vs
            for i in range(len(vs)):
                a, b = vs[i], vs[(i + 1) % len(vs)]
                if a in vmap and b in vmap:
                    faces.append(bm.faces.new((a, b, vmap[b], vmap[a])))
                else:
                    self.warn = getattr(self, 'warn', 0) + 1
        if getattr(self, 'warn', 0):
            print('ВНИМАНИЕ: пересекающиеся контуры в пластине', self.name, mat, self.warn)
            self.warn = 0
        return self._fin(bm, allv, at, rot, faces)

    def lathe(self, mat, prof, at=(0, 0, 0), rot=(0, 0, 0), seg=48, bevel=0.0, closed=False, axis=None):
        """Тело вращения вокруг Z. prof = [(r, z), ...]."""
        bm = self.g(mat, bevel)
        rings, allv, faces = [], [], []
        for r, z in prof:
            if r <= 1e-6:
                ring = [bm.verts.new((0, 0, z))]
            else:
                ring = [bm.verts.new((r * cos(tau * i / seg), r * sin(tau * i / seg), z)) for i in range(seg)]
            rings.append(ring)
            allv += ring
        pairs = list(zip(rings[:-1], rings[1:]))
        if closed:
            pairs.append((rings[-1], rings[0]))
        for a, b in pairs:
            if len(a) == 1 and len(b) == 1:
                continue
            for i in range(seg):
                j = (i + 1) % seg
                if len(a) == 1:
                    faces.append(bm.faces.new((a[0], b[i], b[j])))
                elif len(b) == 1:
                    faces.append(bm.faces.new((a[i], a[j], b[0])))
                else:
                    faces.append(bm.faces.new((a[i], a[j], b[j], b[i])))
        if not closed:
            if len(rings[0]) > 1:
                faces.append(bm.faces.new(rings[0][::-1]))
            if len(rings[-1]) > 1:
                faces.append(bm.faces.new(rings[-1]))
        if axis:
            bmesh.ops.recalc_face_normals(bm, faces=faces)
            m = XF(at) @ XF(rot=AXIS[axis]) @ XF(rot=rot)
            bmesh.ops.transform(bm, matrix=self.cur @ m, verts=allv)
            return self
        return self._fin(bm, allv, at, rot, faces)

    def pipe(self, mat, pts, r, at=(0, 0, 0), rot=(0, 0, 0), seg=16, caps=True, bevel=0.0, closed=False,
             up=(0, 0, 1), flat=1.0, uv=None):
        """Труба вдоль ломаной. r — число или функция t∈[0,1] → радиус. flat — сплющивание сечения."""
        bm = self.g(mat, bevel)
        P = [Vector(p) for p in pts]
        n = len(P)
        T = []
        for i in range(n):
            if closed:
                t = P[(i + 1) % n] - P[i - 1]
            elif i == 0:
                t = P[1] - P[0]
            elif i == n - 1:
                t = P[-1] - P[-2]
            else:
                t = (P[i + 1] - P[i]).normalized() + (P[i] - P[i - 1]).normalized()
            T.append(t.normalized())
        upv = Vector(up)
        if abs(T[0].dot(upv)) > 0.9:
            upv = Vector((1, 0, 0)) if abs(T[0].x) < 0.9 else Vector((0, 1, 0))
        N = (upv - T[0] * upv.dot(T[0])).normalized()
        rings, allv, faces = [], [], []
        for i in range(n):
            if i > 0:
                ax = T[i - 1].cross(T[i])
                if ax.length > 1e-9:
                    N = Matrix.Rotation(T[i - 1].angle(T[i]), 3, ax.normalized()) @ N
                N = (N - T[i] * N.dot(T[i])).normalized()
            B = T[i].cross(N)
            rr = r(i / (n - 1)) if callable(r) else r
            ring = [bm.verts.new(P[i] + (N * cos(tau * k / seg) + B * sin(tau * k / seg) * flat) * rr)
                    for k in range(seg)]
            rings.append(ring)
            allv += ring
        pairs = list(zip(rings[:-1], rings[1:]))
        if closed:
            pairs.append((rings[-1], rings[0]))
        if uv:
            lay = bm.loops.layers.uv.verify()
            acc = [0.0]
            for i in range(1, n):
                acc.append(acc[-1] + (P[i] - P[i - 1]).length)
        for pi, (a, b) in enumerate(pairs):
            for k in range(seg):
                j = (k + 1) % seg
                f = bm.faces.new((a[k], a[j], b[j], b[k]))
                faces.append(f)
                if uv:
                    va, vb = acc[pi] / uv, acc[min(pi + 1, n - 1)] / uv
                    for l, c in zip(f.loops, ((k / seg, va), ((k + 1) / seg, va), ((k + 1) / seg, vb), (k / seg, vb))):
                        l[lay].uv = c
        if caps and not closed:
            faces.append(bm.faces.new(rings[0][::-1]))
            faces.append(bm.faces.new(rings[-1]))
        return self._fin(bm, allv, at, rot, faces)

    def grid(self, mat, P, at=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, close_u=False, close_v=False, cap=False,
             recalc=True):
        """Поверхность по сетке точек P[i][j]."""
        bm = self.g(mat, bevel)
        V = [[bm.verts.new(p) for p in row] for row in P]
        nu, nv = len(V), len(V[0])
        faces = []
        for i in range(nu if close_u else nu - 1):
            for j in range(nv if close_v else nv - 1):
                i2, j2 = (i + 1) % nu, (j + 1) % nv
                faces.append(bm.faces.new((V[i][j], V[i2][j], V[i2][j2], V[i][j2])))
        if cap and close_v:
            faces.append(bm.faces.new(V[0][::-1]))
            faces.append(bm.faces.new(V[-1]))
        allv = [v for row in V for v in row]
        return self._fin(bm, allv, at, rot, faces if recalc else None)

    def text(self, mat, s, size, at=(0, 0, 0), rot=(0, 0, 0), depth=0.1, fnt='bahnschrift', align='CENTER',
             valign='CENTER', spacing=1.0, bevel=0.0, shear=0.0):
        cu = bpy.data.curves.new('t', 'FONT')
        cu.body = s
        cu.size = size
        cu.extrude = depth / 2
        cu.align_x = align
        cu.align_y = valign
        cu.space_character = spacing
        cu.shear = shear
        cu.font = font(fnt)
        cu.resolution_u = 4
        ob = bpy.data.objects.new('t', cu)
        bpy.context.scene.collection.objects.link(ob)
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        me.transform(self.cur @ XF(at, rot))
        bm = self.g(mat, bevel)
        bm.from_mesh(me)
        bpy.data.objects.remove(ob)
        bpy.data.curves.remove(cu)
        bpy.data.meshes.remove(me)
        return self

    # --- готовые мелочи
    def screw(self, at=(0, 0, 0), rot=(0, 0, 0), d=6.0, mat='steel_dark', kind='phillips', h=None):
        """Винт: головка диаметром d, шлиц."""
        h = h or d * 0.38
        with self.at(at, rot):
            # нижняя часть головки и настоящий шлиц: верх — пластина с вырезом
            self.cyl(mat, d * 0.5, h * 0.5, at=(0, 0, h * 0.25), seg=28)
            if kind == 'phillips':
                L, w = d * 0.33, d * 0.07
                hole = [(L, -w), (L, w), (w, w), (w, L), (-w, L), (-w, w), (-L, w), (-L, -w), (-w, -w), (-w, -L),
                        (w, -L), (w, -w)]
            elif kind == 'hex':
                hole = hexagon(d * 0.27)
            else:
                hole = circ(d * 0.2, 16)
            self.plate(mat, circ(d * 0.5, 28), [hole], h * 0.5, z0=h * 0.5, bevel=min(0.35, d * 0.05))
        return self

    def thumbscrew(self, at=(0, 0, 0), rot=(0, 0, 0), d=11.0, h=8.0, mat='alu_black'):
        with self.at(at, rot):
            n = 36
            pts = []
            for i in range(n * 2):
                rr = d / 2 if i % 2 == 0 else d / 2 - 0.45
                a = tau * i / (n * 2)
                pts.append((rr * cos(a), rr * sin(a)))
            self.prism(mat, pts, h * 0.72, z0=h * 0.14)
            self.cyl(mat, d / 2 - 0.5, h * 0.14, at=(0, 0, h * 0.07), seg=36)
            self.lathe(mat, [(d / 2 - 0.5, h * 0.86), (d / 2 - 1.4, h), (0, h)], seg=36)
            self.box('void', (d * 0.6, d * 0.1, 1.2), at=(0, 0, h - 0.5))
        return self

    # --- сборка мешей
    def build(self, sharp=SHARP, segments=2):
        for (matname, bevel), bm in self.groups.items():
            if not bm.verts:
                bm.free()
                continue
            bmesh.ops.transform(bm, matrix=Matrix.Scale(MM, 4), verts=bm.verts)
            me = bpy.data.meshes.new('%s.%s' % (self.name, matname))
            bm.to_mesh(me)
            bm.free()
            me.materials.append(MAT(matname))
            me.shade_smooth()
            me.set_sharp_from_angle(angle=sharp)
            ob = bpy.data.objects.new(me.name, me)
            bpy.context.scene.collection.objects.link(ob)
            ob.parent = self.root
            if bevel > 0:
                m = ob.modifiers.new('bevel', 'BEVEL')
                m.width = bevel * MM
                m.segments = segments
                m.limit_method = 'ANGLE'
                m.angle_limit = sharp
                m.use_clamp_overlap = True
            w = ob.modifiers.new('wn', 'WEIGHTED_NORMAL')
            w.keep_sharp = True
            self.objects.append(ob)
        self.groups = {}
        return self


def screen(name, w, h, at=(0, 0, 0), rot=(0, 0, 0), parent=None, mat=None, corner=0.0):
    """Плоскость-экран с развёрткой 0..1, смотрит по +Z."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    pts = rrect(w, h, corner, 8) if corner > 0 else [(w / 2, h / 2), (-w / 2, h / 2), (-w / 2, -h / 2), (w / 2, -h / 2)]
    vs = [bm.verts.new((x * MM, y * MM, 0)) for x, y in pts]
    f = bm.faces.new(vs)
    for l in f.loops:
        l[uv].uv = (l.vert.co.x / (w * MM) + 0.5, l.vert.co.y / (h * MM) + 0.5)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MAT(mat or name))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(at) * MM
    ob.rotation_euler = Euler([radians(a) for a in rot], 'XYZ')
    if parent is not None:
        ob.parent = parent.root if isinstance(parent, Part) else parent
    return ob


def anchor(name, at=(0, 0, 0), rot=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_size = 0.02
    bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(at) * MM
    ob.rotation_euler = Euler([radians(a) for a in rot], 'XYZ')
    if parent is not None:
        ob.parent = parent.root if isinstance(parent, Part) else parent
    return ob


def box_uv(ob, scale_mm=100.0):
    """Кубическая развёртка: 1 единица UV = scale_mm."""
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    s = 1.0 / (scale_mm * MM)
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda k: abs(n[k]))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if ax == 2:
                uv[li].uv = (co.x * s, co.y * s)
            elif ax == 1:
                uv[li].uv = (co.x * s, co.z * s)
            else:
                uv[li].uv = (co.y * s, co.z * s)


def dup(src, name, at=(0, 0, 0), rot=(0, 0, 0), parent=None):
    """Копия детали с общими мешами (экземпляр)."""
    src_root = src.root if isinstance(src, Part) else src

    def rec(o, par):
        c = o.copy()
        bpy.context.scene.collection.objects.link(c)
        c.parent = par
        for ch in o.children:
            rec(ch, c)
        return c

    root = rec(src_root, None)
    root.name = name
    root.location = Vector(at) * MM
    root.rotation_euler = Euler([radians(a) for a in rot], 'XYZ')
    if parent is not None:
        root.parent = parent.root if isinstance(parent, Part) else parent
    for o in [root] + list(root.children_recursive):
        if o is not root and o.type == 'EMPTY':
            base = o.name.rsplit('.', 1)[0]
            o.name = name + '__' + base
    return root


def bake_modifiers():
    """Применить модификаторы один раз на меш (экземпляры остаются общими)."""
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    done = {}
    for ob in [o for o in bpy.data.objects if o.type == 'MESH' and o.modifiers]:
        old = ob.data
        if old.name not in done:
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
            me.name = old.name + '_b'
            done[old.name] = me
        ob.modifiers.clear()
        ob.data = done[old.name]
    return len(done)


def tri_count():
    n = 0
    seen = set()
    inst = 0
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        me = ob.data
        me.calc_loop_triangles()
        t = len(me.loop_triangles)
        inst += t
        if me.name not in seen:
            seen.add(me.name)
            n += t
    return n, inst
