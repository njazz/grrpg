from reathon.nodes import Project, Track, Item, Source, Node # note new nodes Item() and Source()
from pathlib import Path
import json
import random
import math
import soundfile as sf

####
ts_type_soundtouch = 0
ts_type_elastique_pro = 589824
ts_type_rreeaa = 917504
ts_type_rearearea = 983040

##################################################

class GeneratorContext():
    def __init__(self):
        self.track_number = 0
        self.position = 0
        self.current_file_length = 0

        self.soundtouch = 0
        self.elastique_pro = 589824
        self.rreeaa = 917504
        self.rearearea = 983040

class GeneratorProject():
    def __init__(self):
        self.sources = []

        self.track_count = 24
        self.loop_items = False
        self.project_length = 30

        self.output_file_name = ""

        # tracks
        self.length = {}
        self.rate = {}
        self.spacing = {}
        self.fade_in = {}
        self.fade_out = {}

        self.gain = {}

        self.pitch_offset = {}
        self.ts_type = {}

        self.sample_offset = {}
        self.pan_automation = {}

        self.item_pitch_start = {}
        self.item_pitch_middle = {}
        self.item_pitch_end = {}

        self.item_pan_start = {}
        self.item_pan_middle = {}
        self.item_pan_end = {}

        self.item_probability = {}

        # seed for each automation value
        self.seed_global = 0

        self.seed_source = 0

        self.seed_length = 1
        self.seed_rate = 2
        self.seed_spacing = 3
        self.seed_fade_in = 4
        self.seed_fade_out = 5

        self.seed_gain = 6

        self.seed_pitch_offset = 7
        self.seed_ts_type = 8

        self.seed_sample_offset = 9
        self.seed_pan_automation = 10

        self.seed_item_pitch_start = 11
        self.seed_item_pitch_middle = 12
        self.seed_item_pitch_end = 13

        self.seed_item_pan_start = 14
        self.seed_item_pan_middle = 15
        self.seed_item_pan_end = 16

        self.seed_item_probability = 17


    def load_sources(self, p):
        self.sources = [str(x) for x in Path(p).rglob("*.wav")]

    def from_json_string(self,s: str):
        j = json.loads(s)
        for k in j:
            setattr(self, k, j[k])
        # self = GeneratorProject(**j)

    def to_json_string(self):
        return json.dumps(vars(self), indent = 4)

ctx = GeneratorContext()

##################################################

def generate_default_project():
    ret = GeneratorProject()

    ret.length = {0: "random.uniform(0.5, 1.)", 15: "random.uniform(0.5, 1.75)"}
    ret.rate = {0: "random.uniform(1, 1)", 15: "random.uniform(0.1, 1.)"}
    ret.spacing = {0: "random.uniform(0.1,1.5)", 15: "random.uniform(0.1,1.5)"}
    ret.fade_in = {0: "random.uniform(0, 0.025)", 15: ".1"}
    ret.fade_out = {0: "random.uniform(0, 0.025)", 15: ".1"}

    ret.gain = {0: "random.uniform(-30, 0.0)", 29: "-6"};

    ret.pitch_offset = {0: "0"}
    ret.ts_type = { 0: "ctx.elastique_pro" } #, 15: lambda: random.choice([ts_type_rreeaa, ts_type_rearearea]) }

    ret.sample_offset = {0: "random.uniform(0, 1)"}
    ret.pan_automation = {0: "0." , 15 : "random.uniform(-1, 1)"} # -1..1 # , 5: "float(ctx.context_track_number) / ctx.track_count * 2.0 - 1.0"

    ret.item_pitch_start = {0: "0", 15: "0", 25: "0"}
    ret.item_pitch_middle = {0: "0", 15: "-3", 25: "0"}
    ret.item_pitch_end = {0: "-3.", 15: "0", 25: "0"}

    ret.item_pan_start = {0: "1", 15: "-1", 25: "1"}
    ret.item_pan_middle = {0: "-1", 15: "1", 25: "-1"}
    ret.item_pan_end = {0: "1.", 15: "-1", 25: "1"}

    ret.item_probability = { 0: "1" } #context_track_number == 15, 15: lambda: 1, 30: lambda: abs(context_track_number/(track_count)) }

    #
    ret.sources = [str(x) for x in Path("./files").rglob("*.wav")]
    ret.output_file_name = "test-output.rpp"

    return ret

##################################################

class VolEnv(Node):
    def __init__(self, *nodes_to_add, **kwargs):
        self.name = 'VOLENV2'
        self.valid_children = Source
        super().__init__(*nodes_to_add, **kwargs)

        self.props.append(["PT","0 1 0"])

    def add_point(t, v):
        self.props.append(["PT",f"{t} {v} 0"])

