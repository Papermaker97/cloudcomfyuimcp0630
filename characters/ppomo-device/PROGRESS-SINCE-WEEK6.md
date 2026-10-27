## Ppomo: Progress Since Week 6

My last Ppomo update was in the [Week 6 post](https://wholesale-capricorn-70c.notion.site/PComp-Week-6-Midterm-Visual-Research-with-Albee-and-Synchronous-Serial-Research-for-Ppomo-3f872090eb468195acdbd401b54ade0a). Here is what has moved since then.

### 1. The Winter Show experience is now defined
- A person stands in front of a camera, and a digital Ppomo appears **perched on their head or belly**. I plan to use body tracking such as ml5.js BodyPose for this.
- In their hand they hold the physical Ppomo. **Every squeeze makes the on-screen Ppomo's cheeks, belly, or butt puff up.**
- Behind the show piece, the device keeps its everyday purpose:
  - a normal squishy-toy size
  - each squeeze is sent with its **date and time**
  - the squeezes are recorded on a web page or app

### 2. Character and 3D print
- The base character is now a **sitting Ppomo** (gray cat costume), modeled in 3D. I adjusted it so the arms and legs sit further out to the sides and read clearly from the front.
- I made a **printable 95 mm shell** from the model. It has:
  - a 30 mm opening in the floor for the electronics
  - a 5 mm flat floor so it sits steadily
  - a small cable groove so it can sit flat while plugged in
  - a solid wall kept behind the face so the eyes and mouth don't get thin
- I printed it to check the real size in the hand.

📷 *[3D print photo]*

### 3. Device design (draft for review)
I wrote a full device design to answer the three questions from Week 6. It is a **draft I'd like feedback on**; none of it is built yet.

| Week 6 question | Current plan |
|---|---|
| Where should the sensing happen? | Measure the **air pressure inside the sealed body** (BMP581 sensor). A squeeze anywhere on the body raises the pressure, so one sensor covers the whole body and nothing at the surface bends and wears out. Small FSRs could be added later to tell belly from butt. |
| Where should the memory live? | Each squeeze is logged to the board's **own flash memory first**, with a sequence number. It is uploaded over Wi-Fi to a database (Supabase) and only deleted after the server confirms it, so nothing is lost or counted twice. |
| How does it know the time? | A **DS3231 real-time clock** on I2C keeps the time offline. Whenever Wi-Fi is available, internet time (NTP) corrects it. |
| Haptics | **DRV2605L** haptic driver (I2C) gives a small "tick" in the hand for each counted squeeze. |
| Board | **XIAO ESP32-C3**: tiny, has Wi-Fi, and has a built-in battery charger for a 400 mAh LiPo. |

- **Firmware:** the counting rule uses hysteresis, so a long hold or a slow squeeze still counts once.
  - It compiles and passes 11/11 simulated test cases on the computer.
  - It has **not** been run on hardware yet.
- **Web dashboard:** shows today's count, the last 14 days, counts by hour, and recent squeezes.

### 4. First hardware test: squeeze → computer → screen
This week's serial labs gave me the first working piece of the data path.
- I used an **FSR on A0** as a stand-in squeeze sensor. I'm at home without the shop's flex sensors.
- The value goes from the Arduino to p5.js over WebSerial. The screen shows **0 at rest**, and the value rises as I squeeze.
- That live number is what will eventually drive how much the character inflates.

### 5. ICM side
For the ICM arrays-of-objects assignment, I made a p5.js sketch where **one Ppomo drops onto the screen and piles up for every squeeze**. It was an exercise and not the Winter Show piece. The idea of stacking Ppomos on a person's head and shoulders came from it.

### 6. Product thinking
- Ppomo sits in the same culture as **bag charms and keychain companions** (Pop Mart, Sanrio). It should feel like something you carry and squeeze, not a gadget.
- One worry: I don't want the toy to force people onto their phone to "use" it. The squeezing should be enough on its own, with the record there when you want to look.
- Open question: whether Ppomo itself needs a **screen face** (an LED display), or whether a toy-like face is better and the expression should live on the web side.

### Questions for Tom
1. **Pressure in a sealed body:** does measuring air pressure inside a 3D-printed rubber body sound reliable, or will leaks and temperature drift make it fragile? Should I test with a sealed silicone bulb inside the body instead?
2. **Next test:** what is the smallest test that would tell me whether to commit to pressure sensing or stay with flex/FSR sensors?
3. **Winter Show setup:** for the show, is it better for the toy to talk to the screen over USB (simple, reliable) or wirelessly (closer to the real product)?

*Credit: Parts of the code, the 3D model, the design draft, and this write-up were developed with help from Claude.*
