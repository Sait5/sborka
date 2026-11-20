# Проверочные рендеры: камера, свет, Cycles на видеокарте.
import bpy
from math import radians
from mathutils import Vector
from kit import MM


def setup(samples=64, res=(1400, 900)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for t in ('HIP', 'OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = t
            prefs.get_devices()
            ok = False
            for d in prefs.devices:
                d.use = (d.type == t)
                ok = ok or d.use
            if ok:
                sc.cycles.device = 'GPU'
                break
        except Exception:
            pass
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.transmission_bounces = 8
    sc.cycles.transparent_max_bounces = 16
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.image_settings.file_format = 'PNG'
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass


def world(strength=0.08, color=(0.5, 0.55, 0.65)):
    w = bpy.data.worlds.new('w')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    bg = nt.nodes.new('ShaderNodeBackground')
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg.inputs['Color'].default_value = (color[0], color[1], color[2], 1)
    bg.inputs['Strength'].default_value = strength
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])


def area(name, at, target, size=(300, 300), power=30.0, color=(1, 1, 1)):
    L = bpy.data.lights.new(name, 'AREA')
    L.shape = 'RECTANGLE'
    L.size = size[0] * MM
    L.size_y = size[1] * MM
    L.energy = power
    L.color = color
    ob = bpy.data.objects.new(name, L)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(at) * MM
    d = Vector(target) * MM - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


def shot(path, pos, target, lens=50.0, fstop=None):
    sc = bpy.context.scene
    cam = sc.camera
    if cam is None:
        cd = bpy.data.cameras.new('cam')
        cam = bpy.data.objects.new('cam', cd)
        sc.collection.objects.link(cam)
        sc.camera = cam
    cam.data.lens = lens
    cam.data.clip_start = 0.005
    cam.data.clip_end = 50
    cam.location = Vector(pos) * MM
    d = Vector(target) * MM - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if fstop:
        cam.data.dof.use_dof = True
        cam.data.dof.focus_distance = d.length
        cam.data.dof.aperture_fstop = fstop
    else:
        cam.data.dof.use_dof = False
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
