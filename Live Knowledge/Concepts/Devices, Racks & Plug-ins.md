# Devices, Racks & Plug-ins

*The densest chapters in the recon (Instruments & Effects + Racks).* Signal in a
device chain flows **left to right**; in a MIDI track, devices **before** an
instrument see MIDI and **after** it see audio. Plug-in parameters must be
**published** (Configure Mode) to be addressable in Live's panel — relevant to
automating plug-in params via `.als`. Racks add Macros, Zones, and Drum-Rack
chains (Receive/Play/Choke, up to six return chains, and a 128-chain ceiling
that gates Slice-to-MIDI).

Read this for device-chain ordering, plug-in parameter exposure, and Rack
structure.

## Findings

### In a MIDI track, devices before an instrument receive MIDI while devices after it receive audio.

> If you drop an instrument into a MIDI tracks device chain, be aware that signals following (to the right of) the instrument are audio signals, available only to audio effects. Signals preceding (to the left of) the instrument are MIDI signals, available only to MIDI effects. This means that it's possible for a MIDI tracks device chain to hold all three types of devices: first MIDI effects, then an instrument, and finally audio effects.

`23. Working with Instruments and Effects :: 23.2 Using Devices :: 36` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Signals in a device chain flow from left to right.

> To add another device to the track, simply drag it there or double-click its name to append it to the device chain. Signals in a device chain always travel from left to right.

`23. Working with Instruments and Effects :: 23.2 Using Devices :: 34` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### VST/AU instruments are MIDI-track devices, while plug-in audio effects belong on audio tracks or after instruments.

> Working with VST and Audio Units plug-ins is very much like working with Live devices. VST and AU instruments can only be placed in Live MIDI tracks and, like Live instruments, they will receive MIDI and output audio signals. Plug-in audio effects can only be placed in audio tracks or following instruments. Please see the previous section, Using the Live Devices, for details.

`23. Working with Instruments and Effects :: 23.3 Using Plug-Ins :: 4` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Configure Mode defines which plug-in parameters appear in Live's device panel.

> • Enter Configure Mode by pressing the "Configure" button in the device's header.

`23. Working with Instruments and Effects :: 23.3.1 Plug-Ins in the Device View :: 17` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Plug-ins that do not publish parameters prevent those parameters from being added to Live's panel.

> While in Configure Mode, parameters in Live's panel can be reordered or moved by dragging and dropping them to new locations. Parameters can be deleted by pressing the Delete key. If you try to delete a parameter that has existing automation data, clip envelopes, or MIDI, key or Macro mappings, Live will warn you before proceeding.

`23. Working with Instruments and Effects :: 23.3.1 Plug-Ins in the Device View :: 19` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Configured plug-in parameter sets are per instance, saved with the Set, and can be preserved via Racks or default presets.

> Certain plug-ins do not have their own windows, and instead only show their parameters in Live's panel. For these plug-ins, it is not possible to delete parameters when in Configure Mode (although they can still be moved and reordered).

`23. Working with Instruments and Effects :: 23.3.1 Plug-Ins in the Device View :: 21` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 5/5 &nbsp;·&nbsp; confidence: high

### Floating-window parameter changes create temporary chooser entries until automation, envelope, or X-Y selection makes them permanent.

