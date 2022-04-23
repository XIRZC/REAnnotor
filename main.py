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
import math
import random

# project packages imported

DVC = 'WIN'

# Global Constant and Variables
DEFAULT_SPLIT = 'val_seen'
DEFAULT_SCENE = 3
DEFAULT_EPISODE_IDX = 4
DEFAULT_FRAME_IDX = 1

if DVC == 'WIN':
    WIN_FACTOR = 1.25   # cause my windows has factor 1.5, so need to shrinke resolution  
else:
    WIN_FACTOR = 1  # linux adaption
WINDOW_WIDTH, WINDOW_HEIGHT, FRAME_FACTOR = int(1650 / WIN_FACTOR), int(1050 / WIN_FACTOR), 3 / WIN_FACTOR
FRAME_WIDTH, FRAME_HEIGHT = 256, 144

EXP_SCROLL_HEIGHT = 180 / WIN_FACTOR
EXP_POPUP_SCROLL_HEIGHT = 250 / WIN_FACTOR
INS_SCROLL_HEIGHT = 120 / WIN_FACTOR
INST_SCROLL_HEIGHT = 100 / WIN_FACTOR

ORI_FRAME_OFFSET_X, ORI_FRAME_OFFSET_Y = 0, 75 / WIN_FACTOR
SEG_FRAME_OFFSET_X, SEG_FRAME_OFFSET_Y = 0, 515 / WIN_FACTOR
STATUS_BAR_OFFSET_X, STATUS_BAR_OFFSET_Y = 5, WINDOW_HEIGHT - 60 * math.pow(WIN_FACTOR, 4/3)

ORI_FRAME_END_X, ORI_FRAME_END_Y = ORI_FRAME_OFFSET_X + FRAME_WIDTH * FRAME_FACTOR, ORI_FRAME_OFFSET_Y + FRAME_HEIGHT * FRAME_FACTOR
SEG_FRAME_END_X, SEG_FRAME_END_Y = SEG_FRAME_OFFSET_X + FRAME_WIDTH * FRAME_FACTOR, SEG_FRAME_OFFSET_Y + FRAME_HEIGHT * FRAME_FACTOR

SEG_SIM_THRESHOLD = 4
MULTILINE_WORD_COUNT = 14
MASK_BACKGROUND_COLOR = [0, 0, 0]  # used for mask whose color is not black, and useful for mask and origin fusion
MASK_FOREGROUND_COLOR = [255, 255, 255] # used for mask whose color is black, substitute black
FUSION_FACTOR = 0.5
GRAY_THRESHOLD = 127
COLORS = [[247,247,9], [34,109,221], [150,17,238], [56,247,9], [230,26,26]]

episodes = None
mouse_point = []
selectable_item_exp, items = '', []
raw_data_ori, raw_data_seg = [], []
save_split, save_scene = -1, -1
theme = 'light'


# Json load and write functions
def write_json():
    global episodes
    with open('annotations/{}/{}_seg.json'.format(save_split, save_scene), mode='w+') as f:
        try:
            dpg.configure_item('saving_indicator_group', show=True)
            json.dump({'episodes': episodes}, f, cls=NumpyArrayEncoder)
            dpg.configure_item('saving_indicator_group', show=False)
            # dpg.set_value('save_status_txt', 'Save into annotations/{}/{}_seg.json success!'.format(save_split, save_scene))
            # dpg.configure_item('save_status_modal', show=True)
        except:
            episodes = None
            dpg.configure_item('saving_indicator_group', show=False)
            dpg.set_value('save_status_txt', 'Save into annotations/{}/{}_seg.json failed!'.format(save_split, save_scene))
            dpg.configure_item('save_status_modal', show=True)
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
    def load_scene(split, scene):
        root_path = Path(__file__).resolve().parent
        anno_path = root_path / 'annotations'
        scene_path = anno_path / split / (scene + '.json')
        data = dict()
        with scene_path.open(mode='r') as f:
            data = json.load(f)
        episodes = data['episodes']
        for episode in episodes:
            episode['len_frames'] = len(episode['reference_path'])
        return episodes
    split = dpg.get_value('split')
    scene = dpg.get_value('scene') if dpg.get_value('scene') != 'None' else None 
    global save_split, save_scene
    save_split, save_scene = split, scene
    dpg.set_value('split_txt', 'Split: ' + save_split)
    dpg.set_value('scene_txt', 'Scene: ' + save_scene)
    global episodes
    # for epi in episodes:
    #     epi['expressions'] = []  # list of referring expressions
    #     epi['frames'] = []   # list of dict(key: expression, value: corresponding mask ndarray)
    dpg.configure_item('loading_indicator_group', show=True)
    if os.path.exists('annotations/{}/{}_seg.json'.format(save_split, save_scene)):
        with open('annotations/{}/{}_seg.json'.format(save_split, save_scene), mode='r') as f:
            content = json.loads(f.read())['episodes']
            if content:
                episodes = content
                dpg.configure_item('loading_indicator_group', show=False)
            else:   # not file.close so no content in the json file
                try:
                    episodes = load_scene(split, scene)
                    dpg.configure_item('loading_indicator_group', show=False)
                except:
                    episodes = None
                    dpg.set_value('load_status_txt', 'Load annotations/{}/{}_seg.json failed, file does not exists!'.format(save_split, save_scene))
                    dpg.configure_item('load_status_modal', show=True)
                    dpg.configure_item('loading_indicator_group', show=False)
    else:
        # episodes = load_scene(split, scene)
        # # with open('annotations/{}/{}_seg.json'.format(save_split, save_scene), mode='w+') as f:
        # #     json.dump({'episodes': episodes}, f, indent=4)
        # dpg.configure_item('loading_indicator_group', show=False)
        try:
            episodes = load_scene(split, scene)
            # with open('annotations/{}/{}_seg.json'.format(save_split, save_scene), mode='w+') as f:
            #     json.dump({'episodes': episodes}, f, indent=4)
            dpg.configure_item('loading_indicator_group', show=False)
        except:
            episodes = None
            dpg.set_value('load_status_txt', 'Load annotations/{}/{}_seg.json failed, file does not exists!'.format(save_split, save_scene))
            dpg.configure_item('load_status_modal', show=True)
            dpg.configure_item('loading_indicator_group', show=False)
