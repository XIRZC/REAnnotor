# author: mrxirzzz

# internal packages imported
import dearpygui.dearpygui as dpg
import os
import argparse
from pathlib import Path
import json
import cv2
import numpy as np
from json import JSONEncoder

# project packages imported
from utils.episodes import Episodes


# Global Constant and Variables
DEFAULT_SPLIT = 'val_seen'
DEFAULT_SCENE = 3
DEFAULT_EPISODE_IDX = 4
DEFAULT_FRAME_IDX = 1

WIN_FACTOR = 1   # cause my windows has factor 1.5, so need to shrinke resolution
WINDOW_WIDTH, WINDOW_HEIGHT, FRAME_FACTOR = int(1620 / WIN_FACTOR), int(1020 / WIN_FACTOR), int(3 / WIN_FACTOR)
FRAME_WIDTH, FRAME_HEIGHT = 256, 144
EXP_SCROLL_HEIGHT = 230

ORI_FRAME_OFFSET_X, ORI_FRAME_OFFSET_Y = 0, 70
SEG_FRAME_OFFSET_X, SEG_FRAME_OFFSET_Y = 0, 520
STATUS_BAR_OFFSET_X, STATUS_BAR_OFFSET_Y = 5, WINDOW_HEIGHT - 65

ORI_FRAME_END_X, ORI_FRAME_END_Y = ORI_FRAME_OFFSET_X + FRAME_WIDTH * FRAME_FACTOR, ORI_FRAME_OFFSET_Y + FRAME_HEIGHT * FRAME_FACTOR
SEG_FRAME_END_X, SEG_FRAME_END_Y = SEG_FRAME_OFFSET_X + FRAME_WIDTH * FRAME_FACTOR, SEG_FRAME_OFFSET_Y + FRAME_HEIGHT * FRAME_FACTOR

MASK_BY_COLOR = False
USE_THRESHOLD = False
SEG_SIM_THRESHOLD = 4
MULTILINE_WORD_COUNT = 10

episodes = None
mouse_point = []
selectable_item_exp = ''
raw_data_ori, raw_data_seg = [], []


# Json load and write functions
def write_json():
    split = dpg.get_value('split')
    scene = dpg.get_value('scene') if dpg.get_value('scene') != 'None' else None 
    with open('annotations/{}/{}_seg.json'.format(split, scene), mode='w+') as f:
        try:
            json.dump({'episodes': episodes}, f, indent=4, cls=NumpyArrayEncoder)
            print('Write to json file!')
            dpg.set_value('save_status', 'Save into json success!')
            dpg.configure_item('save_success_modal', show=True)
        except:
            dpg.set_value('save_status', 'Save into json failed!')
            dpg.configure_item('save_success_modal', show=True)
def load_json_callback(sender, app_data, user_data):
    if sender is not None:
        # save all the staged episodes operations
        write_json()
        # load new json to episodes and generate new file IO object
        load_json()
        idx_callback(sender, app_data, ['set', 'episodes', 1])
    else:  # manually invoke
        load_json()
        idx_callback(sender, app_data, ['set', 'episodes', DEFAULT_EPISODE_IDX])
def load_json():
    split = dpg.get_value('split')
    scene = dpg.get_value('scene') if dpg.get_value('scene') != 'None' else None 
    global episodes
    # for epi in episodes:
    #     epi['expressions'] = []  # list of referring expressions
    #     epi['frames'] = []   # list of dict(key: expression, value: corresponding mask ndarray)
    if os.path.exists('annotations/{}/{}_seg.json'.format(split, scene)):
        with open('annotations/{}/{}_seg.json'.format(split, scene), mode='r') as f:
            content = f.read()
            if content:
                episodes = json.loads(content)['episodes']
            else:   # not file.close so no content in the json file
                episodes = Episodes(split, scene=scene, only_json=True).get_episodes()
    else:
        episodes = Episodes(split, scene=scene, only_json=True).get_episodes()
        with open('annotations/{}/{}_seg.json'.format(split, scene), mode='w+') as f:
            json.dump({'episodes': episodes}, f, indent=4)
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


