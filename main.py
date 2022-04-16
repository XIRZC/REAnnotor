# author: mrxirzzz

# internal packages imported
import dearpygui.dearpygui as dpg
import argparse
from pathlib import Path
import json

# project packages imported
from utils.episodes import Episodes


# Global Constant and Variables
DEFAULT_SPLIT = 'val_seen'
DEFAULT_SCENE = 3
DEFAULT_EPISODE_IDX = 4
DEFAULT_FRAME_IDX = 1

WIN_FACTOR = 1   # cause my windows has factor 1.5, so need to shrinke resolution
WINDOW_WIDTH, WINDOW_HEIGHT, FRAME_FACTOR = int(1600 / WIN_FACTOR), int(1000 / WIN_FACTOR), int(3 / WIN_FACTOR)
FRAME_WIDTH, FRAME_HEIGHT = 256, 144

ORIGIN_FRAME_OFFSET_X, ORIGIN_FRAME_OFFSET_Y = 0, 70
SEG_FRAME_OFFSET_X, SEG_FRAME_OFFSET_Y = 0, 520
STATUS_BAR_OFFSET_X, STATUS_BAR_OFFSET_Y = 5, 965

ORIGIN_FRAME_END_X, ORIGIN_FRAME_END_Y = ORIGIN_FRAME_OFFSET_X + FRAME_WIDTH * FRAME_FACTOR, ORIGIN_FRAME_OFFSET_Y + FRAME_HEIGHT * FRAME_FACTOR
SEG_FRAME_END_X, SEG_FRAME_END_Y = SEG_FRAME_OFFSET_X + FRAME_WIDTH * FRAME_FACTOR, SEG_FRAME_OFFSET_Y + FRAME_HEIGHT * FRAME_FACTOR

episodes, f = None, None
mouse_point = []
selectable_item_exp = ''


# Json load and write functions
def write_json():
    dic = dict()
    dic['epoisodes'] = episodes
    f.write(json.dumps(dic))
def load_json_callback(sender, app_data, user_data):
    # save all the staged episodes operations
    write_json()
    # load new json to episodes and generate new file IO object
    load_json()
    idx_callback(sender, app_data, ['reset', 'episodes'])
def load_json():
    split = dpg.get_value('split')
    scene = dpg.get_value('scene') if dpg.get_value('scene') != 'None' else None 
    global episodes, f
    episodes = Episodes(split, scene=scene, only_json=True).get_episodes()
    # for epi in episodes:
    #     epi['expressions'] = []  # list of referring expressions
    #     epi['frames'] = []   # list of dict(key: expression, value: corresponding mask ndarray)
    f = open('annotations/{}_seg.json'.format(split), mode='w+')
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


# load img and expression annotation functions
def load_imgs_callback(sender, app_data, user_data):
    if_seg = user_data
    width, height, data, exp = load_imgs(user_data)
    if not if_seg:
        dpg.set_value('origin_frame', data)
    else:
        dpg.set_value('seg_frame', data)
    return width, height, data, exp
def load_imgs(user_data):
    # picutre loading and registry
    episode_idx, frame_idx = int(dpg.get_value('episode_idx')), int(dpg.get_value('frame_idx'))
    if_seg = user_data
    scene = dpg.get_value('scene')
    split = dpg.get_value('split')
    origin_img_dir = Path('.').resolve() / 'data' / split / 'origin'
    seg_img_dir = Path('.').resolve() / 'data' / split / 'seg'
    trajectory_id = episodes[episode_idx-1]['trajectory_id']
    episode_id = episodes[episode_idx-1]['episode_id']
    # load pictures
    if not if_seg:
        width, height, _, data = dpg.load_image('{}/{:02d}_{}_{}/{:03d}.jpg'.format(str(origin_img_dir),\
            int(scene), trajectory_id, episode_id, frame_idx-1))
    else:
        width, height, _, data = dpg.load_image('{}/{:02d}_{}_{}/{:03d}.jpg'.format(str(seg_img_dir),\
            int(scene), trajectory_id, episode_id, frame_idx-1))
    with (origin_img_dir / '{:02d}_{}_{}'.format(int(scene), trajectory_id, episode_id) / 'expressions.json').open() as f:
        exp = json.loads(f.read())
    return  width, height, data, exp


