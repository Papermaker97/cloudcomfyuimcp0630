# Makes a render-pile layout of lying Ppomos packed wall to wall like jellies in a jar, seen straight on.
# python3 gen-jelly-wall.py [seed] > render-jelly-wall.json; then python3 render-pile.py render-jelly-wall.json out.html
import json, math, random, sys

rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 7)

HALF_H = 6.0                  # half-height of the view (model units); portrait 9:16
HALF_W = HALF_H * 9 / 16
DX, DY = 1.62, 1.18           # packing step: tighter than a Ppomo (~1.8 x 1.3) so neighbours press together
SCALE = 1.15

# mostly Ppomo grey and soft pink, with cream, peach and lilac mixed in
PALETTE = ['#AEB3C2'] * 4 + ['#F2AABD'] * 4 + ['#F3E6D8'] * 2 + ['#F2C7A4'] * 2 + ['#D2C0EC'] * 2 + ['#BCD3F0']

def pose():
    r = rng.random()
    if r < 0.68:   # face front
        return dict(ry=rng.uniform(-0.45, 0.45), rx=rng.uniform(-0.15, 0.25))
    if r < 0.79:   # showing its butt
        return dict(ry=math.pi + rng.uniform(-0.35, 0.35), rx=rng.uniform(-0.2, 0.2))
    if r < 0.92:   # side on, the whole loaf
        return dict(ry=rng.choice([-1, 1]) * (math.pi / 2 + rng.uniform(-0.3, 0.3)), rx=rng.uniform(-0.1, 0.1))
    return dict(ry=rng.uniform(-0.4, 0.4), rx=rng.uniform(0.6, 0.9))   # tipped back, peeking up

def ppomo(x, y, z, scale):
    p = pose()
    tilt = rng.uniform(-0.35, 0.35) if rng.random() < 0.8 else rng.uniform(-0.9, 0.9)
    squish = rng.uniform(0.0, 0.12)   # pressed by its neighbours: wider and flatter
    return {'x': round(x, 3), 'y': round(y, 3), 'z': round(z, 3),
            'rx': round(p['rx'], 3), 'ry': round(p['ry'], 3), 'rz': round(tilt, 3),
            's': round(scale * rng.uniform(0.92, 1.1), 3), 'sx': round(1 + squish, 3), 'sy': round(1 - squish, 3),
            'color': rng.choice(PALETTE)}

out = []
rows = int(2 * HALF_H / DY) + 3
cols = int(2 * HALF_W / DX) + 3
for layer, (z0, shift, sc) in enumerate([(-3.0, 0.5, SCALE * 1.1), (0.0, 0.0, SCALE)]):   # back layer fills the gaps
    for j in range(rows):
        y = -HALF_H - DY + j * DY
        off = (j % 2) * DX / 2 + shift * DX
        for i in range(cols):
            x = -HALF_W - DX + off + i * DX
            out.append(ppomo(x + rng.uniform(-0.18, 0.18), y + rng.uniform(-0.12, 0.12), z0 + rng.uniform(-0.6, 0.6), sc))

print(json.dumps({
    'source': 'ppomo-cat-3d.html',
    'camera': {'ortho': HALF_H, 'target': [0, 0, 0], 'pos': [0, 0, 60]},
    'pivot': [0, 0.65, -0.1],
    'meshStep': 0.03,
    'background': '#F4ECE8',
    'noGround': True,
    'sun': [-5, 9, 16],
    'shadowBox': 10,
    'light': {'hemi': 0.45, 'sun': 1.7, 'env': 0.3, 'exposure': 0.95, 'shadowRadius': 6},
    'ppomos': out,
}, indent=1))