> • Adjusting a parameter in the plug-in's floating window creates temporary entries for that parameter in the clip envelope and automation choosers, as well as the choosers in the panel's X-Y field. These entries are removed when you adjust another parameter. To make the entry permanent (thus adding it to Live's panel), either edit the parameter's automation or clip envelope, select another parameter in the automation or clip envelope choosers, or select the temporary parameter in one of the X-Y field's choosers.

`23. Working with Instruments and Effects :: 23.3.1 Plug-Ins in the Device View :: 23` &nbsp;·&nbsp; **workflow gotcha** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Live needs restart or Plug-Ins Settings rescan to detect plug-ins installed while Live is running.

> If you install/uninstall a plug-in while the program is running, Live will not detect your changes or implement them in the browser until the next time you start the program. Use the Rescan button in the Plug-Ins Settings to rescan your plug-ins while Live is running, so that newly installed devices become immediately available in the browser.

`23. Working with Instruments and Effects :: 23.3 Using Plug-Ins :: 28` &nbsp;·&nbsp; **workflow gotcha** &nbsp;·&nbsp; SC-relevance 3/5 &nbsp;·&nbsp; confidence: high

### Racks package effects, plug-ins, instruments, and control relationships inside a track device chain.

> A Rack is a flexible tool for working with effects, plug-ins and instruments in a track's device chain. Racks can be used to build complex signal processors, dynamic performance instruments, stacked synthesizers and more. Yet they also streamline your device chain by bringing together your most essential controls. While Racks excel at handling multiple devices, they can extend the abilities of even a single device by defining new control relationships between its parameters.

`24. Instrument, Drum and Effect Racks :: 24. Instrument, Drum and Effect Racks :: 2` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Macro Controls can address any number of parameters from devices inside a Rack.

> The Macro Controls are a bank of knobs, each capable of addressing any number of parameters from any devices in a Rack. How you use them is up to you — whether it be for convenience, by making an important device parameter more accessible; for defining exotic, multi-parameter morphs of rhythm and timbre; or for constructing a mega-synth, and hiding it away behind a single customized interface. See Using the Macro Controls for a detailed explanation of how to do this.

`24. Instrument, Drum and Effect Racks :: 24.1.2 Macro Controls :: 3` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Rack zones are Key, Velocity, and Chain Select filters at each chain input.

> Zones are sets of data filters that reside at the input of every chain in an Instrument or Effect Rack. Together, they determine the range of values that can pass through to the device chain. By default, zones behave transparently, never requiring your attention. They can be reconfigured, however, to form sophisticated control setups. The three types of zones, whose editors are toggled with the buttons above the Chain List, are Key, Velocity, and Chain Select. The adjacent Hide button whisks them out of sight.

`24. Instrument, Drum and Effect Racks :: 24.5 Zones :: 1` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Drum Rack chains use Receive, Play, and Choke controls, with All Notes disabling Play and Choke.

> 2. Input/Output Section - The Receive chooser sets the incoming MIDI note to which the drum chain will respond. The list shows note names, MIDI note numbers and standard GM drum equivalents. The Play slider sets the outgoing MIDI note that will be sent to the devices in the chain, lhe Choke chooser allows you to set a chain to one of sixteen choke groups. Any chains that are in the same choke group will silence the others when triggered. This is useful for choking open hihats by triggering closed ones, for example. If "All Notes" is selected in the Receive chooser, the Play and Choke choosers are disabled — in this case, the chain simply passes the note that it receives to its devices, lhe small Preview button to the left of these choosers fires a note into the chain, making it easy to check your mappings away from a MIDI controller.

`24. Instrument, Drum and Effect Racks :: 24.6 Drum Racks :: 4` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Drum Rack send controls do not appear until return chains exist.

> 3. Mixer Section - In addition to the mixer and Hot-Swap controls found in other Rack types, Drum Racks also have send sliders. These sliders allow you to set the amount of post-fader signal sent from each drum chain to any of the available return chains. Note that send controls are not available until return chains have been created.

`24. Instrument, Drum and Effect Racks :: 24.6 Drum Racks :: 5` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 3/5 &nbsp;·&nbsp; confidence: high

### A Drum Rack can have up to six return chains of audio effects.

> 4. Return Chains - A Drum Rack's return chains appear in a separate section at the bottom of the chain list. Up to six chains of audio effects can be added here, which are fed by send sliders in each of the drum chains above.

`24. Instrument, Drum and Effect Racks :: 24.6 Drum Racks :: 6` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 3/5 &nbsp;·&nbsp; confidence: high

### Drum Rack return chains can route either to the Rack's main output or directly to Set return tracks.

> The Audio To chooser in the mixer for return chains allows you to route a return chain's output to either the main output of the Rack or directly to the return tracks of the Set.

`24. Instrument, Drum and Effect Racks :: 24.6 Drum Racks :: 7` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Slice to New MIDI Track cannot proceed if the slice choice would create more than 128 Rack chains.

> When you select Slice to New MIDI track, you'll be presented with a dialog box. This offers a list of slicing divisions, as well as a chooser to select the Slicing Preset, The top chooser allows you to slice at a variety of beat resolutions or according to the clip's transients or Warp Markers. Since a Rack can contain a maximum of 128 chains, Live won't let you proceed if your choice would result in more than 128 slices. You can fix this by either setting a lower slice resolution or by selecting a smaller region of the clip to slice.

`13. Converting Audio to MIDI :: 13.1 Slice to New MIDI Track :: 3` &nbsp;·&nbsp; **hard constraint** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

### Dragging a sample to a MIDI track's Device View creates a Simpler loaded with that sample.

> You can also drag devices into tracks or drop areas in the Session and Arrangement Views, or into the Device View. Dragging a sample to the Device View of a MIDI track creates a Simpler instrument with this sample loaded.

`23. Working with Instruments and Effects :: 23.2 Using Devices :: 30` &nbsp;·&nbsp; **schema element** &nbsp;·&nbsp; SC-relevance 4/5 &nbsp;·&nbsp; confidence: high

## See also

[[Track Types & Clip Hosting]] · [[Routing & Monitoring]] · [[Automation vs Modulation]] · [[Hard Constraints]]