# load img and expression annotation function
def load_imgexpmasks():
    episode_idx, frame_idx = int(dpg.get_value('episode_idx')), int(dpg.get_value('frame_idx'))
    scene = dpg.get_value('scene')
    split = dpg.get_value('split')
    ori_img_dir = Path('.').resolve() / 'data' / split / 'origin'
    seg_img_dir = Path('.').resolve() / 'data' / split / 'seg'
    trajectory_id = episodes[episode_idx-1]['trajectory_id']
    episode_id = episodes[episode_idx-1]['episode_id']
    # load pictures
    global raw_data_ori, raw_data_seg
    # width, height, _, data_ori = dpg.load_image('{}/{:02d}_{}_{}/{:03d}.jpg'.format(str(ori_img_dir),\
    #     int(scene), trajectory_id, episode_id, frame_idx-1))
    ori_img_name = '{}/{:02d}_{}_{}/{:03d}.jpg'.format(str(ori_img_dir),\
        int(scene), trajectory_id, episode_id, frame_idx-1)
    seg_img_name = '{}/{:02d}_{}_{}/{:03d}.jpg'.format(str(seg_img_dir),\
        int(scene), trajectory_id, episode_id, frame_idx-1)
    raw_data_ori = cv2.cvtColor(cv2.imread(ori_img_name), cv2.COLOR_BGR2RGB)
    dpg.set_value('ori_frame', raw_data_ori.astype(np.float32) / 255)
    # _, _, _, data_seg = dpg.load_image('{}/{:02d}_{}_{}/{:03d}.jpg'.format(str(seg_img_dir),\
    #     int(scene), trajectory_id, episode_id, frame_idx-1))
    raw_data_seg = cv2.cvtColor(cv2.imread(seg_img_name), cv2.COLOR_BGR2RGB)
    # print_img_data(raw_data_seg)
    dpg.set_value('seg_frame', raw_data_seg.astype(np.float32) / 255)

    # load exps
    with (ori_img_dir / '{:02d}_{}_{}'.format(int(scene), trajectory_id, episode_id) / 'expressions.json').open() as f:
        exp = json.loads(f.read())
    dpg.set_value('instruction', exp['instruction'])
    dpg.set_value('instruction_translated', exp['instruction_translated'])
    # update expressions json data into episodes
    if 'expressions' not in episodes[episode_idx-1]:
        episodes[episode_idx-1]['expressions'] = exp['expressions']

    # load mask and convert to npndarray
    # multidim python list -> nparray for show, add and delete
    if 'frames' in episodes[episode_idx-1]:
        for dic_key in episodes[episode_idx-1]['frames'][frame_idx-1]:
            episodes[episode_idx-1]['frames'][frame_idx-1][dic_key] = np.asarray(episodes[episode_idx-1]['frames'][frame_idx-1][dic_key])
    return  raw_data_ori, raw_data_seg, exp


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
        else: # set to value
            idx = user_data[2]
        dpg.set_value('drag_int_' + obj, idx)
        return idx
    if obj == 'episodes':
        global selectable_item_exp
        selectable_item_exp = ''
        episode_idx = op(episode_idx, mode)
        frame_idx = 1
        dpg.set_value('episode_idx', episode_idx) 
        dpg.set_value('frame_idx', frame_idx)
        dpg.set_value('drag_int_frames', frame_idx)
        dpg.set_value('len_episodes', '/' + str(len(episodes)))
        dpg.set_value('len_frames', '/' + str(episodes[episode_idx-1]['len_frames']))
        dpg.set_value('episode_id', 'Episode: '+episodes[episode_idx-1]['episode_id'])
        dpg.set_value('trajectory_id', 'Trajectory: '+episodes[episode_idx-1]['trajectory_id'])
        dpg.configure_item('drag_int_episodes', max_value=len(episodes))
        load_imgexpmasks()
        exps_show_callback(sender, app_data, user_data)
    elif obj == 'frames':
        frame_idx = op(frame_idx, mode)
        dpg.set_value('frame_idx', frame_idx)
        dpg.set_value('len_episodes', '/' + str(len(episodes)))
        dpg.set_value('len_frames', '/' + str(episodes[episode_idx-1]['len_frames']))
        dpg.configure_item('drag_int_frames', max_value=episodes[episode_idx-1]['len_frames'])
        load_imgexpmasks()
    else:
        raise ValueError('Not supported object:{} for {}'.format(obj, mode))


