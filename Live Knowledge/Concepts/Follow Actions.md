# Follow Actions

*The richest single concept in the recon (8 of the 34 top-relevance findings)
and the most OCR-damaged section.* Follow Actions are central to SC's
scene/clip-cue work and to `.als` injection, so this hub is high-priority. The
section's **option list** was the worst-hit by OCR, so the authoritative
ten-option set is reproduced from the 16.7 PDF in the **"The ten Follow
Actions"** table below; the recon **Findings** beneath it keep their
byte-for-byte quotes as the audit anchor.

Mental model: a **group** is successive non-empty clip slots in one track; each
clip can carry **two** actions (A/B) with **Chance** weights; timing is the
**Follow Action Time** (or clip end, in Linked mode); Follow Actions bypass
**global** quantization but obey **clip** quantization; and scene Follow Actions
take precedence over clip ones once triggered.

## The ten Follow Actions (authoritative — PDF backfill)

> [!note] Option list backfilled from the 16.7 PDF (2026-06-01)
> The recon fragmented this list. Of the ten actions the manual lists, it
> captured six (two — *Previous*, *Next* — damaged) and omitted four
> (*Play Again*, *First*, *Last*, *Any*) entirely. The table below is the
> clean manual text from the 16.7 PDF (Ableton Reference Manual Version 12, pp. 353-355), supplied 2026-06-01. The recon quotes under
> **Findings** stay byte-for-byte as the audit anchor — this is a
> separately sourced layer. Labels are Live 12's UI names (rendered as
> images in the manual, so absent from the PDF text layer); descriptions
> are verbatim (quotes lightly normalised; raw extract in `_source/`).

The manual: *“There are ten Follow Actions available:”*

| # | Follow Action | What it does (verbatim) | Recon coverage |
|---|---|---|---|
| 1 | **No Action** | means that no Follow Action will occur. Once a clip has been triggered with No Action, any other selected Follow Action in the clip will no longer have a chance of occurring, even if its Follow Action Chance is set to 100%. | ✓ recon `:: 9` |
| 2 | **Stop** | simply stops the clip after it has played for the chosen Follow Action Time. Note that this overrides clip loop/region settings. | ✓ recon `:: 10` |
| 3 | **Play Again** | restarts the clip. | ✗ recon omitted |
| 4 | **Previous** | triggers the previous clip (the one above the current one). | ⚠ recon `:: 12` damaged |
| 5 | **Next** | triggers the next clip down in the group. If a clip with this setting is last in a group, this Follow Action triggers the first clip. | ⚠ recon `:: 14` damaged |
| 6 | **First** | launches the first (top) clip in a group. | ✗ recon omitted |
| 7 | **Last** | launches the last (bottom) clip in a group. | ✗ recon omitted |
| 8 | **Any** | plays any clip in the group. | ✗ recon omitted |
| 9 | **Other** | is similar to "Any," but as long as the current clip is not alone in the group, no clip will play consecutively. | ✓ recon `:: 20` |
| 10 | **Jump** | lets you select a target clip slot or scene for the Follow Action to jump to. When Jump is selected, a Jump Target slider appears next to the Follow Action chooser. To adjust target clip slot or scene value, drag the Jump Target slider up or down, or click and type in a number. | ✓ recon `:: 21` |

*Recon coverage of the option list: 4 clean, 2 damaged, 4 omitted, of 10 — which is why this backfill was needed. The behaviour described in **Findings** below is unaffected; only the option-label wording was in doubt.*


## Findings

### A Follow Action group is defined by successive clip slots in the same track.

> Follow Actions can trigger clips in an orderly or random way (or both). A clip's Follow Action defines what happens to other clips in the same group after the clip plays. A group is defined by clips arranged in successive slots of the same track. Tracks can have an unlimited number of groups, separated by empty slots.

`16. Launching Clips :: 16.7 Follow Actions :: 1` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Chance A and Chance B are percentage probabilities, with 0% meaning an action never triggers.

> 3. The Chance A and Chance B controls set the probability (in a percentage) that each Follow Action will be triggered. If a clip or scene has Chance A set to 100% and Chance B set to 0%, Follow Action A will occur every time the clip or scene is launched. As we can see from this example, a Chance setting of 0% means that an action will never happen. Changing Chance B to 90% in this scenario makes Follow Action A occur much less often — approximately once out of every ten clip or scene launches. Note that in addition to the Chance A and Chance B controls, you can drag the slider located between them to adjust the Chance values.

`16. Launching Clips :: 16.7 Follow Actions :: 6` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### The Linked/Unlinked switch changes whether clip Follow Actions use clip end/loop count or Follow Action Time.

> 4. The Linked/Unlinked switch is only available for clips, and has two different modes. This switch is set to Linked by default. In Linked mode, the Follow Action is triggered at the end of the clip, or after the number of loops set in the Follow Action Multiplier field. In Unlinked mode, the Follow Action is triggered after the clip has played for the duration of the Follow Action Time. The Follow Action Time control, which is available for both clips and scenes, defines when the Follow Action takes place in bars-beats-sixteenths from the point in the clip or scene where play starts. The default for this setting is one bar. In the Sample/MIDI Notes Editor, a marker visualizes the Follow Action Time of a clip, and dragging this marker adjusts the clip's Follow Action Time.