# episode and frame idx editting callback function
def idx_callback(sender, app_data, user_data):
    mode, obj = user_data[0], user_data[1]
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
        elif mode == 'drag':
            idx = drag_int_idx
        else: # reset to 1
            idx = 1
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
        dpg.set_value('split_txt', 'Split: '+dpg.get_value('split'))
        dpg.set_value('scene_txt', 'Scene_id: '+dpg.get_value('scene'))
        dpg.set_value('episode_id', 'Episode_id: '+episodes[episode_idx-1]['episode_id'])
        dpg.set_value('trajectory_id', 'Trajectory_id: '+episodes[episode_idx-1]['trajectory_id'])
        dpg.configure_item('drag_int_episodes', max_value=len(episodes))
        _, _, _, exp = load_imgs_callback(sender, app_data, True)
        load_imgs_callback(sender, app_data, False)
        dpg.set_value('exp', '导航指令：' + exp['instruction'])
        dpg.set_value('exp_translated', '导航指令翻译：' + exp['instruction_translated'])
        # exps = []
        if 'expressions' not in episodes[episode_idx-1]:
            episodes[episode_idx-1]['expressions'] = []
            for value in exp['expressions'].values():
                # exps.append(value['exp']) 
                episodes[episode_idx-1]['expressions'].append(value)
        dpg.delete_item('pop_up_exps_sub')
        with dpg.group(tag='pop_up_exps_sub', parent='pop_up_exps'):
            for e in episodes[episode_idx-1]['expressions']:
                with dpg.group(horizontal=True, tag=e):
                    dpg.add_input_text(default_value=e, tag=e+'input', user_data=[e, 'upd'], callback=exps_callback, on_enter=True)
                    # dpg.add_button(label='Delete', user_data=e, callback=lambda s, a, u: dpg.delete_item(u))
                    dpg.add_button(label='Delete', tag=e+'delbtn', user_data=[e, 'del'], callback=exps_callback)
        items = []
        dpg.delete_item('exps_sub')
        with dpg.group(tag='exps_sub', parent='exps'):
            for e in episodes[episode_idx-1]['expressions']:
                items.append(dpg.add_selectable(label=e))
        for item in items:
            dpg.configure_item(item, callback=_selection, user_data=items)
    elif obj == 'frames':
        frame_idx = op(frame_idx, mode)
        dpg.set_value('frame_idx', frame_idx)
        dpg.set_value('len_episodes', '/' + str(len(episodes)))
        dpg.set_value('len_frames', '/' + str(episodes[episode_idx-1]['len_frames']))
        dpg.configure_item('drag_int_frames', max_value=episodes[episode_idx-1]['len_frames'])
        load_imgs_callback(sender, app_data, True)
        load_imgs_callback(sender, app_data, False)
    else:
        raise ValueError('Not supported object:{} for {}'.format(obj, mode))


# expression show and add/upd/del functions
def exps_callback(sender, app_data, user_data):
    exp, mode = user_data[0], user_data[1]
    callback_val = dpg.get_value(sender)
    episode_idx = int(dpg.get_value('episode_idx'))
    if mode == 'add':
        episodes[episode_idx-1]['expressions'].append(exp)
        with dpg.group(horizontal=True, tag=exp, parent='pop_up_exps_sub'):
            dpg.add_input_text(default_value=exp, tag=exp+'input', user_data=[exp, 'upd'], callback=exps_callback, on_enter=True)
            # dpg.add_button(label='Delete', user_data=e, callback=lambda s, a, u: dpg.delete_item(u))
            dpg.add_button(label='Delete', tag=exp+'delbtn', user_data=[exp, 'del', exp], callback=exps_callback)
        # screen repeat exp
        sorted(set(episodes[episode_idx-1]['expressions']), key=episodes[episode_idx-1]['expressions'].index)
    elif mode == 'del':
        episodes[episode_idx-1]['expressions'].remove(exp)
        dpg.delete_item(user_data[2])
    elif mode == 'upd':
        idx = episodes[episode_idx-1]['expressions'].index(exp)
        episodes[episode_idx-1]['expressions'][idx] = callback_val
        # episodes[episode_idx-1]['expressions'].remove(exp)
        dpg.configure_item(exp+'input', user_data=[callback_val, 'upd'])
        dpg.configure_item(exp+'delbtn', user_data=[callback_val, 'del', exp])
        sorted(set(episodes[episode_idx-1]['expressions']), key=episodes[episode_idx-1]['expressions'].index)
    else:   # save
        items = []
        dpg.delete_item('exps_sub')
        with dpg.group(tag='exps_sub', parent='exps'):
            for e in episodes[episode_idx-1]['expressions']:
                items.append(dpg.add_selectable(label=e))
        for item in items:
            dpg.configure_item(item, callback=_selection, user_data=items)
        dpg.configure_item('pop_edit_panel', show=False)
        write_json()


