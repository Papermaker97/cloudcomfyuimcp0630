# Ppomo inner skeleton: design brief

This brief asks you to design the inside of a squeezable silicone toy called Ppomo: the printed
skeleton, the way a squeeze becomes one counted event, and how the parts go in.

The silicone body is fixed. Everything inside it is open for redesign.

Six earlier attempts by another AI model failed. They are listed in section 7 with the owner's
objections, so that you do not repeat them. Please read that section before proposing anything.

---

## 1. What Ppomo is

- A small squishy companion. When you squeeze it, it records one squeeze, and an on-screen Ppomo puffs up.
- One squeeze is one event. It only counts. It does not measure force or diagnose anything.
- The owner is a solo graduate student (NYU ITP). The first public showing is a show on December 18-19, 2026.
- The long-term goal is a real product.
- Why it exists, in the owner's words: FOMO followed them through every transition (Seoul to New York,
  art to tech, their 20s to their 30s). Making a scary thing small and cute makes it lighter.
  Ppomo is a device, a plush and a companion at the same time.

## 2. Goals (the owner's words, translated)

The owner wants a toy that:

1. feels good to squeeze,
2. counts a squeeze anywhere on the body except the face,
3. is wireless,
4. looks slightly like a skeleton inside (the body is translucent),
5. protects the sensor and electronics,
6. lasts a long time.

For the product the owner also named four constraints for the sensing method:
wireless, mass production, low unit cost, durability.

The interaction the owner described: "I squeeze the body without thinking, like any squishy toy,
and it is recorded in the app."

## 3. What is fixed: the silicone body

### Shape and size

- A lying-down, loaf-shaped animal with a round head, two round ears, four small paws and two butt lobes.
- Overall size: 74.8 mm wide, 110 mm long, 52.2 mm tall. Volume 253 cm3 (about 271 g of silicone if solid).
- Material: platinum-cure silicone, Smooth-On Ecoflex 00-31 Near Clear (very soft, translucent).
  Ecoflex 00-45 Near Clear is the firmer alternative.
- It is cast in a two-part 3D-printed PLA mold.

### Coordinates used below (mm)

- X = left/right, centred on 0.
- Y = length. The face is at Y = -55, the rump at Y = +55.
- Z = up. The flat bottom is at Z = 0.

### Height of the body along its length (measured on the centre line X = 0)

| Y (mm) | top of body Z (mm) | note |
|---|---|---|
| -24 | 39.0 | head |
| -16 | 40.0 | lowest point behind the head |
| -8 | 44.8 | |
| 0 | 48.5 | |
| +8 | 51.0 | |
| +16 | 52.0 | highest point |
| +24 | 51.5 | |
| +32 | 48.8 | rump |
| +40 | 42.8 | |
| +48 | 32.0 | the body ends near Y = +51 on the centre line |

- The body is about 75 mm wide through the torso and about 66 mm wide at the head.
- The bottom is flat only in the middle. Toward the edges the underside curls up.

### Exact shape

The body is a smooth union of ellipsoids and spheres. One model unit is 51.97 mm.
Model axes: x across, y up, z forward (toward the face).
Print coordinates: X = x * 51.97, Y = -(z * 51.97) - 3.21, Z = (y - 0.0355) * 51.97.

| part | centre (x, y, z) | radii or radius |
|---|---|---|
| head | 0, 0.40, 0.52 | 0.65, 0.40, 0.46 |
| torso | 0, 0.48, -0.25 | 0.72, 0.48, 0.66 |
| rump | 0, 0.55, -0.45 | 0.43 |
| belly | 0, 0.18, -0.10 | 0.66, 0.20, 0.85 |
| cheeks (two) | +-0.36, 0.30, 0.78 | 0.21 |
| ears (two) | +-0.31, 0.80, 0.52 | 0.155, 0.155, 0.08 (round discs, tilted 0.18 rad outward) |
| front paws (two) | +-0.50, 0.09, 0.70 | 0.11 |
| back feet (two) | +-0.52, 0.09, -0.86 | 0.11 |
| butt lobes (two) | +-0.27, 0.42, -0.76 | 0.36 |

The floor is cut flat at y = 0.035. The full formula, with the blend radii, is in
`characters/ppomo-skeleton/make_bone_concept.py` (function `body_field`) and in
`characters/ppomo-cat/ppomo-v6.html` (function `modelSDF`).

### Files

- `characters/ppomo-mold/ppomo-v6-body-110mm.stl`: the body, no face.
- `characters/ppomo-mold/ppomo-v6-face-110mm.stl`: the body with carved eyes, nose and mouth.
- `characters/ppomo-mold/mold-left.stl`, `mold-right.stl`: the current casting mold (solid body, open flat bottom).

The mold may be redesigned to leave a cavity. The outside shape of the body may not change.

