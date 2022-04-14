# author: mrxirzzz

import dearpygui.dearpygui as dpg
import argparse
from pathlib import Path
import json
import requests 
import random
from hashlib import md5

from utils.episodes import Episodes

def load_json_callback(sender, app_data, user_data):
    episodes, f = load_json(user_data)
    dpg.set_value('episode_idx', 1)
    dpg.set_value('frame_idx', 1)
    idx_callback(sender, app_data, ['minus', 'episodes', episodes])

def load_json(user_data):
    split = dpg.get_value('split')
    scene = dpg.get_value('scene') if dpg.get_value('scene') != 'None' else None 
    episodes = Episodes(split, scene=scene, only_json=True).get_episodes()
    f = open('annotations/{}_seg.json'.format(split), mode='a+')
    return episodes, f
    

def load_split_callback(sender, app_data):
    split_scene_idx_dict = {}
    split_scene_idx_dict['train'] = [1, 2, 3, 4, 5, 8 ,10 , 11, 12, 14, 16, 17, 20, 22, 23, 25, 26]
    split_scene_idx_dict['val_seen'] = [1, 2, 3, 5, 8, 10, 11, 12, 14, 16, 17, 20, 23, 26]
    split_scene_idx_dict['val_unseen'] = [6, 9, 13, 24]
    split_scene_idx_dict['test'] = [7, 15, 18, 21]
    split = dpg.get_value(sender)
    scene_list = ['None']
    for idx in split_scene_idx_dict[split]:
        scene_list.append(idx)
    dpg.configure_item('scene', items=scene_list) 


def load_imgs_callback(sender, app_data, user_data):
    if_seg = user_data[1]
    width, height, data, exp = load_imgs(user_data)
    if not if_seg:
        dpg.set_value('origin_frame', data)
    else:
        dpg.set_value('seg_frame', data)
    return width, height, data, exp


def load_imgs(user_data):
    # picutre loading and registry
    # load information
    episode_idx, frame_idx = int(dpg.get_value('episode_idx')), int(dpg.get_value('frame_idx'))
    episodes, if_seg = user_data[0], user_data[1]
    scene = dpg.get_value('scene')
    split = dpg.get_value('split')

    origin_img_dir = Path('.').resolve() / 'data' / split / 'origin'
    seg_img_dir = Path('.').resolve() / 'data' / split / 'seg'
    trajectory_id = episodes[episode_idx-1]['trajectory_id']
    episode_id = episodes[episode_idx-1]['episode_id']
    # load pictures
    # print('{}/{:02d}_{}_{}/{:03d}.jpg'.format(str(origin_img_dir),\
    #         scene, trajectory_id, episode_id, frame_idx))
    if not if_seg:
        width, height, _, data = dpg.load_image('{}/{:02d}_{}_{}/{:03d}.jpg'.format(str(origin_img_dir),\
            int(scene), trajectory_id, episode_id, frame_idx-1))
    else:
        width, height, _, data = dpg.load_image('{}/{:02d}_{}_{}/{:03d}.jpg'.format(str(seg_img_dir),\
            int(scene), trajectory_id, episode_id, frame_idx-1))
    with (origin_img_dir / '{:02d}_{}_{}'.format(int(scene), trajectory_id, episode_id) / 'expressions.json').open() as f:
        exp = json.loads(f.read())
    return  width, height, data, exp


def idx_callback(sender, app_data, user_data):
    mode, obj, episodes = user_data[0], user_data[1], user_data[2]
    episode_idx, frame_idx, = int(dpg.get_value('episode_idx')), int(dpg.get_value('frame_idx'))
    if sender == 'drag_int_episodes' or sender == 'drag_int_frames':
        drag_int_idx = int(dpg.get_value(sender))
    def op(idx, mode):
        if mode == 'minus':
            if idx  > 1:
                idx = idx -1
        elif mode == 'plus':
            if idx < dpg.get_item_configuration('drag_int_' + obj)['max_value']:
                idx = idx + 1
        else:
            idx = drag_int_idx
        dpg.set_value('drag_int_' + obj, idx)
        return idx

    if obj == 'episodes':
        episode_idx = op(episode_idx, mode)
        frame_idx = 1
        dpg.set_value('episode_idx', episode_idx) 
        dpg.set_value('frame_idx', frame_idx)
        dpg.set_value('drag_int_frames', frame_idx)
        dpg.set_value('len_episodes', '/' + str(len(episodes)))
        dpg.set_value('len_frames', '/' + str(episodes[episode_idx-1]['len_frames']))
        dpg.configure_item('drag_int_episodes', max_value=len(episodes))
        _, _, _, exp = load_imgs_callback(sender, app_data, [episodes, True])
        load_imgs_callback(sender, app_data, [episodes, False])
        dpg.set_value('exp', '导航指令：' + exp['instruction'])
        dpg.set_value('exp_translated', '导航指令翻译：' + translate(exp['instruction']))

    elif obj == 'frames':
        frame_idx = op(frame_idx, mode)
        dpg.set_value('frame_idx', frame_idx)
        dpg.set_value('len_episodes', '/' + str(len(episodes)))
        dpg.set_value('len_frames', '/' + str(episodes[episode_idx-1]['len_frames']))
        dpg.configure_item('drag_int_frames', max_value=episodes[episode_idx-1]['len_frames'])
        load_imgs_callback(sender, app_data, [episodes, True])
        load_imgs_callback(sender, app_data, [episodes, False])
    else:
        raise ValueError('Not supported object:{} for {}'.format(obj, mode))


