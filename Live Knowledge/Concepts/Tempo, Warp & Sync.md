# Tempo, Warp & Sync

*What determines the clock, and when warping is allowed.* Among multiple tempo
**leaders** only one wins (the bottom-most currently-playing clip); leaders
override the **Tempo Follower**; and **Tempo Follower and External Sync are
mutually exclusive** for receiving sync. Scene Tempo / Scene Time Signature
change the project on scene launch. On the audio side: unwarped clips cannot
loop, and Warp must be on before Loop is reachable.

Relevant to SC whenever a feature touches the transport, scene-level tempo
changes, or clip warp state via `.als` or AbletonOSC.

## Findings

### Only one tempo leader can determine tempo; among multiple leaders, the bottom-most currently playing clip wins.

> Any number of clips can be set as tempo leaders, but only one clip at a time can actually determine the tempo. When multiple clips on different tracks are leaders, the tempo of the currently playing clip on the bottom-most track will take precedence.

`9. Audio Clips, Tempo, and Warping :: 9.1.4 Clip Tempo Followers and Leaders :: 5` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Clip tempo leaders override Tempo Follower input.

> Automation from clip tempo leaders will override the tempo from any audio input being synced via Tempo Follower.

`9. Audio Clips, Tempo, and Warping :: 9.1.4 Clip Tempo Followers and Leaders :: 8` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Tempo-leader automation is created automatically but is not editable until Unfollow Tempo Automation is used.

> Tempo automation is automatically created to track the changes between the clips' tempos and the Set's tempo. This automation is visible in the Main track but is not editable. When leader clips are rearranged in the Arrangement, the resulting automation is also moved. To keep and edit the automation changes, you can use the Un follow Tempo Automation option in the tempo field's context menu. This will switch all leader clips to followers, and the automation in the Main track will become editable.

`9. Audio Clips, Tempo, and Warping :: 9.1.4 Clip Tempo Followers and Leaders :: 6` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### External Sync disables the Lead/Follow toggle.

> Note that when Live's EXT switch is enabled, the Lead/Follow toggle is deactivated.

`9. Audio Clips, Tempo, and Warping :: 9.1.4 Clip Tempo Followers and Leaders :: 9` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Tempo Follower and External Sync are mutually exclusive for receiving sync.

> Note that Tempo Follower and External Sync are mutually exclusive and the External Sync option is disabled when Tempo Follower is active. Live can still send MIDI clock information to external devices when Tempo Follower is enabled, but it cannot receive it.

`36. Synchronizing with Link, Tempo Follower, and MIDI :: 36.2.1 Setting Up Tempo Follower :: 8` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Tempo Follower is disabled when it cannot connect to the configured audio input channel.

> When Tempo Follower cannot be connected to the audio input device channel specified in the Settings, the feature is disabled and the Follow button will appear grayed out.

`36. Synchronizing with Link, Tempo Follower, and MIDI :: 36.2.1 Setting Up Tempo Follower :: 7` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 3/5 &nbsp;·&nbsp; confidence: high

### Recording count-in cannot be used when Link is enabled.

> Note that the metronome's recording count-in cannot be used when Link is enabled.

`36. Synchronizing with Link, Tempo Follower, and MIDI :: 36.1.2 Using Link :: 8` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 3/5 &nbsp;·&nbsp; confidence: high

### MIDI Timecode carries no meter information, cannot track tempo changes, and Live can only act as a sync device for it.

> MIDI Timecode: MIDI Timecode is the MIDI version of the SMPTE protocol, the standard means of synchronizing tape machines and computers in the audio and film industry. A MIDI Timecode message specifies a time in seconds and frames (subdivisions of a second). Live will interpret a Timecode message as a position in the Arrangement. Timecode messages carry no meter-related information; when slaving Live to another sequencer using MIDI Timecode, you will have to adjust the tempo manually. Tempo changes cannot be tracked. Detailed MIDI Timecode Settings are explained later in this chapter. With respect to MIDI Timecode, Live can only act as a MIDI sync device, not a host.

