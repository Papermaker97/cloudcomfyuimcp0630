# Ppomo Playtest (PComp, Nov 24)

Stand in front of the camera and squeeze the soft Ppomo. A 3D Ppomo drops onto your head;
every squeeze puffs it up (cheeks → belly → butt). Stop and the air slowly leaks out.
Walk away and it floats off, ready for the next person.

## Run
1. Arduino: upload `../../ppomo-sensor-mprls/squeeze-amount/arduino/ppomo_squeeze_amount/`, don't touch the squishy for 1 s, close the Serial Monitor.
2. VS Code → open this `playtest` folder → right-click `index.html` → **Open with Live Server** (Chrome).
3. Allow the camera. Click **Connect sensor** (only the first time; Chrome remembers the port).
4. Needs internet (the face detector loads from jsdelivr and Google).

## Keys (for me)
C connect sensor · D debug (fps, pressure, face box) · F fullscreen · S save CSV · R reset · hold SPACE = fake squeeze

## Tune (top of main.js)
- `AMOUNT_FULL = 60` hPa·s to fill Ppomo. Fills too slowly → lower it.
- `PRESS_ON = 3` hPa. Light squeezes missed → 2.
- `SIZE_ON_HEAD = 1.6` Ppomo width / face width.

## Files
- `sprites/puff-00..23.png`: the v6 3D Ppomo pre-rendered at 24 puff levels (`../tools/bake-puff.js`), so an old laptop does not need live 3D.
- `puff-frames-sheet.png`: all 24 frames.