# key bind for episode and frame editing functions
def keyboard_event_handler(sender, app_data, user_data):
    # h,l for episode minus and plus, j,k for frame plus and minus, like vim motion bind keys
    episodes = user_data
    if app_data in [ 72, 87, 265 ]: # press h or w or up key
        idx_callback(sender, app_data, ['minus', 'episodes'])
    elif app_data in [ 74, 68, 262 ]: # press j or d or right key
        idx_callback(sender, app_data, ['plus', 'frames'])
    elif app_data in [ 75, 65, 263 ]: # press k or a or left key
        idx_callback(sender, app_data, ['minus', 'frames'])
    elif app_data in [ 76, 83, 264 ]: # press l or s or down key
        idx_callback(sender, app_data, ['plus', 'episodes'])
    else:
        print('Other key pressed!')
def toggle_bind_key_callback():
    ls = ['h', 'j', 'k', 'l', 'w', 'a', 's', 'd', 'up', 'right', 'left', 'down']
    if dpg.is_key_down(dpg.mvKey_E):
        # print('Press Ctrl E!', dpg.get_item_callback('bind_key_h'))
        for i in ls:
            dpg.configure_item('bind_key_' + i, callback=keyboard_event_handler)
    if dpg.is_key_down(dpg.mvKey_R):
        # print('Press Ctrl R!', dpg.get_item_callback('bind_key_h'))
        for i in ls:
            dpg.configure_item('bind_key_' + i, callback=None)
    dpg.set_value('shortcut', ' Shortcut Mode: '+('enabled' if dpg.get_item_callback('bind_key_h') else 'disabled'))
def toggle_bind_key():
    ls = ['h', 'j', 'k', 'l', 'w', 'a', 's', 'd', 'up', 'right', 'left', 'down']
    for i in ls:
        if dpg.get_item_callback('bind_key_' + i) is None:
            dpg.configure_item('bind_key_' + i, callback=keyboard_event_handler)
        else:
            dpg.configure_item('bind_key_' + i, callback=None)
    dpg.set_value('shortcut', ' Shortcut Mode: '+('enabled' if dpg.get_item_callback('bind_key_h') else 'disabled'))


# mouse action and mask operation function
def mouse_event_handler(sender, data):
    global mouse_point
    type = dpg.get_item_info(sender)["type"]
    if type == "mvAppItemType::mvMouseClickHandler":
        mask_operation('add')
    if type == "mvAppItemType::mvMouseDoubleClickHandler":
        mask_operation('del')
    if type == "mvAppItemType::mvMouseMoveHandler":
        dpg.set_value('mouse_move', f"Mouse pos: {data}")
        mouse_point = data
def mask_operation(mode):
    if mode == 'add':
        if boundary(mouse_point, SEG_FRAME_OFFSET_X, SEG_FRAME_OFFSET_Y, SEG_FRAME_END_X, SEG_FRAME_END_Y):
            print('Clicked at', mouse_point)
            i, j = restore(mouse_point, 'seg')
            print('Frame pixel i:{} j:{}'.format(i, j))
    elif mode == 'del':
        if boundary(mouse_point, ORIGIN_FRAME_OFFSET_X, ORIGIN_FRAME_OFFSET_Y, ORIGIN_FRAME_END_X, ORIGIN_FRAME_END_Y):
            print('DoubleClicked at', mouse_point)
            i, j = restore(mouse_point, 'origin')
            print('Frame pixel i:{} j:{}'.format(i, j))
    else:   
        pass


