# Session vs Arrangement

*The exclusivity model SC keeps rediscovering.* Per track, Session and
Arrangement playback are **mutually exclusive** — launching a Session clip
stops that track's Arrangement playback, and it does not resume until **Back to
Arrangement** is pressed. This is the constraint that forced the scene-cue
redesign. The same split shows up in clip properties (launch controls exist
only for Session clips) and in envelopes (Arrangement clips carry only
modulation; automation lives on the track lane).

If a feature wires up scene cues, follow actions, or per-track playback state,
read this before assuming Session and Arrangement coexist on a track.

## Findings

### Session clips override Arrangement clips per track and require Back to Arrangement before that track resumes Arrangement playback.

> At any one time, a track can be playing either a Session clip or an Arrangement clip, but never both. Session clips take precedence. When a Session clip is launched, the currently playing clip stops in favor of playing the newly-launched clip. In particular, if an Arrangement clip is playing on the track, it will stop so that the Session clip can be played instead — even as the other tracks continue to play Arrangement clips. The Arrangement clips in the track where the Session clip was launched will not resume playback until you manually restart it using the Back to Arrangement button.

`3. Live Concepts :: 3.7 Tracks :: 5` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Within a track, Session clips and Arrangement clips are mutually exclusive and Clip Stop can silence Arrangement playback.

> The Session clips and the Arrangement clips in one track are mutually exclusive: Only one can play at a time. When a Session clip is launched, Live stops playing back that track's Arrangement in favor of the Session clip. Clicking a Clip Stop button causes the Arrangement playback to stop, which produces silence.

`7. Session View :: 7.5 Recording Sessions into the Arrangement :: 13` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Arrangement playback resumes only after explicit Back to Arrangement action.

> Arrangement playback does not resume until you explicitly tell Live to resume by clicking the Back to Arrangement button, which appears in the Arrangement View and lights up to remind you that what you hear differs from the Arrangement.

`7. Session View :: 7.5 Recording Sessions into the Arrangement :: 14` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Recording Session launches into Arrangement copies clip references and timing, not new audio data.

> To view the results of your recording, bring up the Arrangement View. As you can see, Live has copied the clips you launched during recording into the Arrangement, in the appropriate tracks and the correct song positions. Notice that your recording has not created new audio data, only clips.

`7. Session View :: 7.5 Recording Sessions into the Arrangement :: 12` &nbsp;·&nbsp; **workflow gotcha** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Consolidate Time to New Scene creates one Session clip per track and new samples for audio tracks with clips.

> Another way to move material from the Arrangement to the Session is with the Arrangement View's Consolidate Time to New Scene command, which is available from the Create menu or in the context menu of an Arrangement selection. This command consolidates the material within the selected time range to one new clip per track. The new clips are placed into a new Session View scene below the previously selected scene. Note that, as with the Arrangement's Consolidate command, this command creates a new sample for every audio track in the selection that contained at least one clip.

`7. Session View :: 7.5 Recording Sessions into the Arrangement :: 19` &nbsp;·&nbsp; **workflow gotcha** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Launch controls appear only for Session clips because Arrangement clips are timeline-driven rather than launched.

> Note that since Arrangement clips are not launched, but instead played according to their position on the timeline, this panel shows the clip launch controls only when a Session View clip is selected. Th is means that the panel does not appear in the Clip View at all when an Arrangement audio clip is selected, and contains only the MIDI bank/program controls when an Arrangement MIDI clip is selected.

`8. Clip View :: 8.3 Extended Clip Properties :: 3` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Session clips can hold automation and modulation envelopes, but Arrangement clips only hold modulation envelopes.

> Both automation and modulation clip envelopes are available for clips in the Session View. A toggle beneath the envelope choosers allows you to switch between editing automation and modulation clip envelopes for the selected parameter. In the Arrangement, clips only have modulation envelopes, while the automation envelopes reside on the track's automation lane.

`26. Clip Envelopes :: 26.3 Mixer and Device Clip Envelopes :: 3` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Session View automation becomes track-based automation when copied or recorded into Arrangement View.

> Any automation in Session View becomes track-based automation when clips are recorded or copied into Arrangement View.

`25. Automation and Editing Envelopes :: 25.2 Recording Automation in Session View :: 15` &nbsp;·&nbsp; **workflow gotcha** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Session-to-Arrangement recording always records Session clip automation into the Arrangement.

> During Session-to-Arrangement recording, automation in Session clips is always recorded to the Arrangement, as are any manual changes to parameters in tracks that are being recorded from the Session.

`25. Automation and Editing Envelopes :: 25.1 Recording Automation in Arrangement View :: 4` &nbsp;·&nbsp; **workflow gotcha** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Session and Arrangement Arm buttons operate on the same shared track.

> To select a track for recording, click on its Arm button. It doesn't matter if you click a track's Arm button in the Session View or in the Arrangement View, since the two share the same set of tracks.

`19. Recording New Clips :: 19.2 Arming (Record-Enabling) Tracks :: 2` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

## See also

[[Automation vs Modulation]] · [[Follow Actions]] · [[Hard Constraints]]
