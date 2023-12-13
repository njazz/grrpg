import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

from . import core
from .core import ctx

import math
import os
import random
import math

####################################
# state / controller

class ViewState():
    def __init__(self):
        self.selected = "length"
        self.project = core.generate_default_project()

    # file dialogs
    # audio folder

    def file_selector_audio_show(self):
        dpg.show_item("file_selector_audio")
        dpg.hide_item("main_window")

    def file_selector_audio_hide(self):
        dpg.hide_item("file_selector_audio")
        dpg.show_item("main_window")

    def file_selector_audio_select(self, data):
        # print(data)

        self.project.load_sources(data["current_path"])
        dpg.set_value("path_audio", data["current_path"])

        dpg.hide_item("file_selector_audio")
        dpg.show_item("main_window")

    # output project

    def file_selector_reaper_project_show(self):
        dpg.show_item("file_selector_reaper_project")
        dpg.hide_item("main_window")

    def file_selector_reaper_project_hide(self):
        dpg.hide_item("file_selector_reaper_project")
        dpg.show_item("main_window")

    def file_selector_reaper_project_select(self, data):
        # print(data)

        self.project.output_file_name = (data["file_path_name"])
        dpg.set_value("reaper_project_name", data["file_path_name"])

        dpg.hide_item("file_selector_reaper_project")
        dpg.show_item("main_window")

        # self.update_project_view()

    # project file open

    def file_selector_open_project_show(self):
        dpg.show_item("file_selector_open_project")
        dpg.hide_item("main_window")

    def file_selector_open_project_hide(self):
        dpg.hide_item("file_selector_open_project")
        dpg.show_item("main_window")

    def file_selector_open_project_select(self, data):
        # print(data)

        # read file
        try:
            f = open(data["file_path_name"])
            s = f.read()
            f.close()
            self.project.from_json_string(s)
        except Exception:
            pass

        # self.project.output_file_name = (data["current_file"])

        dpg.hide_item("file_selector_open_project")
        dpg.show_item("main_window")

    # project file save

    def file_selector_save_project_show(self):
        dpg.show_item("file_selector_save_project")
        dpg.hide_item("main_window")

    def file_selector_save_project_hide(self):
        dpg.hide_item("file_selector_save_project")
        dpg.show_item("main_window")

    def file_selector_save_project_select(self, data):
        # print(data)

        # write file
        f = open(data["file_path_name"],"w")
        f.write(self.project.to_json_string())
        f.close()

        # self.project.output_file_name = (data["current_file"])
        # print(self.project.to_json_string())

        dpg.hide_item("file_selector_save_project")
        dpg.show_item("main_window")

    # project setters

    def set_track_count(self, x):
        self.project.track_count = x

    def set_loop_items(self, x):
        self.project.loop_items = x

    def set_project_length(self, x):
        self.project.project_length = x

        self.update_selected()
    
    # view_state setters

    def update_project_view(self):
        dpg.set_value("track_count", view_state.project.track_count)
        dpg.set_value("loop_items", view_state.project.loop_items)
        dpg.set_value("project_length", view_state.project.project_length)

    def update_selected(self):
        self.set_selected(self.selected)

    def set_selected(self, x):
        self.selected = x

        datax = [float(x) / 512.0 * self.project.project_length for x in range(512)]
        random.seed(getattr(view_state.project, "seed_" + view_state.selected))
        datay = [core.interpolate_values(x, getattr(view_state.project, view_state.selected)) for x in datax]
            
        min_y = min(datay)
        max_y = max(datay)
        
        dpg.set_value("plot_data", [datax,datay])

        dpg.set_axis_limits("x_axis", 0, self.project.project_length)
        dpg.set_axis_limits("y_axis", min_y - 0.01, max_y + 0.01)

        #
        dpg.delete_item("element_list", children_only = True)

        # with dpg.group(id = "element_list"):
        d = getattr(view_state.project, view_state.selected)

        idx = 0
        dpg.add_text("", tag=f"error_text", parent = "element_list")

        for k in d:            
            with dpg.group(horizontal = True, parent = "element_list"):
                # dpg.add_text(str(k))
                
                def gen_lambda_time(idx_,k_):
                    def _l(sender, data): 
                        self.set_time_for(view_state.selected, idx_, k_, data) #dpg.get_value(f"time_value_{idx}"))
                    return _l

                def gen_lambda_set_new_code(idx_):
                    def _l(sender, data):
                        #print(f"new_code_value_{idx_}")
                        dpg.set_value(f"new_code_value_{idx_}", data)
                    return _l

                def gen_lambda_code(idx_,k_):
                    def _l(sender): 
                        self.set_code_for(view_state.selected,  idx_, k_, dpg.get_value(f"new_code_value_{idx_}")) 
                    return _l

                def gen_lambda_add():
                    def _l(sender):
                        d = getattr(view_state.project, view_state.selected)
                        d[list(d.keys())[-1] + 1] = "0.0"
                        setattr(view_state.project, view_state.selected, d)
                        self.update_selected()

                    return _l

                def gen_lambda_delete(idx_, k_):
                    def _l(sender):
                        d = getattr(view_state.project, view_state.selected)
                        d.pop(k_, None)
                        setattr(view_state.project, view_state.selected, d)
                        self.update_selected()
                    return _l


               
                if (k!=0):
                    dpg.add_text("time:")
                    dpg.add_input_int(width=100, 
                        default_value = int(k), 
                        tag = f"time_value_{idx}", 
                        callback = gen_lambda_time(idx,k)
                        )
                else:
                    dpg.add_text("initial value")

                dpg.add_text("code:")

                dpg.add_input_text(default_value=d[k],
                    tag = f"code_value_{idx}",
                    callback = gen_lambda_set_new_code(idx), #lambda sender, data, idx_ = idx: dpg.set_value(f"new_code_value_{idx_}",data),#gen_lambda_code(idx,k)
                    width = 400
                    )

                dpg.add_button(label="apply",
                    callback = gen_lambda_code(idx, k) #, dpg.get_value(f"new_code_value_{idx}"))#f"code_value_{idx}"))
                    , width = 90
                    )

                if (k!=0):
                    dpg.add_button(label="delete", width = 90, callback = gen_lambda_delete(idx, k))

            idx += 1
        dpg.add_button(label="add", parent = "element_list", callback = gen_lambda_add())

    def set_time_for(self, element_name: str, index: int, time: int, value: int):
        if value == time:
            return

        d = getattr(view_state.project, view_state.selected)

        # print(element_name, index, time, value)
        # print(f"error_text_{index}")

        # exists as other key:
        if value in d:
            dpg.set_value(f"error_text","time value is already used")
            return
        else:
            dpg.set_value(f"error_text","")

        code = d[time]
        d.pop(time, None)
        d[value] = code

        setattr(view_state.project, view_state.selected, d)

        self.update_selected()
        

    def set_code_for(self, element_name: str, index: int, time: int, code: str):
        print(index, time, code)

        # try eval
        try:
            eval(code)
            dpg.set_value(f"error_text","")
        except Exception as e:
            dpg.set_value(f"error_text",f"code error: {str(e)}")
            return


        d = getattr(view_state.project, view_state.selected)
        d[time] = code

        setattr(view_state.project, view_state.selected, d)

        # print(d)

        self.update_selected()

    # more actions

    def btn_generate_and_open(self):
        core.generate_project(self.project)
        os.system("open /Applications/REAPER.app "+self.project.output_file_name)

    def btn_generate(self):
        core.generate_project(self.project)

    current_project_number = 1
    def btn_generate_next_and_open(self):
        t = self.project.output_file_name
        r = t.lower().replace(".rpp", f".{ViewState.current_project_number}.rpp")
        self.project.output_file_name = r
        core.generate_project(self.project)
        self.project.output_file_name = t
        ViewState.current_project_number += 1
        os.system("open /Applications/REAPER.app " + r)

    def btn_project_reset(self):
        self.project = core.generate_default_project()

        self.update_project_view()
        self.set_selected("length")

