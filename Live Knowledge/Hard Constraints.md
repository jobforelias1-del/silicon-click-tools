# Hard Constraints

> The non-negotiable rules of Ableton Live, pulled from Codex's recon and
> **ranked by SC-relevance**. These are the things that break a build
> *silently* if you assume otherwise. Read this before designing any
> feature that touches Live. Source: Live 12, via the recon JSONL in
> `_source/`. Quotes are verbatim (OCR artifacts intact).

**61 hard constraints.** Each links to the concept hub that explains it
in context. See [[README]] for how to read the corpus.

## SC-relevance 5 — these bite hardest

### The Stop Follow Action overrides clip loop and region settings.

> | ■ Stop ▼! simply stops the clip after it has played for the chosen Follow Action Time. Note that this overrides clip loop/region settings.

`16. Launching Clips :: 16.7 Follow Actions :: 10` &nbsp;·&nbsp; [[Follow Actions]]

### Clip Follow Actions bypass global quantization but still obey clip quantization.

> Note that a clip Follow Action happens exactly after the duration that is specified by the Follow Action Time controls unless clip quantization is set to a value other than "None" or "Global." Follow Actions circumvent global quantization but not clip quantization.

`16. Launching Clips :: 16.7 Follow Actions :: 24` &nbsp;·&nbsp; [[Follow Actions]]

### Clip Follow Actions continue while scene Follow Actions are pending, but scene Follow Actions take precedence once triggered.

> Note that Follow Actions in clips will continue to run when a scene Follow Action is created or scheduled, however Follow Actions in scenes always take precedence once they are triggered.

`16. Launching Clips :: 16.7 Follow Actions :: 27` &nbsp;·&nbsp; [[Follow Actions]]

### No Action prevents the other selected clip Follow Action from occurring after it triggers.

> |No Action ▼! means that no Follow Action will occur. Once a clip has been triggered with No Action, any other selected Follow Action in the clip will no longer have a chance of occurring, even if its Follow Action Chance is set to 100%.

`16. Launching Clips :: 16.7 Follow Actions :: 9` &nbsp;·&nbsp; [[Follow Actions]]

### Auto monitoring turns input monitoring off while the track is playing clips.

> • The default Auto-monitoring setting does the right thing for most straightforward recording applications: Monitoring is on when the track is armed, but monitoring is inhibited as long as the track is playing clips.

`17. Routing and 1/O :: 17.1 Monitoring :: 3` &nbsp;·&nbsp; [[Routing & Monitoring]]

### In monitoring permanently passes input and suppresses clip output.

> • To permanently monitor the track's input, regardless of whether the track is armed or clips are playing, choose In. This setting effectively turns the track into what is called an "Aux" on some systems: the track is not used for recording but for bringing in a signal from elsewhere. With this setting, output from the clips is suppressed. An "In" monitoring setting can be easily recognized even when the In/Out section is hidden by the blue color of the track's Activator switch.

`17. Routing and 1/O :: 17.1 Monitoring :: 4` &nbsp;·&nbsp; [[Routing & Monitoring]]

### A resampling track's own output is suppressed and excluded from the resampling recording.

> The "Resampling" option in any audio track's Input Type chooser will route the Main output to that track. You can then decide on what exactly you will be resampling and mute, solo or otherwise adjust the tracks that are feeding the Main output. You will probably want to use the Main Volume meter to make sure that your level is as high as possible without clipping (indicated by red in the meter). Then you can arm the track and record into any of its empty clip slots. Note that the recording track's own output will be suppressed while resampling is taking place, and will not be included in the recording.

`17. Routing and 1/O :: 17.4 Resampling :: 2` &nbsp;·&nbsp; [[Routing & Monitoring]]

### Group Tracks cannot contain clips, even though they have mixer controls and host audio effects.

> Group Tracks themselves cannot contain clips, but they are similar to audio tracks in that they have mixer controls and can host audio effects.

`18. Mixing :: 18.3 Group Tracks :: 2` &nbsp;·&nbsp; [[Track Types & Clip Hosting]]

### Return tracks and the Main track cannot play clips.

