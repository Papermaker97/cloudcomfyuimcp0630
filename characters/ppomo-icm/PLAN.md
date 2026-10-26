# Ppomo — FOMO Piles Up (ICM Week 6 CREATE plan)

## In one line
Every time you squeeze Ppomo, one Ppomo falls from the top of the screen and lands on the pile. The more you squeeze, the more FOMO visibly piles up.

## What I'm making
- Pressing the screen stands in for squeezing Ppomo. The real squeeze happens on the PComp device; in this screen version a click or tap does the same job.
- Each press drops one Ppomo from the top into the column you pressed.
- It lands softly on the floor or on the Ppomos already there, squashing a little and bouncing back.
- Every Ppomo gets a different pastel color (the idea from my #4 proposal).
- When you stop squeezing, nothing new falls, but the pile stays. "Feelings don't get used up; they accumulate" (carried over from #4 and #5).

## Why
Making a scary thing cute makes it easier to carry. I turn FOMO into a soft, cute pile you can see, so you notice how much you've collected.

## How it meets the assignment
| Requirement | In this sketch |
|---|---|
| Array of objects | `Ppomo` class instances stacked in the `ppomos` array |
| Add with click / key | Click (or space) → `push` a new Ppomo |
| Remove | Backspace → `pop` the last Ppomo. Week 2: rub a Ppomo's butt to soothe it and it smiles and floats away |
| Record user actions | Every squeeze and removal goes into a `log` array as `{ action, time }`; the squeeze count is shown on screen |
| Variables, conditionals, loops, functions, classes | Column math, blocking full columns, the draw loop, the `squeeze()` function, the `Ppomo` class |

## Structure
- `class Ppomo`
  - Properties: `col`, `x`, `y`, `targetY` (landing height), `speed`, `landed`, `squash`, `color`
  - Methods: `fall()` falls and lands; `show()` draws ears, body, cheeks, eyes and mouth
- `ppomos = []`: the Ppomos on screen
- `log = []`: the action record
- `squeeze(x)`: finds the pressed column, counts how many Ppomos are already in it to set the landing height, and adds a new Ppomo
- `mousePressed()`, `keyPressed()`: input

## Week 1 (Oct 26) — what's done
- Each press drops a Ppomo that stacks in its column.
- Soft squash on landing.
- A different pastel color for each Ppomo.
- Backspace removes the last Ppomo.
- Squeeze count and Ppomo count are recorded and shown.

## Week 2 — finished scope
- **Puffing up:** pressing a Ppomo already on the pile puffs up its cheeks → belly → butt, step by step. This keeps the core mechanic, "the more you squeeze, the bigger it gets", inside each Ppomo.
- **Soothe and let go:** rubbing a Ppomo's butt with the mouse makes it smile and float away. It is removed from the array and the Ppomos above it drop down.
- When the screen is full, the whole pile wobbles.
- Record screen: squeezes, puff-ups, and Ppomos soothed away.
- Credits, then submit.

## Next — toward the Winter Show
- Right now Ppomos pile up on the **floor** of the screen.
- Later I want to use the camera to **recognize the person's body**, so Ppomos land naturally **on visitors' heads and shoulders** and pile up there.
  - For example, use ml5.js body pose detection to find the head and shoulders, and use those as the landing height instead of the floor.
  - The more you squeeze, the bigger the pile of FOMO Ppomos on your head and shoulders, captured as a photo: an experience only the show can give.
- The input changes from a click to squeezing the real Ppomo device built in PComp. It only has to call the same `squeeze()` function.
- Split across classes: PComp = device, ICM = this screen, Hypercinema = video, Applications = play concept.

## Credits
- p5.js (https://p5js.org)
- The sketch code was written with help from Claude (Anthropic). The concept, character and mechanics are my own.

---

## What I'll say in class
> Ppomo is a creature that soaks up FOMO. Every time you squeeze it — here, every click — one Ppomo falls from the top and lands on the pile. When you stop, nothing new falls, but what you've piled up stays. That's my point: the feeling isn't used up, it accumulates. I make the scary thing cute so it's easier to hold.

> In code, each Ppomo is an object of a `Ppomo` class, stored in an array. A click pushes a new one, Backspace pops the last one, and every action is recorded in a log array with a timestamp.

> Next week, pressing a Ppomo on the pile makes its cheeks, belly and butt puff up, and rubbing its butt makes it smile and float away, removing it from the array. For the Winter Show, I want the Ppomos to land on visitors' heads and shoulders using body tracking instead of the floor, and the input will be squeezing the real Ppomo device.