# expression show and add/upd/del functions
def exps_show_callback(sender, app_data, user_data):
    episode_idx = int(dpg.get_value('episode_idx'))
    _, _, exp = load_imgexpmasks()
    # update exps show selectable list
    items = []
    dpg.delete_item('exps_sub')
    with dpg.group(tag='exps_sub', parent='exps'):
        with dpg.child_window(height=EXP_SCROLL_HEIGHT, delay_search=True):
            for e in episodes[episode_idx-1]['expressions'].values():
                items.append(dpg.add_selectable(label=e))
    for item in items:
        dpg.configure_item(item, callback=exp_select_callback, user_data=items)
    # update popup exps edit panel
    dpg.delete_item('pop_up_exps_sub')
    with dpg.group(tag='pop_up_exps_sub', parent='pop_up_exps'):
        ins = exp['instruction']
        ins_multiline = ''
        for i, ins_word in enumerate(ins.split()):
            ins_multiline += ins_word + ' '
            if (i + 1) % MULTILINE_WORD_COUNT == 0:
                ins_multiline += '\n'
        dpg.add_input_text(default_value=ins_multiline, tag='ins_multiline', multiline=True, readonly=True, width=-1)
        for e_id, e in episodes[episode_idx-1]['expressions'].items():
            with dpg.group(horizontal=True, tag=e_id):
                dpg.add_input_text(default_value=e, tag=e_id+'input', user_data=[e_id, 'upd'], callback=exps_operation)
                dpg.add_button(label='Add', tag=e_id+'addbtn', user_data=[e_id, 'add'], callback=exps_operation)
                dpg.add_button(label='Delete', tag=e_id+'delbtn', user_data=[e_id, 'del'], callback=exps_operation)
        dpg.add_text('注意：仅能在上方插入新的空表达式，编辑操作实时保存,可复制导航指令并在编辑框中粘贴', wrap=0, color=(255, 255, 0))
def exps_operation(sender, app_data, user_data):
    def upd_exps_dict_id():
        n_dic = dict()
        for i, e in enumerate(episodes[episode_idx-1]['expressions'].values()):
            n_dic[str(i)] = e
        episodes[episode_idx-1]['expressions'] = n_dic
    def exchange_exps_dict(dic, i, j):
        v_i = dic[i]
        v_j = dic[j]
        dic[i] = v_j
        dic[j] = v_i
    # def log():
    #     for i in episodes[episode_idx-1]['expressions']:
    #         print(type(i), i)
    e_id, mode = user_data[0], user_data[1]
    episode_idx = int(dpg.get_value('episode_idx'))
    if mode == 'add':
        # log()
        length = len(episodes[episode_idx-1]['expressions'])
        episodes[episode_idx-1]['expressions'][str(length)] = ''
        # log()
        exchange_exps_dict(episodes[episode_idx-1]['expressions'], str(length), e_id)
        # log()
        # exps_show_callback(sender, app_data, user_data)
        # screen repeat exp
        # sorted(set(episodes[episode_idx-1]['expressions']), key=episodes[episode_idx-1]['expressions'].index)
    elif mode == 'del':
        del episodes[episode_idx-1]['expressions'][e_id]
        upd_exps_dict_id()
        # log()
        # exps_show_callback(sender, app_data, user_data)
    elif mode == 'upd':
        episodes[episode_idx-1]['expressions'][e_id] = dpg.get_value(sender)
        upd_exps_dict_id()
        # log()
        # exps_show_callback(sender, app_data, user_data)
        # sorted(set(episodes[episode_idx-1]['expressions']), key=episodes[episode_idx-1]['expressions'].index)
    else:   # save
        exps_show_callback(sender, app_data, user_data)
        # write_json()
        dpg.configure_item('pop_edit_panel', show=False)