# track pan env
class PanEnv(Node):
    def __init__(self, *nodes_to_add, **kwargs):
        self.name = 'PANENV2'
        self.valid_children = Source        
        super().__init__(*nodes_to_add, **kwargs)

        self.props.append(["PT","0 0.5 0"])

    def add_point(self, t, v):
        self.props.append(["PT",f"{t} {v} 0"])

#####

# item pitch
class ItemPitchEnv(Node):
    def __init__(self, *nodes_to_add, **kwargs):
        self.name = 'PITCHENV'
        self.valid_children = Source        
        super().__init__(*nodes_to_add, **kwargs)

        # this starts empty

    def add_point(self, t, v):
        self.props.append(["PT",f"{t} {v} 0"])

# item pan env
class ItemPanEnv(Node):
    def __init__(self, *nodes_to_add, **kwargs):
        self.name = 'PANENV'
        self.valid_children = Source        
        super().__init__(*nodes_to_add, **kwargs)

        self.props.append(["PT","0 0.5 0"])

    def add_point(self, t, v):
        self.props.append(["PT",f"{t} {v} 0"])

##################################################

# sources = []

def interpolate_values(time, time_lambda_dict):
    time = float(time)

    # Ensure the dictionary is not empty
    if not time_lambda_dict:
        raise ValueError("Dictionary is empty")

    if len(time_lambda_dict.keys()) == 1 :
        t1 = list(time_lambda_dict.keys())[0]
        lambda1 = lambda: eval(time_lambda_dict[t1])
        return lambda1()

    # Find the nearest two time indices
    # nearest_times = sorted(time_lambda_dict.keys(), key=lambda t: (t - time) )[:2]

    # nearest_times = sorted(time_lambda_dict.keys(), key=lambda t: abs(float(t) - time) )[:2]

    # lol
    nearest_times = []
    l = sorted(time_lambda_dict.keys())
    
    for a,b in zip(l, l[1:]):
        if int(a) <= time and time < int(b):
            nearest_times = [(a),(b)]
            break

    # print(nearest_times)

    if len(nearest_times) == 0:
        if time>0:
            nearest_times = [l[-1]]
        else:
            nearest_times = [l[0]]


    # If there's an exact match, return the lambda value at that time
    # if time in nearest_times:
    #     return eval(time_lambda_dict[time])

    # only one:
    # print(time, nearest_times)

    if len(nearest_times) == 1 :
        t1 = nearest_times[0]
        lambda1 = lambda: eval(time_lambda_dict[t1])
        return lambda1()


    # Linear interpolation
    t1, t2 = nearest_times
    lambda1, lambda2 = lambda: eval(time_lambda_dict[t1]), lambda: eval(time_lambda_dict[t2])

    # Calculate interpolation weight
    weight = (time - float(t1)) / (float(t2) - float(t1))
    if weight < 0: 
        weight = 0
    if weight > 1:
        weight = 1

    # Mix values linearly
    result = (1 - weight) * lambda1() + weight * lambda2()

    return result

def step_values(time, time_lambda_dict):
    # Ensure the dictionary is not empty
    if not time_lambda_dict:
        raise ValueError("Dictionary is empty")

    # Find the nearest two time indices
    nearest_times = sorted(time_lambda_dict.keys(), key=lambda t: abs(int(t) - time))[:2]

    # If there's an exact match, return the lambda value at that time
    if time in nearest_times:
        return eval(time_lambda_dict[time])

    # only one:


    t1 = nearest_times[0]
    lambda1 = lambda: eval(time_lambda_dict[t1])
    return lambda1()


###############################################################################################

