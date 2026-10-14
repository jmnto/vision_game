# Built-in Image Gen production prompts

All assets generated with the built-in tool, copied into the project, and inspected.

## docs/concept.png
Full desktop ORCHARD autonomous harvest interface. Dark forest-green robotics console,
lime accents, geometric sans-serif. Header ORCHARD / Field simulator / Model lab.
75% photographic orchard viewport, 25% Harvest control sidebar, large score, harvested
count, precision, confidence slider, yolov8n.pt selector, Scan & harvest. Five thumbnail
stages: Morning orchard, Citrus grove, Dense canopy, Late light, Mixed harvest. Scoring
footer +100 correct harvest, −40 false detection. Practical code-native UI.

## assets/orchard.png
Photorealistic natural 1536×1024 orchard background. Eye-level camera near leafy apple
and citrus branches, green foliage and detailed brown bark, soft orchard rows receding
in the background, sunlit morning. No fruit anywhere, no UI or text. Open gaps suitable
for compositing fruit later.

## assets/fruits.png
Transparent production sprite sheet. Two separated, isolated photorealistic fruits:
red ripe apple on the left, ripe orange on the right. Short stems, no leaves. Detailed
natural glossy apple skin and porous orange skin. Outdoor daylight from upper left,
no ground shadows or text, genuine alpha transparency. Renderer splits the sheet,
trims alpha padding and composites the sprites into the scene.

## assets/decoys.png
Built-in Image Gen, transparent 2×2 sprite sheet. Top left: realistic red plastic
apple with visible molded seam and gold sticker. Top right: orange-shaped wax candle
with visible white wick. Bottom left: red glass Christmas bauble with gold hanging
cap. Bottom right: worn orange basketball with dark seams. Each isolated in its
quadrant, outdoor light from upper left, no background, text or ground shadows.
Ground-truth labels identify these as non-harvestable objects, independent of YOLO.