# expression selection function
def exp_select_callback(sender, app_data, user_data):
    global selectable_item_exp
    for item in user_data:
        if item != sender:
            dpg.set_value(item, False)
        else:
            selectable_item_exp = dpg.get_item_configuration(sender)['label']
            print('Now Selected exp are: ', selectable_item_exp)
            mask_show_callback(sender, app_data, user_data)


# mouse action and mask operation function and mask show callback
def mask_show_callback(sender, app_data, user_data):
    episode_idx, frame_idx = int(dpg.get_value('episode_idx')), int(dpg.get_value('frame_idx'))
    load_imgexpmasks()
    if 'frames' in episodes[episode_idx-1]:
        frame_mask_dict =  episodes[episode_idx-1]['frames'][frame_idx-1]
        if selectable_item_exp in frame_mask_dict:
            mask_nparray = frame_mask_dict[selectable_item_exp]
            set_mask(raw_data_ori, mask_nparray)
            dpg.set_value('ori_frame', raw_data_ori.astype(np.float32) / 255)
def mouse_event_handler(sender, data):
    global mouse_point
    type = dpg.get_item_info(sender)["type"]
    if type == "mvAppItemType::mvMouseClickHandler":
        mask_operation('add')
    if type == "mvAppItemType::mvMouseDoubleClickHandler":
        mask_operation('del')
    if type == "mvAppItemType::mvMouseMoveHandler":
        # dpg.set_value('mouse_move', f"Mouse pos: {data}")
        mouse_point = data
def mask_operation(mode):
    episode_idx, frame_idx = int(dpg.get_value('episode_idx')), int(dpg.get_value('frame_idx'))
    if mode == 'add':
        if boundary(mouse_point, SEG_FRAME_OFFSET_X, SEG_FRAME_OFFSET_Y, SEG_FRAME_END_X, SEG_FRAME_END_Y):
            i, j = restore(mouse_point, 'seg')
            print('Clicked at', mouse_point, 'Frame pixel i:{} j:{}'.format(i, j))
            if 'frames' not in episodes[episode_idx-1]:
                episodes[episode_idx-1]['frames'] = init_frames(episodes[episode_idx-1]['len_frames'])
            if MASK_BY_COLOR:
                filtered_mask = get_mask_by_color(raw_data_seg, i, j)
            else:
                filtered_mask = get_mask_by_graph(raw_data_seg, i, j)
            # dpg.set_value('ori_frame', set_mask_for_ori(raw_data_ori, filtered_mask).astype(np.float32) / 255)
            if selectable_item_exp != '':
                if selectable_item_exp in episodes[episode_idx-1]['frames'][frame_idx-1]:
                    set_mask(episodes[episode_idx-1]['frames'][frame_idx-1][selectable_item_exp], filtered_mask)
                else:
                    episodes[episode_idx-1]['frames'][frame_idx-1][selectable_item_exp] = filtered_mask
                mask_show_callback(None, None, None)
    elif mode == 'del':
        if boundary(mouse_point, ORI_FRAME_OFFSET_X, ORI_FRAME_OFFSET_Y, ORI_FRAME_END_X, ORI_FRAME_END_Y):
            i, j = restore(mouse_point, 'ori')
            print('DoubleClicked at', mouse_point, 'Frame pixel i:{} j:{}'.format(i, j))
            if MASK_BY_COLOR:
                filtered_mask = get_mask_by_color(raw_data_seg, i, j)
            else:
                filtered_mask = get_mask_by_graph(raw_data_seg, i, j)
            set_mask(episodes[episode_idx-1]['frames'][frame_idx-1][selectable_item_exp], filtered_mask, mode=='unfill')
            mask_show_callback(None, None, None)
    else:   
        pass