# expression selection function
def _selection(sender, app_data, user_data):
    global selectable_item_exp
    for item in user_data:
        if item != sender:
            dpg.set_value(item, False)
        else:
            selectable_item_exp = dpg.get_item_configuration(sender)['label']
            print('Now Selected exp are: ', selectable_item_exp)


# util functions
def boundary(p, ltx, lty, rbx, rby):
    if (p[0] >= ltx and p[0] < rbx) and (p[1] >= lty and p[1] < rby):
        return True
    return False
def restore(p, mode):
    if mode == 'seg':
        return [(p[0] - SEG_FRAME_OFFSET_X) // FRAME_FACTOR, (p[1] - SEG_FRAME_OFFSET_Y) // FRAME_FACTOR]
    else: # origin
        return [(p[0] - ORIGIN_FRAME_OFFSET_X) // FRAME_FACTOR, (p[1] - ORIGIN_FRAME_OFFSET_Y) // FRAME_FACTOR]


# main UI definition function
def main(args):

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
            
    # Shortcut mode
    with dpg.handler_registry():
        dpg.add_key_press_handler(dpg.mvKey_LControl, callback=toggle_bind_key_callback)
        dpg.add_key_press_handler(dpg.mvKey_H, callback=keyboard_event_handler, tag='bind_key_h')
        dpg.add_key_press_handler(dpg.mvKey_J, callback=keyboard_event_handler, tag='bind_key_j')
        dpg.add_key_press_handler(dpg.mvKey_K, callback=keyboard_event_handler, tag='bind_key_k')
        dpg.add_key_press_handler(dpg.mvKey_L, callback=keyboard_event_handler, tag='bind_key_l')
        dpg.add_key_press_handler(dpg.mvKey_W, callback=keyboard_event_handler, tag='bind_key_w')
        dpg.add_key_press_handler(dpg.mvKey_D, callback=keyboard_event_handler, tag='bind_key_d')
        dpg.add_key_press_handler(dpg.mvKey_A, callback=keyboard_event_handler, tag='bind_key_a')
        dpg.add_key_press_handler(dpg.mvKey_S, callback=keyboard_event_handler, tag='bind_key_s')
        dpg.add_key_press_handler(dpg.mvKey_Up, callback=keyboard_event_handler, tag='bind_key_up')
        dpg.add_key_press_handler(dpg.mvKey_Right, callback=keyboard_event_handler, tag='bind_key_right')
        dpg.add_key_press_handler(dpg.mvKey_Left, callback=keyboard_event_handler, tag='bind_key_left')
        dpg.add_key_press_handler(dpg.mvKey_Down, callback=keyboard_event_handler, tag='bind_key_down')
        dpg.add_mouse_click_handler(tag='mouse_clicked_handler', callback=mouse_event_handler)
        dpg.add_mouse_double_click_handler(tag='mouse_doubelclicked_handler', callback=mouse_event_handler)
        dpg.add_mouse_move_handler(tag='mouse_move_handler', callback=mouse_event_handler)



    # Main window for UI
    with dpg.window(label="AirVLN Referring Expression 标注工具", width=WINDOW_WIDTH, height=WINDOW_HEIGHT, no_collapse=True, no_title_bar=True, no_move=True):

        dpg.bind_font(font1)

        # Menu bar settings
        #TODO
        with dpg.menu_bar():
            with dpg.menu(label="Menu"):
                dpg.add_menu_item(label="Load json file", callback=load_json)
                dpg.add_menu_item(label="Save json file", callback=write_json)
            with dpg.menu(label="Tools"):
                dpg.add_menu_item(label="Show About", callback=lambda:dpg.show_tool(dpg.mvTool_About))
                dpg.add_menu_item(label="Show Metrics", callback=lambda:dpg.show_tool(dpg.mvTool_Metrics))
                dpg.add_menu_item(label="Show Documentation", callback=lambda:dpg.show_tool(dpg.mvTool_Doc))
                dpg.add_menu_item(label="Show Debug", callback=lambda:dpg.show_tool(dpg.mvTool_Debug))
                dpg.add_menu_item(label="Show Style Editor", callback=lambda:dpg.show_tool(dpg.mvTool_Style))
                dpg.add_menu_item(label="Show Font Manager", callback=lambda:dpg.show_tool(dpg.mvTool_Font))
                dpg.add_menu_item(label="Show Item Registry", callback=lambda:dpg.show_tool(dpg.mvTool_ItemRegistry))
            with dpg.menu(label="Settings"):
                dpg.add_menu_item(label="Toggle Fullscreen", callback=lambda:dpg.toggle_viewport_fullscreen())
                dpg.add_menu_item(label="Toggle Shortcut Key for episode and frame", callback=toggle_bind_key)


        # Load split and scene json toolbar
        with dpg.group(horizontal=True):
            # split selector
            dpg.add_text("Toolbar - Split:", tag='split_hint')
            dpg.add_combo(['train', 'val_seen', 'val_unseen', 'test'], tag='split', \
                default_value=DEFAULT_SPLIT, width=90, callback=load_split_callback)
            # scene selector
            dpg.add_text('By Scene:', tag='scene_hint')
            scene_list = ['None', 1, 2, 3, 4, 5, 8,10, 11, 12, 14, 16, 17, 20, 22, 23, 25, 26]
            dpg.add_combo(scene_list, tag='scene', default_value=DEFAULT_SCENE, width=50) 
            load_json()
            # Load button
            dpg.add_button(callback=load_json_callback, label="Load", tag='load_btn')
            # episode_idx selector
            dpg.add_text('| State: Episode')
            dpg.add_text(DEFAULT_EPISODE_IDX, tag='episode_idx')
            dpg.add_text('/{}'.format(len(episodes)), tag='len_episodes')
            dpg.add_button(arrow=True, direction=dpg.mvDir_Left, callback=idx_callback,\
                 user_data=['minus', 'episodes'])
            dpg.add_drag_int(width=50, default_value=DEFAULT_EPISODE_IDX, callback=idx_callback, min_value=1, max_value=len(episodes),\
                 user_data=['drag', 'episodes'], tag='drag_int_episodes')
            dpg.add_button(arrow=True, direction=dpg.mvDir_Right, callback=idx_callback,\
                 user_data=['plus', 'episodes'])
            # frame_idx selector
            dpg.add_text('Frame')
            dpg.add_text(DEFAULT_FRAME_IDX, tag='frame_idx')
            dpg.add_text('/{}'.format(episodes[DEFAULT_EPISODE_IDX-1]['len_frames']), tag='len_frames')
            dpg.add_button(arrow=True, direction=dpg.mvDir_Left, callback=idx_callback, \
                 user_data=['minus', 'frames'])
            dpg.add_drag_int(width=90, default_value=DEFAULT_FRAME_IDX, callback=idx_callback, min_value=1,\
                 max_value=episodes[DEFAULT_EPISODE_IDX-1]['len_frames'],\
                 user_data=['drag', 'frames'], tag='drag_int_frames')
            dpg.add_button(arrow=True, direction=dpg.mvDir_Right, callback=idx_callback, \
                 user_data=['plus', 'frames'])


        # picutre loading and registry
        width, height, data, exp = load_imgs(False)
        width_seg, height_seg, data_seg, _ = load_imgs(True)
        # exps = []
        if 'expressions' not in episodes[DEFAULT_EPISODE_IDX-1]:
            episodes[DEFAULT_EPISODE_IDX-1]['expressions'] = []
        for value in exp['expressions'].values():
            # exps.append(value['exp']) 
            episodes[DEFAULT_EPISODE_IDX-1]['expressions'].append(value)
        # picture registry
        with dpg.texture_registry(show=False):
            dpg.add_dynamic_texture(width, height, data, tag="origin_frame")
            dpg.add_dynamic_texture(width_seg, height_seg, data_seg, tag="seg_frame")


        # Main operating Space
        #FIXME
        with dpg.group(horizontal=True):
            # space to show origin and segmentation frames
            with dpg.group():
                dpg.add_image("origin_frame", width=width*FRAME_FACTOR, height=height*FRAME_FACTOR, pos=[ORIGIN_FRAME_OFFSET_X, ORIGIN_FRAME_OFFSET_Y])
                dpg.add_image("seg_frame", width=width*FRAME_FACTOR, height=height*FRAME_FACTOR, pos=[SEG_FRAME_OFFSET_X, SEG_FRAME_OFFSET_Y])
            # space to show instructions, referring expressions highlighted navigation instructions,
            # tranlated navigation instructions and operating logs
            with dpg.group():
                # Insturctions
                instructions = '使用说明：已自动解析表达式，如有部分错误可通过弹窗编辑。可通过方向键或wasd键同时调整视频的episode和frame序号，在对应帧单击一个高亮的表达式，使用单击选定一个或多个segmentation的mask，选定后会自动保存，并在原图显示已选定的mask。'
                dpg.add_text(default_value=instructions, wrap=0)
                # Navigation instructions, parsed referring expression highlighted and translated results
                dpg.add_text('导航指令：' + exp['instruction'], tag='exp', wrap=0)
                dpg.add_text('导航指令翻译：' + exp['instruction_translated'], tag='exp_translated', wrap=0)
                dpg.add_button(label='已解析表达式(存在冗余或不准确, 单击此处进行编辑)：', tag='pop_up_edit_btn')
                with dpg.popup('pop_up_edit_btn', modal=True, mousebutton=dpg.mvMouseButton_Left, tag="pop_edit_panel"):
                    with dpg.group(tag='pop_up_exps'):
                        with dpg.group(tag='pop_up_exps_sub'):
                            for e in episodes[DEFAULT_EPISODE_IDX-1]['expressions']:
                                with dpg.group(horizontal=True, tag=e):
                                    dpg.add_input_text(default_value=e, tag=e+'input', user_data=[e, 'upd'], callback=exps_callback, on_enter=True)
                                    # dpg.add_button(label='Delete', user_data=e, callback=lambda s, a, u: dpg.delete_item(u))
                                    dpg.add_button(label='Delete', tag=e+'delbtn', user_data=[e, 'del', e], callback=exps_callback)
                    dpg.add_separator()
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Save", width=75, user_data=[None, 'save'], callback=exps_callback)
                        dpg.add_button(label="Cancel", width=75, callback=lambda: dpg.configure_item("pop_edit_panel", show=False))
                items = []
                with dpg.group(tag='exps'):
                    with dpg.group(tag='exps_sub'):
                        for e in episodes[DEFAULT_EPISODE_IDX-1]['expressions']:
                            items.append(dpg.add_selectable(label=e))
                    for item in items:
                        dpg.configure_item(item, callback=_selection, user_data=items)
                # Operating logs
                # dpg.add_text("操作日志：")


        # Statusbar for loaded json file
        with dpg.group(horizontal=True, pos=[STATUS_BAR_OFFSET_X, STATUS_BAR_OFFSET_Y]):
            dpg.add_text('Statusbar -')
            dpg.add_text('Split: '+dpg.get_value('split'), tag='split_txt')
            dpg.add_text('Scene_id: '+dpg.get_value('scene'), tag='scene_txt')
            dpg.add_text('Episode_id: '+episodes[DEFAULT_EPISODE_IDX-1]['episode_id'], tag='episode_id')
            dpg.add_text('Trajectory_id: '+episodes[DEFAULT_EPISODE_IDX-1]['trajectory_id'], tag='trajectory_id')
            dpg.add_text('Mouse pos: []', tag='mouse_move')
            dpg.add_text('Shortcut Mode: '+('enabled' if dpg.get_item_callback('bind_key_h') else 'disabled'), tag='shortcut')

    dpg.create_viewport(title='AirVLN Referring Expression Annotation Tool', width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Main software gui launch program\
        for referring expression annotation in aivln dataset with airsim and dearpygui.')
    args = parser.parse_args()
    main(args)
