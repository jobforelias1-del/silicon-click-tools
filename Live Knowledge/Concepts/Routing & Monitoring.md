# Routing & Monitoring

*Where a signal can be tapped, and when input is heard vs. clips.* Monitoring
state matters for recording features: **Auto** turns input monitoring off while
a track plays clips; **In** passes input permanently and **suppresses clip
output**; a **Resampling** track's own output is excluded from its recording.
Internal routing exposes **Pre FX / Post FX / Post Mixer** taps (including per
Rack chain), and return-track sends are disabled by default to prevent
feedback.

Relevant whenever a feature sets track I/O, sends, monitoring, or internal
routing — especially recording/resampling flows.

## Findings

### Auto monitoring turns input monitoring off while the track is playing clips.

> • The default Auto-monitoring setting does the right thing for most straightforward recording applications: Monitoring is on when the track is armed, but monitoring is inhibited as long as the track is playing clips.

`17. Routing and 1/O :: 17.1 Monitoring :: 3` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### In monitoring permanently passes input and suppresses clip output.

> • To permanently monitor the track's input, regardless of whether the track is armed or clips are playing, choose In. This setting effectively turns the track into what is called an "Aux" on some systems: the track is not used for recording but for bringing in a signal from elsewhere. With this setting, output from the clips is suppressed. An "In" monitoring setting can be easily recognized even when the In/Out section is hidden by the blue color of the track's Activator switch.

`17. Routing and 1/O :: 17.1 Monitoring :: 4` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Monitoring means routing a track's input signal through its device chain to its output.

> "Monitoring," in the context of Live, means passing a track's input signal on to the track's output. Suppose you have set up an audio track to receive its input signal from a guitar. Monitoring then means that the signal from your live guitar playing actually reaches the track's output, via the track's device chain. If the track's output is set to "Main," you can hear the guitar signal, processed by whatever effects are used (and delayed by whatever latency the audio hardware interface incurs), over your speakers.

`17. Routing and 1/O :: 17.1 Monitoring :: 1` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Monitor button defaults differ by track type: Off for audio tracks and Auto for MIDI tracks.

> The Monitor buttons can also be restored to their default state. When the In/Out section is expanded, you can press the Delete key to reset the Monitor buttons to the default ("Off" for audio tracks and "Auto" for MIDI tracks), or you can select the Edit menu option "Return to Default."

`17. Routing and 1/O :: 17.1 Monitoring :: 8` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 3/5 &nbsp;·&nbsp; confidence: high

### A resampling track's own output is suppressed and excluded from the resampling recording.

> The "Resampling" option in any audio track's Input Type chooser will route the Main output to that track. You can then decide on what exactly you will be resampling and mute, solo or otherwise adjust the tracks that are feeding the Main output. You will probably want to use the Main Volume meter to make sure that your level is as high as possible without clipping (indicated by red in the meter). Then you can arm the track and record into any of its empty clip slots. Note that the recording track's own output will be suppressed while resampling is taking place, and will not be included in the recording.

`17. Routing and 1/O :: 17.4 Resampling :: 2` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Post FX taps signal after device chains but before the track mixer.

> • Post FX taps the signal at the output of a track's device chains (FX), but before it has been passed back to the track mixer. Changes to the tapped track's devices will therefore alter the tapped signal, but changes to its mixer settings will not. Soloing a track that taps another track Post FX will allow you to hear the tapped track.

`17. Routing and 1/O :: 17.5.1 Internal Routing Points :: 5` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Post Mixer taps final post-device, post-mixer track output.

> • Post Mixer taps the final output of a track, after it has passed through its device chains and mixer. Soloing a track that taps another track Post Mixer will not allow you to hear the tapped track.

`17. Routing and 1/O :: 17.5.1 Internal Routing Points :: 6` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Rack and Drum Rack chains expose internal routing points such as Pre FX, Post FX, and Post Mixer.

> If a track has one or more Instrument or Effect Racks in its device chain, internal routing points (Pre EX, Post EX and Post Mixer) will also be available for every chain within the Rack. If a track contains one or more Drum Racks, internal routing points will be available for any of the Rack's return chains. Each Rack will also be listed in the Input Channel chooser:

`17. Routing and 1/O :: 17.5.1 Internal Routing Points :: 9` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Mono inputs record mono samples while device-chain signals are always stereo.

> When a mono signal is chosen as an audio track's input, the track will record mono samples; otherwise it will record stereo samples. Signals in the track's device chain are always stereo, even when the track's input is mono or when the track plays mono samples.

`17. Routing and 1/O :: 17.2.1 Mono/Stereo Conversions :: 1` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### External Instrument can send MIDI out and return audio inside a single track.

> In addition to routing via a track's In/Out section, it is also possible to route from within a track's device chain by using the External Instrument device. In this case, you can send MIDI out to the external synthesizer and return its audio — all within a single track.

`17. Routing and 1/O :: 17.3.3 Connecting External Synthesizers :: 2` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### MIDI messages mapped to Live remote control are consumed and do not pass to MIDI tracks.

> MIDI messages that are mapped to remote-control Live's user-interface elements are "eaten up" by the remote control assignment and will not be passed on to the MIDI tracks. This is a common cause of confusion that can be easily resolved by looking at the indicators.

`17. Routing and 1/O :: 17.3.4 MIDI In/Out Indicators :: 8` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Audio/MIDI From chooses track input, with audio tracks, MIDI tracks, and returns receiving different source types.

> • The upper chooser pair ("Audio/MIDI From") selects the track's input. Audio tracks have an audio input, and MIDI tracks have a MIDI input. Return tracks receive their input from the respective sends.

`17. Routing and 1/O :: 17. Routing and 1/O :: 69` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Return-track send controls are disabled by default to avoid runaway feedback.

> A clip or group track's Send control determines how much of the track's output feeds the associated return track's input. What's more, even the return track's own output can be routed to its input, allowing you to create feedback. Because runaway feedback can boost the level dramatically and unexpectedly, the Send controls in Return tracks are disabled by default. To enable them, right-click on a Return track's Send knob and select Enable Send or Enable All Sends.

`18. Mixing :: 18.4 Return Tracks and the Main track :: 9` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Return tracks host effects that process audio sent from multiple tracks.

> Like regular clip tracks, return tracks can host effects devices. However, whereas a clip track's effect processes only the audio within that track, return tracks can process audio sent to them from numerous tracks.

`18. Mixing :: 18.4 Return Tracks and the Main track :: 4` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Under Auto monitoring, the track Arm button must be active to hear external input through the device chain.

> If you want to use an external input signal to feed a track in Live, the track's Arm button in the mixer must be activated in order to hear the input through the devices in the track's device chain when using the default Auto monitoring setting. On MIDI tracks, this is normally activated automatically when inserting an instrument.

`23. Working with Instruments and Effects :: 23.2 Using Devices :: 31` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### When recording MIDI while listening directly to hardware, track monitoring should be disabled to avoid added latency compensation.

> • Do not enable track monitoring if you are recording MIDI while listening directly to a hardware device such as an external synthesizer (as opposed to listening to the device's audio through Live via the External Instrument device). Likewise, disable track monitoring when recording MIDI data that is generated by another MIDI device (such as a drum machine). When monitoring is enabled, Live adds latency to compensate for playthrough jitter. Therefore, it is important to only enable monitoring when actually playing through.

`39. MIDI Fact Sheet :: 39.5 Tips for Achieving Optimal MIDI Performance :: 4` &nbsp;·&nbsp; **workflow gotcha** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

## See also

[[Track Types & Clip Hosting]] · [[Devices, Racks & Plug-ins]] · [[Hard Constraints]]