## 4. What the owner has decided or strongly prefers

These came from the owner during the earlier attempts. Treat them as requirements unless you can show
a clearly better way to reach the same goal.

- **The body has no plug.** Every part of the torso must be squeezable, so the opening cannot be there.
- **The opening is in the face.** The face is never squeezed. The inside parts go in through the face,
  and the piece that closes the opening is the face itself.
- **The face is a skull.** In an animal, the skull is the face and also protects the brain. In Ppomo one
  part should be the face (eyes, nose, mouth), the plug, and the protection for the electronics.
  It should not be a face plate plus a separate plug plus a separate box joined together.
- **Cheeks and ears stay silicone.** Only the eyes, nose and mouth area is hard.
- **The skeleton is small, like a squeaker in a toy.** The hand should first sink into soft silicone
  and then find the click. A skeleton that fills the body kills the feel.
- **No rigid plastic neck.** Between the head and the body only wires (and a pull cord) are needed.
- **It is squeezed, not pressed.** People will grab it like any squishy toy: the whole hand closes
  around it, from slanted directions, and around the rump. A design that only answers straight presses
  from a few directions is wrong.
- **The rump must work.** Grabbing the rump should register.
- **Pressing the belly must feel good.** A doll gets its belly pressed.
- **Curved, plump bone shapes.** The owner modelled an example in Blender: a round core with fat,
  curved limbs that wrap around it, thick in cross-section, swelling and narrowing along their length.
  The owner called this "peanut-like" and meant the three-dimensional curvature, not a peanut outline.
  Reasons given: thin bones snap, and sharp edges would cut the silicone from inside after many squeezes.
- **No pinch points.** Narrow slits between hard parts will pinch the silicone.
- **Bones that interlock** so that no ring of empty space is left between them.
- **The spring belongs next to the button**, as in ordinary clickers, not at the far end of a lever.
- **One squeeze should be one count.**

## 5. How the owner wants the design to be done

This is the main reason the earlier attempts were rejected. The owner's words, translated:

> "I am asking you to do product design. We consider the design in order to make up for the function.
> PLA or anything else will break one day if it is designed badly. The models on MakerWorld raise
> durability by building the structure well out of that limited material."

> "You make a face with an expression drawn on it, then a plug, then a separate box to protect the
> sensor, and join them. If you keep attaching things by logic, you will be making this forever."

What this means in practice:

- **One form should do several jobs.** Count the parts. If each function has its own part, the design is wrong.
- **Durability comes from structure**, not from swapping to a stronger material or adding a metal spring.
- **Use what is already proven.** The owner printed a clicker (reference C below) and played with it for
  a day. It still springs back. That is evidence. Do not replace a proven printed mechanism with a guess.
- **Do not take words literally.** When the owner says "peanut", "skeleton" or "like a clicker ball",
  find the principle behind it.
- **Do not ask permission at every step.** Decide, give the reason, and show the result.
- **Say plainly what is unknown.** Nothing so far has been tested physically.

## 6. References the owner gave

### A. Clicker Ball (MakerWorld, mechanical keyboard fidget toy)

- A small 12-faced core. Each face holds a real keyboard switch pointing outward.
- Twelve curved caps snap onto the switches and together form the whole surface of a ball.
- Principles: the surface itself is the buttons, switches face outward in all directions, the caps are
  pieces of the outer curved surface, and the core is small.
- The owner said: "If it comes to it, I can just put a clicker ball inside and add a sensor. Why not
  something like a clicker ball, with tactile buttons under caps that have the curvature I modelled?"

### B. Printed replacement for a keyboard switch ("Clicky Clicker")

- About 13.6 x 13.6 x 21.8 mm, the same cross-shaped stem as a keyboard switch, so it can replace one.
- A zigzag leaf spring printed inside the box in one material. No electrical contact.
- Principle: the spring and the feel come from the shape.

### C. Print-in-place flat clicker ("Click-CLICK")

- About 28.5 x 89.5 x 10 mm. A rounded serpentine spring with walls about 1.0 mm and gaps about 3 mm,
  a ratchet arm for the click, and a plunger guided at two places.
- Printed flat, so the spring bends inside the print plane.
- The owner's evidence: printed in PLA, played with continuously for a day, still returns.

### D. The owner's Blender model

- A round core, a short post on it, and three fat curved limbs that arc over and around the core.
- It shows the intended form language (plump, curved, wrapping). It is not a finished mechanism.

## 7. What was tried and why it was rejected