def get_mask_by_color(data, i, j):
    point = data[i, j]
    fill = np.zeros_like(data)
    for a in range(FRAME_HEIGHT):
        for b in range(FRAME_WIDTH):
            if threshold(data[a, b], point, SEG_SIM_THRESHOLD):
                fill[a, b] = point
    return fill
def get_mask_by_graph(data, i, j):
    def bfs(data, i, j):
        import queue
        fill = np.zeros_like(data)
        point = data[i, j]
        di, dj = [1, 0, -1, 0], [0, 1, 0, -1]  # adajecent nodes: down, right, up, left
        q = queue.Queue()
        q.put((i, j))
        fill[i, j] = point
        while not q.empty():
            i, j = q.get()
            for k in range(len(di)):
                ni, nj = i + di[k], j + dj[k]
                if boundary((ni, nj), 0, 0, FRAME_HEIGHT, FRAME_WIDTH):
                    if USE_THRESHOLD:
                        condition = threshold(data[ni, nj], data[i, j], SEG_SIM_THRESHOLD)
                    else:
                        condition = np.array_equal(data[ni, nj], data[i, j])
                    if condition:
                        if np.array_equal(fill[ni, nj], np.zeros(3)):
                            fill[ni, nj] = point
                            q.put((ni, nj))
        return fill
    fill = bfs(data, i, j)
    return fill
def set_mask(data, mask, mode='fill'):
    for i in range(FRAME_HEIGHT):
        for j in range(FRAME_WIDTH):
            if not np.array_equal(mask[i, j], np.zeros(3)):
                if mode == 'fill':
                    data[i, j] = mask[i, j]
                else:  # just cause unfill is always used for mask
                    data[i, j] = np.zeros(3)


# key bind for episode and frame editing functions
def keyboard_event_handler(sender, app_data, user_data):
    # h,l for episode minus and plus, j,k for frame plus and minus, like vim motion bind keys
    if app_data in [ 72, 87, 265 ]: # press h or w or up key
        idx_callback(sender, app_data, ['minus', 'episodes'])
    elif app_data in [ 74, 68, 262 ]: # press j or d or right key
        idx_callback(sender, app_data, ['plus', 'frames'])
    elif app_data in [ 75, 65, 263 ]: # press k or a or left key
        idx_callback(sender, app_data, ['minus', 'frames'])
    elif app_data in [ 76, 83, 264 ]: # press l or s or down key
        idx_callback(sender, app_data, ['plus', 'episodes'])
    elif app_data == 256: # press ESC
        load_imgexpmasks()
        dpg.set_value('ori_frame', raw_data_ori.astype(np.float32) / 255)
    else:
        print('Other key_id: {} pressed!'.format(app_data))
def toggle_bind_key_callback():
    ls = ['h', 'j', 'k', 'l', 'up', 'right', 'left', 'down']
    if dpg.is_key_down(dpg.mvKey_E):
        # print('Press Ctrl E!', dpg.get_item_callback('bind_key_h'))
        for i in ls:
            dpg.configure_item('bind_key_' + i, callback=keyboard_event_handler)
    elif dpg.is_key_down(dpg.mvKey_D):
        # print('Press Ctrl D!', dpg.get_item_callback('bind_key_h'))
        for i in ls:
            dpg.configure_item('bind_key_' + i, callback=None)
    elif dpg.is_key_down(dpg.mvKey_S):
        write_json()
    # dpg.set_value('shortcut', ' Shortcut: '+('enabled' if dpg.get_item_callback('bind_key_h') else 'disabled'))
