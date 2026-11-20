# Сборка всей сцены. Примеры:
#   blender -b --factory-startup --python build.py -- --parts case,fans --shot wide=600,-900,500/0,0,260/50
#   blender -b --factory-startup --python build.py -- --export
import bpy, sys, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, 'parts')]
import kit, mats, studio
from kit import Part, dup
from layout import *

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def opt(name, default=None):
    if name in argv:
        i = argv.index(name)
        return argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith('--') else True
    return default


def opts(name):
    return [argv[i + 1] for i, a in enumerate(argv) if a == name]


WORK = r'D:\sborka-work'
only = opt('--parts')
only = set(only.split(',')) if isinstance(only, str) else None


def want(p):
    return only is None or p in only


t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
pc = Part('pc')   # всё, что стоит в корпусе

if want('case'):
    from case import make_case
    make_case().root.parent = pc.root
    from storage import make_storage
    make_storage(pc)

if want('fans'):
    from fan import make_fan
    f = make_fan('fan_top1')
    f.root.parent = pc.root
    f.root.location = (TOP_FANS_X[0] * kit.MM, RAD_Y * kit.MM, (RAD_Z - 12.5) * kit.MM)
    f.root.rotation_euler = (3.14159265, 0, 0)
    dup(f, 'fan_top2', (TOP_FANS_X[1], RAD_Y, RAD_Z - 12.5), (180, 0, 0), pc)
    dup(f, 'fan_top3', (TOP_FANS_X[2], RAD_Y, RAD_Z - 12.5), (180, 0, 0), pc)
    dup(f, 'fan_rear', (XR + 2 + 12.5 + 1, REAR_FAN[0], REAR_FAN[1]), (0, 90, 0), pc)

if want('board'):
    from board import make_board
    make_board(pc)

if want('gpu'):
    from videocard import make_gpu
    make_gpu(pc)

if want('loop'):
    from loop import make_loop
    make_loop(pc)

if want('cables'):
    from cables import make_cables
    make_cables(pc)

if want('desk'):
    from desk import make_desk
    make_desk(pc)

hide = opt('--hide')
if isinstance(hide, str):
    for o in list(bpy.data.objects):
        if any(h in o.name for h in hide.split(',')):
            bpy.data.objects.remove(o)
nb = kit.bake_modifiers()
print('meshes:', nb, 'tris (unique, total):', kit.tri_count(), 'build s:', round(time.time() - t0, 1))

shots = opts('--shot')
if shots:
    mode = opt('--light', 'studio')
    studio.setup(samples=int(opt('--samples', 64)), res=tuple(int(v) for v in opt('--res', '1200x780').split('x')))
    if mode == 'studio':
        studio.world(0.12)
        studio.area('key', (500, -900, 900), (0, 0, 250), (700, 700), 34)
        studio.area('fill', (-700, -500, 300), (0, 0, 250), (500, 800), 10, (0.75, 0.85, 1.0))
        studio.area('top', (0, 0, 1100), (0, 0, 250), (900, 600), 14)
    else:
        studio.world(0.012)
        studio.area('moon', (-900, -700, 900), (0, 0, 250), (600, 600), 6, (0.6, 0.72, 1.0))
    if not want('desk'):
        fl = Part('floor_tmp')
        fl.box('desk_top', (3000, 3000, 10), at=(0, 0, -5))
        fl.build()
    for s in shots:
        name, spec = s.split('=')
        p = spec.split('/')
        pos = tuple(float(v) for v in p[0].split(','))
        tgt = tuple(float(v) for v in p[1].split(','))
        lens = float(p[2]) if len(p) > 2 else 50.0
        fst = float(p[3]) if len(p) > 3 else None
        studio.shot(os.path.join(WORK, 'review', name + '.png'), pos, tgt, lens, fst)
    print('render s:', round(time.time() - t0, 1))

if opt('--save'):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'blend', 'sborka.blend'))

if opt('--export'):
    out = os.path.normpath(os.path.join(HERE, '..', '..', 'public', 'models', 'sborka.glb'))
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=False, export_yup=True,
                              export_cameras=False, export_lights=False, export_extras=False,
                              export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
                              export_draco_position_quantization=14, export_draco_normal_quantization=12,
                              export_draco_texcoord_quantization=12)
    print('exported', out, round(os.path.getsize(out) / 1e6, 2), 'MB')
