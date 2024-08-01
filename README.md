# AutoStereoSpeakerAnimator
Stereo Speakers Auto-Animator is a tool that allows you to automatically generate keyframes by directly importing frames from the waveform of an audio file.

This Blender addon's purpose is to mostly aid in animating the drivers from stereo speaker systems, however, it's versatile enough to be used in varied ways, specially when applied to geometry or material nodes.

![alt text](https://markets-rails.s3.amazonaws.com/cache/acdf7a7b69fb15ba960dadf641b18712.webp)
![alt text](https://markets-rails.s3.amazonaws.com/cache/93b3c94e05c6a803fd5257702a8e3a53.jpg)

The addon is installed like any other addon. From Edit > Preferences > Add-Ons, import the downloaded file and enable it.
Upon activation of this addon, its panel can be found on the 3D Viewport's Sidebar (will hide and show using the N shortcut key), under the "Animate" tab.

1
Audio File: Insert the path for the audio file to process. The only currently supported file format is WAV with up to 3 audio channels (2.1).
Selecting a supported file type will show info about the selected file and the settings sections.

2
File Information: This box will show information about the selected file.
Audio duration should be specifically useful to calculate the animation lenght (total frames = duration * fps).

3
Channel Settings: This box will allow you to select the target object, name your properties and remap the values range used for the animation, per audio channel.
If Property Data Path is left empty, the properties will be given the names "Driver" and "Wobble", suffixed by the name of your channel. You can type up to 2 names for your properties, separated by a comma (,).
Driver, or the first named property, will be a float value responsible for animating the movement of the cone.
Wobble, or the second name after the comma, an optional Vector3 that is meant to be used to animate jittering rotation of the cone.
If only the first property name is typed, the second property will not be generated.

4
Start Frame: The frame offset for the start of the animation.

5
Keyframes Per Video Frame: How many keyframes to create per video frame.
If you are only using basic motion blur or no motion blur, 1 is enough. If, however, your motion blur steps are set higher, it might be of value to go over 1.

6
Pre-process Audio: This function is an alternative to the default keyframe extraction.
(For context, an audio clip with a sample rate of 44100 Hz will have 44100 audio frames in each second. What this script is doing is extracting only a few of those frames as animation keyframes.)
With a trade-off in speed, rather than importing the found frames as they are, this function will process a bracket of surrounding audio frames for each keyframe and do a mix of the two values fetched as the peak amplitude of the bracket, and by averaging the amplitudes of the audio frames in the bracket.
The Bias is the chosen ratio at which these two values are mixed to get your final keyframe value, 0.0 extracting only the averaged values and 1.0 extracting only the values of the amplitude peaks.

7
Animate: Start the process.
Blender will freeze or hang upon pressing this button. Depending on the selected file, processing it might take a few minutes. A good way to tell if the process is done is observing the button itself. If it's blue, it means the process is still going, while if it's back to its grey color, the process should be done.