`36. Synchronizing with Link, Tempo Follower, and MIDI :: 36.3 Synchronizing via MIDI :: 3` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Scene Tempo and Scene Time Signature controls assign project tempo and meter changes on scene launch.

> Dragging the left edge of the Main track's title header reveals the Scene Tempo and Scene Time Signature controls, which allow you to assign a tempo and/or time signature to a selected scene. These controls are hidden by default. The project will automatically adjust to these parameters when the scene is launched. To change a scene's tempo or time signature values:

`7. Session View :: 7.2.1 Editing Scene Tempo and Time Signature Values :: 1` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Sets from before Live 11 convert scene-name tempo or meter values into Scene Tempo and Scene Time Signature controls.

> Note: Sets that were created in older Live versions than Live 11, with tempo and/or time signature values specified by scene names, will have their values carried over to the Scene Tempo and/or Time Signature controls. When opening these Sets in newer versions of Live, the Main track's width is adjusted so that the Scene Tempo and Scene Time Signature controls are visible.

`7. Session View :: 7.2.1 Editing Scene Tempo and Time Signature Values :: 14` &nbsp;·&nbsp; **version sensitive** &nbsp;·&nbsp; SC-relevance 3/5 &nbsp;·&nbsp; confidence: high

### Audio clip looping requires Warp to be enabled first.

> Note that for audio clips, the Warp toggle must be activated in the Audio Utilities panel before the Clip Loop toggle can be enabled, as unwarped audio clips cannot be looped.

`8. Clip View :: 8.2.1 Clip and Loop Region Settings :: 7` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### The Clip Loop switch is unavailable for unwarped audio clips.

> To have the clip play as a (potentially infinite) loop, turn on the the Clip Loop toggle. For audio clips, the Warp switch must be activated before the Loop switch is accessible, as unwarped audio clips cannot be looped.

`8. Clip View :: 8.9 Looping Clips :: 1` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### First-time imports cannot be played or edited until analysis completes.

> When a file is imported into Live for the first time, it is analyzed and cannot be played or edited until the analysis process is complete. Once analyzed, the sample will be accessible in the Sample Editor, and in most cases, synced with the Set's tempo.

`9. Audio Clips, Tempo, and Warping :: 9.2.2 Importing Samples :: 2` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Turning a pseudo-Warp Marker into a real Warp Marker can also change clip tempo if no later Warp Markers exist.

> Pseudo-Warp Markers appear when you hover over transient markers. They look like regular Warp Markers but are gray instead of yellow. Double-clicking or dragging a pseudo-marker turns it into an actual Warp Marker. If there are no Warp Markers after the newly created marker, the clip's tempo will also change. Holding the Ctrl (Win)/ Cmd (Mac) modifier while creating a Warp Marker from a pseudo-marker also creates Warp Markers at the adjacent transients. You can hold Shift and drag a pseudo-marker to move the transient to a new location in the Sample Editor.

`9. Audio Clips, Tempo, and Warping :: 9.2.3 Warp Markers :: 16` &nbsp;·&nbsp; **workflow gotcha** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Tempo automation is edited from the Main track via Mixer and Song Tempo chooser targets.

> To edit the song tempo envelope, unfold the Main track in Arrangement View, choose "Mixer" from the top envelope chooser and "Song Tempo" from the bottom one.

`25. Automation and Editing Envelopes :: 25.5.8 Editing the Tempo Automation :: 2` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Arrangement time-signature changes are represented as time signature markers inserted from the Create menu or scrub-area context menu.

> Live's time signature can be changed at any point in the Arrangement using time signature markers. To add a marker at the current insert marker position, use the Insert Time Signature Change command via the Create menu or the scrub area's context menu.

`6. Arrangement View :: 6.5 Time Signature Changes :: 1` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 3/5 &nbsp;·&nbsp; confidence: high

## See also

[[Routing & Monitoring]] · [[Automation vs Modulation]] · [[Hard Constraints]]
