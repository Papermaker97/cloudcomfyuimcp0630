# AI use: Ppomo Puff Cam (ICM Week 8)

**AI used:** Claude (Anthropic), in Claude Code.
**What it did:** suggested the idea (with two others), and wrote `sketch.js`, `index.html` and `style.css`, which I then read through, tested and adjusted.

## My prompts (original Korean, with English translation)

1. *(I pasted this week's assignment)*
   > 1. 만들기 — PARTS OF A WHOLE: 이미지의 픽셀 영역이나 개별 픽셀을 조작해서 원본과 다른 현실을 만드는 스케치
   > 2. 읽기 — Allison Parrish의 'Working with video' 튜토리얼
   > 3. 보기 — Coding Train 11.1 웹캠 캡처, ml5.js FaceMesh·Pose Estimation·Hand Pose 영상
   > 4. 제출 — 폼에서 Week 08 (Media 1) 선택
   > … 뽀모와 연관지을꺼 있을까?

   *Translation:* "Make: PARTS OF A WHOLE, a sketch that manipulates pixel regions or individual pixels to create a reality different from the original. Read: Allison Parrish's 'Working with video'. Watch: Coding Train 11.1 webcam capture, ml5.js FaceMesh / Pose Estimation / Hand Pose videos. Submit: choose Week 08 (Media 1) on the form. … Is there anything I can connect to Ppomo?"

2. > 아 그래? 만들어줘.

   *Translation:* "Oh really? Make it for me."

3. *(I pasted the p5 web editor error)* "Error: Infinite loop detected at line 85…" and asked:
   > 한번 되긴 했는데 이건 컴퓨터 버벅이는 오류인가

   *Translation:* "It worked once, but is this an error from my computer lagging?"
   *Change made:* added `// noprotect` (the editor's loop guard stopped the long pixel loop) and reduced the frame from 640×480 to 480×360.

4. > 잘 되는데? 블로그좀 올려줘.

   *Translation:* "It works! Please write up the blog post."

5. *(I asked where `// noprotect` is documented, then pasted a new error from my older Mac)* "Error: Multiple infinite loops detected. Stopping execution." and asked:
   > 이걸 지금 코드에서 보완할 수 있게 조언해주고 링크도 추가해줘.

   *Translation:* "Give me advice so the current code can make up for this, and add the links too."
   *Changes made:* added `<!-- noprotect -->` to `index.html` (the newer editor reads it there); a `LITE` switch that bends a 320×240 frame shown at 480×360; the pixel loop now skips the square root outside the circle and uses `Math.*` instead of p5 helpers; and no pixel work at all while both cheeks are deflated and still. Added links to the p5.js reference and the p5.js Web Editor issues and PR about `noprotect`.

*(Add any later prompts here, e.g. follow-up fixes.)*