> In addition to Group Tracks and tracks that play clips, a Live Set has a Main track and return tracks; these cannot play clips, but allow for more flexible signal processing and routing.

`18. Mixing :: 18.4 Return Tracks and the Main track :: 1` &nbsp;·&nbsp; [[Track Types & Clip Hosting]]

### A Set can have multiple return tracks but exactly one Main track.

> You can create multiple return tracks using the Create menu's Insert Return Track command, but by definition, there is only one Main track.

`18. Mixing :: 18.4 Return Tracks and the Main track :: 12` &nbsp;·&nbsp; [[Track Types & Clip Hosting]]

### In a MIDI track, devices before an instrument receive MIDI while devices after it receive audio.

> If you drop an instrument into a MIDI tracks device chain, be aware that signals following (to the right of) the instrument are audio signals, available only to audio effects. Signals preceding (to the left of) the instrument are MIDI signals, available only to MIDI effects. This means that it's possible for a MIDI tracks device chain to hold all three types of devices: first MIDI effects, then an instrument, and finally audio effects.

`23. Working with Instruments and Effects :: 23.2 Using Devices :: 36` &nbsp;·&nbsp; [[Track Types & Clip Hosting]] · [[Devices, Racks & Plug-ins]]

### VST/AU instruments are MIDI-track devices, while plug-in audio effects belong on audio tracks or after instruments.

> Working with VST and Audio Units plug-ins is very much like working with Live devices. VST and AU instruments can only be placed in Live MIDI tracks and, like Live instruments, they will receive MIDI and output audio signals. Plug-in audio effects can only be placed in audio tracks or following instruments. Please see the previous section, Using the Live Devices, for details.

`23. Working with Instruments and Effects :: 23.3 Using Plug-Ins :: 4` &nbsp;·&nbsp; [[Track Types & Clip Hosting]] · [[Devices, Racks & Plug-ins]]

### Plug-ins that do not publish parameters prevent those parameters from being added to Live's panel.

> While in Configure Mode, parameters in Live's panel can be reordered or moved by dragging and dropping them to new locations. Parameters can be deleted by pressing the Delete key. If you try to delete a parameter that has existing automation data, clip envelopes, or MIDI, key or Macro mappings, Live will warn you before proceeding.

`23. Working with Instruments and Effects :: 23.3.1 Plug-Ins in the Device View :: 19` &nbsp;·&nbsp; [[Devices, Racks & Plug-ins]]

### Automation envelopes define absolute values, while modulation envelopes only influence the defined value.