def load_split_callback(sender, app_data):
    split_scene_idx_dict = {}
    split_scene_idx_dict['train'] = [1, 2, 3, 4, 5, 8 ,10 , 11, 12, 14, 16, 17, 20, 22, 23, 25, 26]
    split_scene_idx_dict['val_seen'] = [1, 2, 3, 5, 8, 10, 11, 12, 14, 16, 17, 20, 23, 26]
    split_scene_idx_dict['val_unseen'] = [6, 9, 13, 24]
    split_scene_idx_dict['test'] = [7, 15, 18, 21]
    split = dpg.get_value(sender)
    # scene_list = ['None']
    scene_list = []
    for idx in split_scene_idx_dict[split]:
        scene_list.append(idx)
    dpg.configure_item('scene', items=scene_list) 
    dpg.set_value('scene', scene_list[0])


# load img and expression annotation function
def load_imgexpmasks(mode=''):
    global episodes
    episode_idx, frame_idx = int(dpg.get_value('episode_idx')), int(dpg.get_value('frame_idx'))
    ori_img_dir = Path('.').resolve() / 'data' / save_split / 'origin'
    seg_img_dir = Path('.').resolve() / 'data' / save_split / 'seg'
    trajectory_id = episodes[episode_idx-1]['trajectory_id']
    episode_id = episodes[episode_idx-1]['episode_id']

    # load mask and convert to npndarray
    # multidim python list -> nparray for show, add and delete
    if 'frames' in episodes[episode_idx-1]:
        for dic_key in episodes[episode_idx-1]['frames'][frame_idx-1]:
            # episodes[episode_idx-1]['frames'][frame_idx-1][dic_key] = np.asarray(episodes[episode_idx-1]['frames'][frame_idx-1][dic_key])
            contours = episodes[episode_idx-1]['frames'][frame_idx-1][dic_key]
            for i in range(len(contours)):
                contours[i] = np.asarray(contours[i])

    # load pictures
    global raw_data_ori, raw_data_seg
    # width, height, _, data_ori = dpg.load_image('{}/{:02d}_{}_{}/{:03d}.jpg'.format(str(ori_img_dir),\
    #     int(scene), trajectory_id, episode_id, frame_idx-1))
    ori_img_name = '{}/{:02d}_{}_{}/{:03d}.jpg'.format(str(ori_img_dir),\
        int(save_scene), trajectory_id, episode_id, frame_idx-1)
    seg_img_name = '{}/{:02d}_{}_{}/{:03d}.jpg'.format(str(seg_img_dir),\
        int(save_scene), trajectory_id, episode_id, frame_idx-1)
    try:
        raw_data_ori = cv2.cvtColor(cv2.imread(ori_img_name), cv2.COLOR_BGR2RGB)
    except:
        dpg.set_value('load_status_txt', 'Load data/{}/{:02d}_{}_{} failed, dir does not exists!'.format(save_split, int(save_scene), trajectory_id, episode_id))
        dpg.configure_item('load_status_modal', show=True)
    if dpg.get_value('eval_mode_txt').split()[1] == 'enabled' and mode != 'single_show':
        eval_enable()
    else:
        dpg.set_value('ori_frame', raw_data_ori.astype(np.float32) / 255)
    # _, _, _, data_seg = dpg.load_image('{}/{:02d}_{}_{}/{:03d}.jpg'.format(str(seg_img_dir),\
    #     int(scene), trajectory_id, episode_id, frame_idx-1))
    try:
        raw_data_seg = cv2.cvtColor(cv2.imread(seg_img_name), cv2.COLOR_BGR2RGB)
    except:
        dpg.set_value('load_status_txt', 'Load data/{}/{:02d}_{}_{} failed, dir does not exists!'.format(save_split, int(save_scene), trajectory_id, episode_id))
        dpg.configure_item('load_status_modal', show=True)
    dpg.set_value('seg_frame', raw_data_seg.astype(np.float32) / 255)
    # load exps
    try:
        with (ori_img_dir / '{:02d}_{}_{}'.format(int(save_scene), trajectory_id, episode_id) / 'expressions.json').open() as f:
            exp = json.loads(f.read())
        dpg.set_value('instruction', exp['instruction'])
        dpg.set_value('instruction_translated', exp['instruction_translated'])
        # update expressions json data into episodes
        if 'expressions' not in episodes[episode_idx-1]:
            episodes[episode_idx-1]['expressions'] = exp['expressions']
    except:
        dpg.set_value('load_status_txt', 'Load data/{}/{:02d}_{}_{} failed, dir does not exists!'.format(save_split, int(save_scene), trajectory_id, episode_id))
        dpg.configure_item('load_status_modal', show=True)

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
        dpg.set_value('episode_id', 'Episode_ID: '+episodes[episode_idx-1]['episode_id'])
        dpg.set_value('trajectory_id', 'Trajectory_ID: '+episodes[episode_idx-1]['trajectory_id'])
        dpg.configure_item('drag_int_episodes', max_value=len(episodes))
        load_imgexpmasks()
        exps_show_callback(sender, app_data, True)
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
    global items
    items = []
    dpg.delete_item('exps_sub')
    with dpg.group(tag='exps_sub', parent='exps'):
        with dpg.child_window(height=EXP_SCROLL_HEIGHT, delay_search=True, tag='exp_scroll'):
            for e in episodes[episode_idx-1]['expressions'].values():
                items.append(dpg.add_selectable(label=e))
    for item in items:
        dpg.configure_item(item, callback=exp_select_callback)
    # update popup exps edit panel
    if user_data:
        ins = exp['instruction']
        ins_multiline = ''
        for i, ins_word in enumerate(ins.split()):
            ins_multiline += ins_word + ' '
            if (i + 1) % MULTILINE_WORD_COUNT == 0:
                ins_multiline += '\n'
        dpg.set_value('ins_multiline', ins_multiline)
    dpg.delete_item('pop_up_exps_sub')
    with dpg.group(tag='pop_up_exps_sub', parent='pop_up_exps'):
        with dpg.child_window(height=EXP_POPUP_SCROLL_HEIGHT, width=600, delay_search=True, tag='exp_popup_scroll'):
            dpg.add_text('注：所有编辑操作完成后需确认,可复制粘贴', wrap=0, color=(255, 0, 0))
            for e_id, e in episodes[episode_idx-1]['expressions'].items():
                with dpg.group(horizontal=True, tag=e_id):
                    dpg.add_input_text(default_value=e, tag=e_id+'input', user_data=[e_id, 'upd'], callback=exps_operation)
                    dpg.add_button(label='上插入', tag=e_id+'addbtnabove', user_data=[e_id, 'add', 'above'], callback=exps_operation)
                    dpg.add_button(label='下插入', tag=e_id+'addbtnbelow', user_data=[e_id, 'add', 'below'], callback=exps_operation)
                    dpg.add_button(label='删除', tag=e_id+'delbtn', user_data=[e_id, 'del'], callback=exps_operation)
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
    def log():
        for id, exp in episodes[episode_idx-1]['expressions'].items():
            print(id, exp)
    e_id, mode = int(user_data[0]) if user_data[0] else user_data[0], user_data[1]
    episode_idx = int(dpg.get_value('episode_idx'))
    if mode == 'add':
        loc = user_data[2]
        # log()
        if loc == 'below':
            e_id += 1
        length = len(episodes[episode_idx-1]['expressions'])
        episodes[episode_idx-1]['expressions'][str(length)] = ''
        # log()
        for i in range(length, e_id, -1):
            episodes[episode_idx-1]['expressions'][str(i)] = episodes[episode_idx-1]['expressions'][str(i-1)]
        episodes[episode_idx-1]['expressions'][str(e_id)] = ''
        # log()
        exps_show_callback(sender, app_data, user_data)
        # screen repeat exp
        # sorted(set(episodes[episode_idx-1]['expressions']), key=episodes[episode_idx-1]['expressions'].index)
    elif mode == 'del':
        del episodes[episode_idx-1]['expressions'][str(e_id)]
        upd_exps_dict_id()
        # log()
        exps_show_callback(sender, app_data, user_data)
    elif mode == 'upd':
        episodes[episode_idx-1]['expressions'][str(e_id)] = dpg.get_value(sender)
        upd_exps_dict_id()
        # log()
        # exps_show_callback(sender, app_data, user_data)
        # sorted(set(episodes[episode_idx-1]['expressions']), key=episodes[episode_idx-1]['expressions'].index)
    else:   # save
        exps_show_callback(sender, app_data, user_data)
        # write_json()
        dpg.configure_item('pop_edit_panel', show=False)
        for item in dpg.get_item_children('key_event_handler', 1):
            dpg.set_item_callback(item, key_event_handler)
        for item in dpg.get_item_children('mouse_event_handler', 1):
            dpg.set_item_callback(item, mouse_event_handler)
