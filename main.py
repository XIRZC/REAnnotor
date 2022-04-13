import dearpygui.dearpygui as dpg
import argparse
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from episodes import Episodes

def load_json(sender, app_data, comps):
    split = dpg.get_value('split')
    scene = dpg.get_value('scene') if dpg.get_value('scene') != 'None' else None 
    episodes = Episodes(split, scene=scene).get_episodes()
    txt = 'frame{}/{}-episode{}/{} of split:{}{}'.format(1, len(episodes[0]), 1, len(episodes), split, '_scene:{}'.format(scene) if scene else '')
    dpg.set_value('status_txt', txt)
    f = open('annotations/{}_seg.json'.format(split), mode='a+')
    return episodes, f
    

def load_split(sender, app_data):
    split_scene_idx_dict = {}
    split_scene_idx_dict['train'] = [1, 2, 3, 4, 5, 8 ,10 , 11, 12, 14, 16, 17, 20, 22, 23, 25, 26]
    split_scene_idx_dict['val_seen'] = [1, 2, 3, 5, 8, 10, 11, 12, 14, 16, 17, 20, 23, 26]
    split_scene_idx_dict['val_unseen'] = [6, 9, 13, 24]
    split_scene_idx_dict['test'] = [7, 15, 18, 21]
    split = dpg.get_value(sender)
    scene_list = ['None']
    for idx in split_scene_idx_dict[split]:
        scene_list.append(idx)
    print(dpg.get_item_configuration('scene'))
    dpg.configure_item('scene', items=scene_list) 


def main(args):

    dpg.create_context()

    with dpg.window(label="AirVLN RE Annotation Tool", width=1280, height=960):

        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Load json file")
                dpg.add_menu_item(label="Save json file")
                dpg.add_menu_item(label="Save json file As")

            with dpg.menu(label="Settings"):
                dpg.add_menu_item(label="Setting 1", check=True)
                dpg.add_menu_item(label="Setting 2")
            dpg.add_menu_item(label="Help")

        with dpg.group(horizontal=True):
            dpg.add_text('Status Info: Not Loaded Yet.', tag='status_txt')
            dpg.add_text("| Split:", tag='split_hint')
            dpg.add_combo(['train', 'val_seen', 'val_unseen', 'test'], tag='split', \
                default_value='train', width=75, callback=load_split)
            dpg.add_text('By Scene:', tag='scene_hint')
            scene_list = ['None', 1, 2, 3, 4, 5, 8,10, 11, 12, 14, 16,\
                17, 20, 22, 23, 25, 26]
            dpg.add_combo(scene_list, tag='scene', default_value='None', width=50) 

            dpg.add_button(callback=load_json, label="Load", tag='load_btn')
            # dpg.add_text("Hello, world")
            # dpg.add_input_text(label="string", default_value="Quick brown fox")
            # dpg.add_slider_float(label="float", default_value=0.273, max_value=1)
        
            origin_img_dir = Path('.').resolve() / 


            width, height, channels, data = dpg.load_image("")

            with dpg.texture_registry(show=True):
                dpg.add_static_texture(width, height, data, tag="texture_tag")

            with dpg.window(label="Tutorial"):
                dpg.add_image("texture_tag")



    dpg.create_viewport(title='AirVLN RE Annotation Tool', width=1280, height=960)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Main software gui launch program for referring expression annotation in aivln dataset with airsim and dearpygui.')

    args = parser.parse_args()
    main(args)