def translate(instruction):
    # translate navigation instructions by Baidu Translate API
    query = instruction
    from_lang = 'en'
    to_lang = 'zh'
    appid = '20210825000926998'
    appkey = 'N54Ev0fTKeyiZ5Tn4tX3'
    endpoint = 'http://api.fanyi.baidu.com'
    path = '/api/trans/vip/translate'
    url = endpoint + path
    salt = random.randint(32768, 65536)
    def make_md5(s, encoding='utf-8'):
        return md5(s.encode(encoding)).hexdigest()
    sign = make_md5(appid + query + str(salt) + appkey)

    # Build request
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {'appid': appid, 'q': query, 'from': from_lang, \
        'to': to_lang, 'salt': salt, 'sign': sign}

    # Send request
    r = requests.post(url, params=payload, headers=headers)
    r = r.json()['trans_result'][0]['dst']
    return r


def main(args):

    default_split = 'train'
    default_scene = 3
    default_episode_idx = 1
    default_frame_idx = 1

    dpg.create_context()
    
    # Chinese support
    with dpg.font_registry():
        with dpg.font("resources/wqy-MicroHei.ttf", 20) as font1:
        
            # add the default font range
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            # helper to add range of characters
            #    Options:
            #        mvFontRangeHint_Chinese_Full
            #        mvFontRangeHint_Chinese_Simplified_Common
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Simplified_Common)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full)


    # Main window for UI
    with dpg.window(label="AirVLN Referring Expression 标注工具", width=1680, height=1080, no_collapse=True):

        dpg.bind_font(font1)

        # Menu bar settings
        #TODO
        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Load json file")
                dpg.add_menu_item(label="Save json file")
                dpg.add_menu_item(label="Save json file As")

            with dpg.menu(label="Settings"):
                dpg.add_menu_item(label="Setting 1", check=True)
                dpg.add_menu_item(label="Setting 2")
            dpg.add_menu_item(label="Help")

        # Load split and scene json toolbar and statusbar for loaded json file
        with dpg.group(horizontal=True):
            # split selector
            dpg.add_text("Split:", tag='split_hint')
            dpg.add_combo(['train', 'val_seen', 'val_unseen', 'test'], tag='split', \
                default_value=default_split, width=90, callback=load_split_callback)
            # scene selector
            dpg.add_text('By Scene:', tag='scene_hint')
            scene_list = ['None', 1, 2, 3, 4, 5, 8,10, 11, 12, 14, 16,\
                17, 20, 22, 23, 25, 26]
            dpg.add_combo(scene_list, tag='scene', default_value=default_scene, width=50) 
            episodes, f = load_json([])
            # Load button
            dpg.add_button(user_data=[episodes, f], callback=load_json_callback,\
                label="Load", tag='load_btn')


            # episode_idx selector
            dpg.add_text('| State: Episode')
            dpg.add_text(default_episode_idx, tag='episode_idx')
            dpg.add_text('/{}'.format(len(episodes)), tag='len_episodes')
            dpg.add_button(arrow=True, direction=dpg.mvDir_Left, callback=idx_callback,\
                 user_data=['minus', 'episodes', episodes])
            dpg.add_drag_int(width=50, default_value=1, callback=idx_callback, min_value=1, max_value=len(episodes),\
                 user_data=['drag', 'episodes', episodes], tag='drag_int_episodes')
            dpg.add_button(arrow=True, direction=dpg.mvDir_Right, callback=idx_callback,\
                 user_data=['plus', 'episodes', episodes])
            # frame_idx selector
            dpg.add_text('Frame')
            dpg.add_text(default_frame_idx, tag='frame_idx')
            dpg.add_text('/{}'.format(episodes[default_episode_idx-1]['len_frames']), tag='len_frames')
            dpg.add_button(arrow=True, direction=dpg.mvDir_Left, callback=idx_callback, \
                 user_data=['minus', 'frames', episodes])
            dpg.add_drag_int(width=90, default_value=1, callback=idx_callback, min_value=1,\
                 max_value=episodes[default_episode_idx-1]['len_frames'],\
                 user_data=['drag', 'frames', episodes], tag='drag_int_frames')
            dpg.add_button(arrow=True, direction=dpg.mvDir_Right, callback=idx_callback, \
                 user_data=['plus', 'frames', episodes])

        # picutre loading and registry
        width, height, data, exp = load_imgs([episodes, False])
        width_seg, height_seg, data_seg, _ = load_imgs([episodes, True])
        # picture registry
        with dpg.texture_registry(show=False):
            dpg.add_dynamic_texture(width, height, data, tag="origin_frame")
            dpg.add_dynamic_texture(width_seg, height_seg, data_seg, tag="seg_frame")

        # Main operating UI
        #FIXME
        with dpg.group(horizontal=True):

            # space to show origin and segmentation frames
            with dpg.group():
                factor = 3.3
                dpg.add_image("origin_frame", width=width*factor, height=height*factor)
                dpg.add_image("seg_frame", width=width*factor, height=height*factor)

            # space to show instructions, referring expressions highlighted navigation instructions,
            # tranlated navigation instructions and operating logs
            with dpg.group():
                # Insturctions
                instructions = '使用说明：已自动解析表达式，如有部分错误可通过弹窗编辑。可通过方向键或wasd键同时调整视频的episode和frame序号，在对应帧单击一个高亮的表达式，使用单击选定一个或多个segmentation的mask，选定后会自动保存，并在原图显示已选定的mask。'
                dpg.add_text(default_value=instructions, wrap=0)
                # Navigation instructions, parsed referring expression highlighted and translated results
                dpg.add_text('导航指令：' + exp['instruction'], tag='exp', wrap=0)
                dpg.add_text('导航指令翻译：' + translate(exp['instruction']), tag='exp_translated', wrap=0)
                dpg.add_text('已解析表达式(存在冗余或不准确)：')
                exps = []
                items = []
                for key, value in exp['expressions'].items():
                    exps.append(value['exp']) 
                    items.append(dpg.add_selectable(label=value['exp']))
                def _selection(sender, app_data, user_data):
                    for item in user_data:
                        if item != sender:
                            dpg.set_value(item, False)
                for item in items:
                    dpg.configure_item(item, callback=_selection, user_data=items)

                # print(exps)
                # Operating logs
                # dpg.add_text("操作日志：")


    # key bind for episode and frame editing
    def vim_key_fe_callback(sender, app_data, user_data):
        # h,l for episode minus and plus, j,k for frame plus and minus, like vim motion bind keys
        episodes = user_data
        if app_data in [ 72, 87, 265 ]: # press h or w or up key
            idx_callback(sender, app_data, ['minus', 'episodes', episodes])
        elif app_data in [ 74, 68, 262 ]: # press j or d or right key
            idx_callback(sender, app_data, ['plus', 'frames', episodes])
        elif app_data in [ 75, 65, 263 ]: # press k or a or left key
            idx_callback(sender, app_data, ['minus', 'frames', episodes])
        elif app_data in [ 76, 83, 264 ]: # press l or s or down key
            idx_callback(sender, app_data, ['plus', 'episodes', episodes])
        else:
            print('Other key pressed!')
    with dpg.handler_registry():
        dpg.add_key_press_handler(dpg.mvKey_H, callback=vim_key_fe_callback, user_data=episodes)
        dpg.add_key_press_handler(dpg.mvKey_J, callback=vim_key_fe_callback, user_data=episodes)
        dpg.add_key_press_handler(dpg.mvKey_K, callback=vim_key_fe_callback, user_data=episodes)
        dpg.add_key_press_handler(dpg.mvKey_L, callback=vim_key_fe_callback, user_data=episodes)
        dpg.add_key_press_handler(dpg.mvKey_Up, callback=vim_key_fe_callback, user_data=episodes)
        dpg.add_key_press_handler(dpg.mvKey_Right, callback=vim_key_fe_callback, user_data=episodes)
        dpg.add_key_press_handler(dpg.mvKey_Left, callback=vim_key_fe_callback, user_data=episodes)
        dpg.add_key_press_handler(dpg.mvKey_Down, callback=vim_key_fe_callback, user_data=episodes)
        dpg.add_key_press_handler(dpg.mvKey_W, callback=vim_key_fe_callback, user_data=episodes)
        dpg.add_key_press_handler(dpg.mvKey_D, callback=vim_key_fe_callback, user_data=episodes)
        dpg.add_key_press_handler(dpg.mvKey_A, callback=vim_key_fe_callback, user_data=episodes)
        dpg.add_key_press_handler(dpg.mvKey_S, callback=vim_key_fe_callback, user_data=episodes)


    dpg.create_viewport(title='AirVLN Referring Expression 标注工具', width=1680, height=1080)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Main software gui launch program\
        for referring expression annotation in aivln dataset with airsim and dearpygui.')

    args = parser.parse_args()
    main(args)