# expression selection function
def exp_select_callback(sender, app_data, user_data):
    global selectable_item_exp
    for item in items:
        if item != sender:
            dpg.set_value(item, False)
        else:
            selectable_item_exp = dpg.get_item_configuration(sender)['label']
            mask_show_callback(sender, app_data, user_data)


# mouse action and mask operation function and mask show callback
def mask_show_callback(sender, app_data, user_data):
    global raw_data_ori
    episode_idx, frame_idx = int(dpg.get_value('episode_idx')), int(dpg.get_value('frame_idx'))
    load_imgexpmasks('single_show')
    if 'frames' in episodes[episode_idx-1]:
        frame_mask_dict =  episodes[episode_idx-1]['frames'][frame_idx-1]
        if selectable_item_exp in frame_mask_dict:
            color = COLORS[random.randint(0, 4)]
            contours = frame_mask_dict[selectable_item_exp]
            # set_mask(raw_data_ori, mask_nparray)
            bk = np.zeros_like(raw_data_ori)
            bk = cv2.drawContours(bk, contours, -1, color, -1)
            raw_data_ori = cv2.addWeighted(raw_data_ori, 1, bk.astype(np.uint8), FUSION_FACTOR, 0)
            # raw_data_ori = cv2.drawContours(raw_data_ori, contours, -1, color, -1)
            dpg.set_value('ori_frame', raw_data_ori.astype(np.float32) / 255)
