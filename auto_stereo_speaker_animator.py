from os import path
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup,
)
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
import bpy
bl_info = {
    "name": "Stereo Speakers Auto-Animator",
    "author": "Sebastião Silva <info@sebastiaosilva.xyz>",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Animate Tab > Speakers Animator",
    "description": "Animate the drivers of a speaker set directly from the audio file.",
    "doc_url": "http://sebastiaosilva.xyz/projects/blender-tools/stereo-speakers-auto-animator.html",
    "category": "Animation",
    "support": "COMMUNITY",
}


class SPEAKERSANIM_OT_RunAction(Operator):
    bl_idname = "object.animate_speakers"
    bl_label = "Animate from Audio File"
    bl_description = "Create an animation from the selected audio file."
    bl_options = {'REGISTER', 'UNDO'}

    fpath: StringProperty()
    nchannels: IntProperty()
    samplerate: IntProperty()
    duration: IntProperty()
    framecount: IntProperty()

    def execute(self, context):
        scene = context.scene
        signal = None
        if self.samplerate // (scene.render.fps * scene.speakers_animator.keyframes) >= 1:
            signal = self.get_signal(self.fpath)
        if signal is not None:
            step = self.get_stepping(context)
            if self.nchannels < 4:
                self.process_signal(
                    scene,
                    signal,
                    step,
                    scene.speakers_animator.l_obj,
                    scene.speakers_animator.l_prop,
                    0,
                    "L",
                )
            if self.nchannels > 1 and self.nchannels < 4:
                self.process_signal(
                    scene,
                    signal,
                    step,
                    scene.speakers_animator.r_obj,
                    scene.speakers_animator.r_prop,
                    1,
                    "R",
                )
            if self.nchannels > 2 and self.nchannels < 4:
                self.process_signal(
                    scene,
                    signal,
                    step,
                    scene.speakers_animator.r_obj,
                    scene.speakers_animator.r_prop,
                    2,
                    "S",
                )
            return {'FINISHED'}
        else:
            return {'CANCELED'}

    def process_signal(self, scene, signal, step, object, property, channel, suffix):
        if object and isinstance(object, str):
            c_signal = self.get_channel_signal(signal, channel, self.nchannels)
            if scene.speakers_animator.preprocess == True:
                c_signal = self.get_processed_signal(scene, c_signal)
            else:
                c_signal = self.int2float(c_signal[0::step])
            target_props = None
            target_obj = scene.objects[object]
            if not property or not isinstance(property, str):
                target_props = ("Driver_" + suffix, "Wobble_" + suffix)
            else:
                target_props = property.split(",")
            self.animate_float_property(
                target_obj,
                target_props[0],
                c_signal,
                scene.speakers_animator.keyframes,
                scene.speakers_animator.offset,
            )
            if len(target_props) > 1:
                self.animate_float_array_property(
                    target_obj,
                    target_props[1].strip(),
                    c_signal[0::scene.speakers_animator.keyframes],
                    scene.speakers_animator.offset,
                )

    def get_signal(self, fpath):
        if path.isfile(fpath) and path.splitext(fpath)[1] == ".wav":
            import wave
            import numpy as np
            obj = wave.open(fpath, "rb")
            signal = np.frombuffer(
                obj.readframes(self.framecount), dtype=np.int16)
            obj.close()
            return signal
        else:
            return None

    def get_stepping(self, context):
        fps = context.scene.render.fps
        samplerate = self.samplerate
        animation_keyframes_per_video_frame = context.scene.speakers_animator.keyframes
        audio_keyframes_per_video_frame = samplerate // fps
        step = audio_keyframes_per_video_frame // animation_keyframes_per_video_frame
        return step

    def int2float(self, in_array):
        out_array = []
        for in_value in in_array:
            out_value = in_value / 32767
            out_array.append(out_value)
        return out_array

    def apply_range(self, value, min, max):
        # This does not need to be calculated every frame if it's moved outside of function.
        range = max - min
        scaler = (value + 1.0) * 0.5
        val_to_add = range * scaler
        output = val_to_add + min
        output *= 0.01
        return output

    def get_channel_signal(self, signal, channel, total_channels):
        return signal[channel::total_channels]

    def animate_float_property(self, object, property, signal, keyframes, offset):
        # Remember to create an action named after the audio file and set it.
        object[property]: FloatProperty(name=property) = 0.0
        property = "[\"" + property + "\"]"
        keyframe_span = 1.0 / keyframes
        t = 0.0 + offset
        for keyframe in signal:
            setattr(object, property, keyframe)
            object.keyframe_insert(property, frame=t)
            t += keyframe_span

    def animate_float_array_property(self, object, property, signal, offset):
        object[property]: FloatVectorProperty(name=property) = [0.0, 0.0, 0.0]
        property = "[\"" + property + "\"]"
        # keyframe_span is set to 1
        t = 0.0 + offset
        # Generate randomized vector
        from random import uniform
        for keyframe in signal:
            randomized_vec = (
                uniform(-1.0, 1.0) * keyframe,
                uniform(-1.0, 1.0) * keyframe,
                uniform(-1.0, 1.0) * keyframe,
            )
            setattr(object, property, randomized_vec)
            object.keyframe_insert(property, frame=t)
            t += 1.0

    def get_signal_peaks(self, scene, signal):
        output = []
        fps = scene.speakers_animator.keyframes * scene.render.fps
        bracket = self.samplerate // fps
        start_index = 0
        for _ in range(len(signal) // bracket):
            out_value = 0
            for in_value in signal[start_index:start_index + bracket]:
                if abs(in_value) > abs(out_value):
                    out_value = in_value
            out_value /= 32767
            output.append(out_value)
            start_index += bracket
        return output

    def get_averaged_signal(self, scene, signal):
        output = []
        fps = scene.speakers_animator.keyframes * scene.render.fps
        bracket = self.samplerate // fps
        start_index = 0
        for _ in range(len(signal) // bracket):
            average = 0
            charge = 0
            for in_value in signal[start_index:start_index + bracket]:
                charge += in_value
                average += abs(in_value)
            average /= bracket
            average /= 32767
            if charge < 0:
                average *= -1.0
            output.append(average)
            start_index += bracket
        return output

    def get_processed_signal(self, scene, signal):
        bias = scene.speakers_animator.bias
        if bias == 0.0:
            return self.get_averaged_signal(scene, signal)
        elif bias == 1.0:
            return self.get_signal_peaks(scene, signal)
        else:
            average_mult = 1.0 - bias
            peak_mult = bias
            output = []
            fps = scene.speakers_animator.keyframes * scene.render.fps
            bracket = self.samplerate // fps
            start_index = 0
            for _ in range(len(signal) // bracket):
                peak = 0
                average = 0
                charge = 0
                for in_value in signal[start_index:start_index + bracket]:
                    charge += in_value
                    average += abs(in_value)
                    if abs(in_value) > abs(peak):
                        peak = in_value
                average /= bracket
                if charge < 0:
                    average *= -1.0
                average *= average_mult
                peak *= peak_mult
                out_value = (average + peak) / 32767
                output.append(out_value)
                start_index += bracket
            return output


class SPEAKERSANIM_Props(PropertyGroup):

    f_path: StringProperty(
        name="Audio File",
        subtype="FILE_PATH",
        default="//",
        description="The audio file to process. The supported file types are: WAV",
    )
    f_info: StringProperty(
    )
    l_obj: StringProperty(
        name="Object",
        description="The object to be animated",
    )
    l_prop: StringProperty(
        name="Property Data Path",
        description="Path to the property. If left blank, a custom object property will be created",
    )
    l_range_min: FloatProperty(
        name="Min",
        min=-9999, max=9999, default=-1,
        precision=1,
        description="Floor value of the amplitude"
    )
    l_range_max: FloatProperty(
        name="Max",
        min=-9999, max=9999, default=1,
        precision=1,
        description="Floor value of the amplitude"
    )
    r_obj: StringProperty(
        name="Object",
        description="The object to be animated",
    )
    r_prop: StringProperty(
        name="Property Data Path",
        description="Path to the property. If left blank, a custom object property will be created",
    )
    r_range_min: FloatProperty(
        name="Min",
        min=-9999, max=9999, default=-1,
        precision=1,
        description="Floor value of the amplitude"
    )
    r_range_max: FloatProperty(
        name="Max",
        min=-9999, max=9999, default=1,
        precision=1,
        description="Floor value of the amplitude"
    )
    s_obj: StringProperty(
        name="Object",
        description="The object to be animated",
    )
    s_prop: StringProperty(
        name="Property Data Path",
        description="Path to the property. If left blank, a custom object property will be created",
    )
    s_range_min: FloatProperty(
        name="Min",
        min=-9999, max=9999, default=-1,
        precision=1,
        description="Floor value of the amplitude"
    )
    s_range_max: FloatProperty(
        name="Max",
        min=-9999, max=9999, default=1,
        precision=1,
        description="Floor value of the amplitude"
    )
    offset: IntProperty(
        name="Start Frame:",
        default=1,
        description="The frame at which the animation will start"
    )
    keyframes: IntProperty(
        name="Keyframes per video frame:",
        min=1, max=48000, default=2,
        description="Floor value of the amplitude"
    )
    preprocess: BoolProperty(
        name="Pre-process audio?",
        description="Process the audio in order to bias the keyframes to either averaged or peak values",
        default=False
    )
    bias: FloatProperty(
        name="Averaged-Peak Bias",
        min=0.0, max=1.0, default=0.5,
        precision=2,
        description="Averaged - Peak mixer for the keyframes' values"
    )


class SPEAKERSANIM_PT_ui(Panel):
    bl_label = "Speakers Animator"
    bl_idname = "SPEAKERS_ANIMATOR_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animate"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    file_path = None
    file_type = None
    file_nchannels = None
    file_samplerate = None
    file_duration = None
    file_framecount = None

    def draw(self, context):
        layout = self.layout
        #layout.use_property_split = True
        layout.use_property_decorate = False
        scene = context.scene

        col = layout.column(align=True)
        col.prop(scene.speakers_animator, "f_path")
        self.update_panel(scene, col, layout)

    def update_panel(self, scene, col, layout):
        validated = self.validate_file(scene).split("\n")
        if validated[0] != "This file type is not supported." and validated[0] != "Select a .wav file to process.":
            box = col.box()
            sub = box.column(align=True)
            for infoline in validated:
                row = sub.row(align=False)
                row.alignment = 'CENTER'
                row.label(text=infoline)
            box = layout.box()
            col = box.column(align=True)
            if self.file_nchannels == 1:
                col.label(text="Speaker Driver:")
            else:
                col.label(text="Left Speaker Driver:")
            col.prop_search(scene.speakers_animator, "l_obj",
                            bpy.data, "objects", text="Object")
            # Colorize these props according the the validity of the inputs (normal, red)
            col.prop(scene.speakers_animator, "l_prop", icon="RNA")
            row = col.row(align=True, heading="Range:")
            row.prop(scene.speakers_animator, "l_range_min")
            row.prop(scene.speakers_animator, "l_range_max")
            if self.file_nchannels > 1:
                box = layout.box()
                col = box.column(align=True)
                col.label(text="Right Speaker Driver:")
                col.prop_search(scene.speakers_animator, "r_obj",
                                bpy.data, "objects", text="Object")
                # Colorize these props according the the validity of the inputs (normal, red)
                col.prop(scene.speakers_animator, "r_prop", icon="RNA")
                row = col.row(align=True, heading="Range:")
                row.prop(scene.speakers_animator, "r_range_min")
                row.prop(scene.speakers_animator, "r_range_max")
            if self.file_nchannels > 2:
                box = layout.box()
                col = box.column(align=True)
                col.label(text="Subwoofer Driver:")
                col.prop_search(scene.speakers_animator, "s_obj",
                                bpy.data, "objects", text="Object")
                # Colorize these props according the the validity of the inputs (normal, red)
                col.prop(scene.speakers_animator, "s_prop", icon="RNA")
                row = col.row(align=True, heading="Range:")
                row.prop(scene.speakers_animator, "s_range_min")
                row.prop(scene.speakers_animator, "s_range_max")
            col = layout.column(align=True)
            col.prop(scene.speakers_animator, "offset")
            col.prop(scene.speakers_animator, "keyframes")
            col.prop(scene.speakers_animator, "preprocess", toggle=True)
            if scene.speakers_animator.preprocess == True:
                col.prop(scene.speakers_animator, "bias", slider=True)

            # Only spawn operator if >1 valid channel in input and both channels don't target the same property
            prop = layout.operator(
                "object.animate_speakers", text="Animate", icon="GRAPH")
            prop.nchannels = self.file_nchannels
            prop.samplerate = self.file_samplerate
            prop.duration = self.file_duration
            prop.framecount = self.file_framecount
            prop.fpath = self.file_path
        else:
            col.label(text=validated[0])

    def validate_file(self, scene):
        abspath = bpy.path.abspath(scene.speakers_animator.f_path)
        if path.isfile(abspath):
            self.file_path = abspath
            if path.splitext(abspath)[1] == ".wav":
                self.process_wave_file()
                string = "File Type: WAV\n" + \
                    "Number of Channels: " + str(self.file_nchannels) + "\n" + \
                    "Sample Frequency: " + str(self.file_samplerate) + "Hz\n" + \
                    "Audio Duration: " + str(self.file_duration) + " seconds\n" + \
                    "Number of Audio Frames: " + str(self.file_framecount)
                return string
            else:
                return "This file type is not supported."
        else:
            return "Select a .wav file to process."

    def process_wave_file(self):
        import wave
        import numpy as np
        file_obj = wave.open(self.file_path, "rb")
        self.file_nchannels = file_obj.getnchannels()
        self.file_samplerate = file_obj.getframerate()
        self.file_framecount = file_obj.getnframes()
        self.file_duration = self.file_framecount // self.file_samplerate
        file_obj.close()


classes = (
    SPEAKERSANIM_OT_RunAction,
    SPEAKERSANIM_PT_ui,
    SPEAKERSANIM_Props
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.speakers_animator = PointerProperty(
        type=SPEAKERSANIM_Props)
    #print("Registered Speakers Animator")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.speakers_animator
    #print("Unregistered Speakers Animator")


if __name__ == "__main__":
    register()