`16. Launching Clips :: 16.7 Follow Actions :: 7` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### No Action prevents the other selected clip Follow Action from occurring after it triggers.

> |No Action ▼! means that no Follow Action will occur. Once a clip has been triggered with No Action, any other selected Follow Action in the clip will no longer have a chance of occurring, even if its Follow Action Chance is set to 100%.

`16. Launching Clips :: 16.7 Follow Actions :: 9` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### The Stop Follow Action overrides clip loop and region settings.

> | ■ Stop ▼! simply stops the clip after it has played for the chosen Follow Action Time. Note that this overrides clip loop/region settings.

`16. Launching Clips :: 16.7 Follow Actions :: 10` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Other behaves like Any but avoids immediately repeating the current clip when alternatives exist.

> | Other ▼! is similar to "Any," but as long as the current clip is not alone in the group, no clip will play consecutively.

`16. Launching Clips :: 16.7 Follow Actions :: 20` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: medium

### Jump uses a Jump Target slider to select a destination clip slot or scene.

> | Jump| |efS you select a target clip slot or scene for the Follow Action to jump to. When Jump is selected, a Jump Target slider appears next to the Follow Action chooser. To adjust target clip slot or scene value, drag the Jump Target slider up or down, or click and type in a number.

`16. Launching Clips :: 16.7 Follow Actions :: 21` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: medium

### Clip Follow Actions bypass global quantization but still obey clip quantization.

> Note that a clip Follow Action happens exactly after the duration that is specified by the Follow Action Time controls unless clip quantization is set to a value other than "None" or "Global." Follow Actions circumvent global quantization but not clip quantization.

`16. Launching Clips :: 16.7 Follow Actions :: 24` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Enable Follow Actions Globally controls all clip and scene Follow Actions in the Set.

> Next to the Back to Arrangement button, an Enable Follow Actions Globally button lets you enable or disable all clip and scene Follow Actions in the Live Set. By disabling the Enable Follow Actions Globally button, you can edit running clips without being interrupted by playback jumping to other clips. Note that when a Live Set does not contain any clip or scene Follow Actions, the Enable Follow Actions Globally button will appear grayed out.

`16. Launching Clips :: 16.7 Follow Actions :: 25` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Clip Follow Actions continue while scene Follow Actions are pending, but scene Follow Actions take precedence once triggered.

> Note that Follow Actions in clips will continue to run when a scene Follow Action is created or scheduled, however Follow Actions in scenes always take precedence once they are triggered.

`16. Launching Clips :: 16.7 Follow Actions :: 27` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Each clip can hold two Follow Actions with corresponding Chance values.

> Follow Actions are great when it comes to sound installations, as they allow you to create structures that play for weeks or months and never exactly repeat. You can set the Follow Action Time controls in a series of clips to odd intervals, and the clips will interact with each other so that they never quite play in the same order or musical position. Remember that each clip can have two different Follow Actions with corresponding Chance settings... have fun!

`16. Launching Clips :: 16.7.6 Creating Nonrepetitive Structures :: 1` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Legato Mode keeps Follow Action transitions synchronized by inheriting beat-time play position.

> Using Follow Actions and Legato Mode together provides a powerful way of gradually changing a melody or beat. Imagine that you have several identical clips of a melody that form a group, and they are set up to play in Legato Mode. Whenever their Follow Actions tell them to move on to another clip in the group, the melody will not change, as Legato Mode will sync the new play position with the old one in beat-time. The settings and clip envelopes of each clip (or even the actual notes contained in a MIDI clip) can then be slowly adjusted, so that the melody goes through a gradual metamorphosis.

`16. Launching Clips :: 16.7.4 Adding Variations in Sync :: 2` &nbsp;·&nbsp; **workflow gotcha** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Next Follow Actions can make selected clips or scenes cycle indefinitely until stopped.

> One of the most obvious possibilities that Follow Actions open up is using a group of samples to form a musical cycle. If we organize several clips or scenes as a group and use the "Next" Follow Action with each clip or scene, they will play one after the other ad infinitum, or until we tell them to stop.

`16. Launching Clips :: 16.7.2 Creating Cycles :: 1` &nbsp;·&nbsp; **workflow gotcha** &nbsp;·&nbsp; SC-relevance 3/5 &nbsp;·&nbsp; confidence: high

### Legato Mode launches a clip at the previous clip's play position in the same track.

> Another option, which works even with quantization turned off, is to engage Legato Mode for the respective clips. When a clip in Legato Mode is launched, it takes over the play position from whatever clip was played in that track before. Hence, you can toggle clips at any moment and rate without ever losing the sync.

`16. Launching Clips :: 16.3 Legato Mode :: 7` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

## See also

[[Session vs Arrangement]] · [[Tempo, Warp & Sync]] · [[Hard Constraints]]
