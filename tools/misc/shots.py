# Уменьшенные снимки проектов для стартовой страницы браузера.
import bpy, os
SRC = r'C:\Users\Admin\Desktop\Новая папка\hh-portfolio'
DST = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'public', 'shots'))
M = {'velocity': '2a-velocity-atelier.jpg', 'resonance': '6-resonance.png', 'city': '8-city.png', 'iphone18': '7-iphone18.png',
     'backrooms': '9-backrooms.png', 'intercargo': '4-intercargo.png', 'travellian': '5-travellian.png',
     'teamline': '3-teamline.png', 'forma': '2-forma.png'}
sc = bpy.context.scene
sc.render.image_settings.file_format = 'JPEG'
sc.render.image_settings.quality = 84
sc.view_settings.view_transform = 'Standard'
for k, f in M.items():
    img = bpy.data.images.load(os.path.join(SRC, f))
    w, h = img.size
    nw = 720
    img.scale(nw, int(h * nw / w))
    img.save_render(os.path.join(DST, k + '.jpg'), scene=sc)
    print(k, w, h)