def toggle_bind_key():
    ls = ['h', 'j', 'k', 'l', 'up', 'right', 'left', 'down']
    for i in ls:
        if dpg.get_item_callback('bind_key_' + i) is None:
            dpg.configure_item('bind_key_' + i, callback=keyboard_event_handler)
        else:
            dpg.configure_item('bind_key_' + i, callback=None)
    # dpg.set_value('shortcut', ' Shortcut Mode: '+('enabled' if dpg.get_item_callback('bind_key_h') else 'disabled'))


# util functions
def boundary(p, ltx, lty, rbx, rby):
    if (p[0] >= ltx and p[0] < rbx) and (p[1] >= lty and p[1] < rby):
        return True
    return False
def threshold(src, dst, th):
    for i in range(len(src)):
        if abs(src[i]-dst[i]) > th:
            return False
    return True
def restore(p, mode):
    if mode == 'seg':
        return [int((p[1] - SEG_FRAME_OFFSET_Y) // FRAME_FACTOR), int((p[0] - SEG_FRAME_OFFSET_X) // FRAME_FACTOR)]
    else: # ori
        return [int((p[1] - ORI_FRAME_OFFSET_Y) // FRAME_FACTOR), int((p[0] - ORI_FRAME_OFFSET_X) // FRAME_FACTOR)]
def print_img_data(data):
    print(data.dtype)
    print(data.shape)
    print(data)
def init_frames(length):
    frames = []
    for _ in range(length):
        frames.append(dict())
    return frames
# popup window for editting expressions callback function
def popup_callback(sender, app_data, user_data):
    print('popup callback')
class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


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
        # dpg.add_key_press_handler(dpg.mvKey_W, callback=keyboard_event_handler, tag='bind_key_w')
        # dpg.add_key_press_handler(dpg.mvKey_D, callback=keyboard_event_handler, tag='bind_key_d')
        # dpg.add_key_press_handler(dpg.mvKey_A, callback=keyboard_event_handler, tag='bind_key_a')
        # dpg.add_key_press_handler(dpg.mvKey_S, callback=keyboard_event_handler, tag='bind_key_s')
        dpg.add_key_press_handler(dpg.mvKey_Up, callback=keyboard_event_handler, tag='bind_key_up')
        dpg.add_key_press_handler(dpg.mvKey_Right, callback=keyboard_event_handler, tag='bind_key_right')
        dpg.add_key_press_handler(dpg.mvKey_Left, callback=keyboard_event_handler, tag='bind_key_left')
        dpg.add_key_press_handler(dpg.mvKey_Down, callback=keyboard_event_handler, tag='bind_key_down')
        dpg.add_key_press_handler(dpg.mvKey_Escape, callback=keyboard_event_handler, tag='bind_key_esc')
        dpg.add_mouse_click_handler(tag='mouse_clicked_handler', callback=mouse_event_handler)
        dpg.add_mouse_double_click_handler(tag='mouse_doubelclicked_handler', callback=mouse_event_handler)
        dpg.add_mouse_move_handler(tag='mouse_move_handler', callback=mouse_event_handler)



    # Main window for UI
    with dpg.window(label="AirVLN Referring Expression 标注工具", width=WINDOW_WIDTH, height=WINDOW_HEIGHT, no_collapse=True, no_title_bar=True, no_move=True, tag='main_window'):

        dpg.bind_font(font1)

        # Menu bar settings
        #TODO
        with dpg.menu_bar():
            with dpg.menu(label="Menu"):
                # dpg.add_menu_item(label="Load json file", callback=load_json)
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
        with dpg.group(horizontal=True, tag='toolbar'):
            # split selector
            dpg.add_text("Toolbar - Split:", tag='split_hint')
            dpg.add_combo(['train', 'val_seen', 'val_unseen', 'test'], tag='split', \
                default_value=DEFAULT_SPLIT, width=90, callback=load_split_callback)
            # scene selector
            dpg.add_text('By Scene:', tag='scene_hint')
            scene_list = ['None', 1, 2, 3, 4, 5, 8,10, 11, 12, 14, 16, 17, 20, 22, 23, 25, 26]
            dpg.add_combo(scene_list, tag='scene', default_value=DEFAULT_SCENE, width=50) 
            # Load button
            dpg.add_button(callback=load_json_callback, label="Load", tag='load_btn')
            # episode_idx selector
            dpg.add_text('| State: Episode')
            dpg.add_text(DEFAULT_EPISODE_IDX, tag='episode_idx')
            dpg.add_text('', tag='len_episodes')
            dpg.add_button(arrow=True, direction=dpg.mvDir_Left, callback=idx_callback,\
                 user_data=['minus', 'episodes'])
            dpg.add_drag_int(width=50, default_value=DEFAULT_EPISODE_IDX, callback=idx_callback, min_value=1,\
                 user_data=['drag', 'episodes'], tag='drag_int_episodes')
            dpg.add_button(arrow=True, direction=dpg.mvDir_Right, callback=idx_callback,\
                 user_data=['plus', 'episodes'])
            # frame_idx selector
            dpg.add_text('Frame')
            dpg.add_text(DEFAULT_FRAME_IDX, tag='frame_idx')
            dpg.add_text('', tag='len_frames')
            dpg.add_button(arrow=True, direction=dpg.mvDir_Left, callback=idx_callback, \
                 user_data=['minus', 'frames'])
            dpg.add_drag_int(width=90, default_value=DEFAULT_FRAME_IDX, callback=idx_callback, min_value=1,\
                 user_data=['drag', 'frames'], tag='drag_int_frames')
            dpg.add_button(arrow=True, direction=dpg.mvDir_Right, callback=idx_callback, \
                 user_data=['plus', 'frames'])


        # Origin and segmentation frames show and operation space
        texture_data = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), np.float32)
        with dpg.texture_registry(show=False):
            dpg.add_raw_texture(FRAME_WIDTH, FRAME_HEIGHT, texture_data, format=dpg.mvFormat_Float_rgb, tag="ori_frame")
            dpg.add_raw_texture(FRAME_WIDTH, FRAME_HEIGHT, texture_data, format=dpg.mvFormat_Float_rgb, tag="seg_frame")


        # Instruction, translated, expressions show and edit space
        #FIXME
        with dpg.group(horizontal=True):
            # space to show origin and segmentation frames
            with dpg.group():
                dpg.add_image("ori_frame", width=FRAME_WIDTH*FRAME_FACTOR, height=FRAME_HEIGHT*FRAME_FACTOR, pos=[ORI_FRAME_OFFSET_X, ORI_FRAME_OFFSET_Y])
                dpg.add_image("seg_frame", width=FRAME_WIDTH*FRAME_FACTOR, height=FRAME_HEIGHT*FRAME_FACTOR, pos=[SEG_FRAME_OFFSET_X, SEG_FRAME_OFFSET_Y])
            # space to show instructions, referring expressions highlighted navigation instructions,
            # tranlated navigation instructions and operating logs
            with dpg.group():
                # Insturctions
                with dpg.tree_node(tag='user_instruction', label='使用说明'):
                    with dpg.tree_node(label='准备事项'):
                        dpg.add_text("1. 运行scripts/stscene.sh打开场景", wrap=0)
                        dpg.add_text("2. 运行scripts/save_imgs.sh(需修改对应split、scene和保存路径)保存需要的图片和表达式信息", wrap=0)
                    with dpg.tree_node(label='使用事项'):
                        dpg.add_text("通过工具栏选定split和scene(第2步一致)后Load图片和表达式信息", wrap=0, bullet=True)
                        dpg.add_text("通过方向键或工具栏中拖动栏控制episode和frame序号来调整左侧原图和segmentation图", wrap=0, bullet=True)
                        dpg.add_text("在左下方segmentation图单击任一mask任一点对当前帧当前表达式添加mask并在原图显示", wrap=0, bullet=True)
                        dpg.add_text("在左上方原图双击任一mask任一点来删除当前选定表达式的mask", wrap=0, bullet=True)
                        dpg.add_text("可通过点击任一表达式来在原图中查看当前帧该表达式已添加的mask, ESC键清除原图mask", wrap=0, bullet=True)
                        dpg.add_text("可通过表达式选择列表上方的编辑按钮对不正确表达式进行修改和删除", wrap=0, bullet=True)
                        dpg.add_text("下方状态栏显示当前界面所在的episode_id、trajectory_id和scene_id等状态信息", wrap=0, bullet=True)
                        dpg.add_text("可通过Ctrl+E打开快捷键模式，Ctrl+D关闭快捷键模式，可在下方状态栏看到当前快捷键模式状态", wrap=0, bullet=True)
                    with dpg.tree_node(label='注意事项'):
                        dpg.add_text("关闭软件前按Ctrl+S进行保存！", bullet=True)
                        dpg.add_text("在弹出窗口编辑或删除完表达式后，需通过保存按钮关闭！", bullet=True)
                # Navigation instructions, parsed referring expression highlighted and translated results
                with dpg.group():
                    dpg.add_text('导航指令：', color=(255, 0, 0))
                    dpg.add_text('', tag='instruction', wrap=0)
                with dpg.group():
                    dpg.add_text('导航指令翻译：', color=(255, 0, 0))
                    dpg.add_text('', tag='instruction_translated', wrap=0)
                with dpg.group(horizontal=True):
                    dpg.add_text('已解析表达式(存在冗余或不准确)', color=(0, 255, 0))
                    dpg.add_button(label='编辑', tag='pop_up_edit_btn', callback=popup_callback)
                # dpg.add_button(label='button', callback=popup_callback)
                with dpg.popup('pop_up_edit_btn', modal=True, tag="save_success_modal", no_move=True):
                    dpg.add_text('Save into json success!', tag='save_status')
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Okay", width=75, callback=lambda: dpg.configure_item("save_success_modal", show=False))
                with dpg.popup('pop_up_edit_btn', modal=True, mousebutton=dpg.mvMouseButton_Left, tag="pop_edit_panel"):
                    with dpg.group(tag='pop_up_exps'):
                        with dpg.group(tag='pop_up_exps_sub'):
                            pass
                    dpg.add_separator()
                    with dpg.group(horizontal=True, tag='btnlist'):
                        dpg.add_button(label="Save", width=75, tag='savebtn', user_data=[None, 'save'], callback=exps_operation, parent='btnlist')
                        dpg.add_button(label="Cancel", width=75, tag='clcbtn', callback=lambda: dpg.configure_item("pop_edit_panel", show=False), parent='btnlist')
                    dpg.set_item_pos('pop_edit_panel', [780, 350])
                with dpg.group(tag='exps'):
                    with dpg.group(tag='exps_sub'):
                        pass
                # Operating logs
                # dpg.add_text("操作日志：")


        # Statusbar for loaded json file
        with dpg.group(horizontal=True, pos=[STATUS_BAR_OFFSET_X, STATUS_BAR_OFFSET_Y], tag='statusbar'):
            # dpg.add_text('Statusbar -')
            dpg.add_text('', tag='episode_id')
            dpg.add_text('', tag='trajectory_id')
            dpg.add_text('', tag='mouse_move')
            # dpg.add_text('Shortcut: enabled', tag='shortcut')
        
        # load_json_callback for default split, scene, episode_idx, frame_idx
        load_json_callback(None, None, None)

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
