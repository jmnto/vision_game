# ORCHARD design specification
Reference: concept.png, generated with built-in Image Gen.
Dark forest #081b16 background; lime #b9f477 accent; white #f1f5f1 text;
muted sage #a7b8b0; fine #30473e borders. System sans with monospace metrics.
Full width header, 75/25 camera/control split, five thumbnail phase rail, scoring footer.
Native UI: Field simulator / Model lab, phase title, phase count, Harvest control,
Current score, Harvested, Precision, Model confidence, Detection model, Scan & harvest.
Required functional additions: scan budget, scan feedback, next-phase / finish control,
report download, reset, model setup guidance, loading/error states and completion summary.
Assets: generated fruitless orchard photograph and transparent fruit sprite sheet.
The renderer composes fruit sprites and removes layers after harvest; no image inpainting.
One shared photographic orchard asset is reframed and relit across five stages.
This is a synthetic vision simulation, not validation of field performance.

## Arcade expansion
Ten Portuguese-language stages. Retain the field console and photographic style;
add a compact Robô Zé commentary/action strip, automatic scan and sound toggles,
combo counter, floating harvest points, confetti and a brief mistake reaction.
The phase rail scrolls horizontally and follows campaign progress. Fruit-like props
are real generated image assets, not score-injected errors. Motion respects reduced
motion preferences; sound starts disabled and is activated only by the user.