def generate_project(p: GeneratorProject):
    sources = [
        Source(file=f'{str(x)}')
        for x in p.sources
    ]

    if not len(sources):
        print("no sources available")
        return

    # file lengths
    source_length = {}
    for src in p.sources:
        f = sf.SoundFile(src)
        source_length[src] = f.frames / f.samplerate
    f = None

    # pan distribution
    # tracks = [Track(volpan = f"1 {x/float(8/2)-1} -1 -1 1") for x in range(track_count)]
    # center

    tracks = [Track(volpan = f"1 0 -1 -1 1") for x in range(p.track_count)]

    # ctx = GeneratorContext()

    grain_seed_index = 0

    for track in tracks:
        
        pos = 0.0 # set our initial position to 0
        pan_envelope = PanEnv()

        while pos < p.project_length: # 1000 grains
            ctx.position = pos

            random.seed(grain_seed_index * 100000 + p.seed_global + p.seed_source + 10000 * ctx.track_number)
            grain_file = random.choice(p.sources)
            grain = Source(file=grain_file)#random.choice(sources) # random file from our sources
            grain_seed_index += 1

            ctx.current_file_length = source_length[grain_file]

            random.seed(p.seed_global + p.seed_item_probability + 10000 * ctx.track_number)
            d = random.uniform(0, 1)
            item_probability = interpolate_values(pos, p.item_probability)

            random.seed(p.seed_global + p.seed_length + 10000 * ctx.track_number)
            length = interpolate_values(pos, p.length) #random.uniform(0.01, 0.05) # random length of the item

            random.seed(p.seed_global + p.seed_rate + 10000 * ctx.track_number)
            rate = interpolate_values(pos, p.rate)#random.uniform(0.1, 1)

            random.seed(p.seed_global + p.seed_spacing + 10000 * ctx.track_number)
            spacing = interpolate_values(pos, p.spacing)#random.uniform(0,0.5)

            random.seed(p.seed_global + p.seed_fade_in + 10000 * ctx.track_number)
            fade_in = interpolate_values(pos, p.fade_in)#random.uniform(0, 0.025)

            random.seed(p.seed_global + p.seed_fade_out + 10000 * ctx.track_number)
            fade_out = interpolate_values(pos, p.fade_out)#random.uniform(0, 0.025)

            random.seed(p.seed_global + p.seed_gain + 10000 * ctx.track_number)
            gain = interpolate_values(pos, p.gain)
            def db_to_a(dB):
                return 10 ** (dB / 20)
            gain = db_to_a(gain)


            random.seed(p.seed_global + p.seed_pitch_offset + 10000 * ctx.track_number)
            pitch_offset = interpolate_values(pos, p.pitch_offset)#0

            random.seed(p.seed_global + p.seed_sample_offset + 10000 * ctx.track_number)
            sample_offset = interpolate_values(pos, p.sample_offset)#random.uniform(0, 1)

            random.seed(p.seed_global + p.seed_pan_automation + 10000 * ctx.track_number)
            pan_automation = interpolate_values(pos, p.pan_automation)

            random.seed(p.seed_global + p.seed_ts_type + 10000 * ctx.track_number)
            ts_type = step_values(pos, p.ts_type)

            new_item = Item(
                    grain, # Item()'s have a child Source() node, which is randomly selected above
                    position = pos, # and we set the position

                    length = length / rate , # and we set the length
                    playrate = f"{rate} 1 {pitch_offset} {ts_type} 0 0.0025",
                    fadein = f"0 {fade_in} 0 0 0 0",
                    fadeout = f"0 {fade_out} 0 0 0 0",
                    soffs = sample_offset,

                    loop = 1 if p.loop_items else 0,

                    volpan = f"1 0 {gain} -1"
                )

            pitch_envelope = ItemPitchEnv()

            random.seed(p.seed_global + p.seed_item_pitch_start + 10000 * ctx.track_number)
            pitch_start_point = interpolate_values(pos, p.item_pitch_start)

            random.seed(p.seed_global + p.seed_item_pitch_middle + 10000 * ctx.track_number)
            pitch_middle_point = interpolate_values(pos, p.item_pitch_middle)        

            random.seed(p.seed_global + p.seed_item_pitch_end + 10000 * ctx.track_number)
            pitch_end_point = interpolate_values(pos, p.item_pitch_end)
            
            pitch_envelope.add_point(0, pitch_start_point)
            pitch_envelope.add_point(length/2, pitch_middle_point)
            pitch_envelope.add_point(length, pitch_end_point)

            new_item.nodes.append(pitch_envelope)
            pitch_envelope.parents.append(new_item)

            #
            pan_envelope = ItemPanEnv()

            random.seed(p.seed_global + p.seed_item_pan_start + 10000 * ctx.track_number)
            pan_start_point = interpolate_values(pos, p.item_pan_start)

            random.seed(p.seed_global + p.seed_item_pitch_middle + 10000 * ctx.track_number)
            pan_middle_point = interpolate_values(pos, p.item_pan_middle)

            random.seed(p.seed_global + p.seed_item_pitch_end + 10000 * ctx.track_number)
            pan_end_point = interpolate_values(pos, p.item_pan_end)
            
            pan_envelope.add_point(0, pan_start_point)
            pan_envelope.add_point(length/2, pan_middle_point)
            pan_envelope.add_point(length, pan_end_point)

            new_item.nodes.append(pan_envelope)
            pan_envelope.parents.append(new_item)

            if d < item_probability:            
                track.add(
                    new_item
                )

            pan_envelope.add_point(pos, pan_automation)
            pos += float(length) / float(rate) + spacing # increment the position by the length to create contiguous blocks
        
        # disabled when available in items
        # track.nodes.append(pan_envelope)
        # pan_envelope.parents.append(track)

        ctx.track_number += 1

    project = Project(*tracks) # create the project with our composed track

    project.props.append(["ZOOM","30 0 0"])
    project.props.append(["VZOOMEX","0 0"])

    project.write(p.output_file_name) # write it out

generate_project(generate_default_project())