view_state = ViewState()

# with dpg.file_dialog(directory_selector=False, show=False, callback=callback, id="file_dialog_id", width=700 ,height=400):
#     dpg.add_file_extension(".*")
#     dpg.add_file_extension("", color=(150, 255, 150, 255))
#     dpg.add_file_extension("Source files (*.cpp *.h *.hpp){.cpp,.h,.hpp}", color=(0, 255, 255, 255))
#     dpg.add_file_extension(".h", color=(255, 0, 255, 255), custom_text="[header]")
#     dpg.add_file_extension(".py", color=(0, 255, 0, 255), custom_text="[Python]")

####################################
# init

dpg.create_context()
dpg.create_viewport(title="REAPER project generator", width=1280, height=900)
dpg.setup_dearpygui()

####################################
# theme

with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 5, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 5, category=dpg.mvThemeCat_Core)
dpg.bind_theme(global_theme)

####################################
# file io

dpg.add_file_dialog(
        directory_selector=True, show=False, callback=lambda s, d: view_state.file_selector_audio_select(d), tag="file_selector_audio",
        cancel_callback=lambda: view_state.file_selector_audio_hide(), width=700 ,height=400)

with dpg.file_dialog(
        show=False, callback=lambda s, d: view_state.file_selector_reaper_project_select(d), tag="file_selector_reaper_project",
        cancel_callback=lambda: view_state.file_selector_reaper_project_hide(), width=700 ,height=400):
    dpg.add_file_extension(".rpp", color=(0, 255, 0, 255), custom_text="[REAPER Project]")

