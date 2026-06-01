# Automation vs Modulation

*Who owns a parameter's value right now.* The load-bearing distinction:
**automation envelopes define the absolute value** of a control; **modulation
envelopes only influence** that value (relative). Both can act on one
parameter; automation is red, modulation is blue. Session clips can hold both;
**Arrangement clips hold only modulation** (automation lives on the track
lane). Manual moves override automation until re-enabled (or until a Session
clip with automation relaunches). Session-View automation becomes track-based
automation when copied/recorded into the Arrangement.

Critical for any feature that writes or reasons about envelopes/automation via
`.als` — confusing the two yields parameters that look automated but behave
unexpectedly.

## Findings

### Automation envelopes define absolute values, while modulation envelopes only influence the defined value.

> Clip envelopes can be used to automate or modulate mixer and device controls. Since mixer and device controls can potentially be controlled by both types of envelopes at the same time (and also by the Arrangement's automation envelopes, this is a potential source of confusion. However, modulation envelopes differ from automation envelopes in one important way: Whereas automation envelopes define the absolute value of a control at any given point in time, modulation envelopes can only influence this defined value. This difference allows the two types of envelopes to work together in harmony when controlling the same parameter. To help you distinguish between these, automation envelopes are colored in red, whereas modulation envelopes are colored in blue. Additionally, in parameters with knob controls, automation moves the absolute position (or the "needle"), whereas modulation is indicated by the blue segment on the ring.

`26. Clip Envelopes :: 26.3 Mixer and Device Clip Envelopes :: 1` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Session clips can hold automation and modulation envelopes, but Arrangement clips only hold modulation envelopes.

> Both automation and modulation clip envelopes are available for clips in the Session View. A toggle beneath the envelope choosers allows you to switch between editing automation and modulation clip envelopes for the selected parameter. In the Arrangement, clips only have modulation envelopes, while the automation envelopes reside on the track's automation lane.

`26. Clip Envelopes :: 26.3 Mixer and Device Clip Envelopes :: 3` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Red and blue LEDs indicate clip automation and modulation envelopes for a parameter.

> In a clip, parameters that have an automation envelope are indicated by a red LED in the Control chooser. Similarly, parameters that have a modulation envelope are indicated by a blue LED. Some parameters may have both red and blue LEDs, indicating that they are being automated and modulated by the clip.

`26. Clip Envelopes :: 26.3 Mixer and Device Clip Envelopes :: 5` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Every clip can have clip envelopes whose targets depend on clip type and setup.

> Every clip in Live can have its own clip envelopes. The aspects of a clip that are influenced by clip envelopes change depending upon clip type and setup; clip envelopes can do anything from representing MIDI controller data to automating or modulating device parameters. In this chapter, we will first look at how all clip envelopes are drawn and edited, and then get into the details of their various applications.

`26. Clip Envelopes :: 26. Clip Envelopes :: 1` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Clip-envelope Device chooser entries vary by clip type.

> The left-hand side menu is the Device chooser, which selects a general category of controls with which to work. Device chooser entries are different for different kinds of clips:

`26. Clip Envelopes :: 26.1 The Clip Envelope Editor :: 3` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### The clip-envelope Control chooser selects a target control and marks changed envelopes with LEDs.

> The right-hand side menu, the Control chooser, selects among the controls of the item chosen in the Device chooser menu. In both choosers, parameters with altered clip envelopes appear with LEDs next to their names. You can simplify the appearance of these choosers by selecting "Only show adjusted envelopes" from either of them.

`26. Clip Envelopes :: 26.1 The Clip Envelope Editor :: 6` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### A clip envelope can be unlinked from its clip and given local loop or region settings.

> A clip envelope can have its own local loop/region settings. The ability to unlink the envelope from its clip creates an abundance of exciting creative options, some of which we will present in the rest of this chapter.

`26. Clip Envelopes :: 26.5 Unlinking Clip Envelopes From Clips :: 1` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Linked clip envelopes stretch with Warp Marker edits and can be adjusted from the envelope editor.

> When in Linked mode, clip envelopes respond to changes in the clip's Warp Markers. This means that moving a warp marker will lengthen or shorten the clip envelope accordingly. Additionally, Warp Markers can be adjusted from within the envelope editor.

`26. Clip Envelopes :: 26.5.5 Warping Linked Envelopes :: 1` &nbsp;·&nbsp; **workflow gotcha** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### MIDI controller clip envelopes are selected through MIDI Ctrl and the adjacent Control chooser.

> Choose "MIDI Ctrl" from a MIDI clip's Device chooser and use the Control chooser next to it to select a specific MIDI controller. You can create new clip envelopes for any of the listed controllers by drawing steps or using breakpoints. You can also edit clip envelope representations of controller data that is imported as part of your MIDI files or is created while recording new clips: names of controllers that already have clip envelopes appear with an adjacent LED in the Control chooser.

`26. Clip Envelopes :: 26.4 MIDI Controller Clip Envelopes :: 2` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Clip envelope modulation is non-destructive because it does not alter the sample on disk.

> Using clip envelopes, you can create new sounds from a sample without actually affecting the sample on disk. Because Live calculates the envelope modulations in real time, you can have hundreds of clips in a Live Set that all sound different, but use the same sample.

`26. Clip Envelopes :: 26.2.1 Clip Envelopes are Non-Destructive :: 1` &nbsp;·&nbsp; **workflow gotcha** &nbsp;·&nbsp; SC-relevance 3/5 &nbsp;·&nbsp; confidence: high

### Automation is control movement over the Arrangement timeline or a Session clip.

> Often, when working with Live's mixer and devices, you will want the controls' movements to become part of the music. The movement of a control across the song timeline or Session clip is called automation; a control whose value changes in the course of this timeline is automated. Practically all mixer and device controls in Live can be automated, including the song tempo.

`25. Automation and Editing Envelopes :: 25. Automation and Editing Envelopes :: 1` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Automation Arm determines whether manual parameter moves become Arrangement automation when recording directly.

> When recording new material directly to the Arrangement, the Automation Arm button determines whether or not manual parameter changes will be recorded.

`25. Automation and Editing Envelopes :: 25.1 Recording Automation in Arrangement View :: 5` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Session View automation becomes track-based automation when copied or recorded into Arrangement View.

> Any automation in Session View becomes track-based automation when clips are recorded or copied into Arrangement View.

`25. Automation and Editing Envelopes :: 25.2 Recording Automation in Session View :: 15` &nbsp;·&nbsp; **workflow gotcha** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Session automation can be recorded into all playing Session clips even when their tracks are not armed.

> It is also possible to record automation into all playing Session clips, regardless of whether or not they are in armed tracks. This is done via the Session Automation Recording switch in the Record, Warp & Launch Settings.

`25. Automation and Editing Envelopes :: 25.2 Recording Automation in Session View :: 5` &nbsp;·&nbsp; **workflow gotcha** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Automation can be re-enabled per parameter or by relaunching a Session clip containing automation.

> You can also re-enable automation for only one parameter via the Re-Enable Automation option in the context menu forthat parameter. And in the Session View, you can re-enable overridden automation by simply relaunching a clip that contains automation.

`25. Automation and Editing Envelopes :: 25.4 Overriding Automation :: 5` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### The automation Device chooser can target Mixer, a track device, or None and can show automated parameters only.

> 4. The Device chooser either selects the track mixer, one of the track's devices, or "None" to hide the envelope. It also provides you with an overview of which devices actually have automation by showing an LED next to their labels. You can make things clearer still by selecting "Show Automated Parameters Only" from the bottom of the chooser.

`25. Automation and Editing Envelopes :: 25.5 Drawing and Editing Automation :: 7` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Manual control changes override automation until automation is re-enabled or a Session clip with automation launches.

> Changing an automated control's value while not recording is similar to launching a Session clip while the Arrangement is playing: It deactivates the control's automation (in favor of the new control setting). The control will stop tracking its automation and continue using the new value until the Re-Enable Automation button is pressed or a Session clip that contains automation is launched.

`3. Live Concepts :: 3.18 Automation Envelopes :: 4` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

## See also

[[Session vs Arrangement]] · [[Devices, Racks & Plug-ins]] · [[Hard Constraints]]
