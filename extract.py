#!/usr/bin/env python3
"""Regenerate shrimp_data.json: cut the shrimp out of the source memes (orange
hue-key), clean the mask, and pair each with its hand-traced spine.

Usage: extract.py <photo_shrimp.png> <cartoon_shrimp.png>
Spine points are (x, y, half_width_back, half_width_belly) in source-image
coordinates, head to tail. `gaps` are segment indices where the chair occluded
the body; the renderer collapses them so the texture stays continuous.
"""
from PIL import Image
from collections import deque
import base64, io, json, sys

SPINES = {
 'photo': dict(gaps=[9, 12], pts=[
    (348,62,12,55),(325,68,16,50),(290,70,22,45),(255,70,28,45),(220,72,30,60),
    (185,76,30,80),(150,84,30,90),(118,96,28,55),(92,115,26,35),(78,140,22,25),
    (82,162,18,20),(95,176,16,18),(110,186,15,16),(138,183,20,20),(175,188,20,20),
    (210,190,20,20),(245,185,18,18)]),
 'cartoon': dict(gaps=[7, 10], pts=[
    (335,152,18,30),(290,150,25,35),(250,143,30,45),(205,138,32,72),(160,138,32,72),
    (122,150,30,50),(95,172,28,32),(80,198,26,26),(84,222,24,24),(102,240,22,22),
    (124,246,22,22),(142,239,24,24),(168,227,26,26),(196,212,26,26)]),
}

def cutout(path):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    px = im.load()
    mask = [[px[x, y][0] - px[x, y][2] > 25 and px[x, y][0] - px[x, y][1] > 5
             and max(px[x, y]) - min(px[x, y]) > 30 for x in range(w)] for y in range(h)]
    # drop specks: connected components < 40 px
    seen = [[False] * w for _ in range(h)]
    for y0 in range(h):
        for x0 in range(w):
            if mask[y0][x0] and not seen[y0][x0]:
                comp = []; q = deque([(x0, y0)]); seen[y0][x0] = True
                while q:
                    x, y = q.popleft(); comp.append((x, y))
                    for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                        if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True; q.append((nx, ny))
                if len(comp) < 40:
                    for x, y in comp: mask[y][x] = False
    # fill enclosed holes (eye, pale spots): flood background from the borders
    outside = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        for y in (0, h - 1): q.append((x, y))
    for y in range(h):
        for x in (0, w - 1): q.append((x, y))
    for x, y in q: outside[y][x] = not mask[y][x]
    q = deque(p for p in q if outside[p[1]][p[0]])
    while q:
        x, y = q.popleft()
        for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if 0 <= nx < w and 0 <= ny < h and not mask[ny][nx] and not outside[ny][nx]:
                outside[ny][nx] = True; q.append((nx, ny))
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    op = out.load()
    for y in range(h):
        for x in range(w):
            if mask[y][x] or not outside[y][x]:
                op[x, y] = px[x, y] + (255,)
    return out

if __name__ == '__main__':
    data = {}
    for key, path in zip(('photo', 'cartoon'), sys.argv[1:3]):
        img = cutout(path)
        buf = io.BytesIO(); img.save(buf, 'PNG', optimize=True)
        data[key] = dict(src='data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(),
                         **SPINES[key])
        print(key, img.size, len(buf.getvalue()) // 1024, 'KB')
    json.dump(data, open('shrimp_data.json', 'w'))