> Clip envelopes can be used to automate or modulate mixer and device controls. Since mixer and device controls can potentially be controlled by both types of envelopes at the same time (and also by the Arrangement's automation envelopes, this is a potential source of confusion. However, modulation envelopes differ from automation envelopes in one important way: Whereas automation envelopes define the absolute value of a control at any given point in time, modulation envelopes can only influence this defined value. This difference allows the two types of envelopes to work together in harmony when controlling the same parameter. To help you distinguish between these, automation envelopes are colored in red, whereas modulation envelopes are colored in blue. Additionally, in parameters with knob controls, automation moves the absolute position (or the "needle"), whereas modulation is indicated by the blue segment on the ring.

`26. Clip Envelopes :: 26.3 Mixer and Device Clip Envelopes :: 1` &nbsp;·&nbsp; [[Automation vs Modulation]]

### Session clips can hold automation and modulation envelopes, but Arrangement clips only hold modulation envelopes.

> Both automation and modulation clip envelopes are available for clips in the Session View. A toggle beneath the envelope choosers allows you to switch between editing automation and modulation clip envelopes for the selected parameter. In the Arrangement, clips only have modulation envelopes, while the automation envelopes reside on the track's automation lane.

`26. Clip Envelopes :: 26.3 Mixer and Device Clip Envelopes :: 3` &nbsp;·&nbsp; [[Session vs Arrangement]] · [[Automation vs Modulation]]

### Audio and return tracks only accept audio effects, while MIDI tracks can also host MIDI effects and instruments.

> Devices that receive and deliver audio signals are called audio effects. Audio effects are the only type of device that fits in an audio track or a return track. However, two more types of devices are available for use in MIDI tracks: MIDI effects and instruments.

`3. Live Concepts :: 3.11 Devices :: 3` &nbsp;·&nbsp; [[Track Types & Clip Hosting]]

### A track is monophonic at the clip-playback layer, so simultaneous material must be spread across tracks or scenes.

> A track can only play one clip at a time. Therefore, one usually places clips that should play alternatively in the same Session View column, and spreads out clips that should play together across tracks in rows, or what we call scenes.

`3. Live Concepts :: 3.7 Tracks :: 3` &nbsp;·&nbsp; [[Track Types & Clip Hosting]]

### Session clips override Arrangement clips per track and require Back to Arrangement before that track resumes Arrangement playback.

> At any one time, a track can be playing either a Session clip or an Arrangement clip, but never both. Session clips take precedence. When a Session clip is launched, the currently playing clip stops in favor of playing the newly-launched clip. In particular, if an Arrangement clip is playing on the track, it will stop so that the Session clip can be played instead — even as the other tracks continue to play Arrangement clips. The Arrangement clips in the track where the Session clip was launched will not resume playback until you manually restart it using the Back to Arrangement button.

`3. Live Concepts :: 3.7 Tracks :: 5` &nbsp;·&nbsp; [[Session vs Arrangement]]

### Audio and MIDI tracks have distinct clip types and cannot host the other track type's clips.

> Audio signals are recorded and played back using audio tracks, and MIDI signals are recorded and played back using MIDI tracks. The two track types have their own corresponding clip types. Audio clips cannot be added to MIDI tracks and vice versa.

`3. Live Concepts :: 3.8 Audio and MIDI :: 3` &nbsp;·&nbsp; [[Track Types & Clip Hosting]]

### Tempo Follower and External Sync are mutually exclusive for receiving sync.

> Note that Tempo Follower and External Sync are mutually exclusive and the External Sync option is disabled when Tempo Follower is active. Live can still send MIDI clock information to external devices when Tempo Follower is enabled, but it cannot receive it.

`36. Synchronizing with Link, Tempo Follower, and MIDI :: 36.2.1 Setting Up Tempo Follower :: 8` &nbsp;·&nbsp; [[Tempo, Warp & Sync]]

### A Session View track column can play only one clip at a time.

> Each vertical column, or track, can play only one clip at a time. It therefore makes sense to put a set of clips that are supposed to be played alternatively in the same columns: parts of a song, variations of a drum loop, etc.

`7. Session View :: 7.2 Tracks and Scenes :: 1` &nbsp;·&nbsp; [[Track Types & Clip Hosting]]

### Within a track, Session clips and Arrangement clips are mutually exclusive and Clip Stop can silence Arrangement playback.

> The Session clips and the Arrangement clips in one track are mutually exclusive: Only one can play at a time. When a Session clip is launched, Live stops playing back that track's Arrangement in favor of the Session clip. Clicking a Clip Stop button causes the Arrangement playback to stop, which produces silence.

`7. Session View :: 7.5 Recording Sessions into the Arrangement :: 13` &nbsp;·&nbsp; [[Session vs Arrangement]]

### Arrangement playback resumes only after explicit Back to Arrangement action.

> Arrangement playback does not resume until you explicitly tell Live to resume by clicking the Back to Arrangement button, which appears in the Arrangement View and lights up to remind you that what you hear differs from the Arrangement.

`7. Session View :: 7.5 Recording Sessions into the Arrangement :: 14` &nbsp;·&nbsp; [[Session vs Arrangement]]

### Only one tempo leader can determine tempo; among multiple leaders, the bottom-most currently playing clip wins.

> Any number of clips can be set as tempo leaders, but only one clip at a time can actually determine the tempo. When multiple clips on different tracks are leaders, the tempo of the currently playing clip on the bottom-most track will take precedence.

`9. Audio Clips, Tempo, and Warping :: 9.1.4 Clip Tempo Followers and Leaders :: 5` &nbsp;·&nbsp; [[Tempo, Warp & Sync]]

### Clip tempo leaders override Tempo Follower input.

> Automation from clip tempo leaders will override the tempo from any audio input being synced via Tempo Follower.

`9. Audio Clips, Tempo, and Warping :: 9.1.4 Clip Tempo Followers and Leaders :: 8` &nbsp;·&nbsp; [[Tempo, Warp & Sync]]

## SC-relevance 4

### Slice to New MIDI Track cannot proceed if the slice choice would create more than 128 Rack chains.

> When you select Slice to New MIDI track, you'll be presented with a dialog box. This offers a list of slicing divisions, as well as a chooser to select the Slicing Preset, The top chooser allows you to slice at a variety of beat resolutions or according to the clip's transients or Warp Markers. Since a Rack can contain a maximum of 128 chains, Live won't let you proceed if your choice would result in more than 128 slices. You can fix this by either setting a lower slice resolution or by selecting a smaller region of the clip to slice.

`13. Converting Audio to MIDI :: 13.1 Slice to New MIDI Track :: 3` &nbsp;·&nbsp; [[Devices, Racks & Plug-ins]]

### MIDI messages mapped to Live remote control are consumed and do not pass to MIDI tracks.

> MIDI messages that are mapped to remote-control Live's user-interface elements are "eaten up" by the remote control assignment and will not be passed on to the MIDI tracks. This is a common cause of confusion that can be easily resolved by looking at the indicators.

`17. Routing and 1/O :: 17.3.4 MIDI In/Out Indicators :: 8` &nbsp;·&nbsp; [[Routing & Monitoring]]

### Exclusive Arm allows only one armed track unless modifiers or settings permit multiple armed tracks.

> 6. If the Arm Recording button is on, the track is record-enabled. With multiple tracks selected, pressing any of their Arm switches will arm all of them. Otherwise, tracks can only be armed one at a time unless the Ctrl (Win)/ Cmd (Mac) modifier is held down or the Exclusive Arm option in the Record, Warp & Launch Settings is deactivated. With Exclusive Arm enabled, inserting an instrument into a new or empty MIDI track will automatically arm the track.

`18. Mixing :: 18.1 The Live Mixer :: 19`

### Return-track send controls are disabled by default to avoid runaway feedback.

> A clip or group track's Send control determines how much of the track's output feeds the associated return track's input. What's more, even the return track's own output can be routed to its input, allowing you to create feedback. Because runaway feedback can boost the level dramatically and unexpectedly, the Send controls in Return tracks are disabled by default. To enable them, right-click on a Return track's Send knob and select Enable Send or Enable All Sends.

`18. Mixing :: 18.4 Return Tracks and the Main track :: 9` &nbsp;·&nbsp; [[Routing & Monitoring]]

### Track Delay controls are unavailable when device delay compensation is off.

> Note that delay compensation for plug-ins and Live devices is a separate feature, and is automatic by default. Unusually high Track Delay settings or reported latencies from plug-ins may cause noticeable sluggishness in the software. If you are having latency-related difficulties while recording and playing back instruments, you may want to try turning off device delay compensation, however this is not normally recommended. You may also find that adjusting the individual track delays is useful in these cases. Note that the Track Delay controls are unavailable when device delay compensation is deactivated.

`18. Mixing :: 18.7 Track Delays :: 12`

### Clicking one Arm button unarms other tracks unless multi-arm behavior is invoked.

> Clicking one track's Arm button unarms all other tracks unless the Ctrl (Win) / Cmd (Mac) modifier is held. If multiple tracks are selected, clicking one of their Arm buttons will arm the other tracks as well. Arming a track selects the track so you can readily access its devices in the Device View.

`19. Recording New Clips :: 19.2 Arming (Record-Enabling) Tracks :: 5`

### Record Quantization cannot be changed during Session or Arrangement recording.

> For Session and Arrangement recording, the Record Quantization setting cannot be changed midrecording.

`19. Recording New Clips :: 19.5 Recording Quantized MIDI Notes :: 2`

### Under Auto monitoring, the track Arm button must be active to hear external input through the device chain.

> If you want to use an external input signal to feed a track in Live, the track's Arm button in the mixer must be activated in order to hear the input through the devices in the track's device chain when using the default Auto monitoring setting. On MIDI tracks, this is normally activated automatically when inserting an instrument.

`23. Working with Instruments and Effects :: 23.2 Using Devices :: 31` &nbsp;·&nbsp; [[Routing & Monitoring]]

### Automation Arm determines whether manual parameter moves become Arrangement automation when recording directly.

> When recording new material directly to the Arrangement, the Automation Arm button determines whether or not manual parameter changes will be recorded.

`25. Automation and Editing Envelopes :: 25.1 Recording Automation in Arrangement View :: 5` &nbsp;·&nbsp; [[Automation vs Modulation]]

### Manual control changes override automation until automation is re-enabled or a Session clip with automation launches.

> Changing an automated control's value while not recording is similar to launching a Session clip while the Arrangement is playing: It deactivates the control's automation (in favor of the new control setting). The control will stop tracking its automation and continue using the new value until the Re-Enable Automation button is pressed or a Session clip that contains automation is launched.

`3. Live Concepts :: 3.18 Automation Envelopes :: 4` &nbsp;·&nbsp; [[Automation vs Modulation]]

### MIDI Timecode carries no meter information, cannot track tempo changes, and Live can only act as a sync device for it.

> MIDI Timecode: MIDI Timecode is the MIDI version of the SMPTE protocol, the standard means of synchronizing tape machines and computers in the audio and film industry. A MIDI Timecode message specifies a time in seconds and frames (subdivisions of a second). Live will interpret a Timecode message as a position in the Arrangement. Timecode messages carry no meter-related information; when slaving Live to another sequencer using MIDI Timecode, you will have to adjust the tempo manually. Tempo changes cannot be tracked. Detailed MIDI Timecode Settings are explained later in this chapter. With respect to MIDI Timecode, Live can only act as a MIDI sync device, not a host.

`36. Synchronizing with Link, Tempo Follower, and MIDI :: 36.3 Synchronizing via MIDI :: 3` &nbsp;·&nbsp; [[Tempo, Warp & Sync]]

### Group Tracks cannot be frozen.

> Live's Freeze Track command can greatly help in managing the CPU load incurred by devices and clip settings. When you select a track and execute the Freeze Track command, Live will create a sample file for each Session clip in the track, plus one for the Arrangement. Thereafter, clips in the track will simply play back their "freeze files" rather than repeatedly calculating processor-intensive device and clip settings in real time. The Freeze Track command is available from Live's Edit menu and from the context menu of tracks and clips. Be aware that it is not possible to freeze a Group Track; you can only freeze tracks that hold clips.

`37. Computer Audio Resources and Strategies :: 37.1.4 Track Freeze :: 1` &nbsp;·&nbsp; [[Track Types & Clip Hosting]]

### Return track clip slots cannot contain or launch clips.

> (Win) / Cmd Shift M (Mac). You can launch a selected clip by pressing Enter. If Live's transport is running, the clip will begin playing based on the current setting in the Control Bar's quantization menu. Note that while clip slots also appear in return tracks, these slots cannot contain or launch any clips.

`40. Accessibility and Keyboard Navigation :: 40.4.1 Navigate Menu :: 10` &nbsp;·&nbsp; [[Track Types & Clip Hosting]]

### Long samples may be unavailable for playback until Live has finished analysis or found an existing analysis file.

> When adding a long sample to a project, Live might tell you that it cannot play the sample before it has been analyzed. This will not happen if the sample has already been analyzed (i.e., Live finds an analysis file for this sample), or if the Record, Warp & Launch Settings' Auto-Warp Long Samples preference has been deactivated.

`5. Managing Files and Sets :: 5.1.2 Analysis Files (.asd) :: 2`

### Merging Sets reconstructs regular tracks but explicitly excludes return tracks.

> Live makes it easy to merge Sets, which can come in handy when combining work from different versions or pieces. To add all tracks (except the return tracks) from one Live Set into another, drag the Set from the browser into the current Set, and drop it onto any track title bar or into the drop area next to or below the tracks. The tracks from the dropped Set will be completely reconstructed, including their clips in the Session and Arrangement View, their devices, and their automation.

`5. Managing Files and Sets :: 5.4.2 Merging Sets :: 1`

### Fragmentary-bar delete and complete operations alter all tracks by deleting or inserting Arrangement time.

> Complete Fragmentary Bar inserts time at the beginning of the fragmentary bar, so that it becomes complete. The next time signature marker will now fall on the expected barline.

`6. Arrangement View :: 6.5 Time Signature Changes :: 14`

### Audio clip looping requires Warp to be enabled first.

> Note that for audio clips, the Warp toggle must be activated in the Audio Utilities panel before the Clip Loop toggle can be enabled, as unwarped audio clips cannot be looped.

`8. Clip View :: 8.2.1 Clip and Loop Region Settings :: 7` &nbsp;·&nbsp; [[Tempo, Warp & Sync]]

### Launch controls appear only for Session clips because Arrangement clips are timeline-driven rather than launched.

> Note that since Arrangement clips are not launched, but instead played according to their position on the timeline, this panel shows the clip launch controls only when a Session View clip is selected. Th is means that the panel does not appear in the Clip View at all when an Arrangement audio clip is selected, and contains only the MIDI bank/program controls when an Arrangement MIDI clip is selected.

`8. Clip View :: 8.3 Extended Clip Properties :: 3` &nbsp;·&nbsp; [[Session vs Arrangement]]

### The Clip Loop switch is unavailable for unwarped audio clips.

> To have the clip play as a (potentially infinite) loop, turn on the the Clip Loop toggle. For audio clips, the Warp switch must be activated before the Loop switch is accessible, as unwarped audio clips cannot be looped.

`8. Clip View :: 8.9 Looping Clips :: 1` &nbsp;·&nbsp; [[Tempo, Warp & Sync]]

### Tempo-leader automation is created automatically but is not editable until Unfollow Tempo Automation is used.

> Tempo automation is automatically created to track the changes between the clips' tempos and the Set's tempo. This automation is visible in the Main track but is not editable. When leader clips are rearranged in the Arrangement, the resulting automation is also moved. To keep and edit the automation changes, you can use the Un follow Tempo Automation option in the tempo field's context menu. This will switch all leader clips to followers, and the automation in the Main track will become editable.

`9. Audio Clips, Tempo, and Warping :: 9.1.4 Clip Tempo Followers and Leaders :: 6` &nbsp;·&nbsp; [[Tempo, Warp & Sync]]

### External Sync disables the Lead/Follow toggle.

> Note that when Live's EXT switch is enabled, the Lead/Follow toggle is deactivated.

`9. Audio Clips, Tempo, and Warping :: 9.1.4 Clip Tempo Followers and Leaders :: 9` &nbsp;·&nbsp; [[Tempo, Warp & Sync]]

### First-time imports cannot be played or edited until analysis completes.

> When a file is imported into Live for the first time, it is analyzed and cannot be played or edited until the analysis process is complete. Once analyzed, the sample will be accessible in the Sample Editor, and in most cases, synced with the Set's tempo.

`9. Audio Clips, Tempo, and Warping :: 9.2.2 Importing Samples :: 2` &nbsp;·&nbsp; [[Tempo, Warp & Sync]]

## SC-relevance 3

### Velocity and Chance editor actions in multi-clip editing affect only the foreground clip.

> • Actions in Velocity or Chance Editor are only ever applied to a single clip at a time. The velocity and probability markers are displayed for the foreground clip, not for all clips. It is not possible to make changes to velocity or probability for all notes in all selected clips.

`10. Editing MIDI :: 10.8 Multi-Clip Editing :: 14`

### Some Audio Unit device mode choosers are accessible only through the original plug-in panel.

> Audio Units plug-ins sometimes hove a feature that allows choosing between different modes for the device. You might be able to choose, for example, between different levels of quality in the rendering of a reverb. Choosers for these device modes can only be accessed through the original plug-in panel, which is opened using the Show/Hide Plug-In Window button.

`23. Working with Instruments and Effects :: 23.5 Audio Units Plug-Ins :: 12`

### Drum Rack send controls do not appear until return chains exist.

> 3. Mixer Section - In addition to the mixer and Hot-Swap controls found in other Rack types, Drum Racks also have send sliders. These sliders allow you to set the amount of post-fader signal sent from each drum chain to any of the available return chains. Note that send controls are not available until return chains have been created.

`24. Instrument, Drum and Effect Racks :: 24.6 Drum Racks :: 5` &nbsp;·&nbsp; [[Devices, Racks & Plug-ins]]

### Envelope MIDI Remote Control owns parameter values and prevents manual changes while enabled.

> When Remote Control is enabled, parameter values are determined solely by Envelope MIDI and cannot be changed manually. Use the Min and Max sliders to scale the modulation range.

`32. Max for Live Devices :: 32.3.1 Envelope MIDI :: 9`

### Recording count-in cannot be used when Link is enabled.

> Note that the metronome's recording count-in cannot be used when Link is enabled.

`36. Synchronizing with Link, Tempo Follower, and MIDI :: 36.1.2 Using Link :: 8` &nbsp;·&nbsp; [[Tempo, Warp & Sync]]

### Tempo Follower is disabled when it cannot connect to the configured audio input channel.

> When Tempo Follower cannot be connected to the audio input device channel specified in the Settings, the feature is disabled and the Follow button will appear grayed out.

`36. Synchronizing with Link, Tempo Follower, and MIDI :: 36.2.1 Setting Up Tempo Follower :: 7` &nbsp;·&nbsp; [[Tempo, Warp & Sync]]

### Audio fades cannot cross clip loop boundaries.

> • Fades cannot cross a clip's loop boundaries.

`6. Arrangement View :: 6.8 Audio Clip Fades and Crossfades :: 26`

### A clip's start and end fades cannot overlap.

> • A clip's start and end fades cannot overlap each other.

`6. Arrangement View :: 6.8 Audio Clip Fades and Crossfades :: 27`

### Multiple clips cannot be reversed together in Session View, although Arrangement range reversal can include multiple clips.

> In the Session View, it is not possible to reverse multiple clips at the same time. In the Arrangement View, it is possible to reverse a selection of material, even if it contains multiple clips. To do this, select the range of time you want to reverse, and choose the Reverse Cl ip (s) command from the clip's context menu, or press the R shortcut key.

`8. Clip View :: 8.4.2 Reversing Samples :: 6`

## SC-relevance 2

### Limiter should be last in the Main track chain if it is meant to prevent final clipping.

> Note that adding any further processing effects after Limiter may add gain. To ensure that your final output will never clip, place Limiter as the last device in the Main track's device chain and keep the Main track's volume below 0 dB.

`28. Live Audio Effect Reference :: 28.24 Limiter :: 15`

### Live cannot render video alone; video rendering always also creates rendered audio.

> • Create Video — If this is activated, a video file will be created in the same directory as your rendered audio. Note that this option is only enabled if you have video clips in the Arrangement View. Also, it is not possible to only render a video file — enabling video rendering will always produce a video in addition to rendered audio.

`5. Managing Files and Sets :: 5.1.3 Exporting Audio and Video :: 45`

### A track can participate in only one linked-track instance.

> Note that you can create multiple instances of linked tracks in a Set, however each track can only belong to one of these instances.

`6. Arrangement View :: 6.14.1 Linking and Unlinking Tracks :: 8`

### Arrangement clips can be dragged only from the clip bar, not from waveform or MIDI display areas.

> Note that only the clip bar is draggable, it is not possible to drag from the clip's waveform or MIDI display.

`6. Arrangement View :: 6.7 Moving and Resizing Clips :: 6`

### Fade edge handles cannot pass their fade peaks.

> The Fade In Start and Fade Out End handles let you change the duration of a fade in or fade out without affecting the fade peaks. However, fade edges cannot move beyond fade peaks. You can select one of the handles and drag it out across the clip to change the length of the fade. You can further adjust the fade's intensity using the Fade Curve handle, which shapes the curve of the fade.

`6. Arrangement View :: 6.8 Audio Clip Fades and Crossfades :: 6`
