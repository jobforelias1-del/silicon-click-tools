# Track Types & Clip Hosting

*What kind of track can hold what.* This is the model that, mis-set, cost the
first SC track (*Pression Archivée*) seven tracks of silent drums: AbletonOSC
accepts MIDI note-writes onto an audio track and drops them on the floor, no
error. The structure spec declares track type once and `scaffold` builds it
correctly — but a session reasoning about *where a clip or device can live*
needs the rules below.

The short version: **audio clips and MIDI clips are not interchangeable**, the
device a track will accept depends on its type, and several track kinds (Group,
Return, Main) cannot hold clips at all.

## Findings

### Audio and MIDI tracks have distinct clip types and cannot host the other track type's clips.

> Audio signals are recorded and played back using audio tracks, and MIDI signals are recorded and played back using MIDI tracks. The two track types have their own corresponding clip types. Audio clips cannot be added to MIDI tracks and vice versa.

`3. Live Concepts :: 3.8 Audio and MIDI :: 3` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Audio and return tracks only accept audio effects, while MIDI tracks can also host MIDI effects and instruments.

> Devices that receive and deliver audio signals are called audio effects. Audio effects are the only type of device that fits in an audio track or a return track. However, two more types of devices are available for use in MIDI tracks: MIDI effects and instruments.

`3. Live Concepts :: 3.11 Devices :: 3` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### A track is monophonic at the clip-playback layer, so simultaneous material must be spread across tracks or scenes.

> A track can only play one clip at a time. Therefore, one usually places clips that should play alternatively in the same Session View column, and spreads out clips that should play together across tracks in rows, or what we call scenes.

`3. Live Concepts :: 3.7 Tracks :: 3` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### A Session View track column can play only one clip at a time.

> Each vertical column, or track, can play only one clip at a time. It therefore makes sense to put a set of clips that are supposed to be played alternatively in the same columns: parts of a song, variations of a drum loop, etc.

`7. Session View :: 7.2 Tracks and Scenes :: 1` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### In a MIDI track, devices before an instrument receive MIDI while devices after it receive audio.

> If you drop an instrument into a MIDI tracks device chain, be aware that signals following (to the right of) the instrument are audio signals, available only to audio effects. Signals preceding (to the left of) the instrument are MIDI signals, available only to MIDI effects. This means that it's possible for a MIDI tracks device chain to hold all three types of devices: first MIDI effects, then an instrument, and finally audio effects.

`23. Working with Instruments and Effects :: 23.2 Using Devices :: 36` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Signals in a device chain flow from left to right.

> To add another device to the track, simply drag it there or double-click its name to append it to the device chain. Signals in a device chain always travel from left to right.

`23. Working with Instruments and Effects :: 23.2 Using Devices :: 34` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### VST/AU instruments are MIDI-track devices, while plug-in audio effects belong on audio tracks or after instruments.

> Working with VST and Audio Units plug-ins is very much like working with Live devices. VST and AU instruments can only be placed in Live MIDI tracks and, like Live instruments, they will receive MIDI and output audio signals. Plug-in audio effects can only be placed in audio tracks or following instruments. Please see the previous section, Using the Live Devices, for details.

`23. Working with Instruments and Effects :: 23.3 Using Plug-Ins :: 4` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Group Tracks cannot contain clips, even though they have mixer controls and host audio effects.

> Group Tracks themselves cannot contain clips, but they are similar to audio tracks in that they have mixer controls and can host audio effects.

`18. Mixing :: 18.3 Group Tracks :: 2` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Return tracks and the Main track cannot play clips.

> In addition to Group Tracks and tracks that play clips, a Live Set has a Main track and return tracks; these cannot play clips, but allow for more flexible signal processing and routing.

`18. Mixing :: 18.4 Return Tracks and the Main track :: 1` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### A Set can have multiple return tracks but exactly one Main track.

> You can create multiple return tracks using the Create menu's Insert Return Track command, but by definition, there is only one Main track.

`18. Mixing :: 18.4 Return Tracks and the Main track :: 12` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Return track clip slots cannot contain or launch clips.

> (Win) / Cmd Shift M (Mac). You can launch a selected clip by pressing Enter. If Live's transport is running, the clip will begin playing based on the current setting in the Control Bar's quantization menu. Note that while clip slots also appear in return tracks, these slots cannot contain or launch any clips.

`40. Accessibility and Keyboard Navigation :: 40.4.1 Navigate Menu :: 10` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Group Tracks cannot be frozen.

> Live's Freeze Track command can greatly help in managing the CPU load incurred by devices and clip settings. When you select a track and execute the Freeze Track command, Live will create a sample file for each Session clip in the track, plus one for the Arrangement. Thereafter, clips in the track will simply play back their "freeze files" rather than repeatedly calculating processor-intensive device and clip settings in real time. The Freeze Track command is available from Live's Edit menu and from the context menu of tracks and clips. Be aware that it is not possible to freeze a Group Track; you can only freeze tracks that hold clips.

`37. Computer Audio Resources and Strategies :: 37.1.4 Track Freeze :: 1` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

## See also

[[Devices, Racks & Plug-ins]] · [[Routing & Monitoring]] · [[Hard Constraints]]