with dpg.file_dialog(
        show=False, callback=lambda s, d: view_state.file_selector_open_project_select(d), tag="file_selector_open_project",
        cancel_callback=lambda: view_state.file_selector_open_project_hide(), width=700 ,height=400):
    dpg.add_file_extension(".json", color=(0, 255, 0, 255), custom_text="[grrpg JSON Project]")

with dpg.file_dialog(
        show=False, callback=lambda s, d: view_state.file_selector_save_project_select(d), tag="file_selector_save_project",
        cancel_callback=lambda: view_state.file_selector_save_project_hide(), width=700 ,height=400):
    dpg.add_file_extension(".grrpg.json", color=(0, 255, 0, 255), custom_text="[grrpg JSON Project]")

####################################
# value storage init

with dpg.value_registry():
    [dpg.add_string_value(tag = f"new_code_value_{idx}") for idx in range(4096)]

####################################
# window

with dpg.window(label="main", width=1280, height=900, no_title_bar=True, no_resize=True, no_move = True, tag="main_window"):

    with dpg.group(horizontal=True):
        dpg.add_button(label="open project", width = 120, callback = lambda: view_state.file_selector_open_project_show())
        dpg.add_button(label="save project", width = 120, callback = lambda: view_state.file_selector_save_project_show())
        dpg.add_button(label="reset project", width = 120, callback = lambda: view_state.btn_project_reset())

    dpg.add_separator()

    with dpg.group(horizontal=True):
        dpg.add_button(label="open files", width = 120, callback = lambda: view_state.file_selector_audio_show())
        dpg.add_text("./files/", tag = "path_audio")

    with dpg.group(horizontal=True):
        dpg.add_button(label="output file", width = 120, callback= lambda: view_state.file_selector_reaper_project_show())
        dpg.add_text("./test-project.rpp", tag = "reaper_project_name")

    dpg.add_separator()

    with dpg.group(horizontal=True):
        dpg.add_button(label="generate & open", width = 240, height = 40, callback = lambda s: view_state.btn_generate_and_open())
        dpg.add_button(label="generate", width = 240, height = 40, callback = lambda s: view_state.btn_generate())
        dpg.add_button(label="generate next & open", width = 240, height = 40, callback = lambda s: view_state.btn_generate_next_and_open())

    dpg.add_separator()

    with dpg.group(horizontal=True):

        # dpg.add_spacer(width = 60)
        dpg.add_input_int(label = "track count", width=120, tag="track_count", callback = lambda sender: view_state.set_track_count(dpg.get_value(sender)) )

        dpg.add_spacer(width = 60)
        dpg.add_checkbox(label="loop items",   tag = "loop_items", callback = lambda sender: view_state.set_loop_items(dpg.get_value(sender)))
        
        dpg.add_spacer(width = 60)
        dpg.add_input_int(label = "project length (sec)", width = 120, tag = "project_length", callback = lambda sender: view_state.set_project_length(dpg.get_value(sender)))

    dpg.add_separator()
    
    button_labels_1 = [
    "length", "rate", "spacing", "fade_in", "fade_out","gain",
    "pitch_offset", "ts_type",
    "sample_offset", "pan_automation","item_probability",
    "item_pitch_start", "item_pitch_middle", "item_pitch_end",
    "item_pan_start", "item_pan_middle", "item_pan_end",
    ]

    with dpg.group(horizontal = True):

        with dpg.group(horizontal = False, width = 200):
            dpg.add_radio_button(button_labels_1, callback=lambda sender: view_state.set_selected(dpg.get_value(sender)))

            # dpg.add_separator()

            dpg.add_text(core.get_generator_context_doc())
        
        # dpg.add_text("Anti-aliasing can be enabled from the plot's context menu (see Help).", bullet=True)
    
        with dpg.group():
            datax = []#[float(x)/256.0 * 30 for x in range(256)]
            # random.seed(getattr(view_state.project, "seed_"+view_state.selected))
            datay = []#[core.interpolate_values(x, getattr(view_state.project, view_state.selected)) for x in datax]
            
            min_y = 0#min(datay)
            max_y = 1#max(datay)

            # create plot
            with dpg.plot(height=300, width=-1, no_title=True, anti_aliased = True):
                dpg.add_plot_axis(dpg.mvXAxis, label="x", tag = "x_axis")
                dpg.set_axis_limits(dpg.last_item(), 0, 30)
                    
                with dpg.plot_axis(dpg.mvYAxis, label="y", tag ="y_axis"):
                    dpg.set_axis_limits(dpg.last_item(), min_y, max_y)

                    # series belong to a y axis
                    dpg.add_line_series(datax, datay, tag="plot_data")

            with dpg.group(id = "element_list"):
                pass

    view_state.update_project_view()
    view_state.set_selected("length")
    


dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