def eval_enable():
    global raw_data_ori
    episode_idx, frame_idx = int(dpg.get_value('episode_idx')), int(dpg.get_value('frame_idx'))
    dpg.delete_item('exps_masked_sub')
    with dpg.group(tag='exps_masked_sub', horizontal=True, parent='exps_masked'):
        if 'frames' in episodes[episode_idx-1]:
            frame_mask_dict =  episodes[episode_idx-1]['frames'][frame_idx-1]
            color_id = 0
            ids = [0, 1, 2, 3, 4]
            random.shuffle(ids)
            for exp, contours in frame_mask_dict.items():
                color = COLORS[ids[color_id]]
                # set_mask(raw_data_ori, mask_nparray)
                # raw_data_ori = cv2.addWeighted(raw_data_ori, 1, mask_nparray.astype(np.uint8), FUSION_FACTOR, 0)
                dpg.add_text(exp, color=color)
                bk = np.zeros_like(raw_data_ori)
                bk = cv2.drawContours(bk, contours, -1, color, -1)
                raw_data_ori = cv2.addWeighted(raw_data_ori, 1, bk.astype(np.uint8), FUSION_FACTOR, 0)
                # raw_data_ori = cv2.drawContours(raw_data_ori, contours, -1, color, -1)
                color_id += 1
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
            color = raw_data_seg[i, j].tolist()
            # substitute black by foreground color
            if np.array_equal(color, np.array(MASK_BACKGROUND_COLOR)):
                filtered_mask = get_mask_by_graph(raw_data_seg, i, j, mode='subs')
            else:
                filtered_mask = get_mask_by_graph(raw_data_seg, i, j)

            mask_gray = cv2.cvtColor(filtered_mask, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(mask_gray, GRAY_THRESHOLD, 255, 0)
            contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            # cv2.imwrite('polyimage.jpg', cv2.drawContours(filtered_mask, [contours[0]], 0, (0, 255, 255), -1))

            # dpg.set_value('ori_frame', set_mask_for_ori(raw_data_ori, filtered_mask).astype(np.float32) / 255)
            if selectable_item_exp != '':
                if selectable_item_exp in episodes[episode_idx-1]['frames'][frame_idx-1]:
                    if not contour_contains(episodes[episode_idx-1]['frames'][frame_idx-1][selectable_item_exp], contours[0]):
                        episodes[episode_idx-1]['frames'][frame_idx-1][selectable_item_exp].append(contours[0])
                        # set_mask(episodes[episode_idx-1]['frames'][frame_idx-1][selectable_item_exp], filtered_mask)
                else:
                    episodes[episode_idx-1]['frames'][frame_idx-1][selectable_item_exp] = [contours[0]]
                    # episodes[episode_idx-1]['frames'][frame_idx-1][selectable_item_exp] = filtered_mask
                mask_show_callback(None, None, None)
    elif mode == 'del':
        if boundary(mouse_point, ORI_FRAME_OFFSET_X, ORI_FRAME_OFFSET_Y, ORI_FRAME_END_X, ORI_FRAME_END_Y):
            i, j = restore(mouse_point, 'ori')
            print('DoubleClicked at', mouse_point, 'Frame pixel i:{} j:{}'.format(i, j))
            filtered_mask = get_mask_by_graph(raw_data_seg, i, j)
            mask_gray = cv2.cvtColor(filtered_mask, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(mask_gray, GRAY_THRESHOLD, 255, 0)
            contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if selectable_item_exp != '':
                if selectable_item_exp in episodes[episode_idx-1]['frames'][frame_idx-1]:
                    # set_mask(episodes[episode_idx-1]['frames'][frame_idx-1][selectable_item_exp], filtered_mask, mode=='unfill')
                    for contour in episodes[episode_idx-1]['frames'][frame_idx-1][selectable_item_exp]:
                        if np.array_equal(contour, contours[0]):
                            episodes[episode_idx-1]['frames'][frame_idx-1][selectable_item_exp].remove(contour)
                            if len(episodes[episode_idx-1]['frames'][frame_idx-1][selectable_item_exp]) == 0:
                                del episodes[episode_idx-1]['frames'][frame_idx-1][selectable_item_exp]
                            break
                    mask_show_callback(None, None, None)
            else:
                exp = ''
                for exp in episodes[episode_idx-1]['frames'][frame_idx-1]:
                    for contour in episodes[episode_idx-1]['frames'][frame_idx-1][exp]:
                        if np.array_equal(contour, contours[0]):
                            episodes[episode_idx-1]['frames'][frame_idx-1][exp].remove(contour)
                            break
                        # set_mask(mask, filtered_mask, mode=='unfill')
                if len(episodes[episode_idx-1]['frames'][frame_idx-1][exp]) == 0:
                    del episodes[episode_idx-1]['frames'][frame_idx-1][exp]
                mask_show_callback(None, None, None)
    else:   
        pass
def get_mask_by_graph(data, i, j, mode=''):
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
                    if np.array_equal(data[ni, nj], data[i, j]):
                        if np.array_equal(fill[ni, nj], np.zeros(3)):
                            fill[ni, nj] = point
                            q.put((ni, nj))
        for i in range(FRAME_HEIGHT):
            for j in range(FRAME_WIDTH):
                if np.array_equal(fill[i, j], np.zeros(3)):
                    fill[i, j] = np.array(MASK_BACKGROUND_COLOR)
                else:
                    fill[i, j] = np.array(MASK_FOREGROUND_COLOR)
        return fill
    def bfs_subs(data, i, j):
        import queue
        fill = np.ones_like(data)
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
                    if np.array_equal(data[ni, nj], data[i, j]):
                        if np.array_equal(fill[ni, nj], np.ones(3)):
                            fill[ni, nj] = point
                            q.put((ni, nj))
        for i in range(FRAME_HEIGHT):
            for j in range(FRAME_WIDTH):
                if np.array_equal(fill[i, j], np.ones(3)):
                    fill[i, j] = np.array(MASK_BACKGROUND_COLOR)
                # substitute black by foreground color
                else:
                    fill[i, j] = np.array(MASK_FOREGROUND_COLOR)
        return fill
    if mode == 'subs':
        fill = bfs_subs(data, i, j)
    else:
        fill = bfs(data, i, j)
    return fill
def set_mask(data, mask, mode='fill'):
    for i in range(FRAME_HEIGHT):
        for j in range(FRAME_WIDTH):
            if not np.array_equal(mask[i, j], np.array(MASK_BACKGROUND_COLOR)):
                if mode == 'fill':
                    data[i, j] = mask[i, j]
                else:  # just cause unfill is always used for mask
                    data[i, j] = np.array(MASK_BACKGROUND_COLOR)
def contour_contains(contours, contour):
    for c in contours:
        if np.array_equal(c, contour):
            return True
    return False

# key bind for episode and frame editing functions
def key_event_handler(sender, app_data, user_data):
    # h,l for episode minus and plus, j,k for frame plus and minus, like vim motion bind keys
    if DVC == 'WIN':
        key_ctrl = 17
    else:  # press linux LCtrl
        key_ctrl = 341
    if DVC == 'WIN':
        key_esc = 27
    else:  # press linux ESC
        key_ctrl = 256
    if app_data in [ 72, 265 ]: # press h or w or up key 87 is w
        idx_callback(sender, app_data, ['minus', 'episodes'])
    elif app_data in [ 74, 262 ]: # press j or d or right key 68 is d
        idx_callback(sender, app_data, ['plus', 'frames'])
    elif app_data in [ 75, 263 ]: # press k or a or left key 65 is a
        idx_callback(sender, app_data, ['minus', 'frames'])
    elif app_data in [ 76, 264 ]: # press l or s or down key 83 is s
        idx_callback(sender, app_data, ['plus', 'episodes'])
    elif app_data == key_ctrl:  # press windows Ctrl
        ctrl_combo_key_callback()
    elif app_data == key_esc: # press windows ESC
        load_imgexpmasks()
        dpg.set_value('ori_frame', raw_data_ori.astype(np.float32) / 255)
        global selectable_item_exp
        selectable_item_exp = ''
        exp_select_callback(None, None, None)
    else:
        print('Other key_id: {} pressed!'.format(app_data))
def ctrl_combo_key_callback():
    ls = ['h', 'j', 'k', 'l', 'up', 'right', 'left', 'down']  
    if dpg.is_key_down(dpg.mvKey_E):   # navigation shortcut mode enable
        for i in ls:
            dpg.configure_item('bind_key_' + i, callback=key_event_handler)
    elif dpg.is_key_down(dpg.mvKey_D):  # navigation shortcut mode disalbe
        for i in ls:
            dpg.configure_item('bind_key_' + i, callback=None)
    elif dpg.is_key_down(dpg.mvKey_S):
        write_json()
    elif dpg.is_key_down(dpg.mvKey_W): # evaluation or check mode enable
        dpg.set_value('eval_mode_txt', 'Evaluation: enabled')
        load_imgexpmasks()
    elif dpg.is_key_down(dpg.mvKey_Q): # evaluation or check mode disable
        dpg.set_value('eval_mode_txt', 'Evaluation: disabled')
        dpg.delete_item('exps_masked_sub')
        with dpg.group(tag='exps_masked_sub', parent='exps_masked', horizontal=True):
            pass
        load_imgexpmasks()
    elif dpg.is_key_down(dpg.mvKey_R):  # dark theme mode enable
        toggle_theme(None, None, None, mode='dark')
    elif dpg.is_key_down(dpg.mvKey_T):  # light theme mode enable
        toggle_theme(None, None, None, mode='light')
    # dpg.set_value('shortcut', ' Shortcut: '+('enabled' if dpg.get_item_callback('bind_key_h') else 'disabled'))
def toggle_bind_key():
    ls = ['h', 'j', 'k', 'l', 'up', 'right', 'left', 'down']
    for i in ls:
        if dpg.get_item_callback('bind_key_' + i) is None:
            dpg.configure_item('bind_key_' + i, callback=key_event_handler)
        else:
            dpg.configure_item('bind_key_' + i, callback=None)
    # dpg.set_value('shortcut', ' Shortcut Mode: '+('enabled' if dpg.get_item_callback('bind_key_h') else 'disabled'))


# scale callback function
def scale_callback(sender, app_data, user_data):
    scale = dpg.get_value(sender)

    global WINDOW_WIDTH, WINDOW_HEIGHT, FRAME_FACTOR
    WINDOW_WIDTH, WINDOW_HEIGHT, FRAME_FACTOR = int(1650 / scale), int(1050 / scale), 3 / scale

    global EXP_SCROLL_HEIGHT, INS_SCROLL_HEIGHT, INST_SCROLL_HEIGHT
    EXP_SCROLL_HEIGHT = 180 / scale
    EXP_POPUP_SCROLL_HEIGHT = 250 / scale
    INS_SCROLL_HEIGHT = 120 / scale
    INST_SCROLL_HEIGHT = 100 / scale

    global ORI_FRAME_OFFSET_X, ORI_FRAME_OFFSET_Y, ORI_FRAME_END_X, ORI_FRAME_END_Y
    global SEG_FRAME_OFFSET_X, SEG_FRAME_OFFSET_Y, SEG_FRAME_END_X, SEG_FRAME_END_Y
    ORI_FRAME_OFFSET_X, ORI_FRAME_OFFSET_Y = 0, 90 / scale
    SEG_FRAME_OFFSET_X, SEG_FRAME_OFFSET_Y = 0, 530 / scale
    ORI_FRAME_END_X, ORI_FRAME_END_Y = ORI_FRAME_OFFSET_X + FRAME_WIDTH * FRAME_FACTOR, ORI_FRAME_OFFSET_Y + FRAME_HEIGHT * FRAME_FACTOR
    SEG_FRAME_END_X, SEG_FRAME_END_Y = SEG_FRAME_OFFSET_X + FRAME_WIDTH * FRAME_FACTOR, SEG_FRAME_OFFSET_Y + FRAME_HEIGHT * FRAME_FACTOR

    global STATUS_BAR_OFFSET_X, STATUS_BAR_OFFSET_Y

    STATUS_BAR_OFFSET_X, STATUS_BAR_OFFSET_Y = 5, WINDOW_HEIGHT - 60 * math.pow(scale, 4/3)

    # set window and item size and pos
    dpg.set_viewport_height(WINDOW_HEIGHT)
    dpg.set_viewport_width(WINDOW_WIDTH)
    dpg.configure_item('main_window', width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
    dpg.configure_item('exp_scroll', height=EXP_SCROLL_HEIGHT)
    dpg.configure_item('exp_popup_scroll', height=EXP_POPUP_SCROLL_HEIGHT)
    dpg.configure_item('ins_scroll', height=INS_SCROLL_HEIGHT)
    dpg.configure_item('inst_scroll', height=INST_SCROLL_HEIGHT)
    dpg.configure_item('ori_frame_img', pos=[ORI_FRAME_OFFSET_X, ORI_FRAME_OFFSET_Y], width=FRAME_WIDTH*FRAME_FACTOR, height=FRAME_HEIGHT*FRAME_FACTOR)
    dpg.configure_item('seg_frame_img', pos=[SEG_FRAME_OFFSET_X, SEG_FRAME_OFFSET_Y], width=FRAME_WIDTH*FRAME_FACTOR, height=FRAME_HEIGHT*FRAME_FACTOR)
    dpg.configure_item('statusbar', pos=[STATUS_BAR_OFFSET_X, STATUS_BAR_OFFSET_Y])


# toggle theme
def toggle_theme(sender, app_data, user_data, mode=''):
    global theme
    from dearpygui_ext.themes import create_theme_imgui_light, create_theme_imgui_dark
    light_theme = create_theme_imgui_light()
    dark_theme = create_theme_imgui_dark()
    if not mode:
        if theme == 'light':
            dpg.bind_theme(dark_theme)
            theme = 'dark'
        else:
            dpg.bind_theme(light_theme)
            theme = 'light'
    else:
        dpg.bind_theme(light_theme if mode == 'light' else dark_theme)


# util functions
def boundary(p, ltx, lty, rbx, rby):
    if (p[0] >= ltx and p[0] < rbx) and (p[1] >= lty and p[1] < rby):
        return True
    return False
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
    dpg.configure_item('pop_edit_panel', show=True)
    for item in dpg.get_item_children('key_event_handler', 1):
        dpg.set_item_callback(item, None)
    for item in dpg.get_item_children('mouse_event_handler', 1):
        dpg.set_item_callback(item, None)
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

    # theme setting
    toggle_theme(None, None ,None, mode='light')
            
    # Shortcut mode
    with dpg.handler_registry(tag='key_event_handler'):
        if DVC == 'WIN':
            dpg.add_key_press_handler(dpg.mvKey_Control, callback=key_event_handler, tag='bind_key_ctrl')
        else:
            dpg.add_key_press_handler(dpg.mvKey_LControl, callback=key_event_handler, tag='bind_key_ctrl') # linux adaption
        dpg.add_key_press_handler(dpg.mvKey_H, callback=key_event_handler, tag='bind_key_h')
        dpg.add_key_press_handler(dpg.mvKey_J, callback=key_event_handler, tag='bind_key_j')
        dpg.add_key_press_handler(dpg.mvKey_K, callback=key_event_handler, tag='bind_key_k')
        dpg.add_key_press_handler(dpg.mvKey_L, callback=key_event_handler, tag='bind_key_l')
        # dpg.add_key_press_handler(dpg.mvKey_W, callback=key_event_handler, tag='bind_key_w')
        # dpg.add_key_press_handler(dpg.mvKey_D, callback=key_event_handler, tag='bind_key_d')
        # dpg.add_key_press_handler(dpg.mvKey_A, callback=key_event_handler, tag='bind_key_a')
        # dpg.add_key_press_handler(dpg.mvKey_S, callback=key_event_handler, tag='bind_key_s')
        dpg.add_key_press_handler(dpg.mvKey_Up, callback=key_event_handler, tag='bind_key_up')
        dpg.add_key_press_handler(dpg.mvKey_Right, callback=key_event_handler, tag='bind_key_right')
        dpg.add_key_press_handler(dpg.mvKey_Left, callback=key_event_handler, tag='bind_key_left')
        dpg.add_key_press_handler(dpg.mvKey_Down, callback=key_event_handler, tag='bind_key_down')
        dpg.add_key_press_handler(dpg.mvKey_Escape, callback=key_event_handler, tag='bind_key_esc')
    with dpg.handler_registry(tag='mouse_event_handler'):
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
                dpg.add_menu_item(label="Toggle Light/Dark Theme", callback=toggle_theme)
                dpg.add_slider_float(label="Window scale factor", min_value=1.0, max_value=1.5, callback=scale_callback, default_value=1.25, format='%.2f')


        # Load split and scene json toolbar
        with dpg.group(horizontal=True, tag='toolbar'):
            # split selector
            dpg.add_text("Toolbar - Split:", tag='split_hint')
            dpg.add_combo(['train', 'val_seen', 'val_unseen', 'test'], tag='split', \
                default_value=DEFAULT_SPLIT, width=90, callback=load_split_callback)
            # scene selector
            dpg.add_text('By Scene:', tag='scene_hint')
            scene_list = [1, 2, 3, 4, 5, 8,10, 11, 12, 14, 16, 17, 20, 22, 23, 25, 26]
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
                dpg.add_image("ori_frame", width=FRAME_WIDTH*FRAME_FACTOR, height=FRAME_HEIGHT*FRAME_FACTOR, pos=[ORI_FRAME_OFFSET_X, ORI_FRAME_OFFSET_Y], tag='ori_frame_img')
                dpg.add_image("seg_frame", width=FRAME_WIDTH*FRAME_FACTOR, height=FRAME_HEIGHT*FRAME_FACTOR, pos=[SEG_FRAME_OFFSET_X, SEG_FRAME_OFFSET_Y], tag='seg_frame_img')
            # space to show instructions, referring expressions highlighted navigation instructions,
            # tranlated navigation instructions and operating logs
            with dpg.group():
                # Insturctions
                with dpg.tree_node(tag='user_instruction', label='使用说明'):
                    with dpg.tree_node(label='准备事项'):
                        dpg.add_text("确保已下载好标注和场景文件并放置在annotations和scenes目录下", wrap=0, bullet=True)
                        dpg.add_text("运行scripts/stscene.sh打开场景", wrap=0, bullet=True)
                        dpg.add_text("运行scripts/save_imgs.sh保存需要的图片和表达式信息到data目录下", wrap=0, bullet=True)
                    with dpg.tree_node(label='使用事项'):
                        dpg.add_text("通过工具栏选定split和scene后Load图片和表达式信息", wrap=0, bullet=True)
                        dpg.add_text("通过方向键或工具栏中拖动栏控制episode和frame序号来调整左侧原图和segmentation图", wrap=0, bullet=True)
                        dpg.add_text("在左下方segmentation图单击任一mask任一点对当前帧当前表达式添加mask并在原图显示", wrap=0, bullet=True)
                        dpg.add_text("在左上方原图双击任一mask任一点来删除当前选定表达式的mask", wrap=0, bullet=True)
                        dpg.add_text("可通过点击任一表达式来在原图中查看当前帧该表达式已添加的mask, ESC键清除原图mask", wrap=0, bullet=True)
                        dpg.add_text("可通过编辑按钮触发弹出窗并进行表达式增加删除和编辑，需按保存按钮关闭", wrap=0, bullet=True)
                        dpg.add_text("关闭软件前按Ctrl+S进行保存！", bullet=True, wrap=0)
                        # dpg.add_text("下方状态栏显示当前界面所在的episode_id、trajectory_id和scene_id等状态信息", wrap=0, bullet=True)
                        # dpg.add_text("可通过Ctrl+E打开快捷键模式，Ctrl+D关闭快捷键模式，可在下方状态栏看到当前快捷键模式状态", wrap=0, bullet=True)
                    # with dpg.tree_node(label='注意事项'):
                    #     dpg.add_text("关闭软件前按Ctrl+S进行保存！", bullet=True)
                    #     dpg.add_text("在弹出窗口编辑或删除完表达式后，需通过保存按钮关闭！", bullet=True)
                # Navigation instructions, parsed referring expression highlighted and translated results
                with dpg.group():
                    dpg.add_text('导航指令：', color=(255, 0, 0))
                    with dpg.child_window(height=INS_SCROLL_HEIGHT, delay_search=True, tag='ins_scroll'):
                        dpg.add_text('', tag='instruction', wrap=0)
                with dpg.group():
                    dpg.add_text('导航指令翻译：', color=(255, 0, 0))
                    with dpg.child_window(height=INST_SCROLL_HEIGHT, delay_search=True, tag='inst_scroll'):
                        dpg.add_text('', tag='instruction_translated', wrap=0)
                with dpg.group(horizontal=True):
                    dpg.add_text('已解析表达式(存在冗余或不准确)', color=(0, 255, 0))
                    dpg.add_button(label='编辑', tag='pop_up_edit_btn', callback=popup_callback)
                # dpg.add_button(label='button', callback=popup_callback)
                # saving status popup tooltip if failed
                with dpg.popup('pop_up_edit_btn', modal=True, tag="save_status_modal", no_move=True):
                    dpg.add_text('', tag='save_status_txt', wrap=0)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="确认", width=75, tag='savecfmbtn', callback=lambda: dpg.configure_item("save_status_modal", show=False))
                        dpg.set_item_pos('savecfmbtn', [130, 80])
                # loading status popup tooltip if failed
                with dpg.popup('pop_up_edit_btn', modal=True, tag="load_status_modal", no_move=True):
                    dpg.add_text('', tag='load_status_txt')
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="确认", width=75, tag='loadcfmbtn', callback=lambda: dpg.configure_item("load_status_modal", show=False))
                        dpg.set_item_pos('loadcfmbtn', [450, 80])
                # exp edit window
                with dpg.window(modal=True, tag='pop_edit_panel', show=False):
                    with dpg.group(tag='pop_up_exps'):
                        dpg.add_input_text(default_value='', tag='ins_multiline', multiline=True, readonly=True, width=-1)
                        with dpg.group(tag='pop_up_exps_sub'):
                            pass
                    dpg.add_separator()
                    with dpg.group(horizontal=True, tag='btnlist'):
                        dpg.add_button(label="确认", width=75, tag='savebtn', user_data=[None, 'save'], callback=exps_operation, parent='btnlist')
                        # dpg.add_button(label="取消", width=75, tag='clcbtn', callback=lambda: dpg.configure_item("pop_edit_panel", show=False), parent='btnlist')
                    # dpg.set_item_pos('pop_edit_panel', [780, 350])
                    dpg.set_item_pos('pop_edit_panel', [650, 250])
                # with dpg.popup('pop_up_edit_btn', modal=True, mousebutton=dpg.mvMouseButton_Left, tag="pop_edit_panel"):
                #     with dpg.group(tag='pop_up_exps'):
                #         dpg.add_input_text(default_value='', tag='ins_multiline', multiline=True, readonly=True, width=-1)
                #         with dpg.group(tag='pop_up_exps_sub'):
                #             pass
                #     dpg.add_separator()
                #     with dpg.group(horizontal=True, tag='btnlist'):
                #         dpg.add_button(label="确认", width=75, tag='savebtn', user_data=[None, 'save'], callback=exps_operation, parent='btnlist')
                #         # dpg.add_button(label="取消", width=75, tag='clcbtn', callback=lambda: dpg.configure_item("pop_edit_panel", show=False), parent='btnlist')
                #     # dpg.set_item_pos('pop_edit_panel', [780, 350])
                #     dpg.set_item_pos('pop_edit_panel', [650, 250])
                with dpg.group(tag='exps'):
                    with dpg.group(tag='exps_sub'):
                        pass
                    with dpg.group(tag='exps_masked', horizontal=True):
                        with dpg.group(tag='exps_masked_sub', horizontal=True):
                            pass
                # Operating logs
                # dpg.add_text("操作日志：")


        # Statusbar for loaded json file
        with dpg.group(horizontal=True, pos=[STATUS_BAR_OFFSET_X, STATUS_BAR_OFFSET_Y], tag='statusbar'):
            dpg.add_text('Statusbar -')
            with dpg.group(horizontal=True, tag='saving_indicator_group', show=False):
                dpg.add_text("Saving file")
                dpg.add_loading_indicator(style=1, tag='saving_indicator', radius=1.3, color=[0, 111, 255])
            with dpg.group(horizontal=True, tag='loading_indicator_group', show=False):
                dpg.add_text("Loading file")
                dpg.add_loading_indicator(style=1, tag='loading_indicator', radius=1.3, color=[0, 111, 255])
            dpg.add_text('', tag='split_txt')
            dpg.add_text('', tag='scene_txt')
            dpg.add_text('', tag='episode_id')
            dpg.add_text('', tag='trajectory_id')
            dpg.add_text('', tag='mouse_move')
            # dpg.add_text('Shortcut: enabled', tag='shortcut')
            dpg.add_text('Evaluation: disabled', tag='eval_mode_txt')

        # test component
        
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