| version | idea | why it failed |
|---|---|---|
| Cone clicker v1, v1.1 | A 28 mm block. A rod with a 45-degree cone. Four plungers slide on the cone and push the rod onto one tactile button. A printed spiral plate returns it. | v1 could not be assembled (sealed button pocket, a ring trapped on the rod). It answers four straight directions plus the back. It is a box, not a skeleton. |
| Concept v1 | The same rod, made long, with four identical flat "peanut" pads. | The owner: "You made a literal peanut. Four identical pads: I could buy four keycaps." Pads were too close and the tail was a spike. |
| Concept v2 | Pads cut from an inner copy of the body surface, with wavy interlocking seams. | It filled the body, so no squish was left. Thin plates with edges: "that will pinch". |
| Concept v3 | A small version: visible rod, two hub beads, four plump straight bones on stems, a metal return spring, tail dome. | "Your bones are straight bars. This is pressing, not squeezing." Grabbing the rump does nothing. A metal spring and stems were added instead of solving it by form. |
| Concept v4 | A pebble core with five tactile buttons, four curved bones hinged at one end by a printed zigzag. | The spring was at the far end, so the bone tilts like a lever. One bone pressed two buttons. A plastic neck was not needed. The face was still an old plate. |
| Concept v5 | Five short curved bones, each sitting on its button with a zigzag on both sides, in pockets in the core. | It could not be printed (springs inside a 3D core, bones in different print planes). The button was the end stop. Nothing held a bone sideways. Still five straight directions. |
| Concept v6 | Identical flat print-in-place discs ("vertebrae"), each a whole button: cap, stem, two zigzags, lips as guide and stop. Two at right angles plus one upright as a tail. | It is printable and its numbers check, but it is a stack of machine parts, not bones. It has none of the curvature the owner asked for. The neck and chest have no bones. The owner judged that this line of work was not converging. |

Patterns in these failures:

- Functions were added as separate parts (rod, cones, stems, hubs, spring, plate, plug, box).
- The mechanism was chosen first and the form was wrapped around it afterwards.
- Squeezing was treated as a few straight presses.
- Checks were done on screen (clearances, strain formulas). Nothing was printed and squeezed.
- Each fix answered the latest objection and broke an earlier requirement.

## 8. What is known and what is not

### Known

- A pressure sensor (Adafruit MPRLS) on an Arduino Nano 33 IoT works: blowing into its tube changes the reading.
- A printed serpentine spring in PLA survives at least a day of play (reference C).
- The body shape, size and mold exist.

### Not known (none of this has been tested)

- How well a squeeze passes through 5 to 25 mm of Ecoflex 00-31 to a hard part inside.
- Whether a small click can be felt through that much silicone.
- Whether silicone creeps into gaps in a mechanism and jams it.
- How far the face opening can be stretched in practice to insert the inside parts.
- How long any printed spring lasts beyond a day.

### An option that was set aside

Sensing air pressure in a sealed cavity answers a squeeze from any direction with no mechanism at all.
The owner chose a mechanical click first, because sealing is hard to mass-produce and because the click
is part of the feel. You may reopen this if you can show it meets the goals better.

Another untested idea: let printed parts give the click everywhere, and count squeezes with one
vibration or sound sensor in the skull, so that no button or wire is needed in the body.

## 9. Parts and tools available

- 3D printer: Bambu Lab P2S (FDM). PLA and PETG. Resin prints cannot touch the silicone (they stop it curing).
- 6 x 6 mm tactile buttons (body about 3.5 mm tall, plunger about 1.5 mm, travel about 0.25 mm).
- Arduino Nano 33 IoT (Bluetooth, 3.3 V). A smaller board will be needed for the final toy.
  An earlier layout assumed a Seeed XIAO nRF52840 (21 x 17.5 mm) and a small LiPo cell (about 5 x 10 x 20 mm).
  Neither has been bought.
- Pressure sensors on loan: Adafruit MPRLS, MPX2102ASX, and an MPXV-series part.
- A vacuum chamber at school for degassing silicone.

## 10. What we need from you

A design for the inside of Ppomo that meets the goals in section 2 and the requirements in sections 4 and 5.

Please give:

1. **The concept in a few sentences**, and how a squeeze from any direction becomes one count.
2. **The parts list**: every printed part and every bought part, with what jobs each one does.
   Fewer parts with more jobs each is better.
3. **The skull**: how one part is the face, the plug and the protection for the electronics.
4. **The skeleton in the body**: its form, how it responds to a whole-hand squeeze, a rump grab,
   a belly press and a slanted squeeze, and why it reads as bones.
5. **Where the spring and the click come from**, and why they will last.
6. **How each part is printed** (orientation, supports) and **how it is assembled and inserted** through the face.
7. **How the silicone is cast around it** (what leaves the cavity, where the silicone is poured).
8. **Dimensions** that fit the body in section 3, with the silicone thickness left over each part.
9. **What you are unsure about**, and the single cheapest physical test that would settle the biggest doubt.

Please do not answer with a mechanism first and a shape afterwards.
