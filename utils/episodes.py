# author: mrxirzzz

import os
from pathlib import Path
import json
import argparse
import random

import airsim
import numpy as np
import nltk
from nltk.tree import *
from stanfordcorenlp import StanfordCoreNLP

class Episodes(object):

    def __init__(self, split, scene=None, only_json=False):
        # split train/val_seen/val_unseen/test split into scene-split subsplit into subfolders
        # and this is optional if your pc gpu is not great or you want to just run one scene 
        # for demonstration

        sets = ['train', 'val_seen', 'val_unseen', 'test']
        self.root_path = Path(__file__).resolve().parent
        self.anno_path = self.root_path / 'annotations'
        for s in sets:
            if not (self.anno_path / s).exists():
                print('Note: scene-seperate s for {} not exists, generating...')
                self.save_scenes(s, self.load_dict(s))

        if only_json:
            # connect to the AirSim simulator
            # print('------------------------------------------')
            # self.client = airsim.VehicleClient(port=int(scene)+25030)
            self.client = airsim.VehicleClient()
            self.client.confirmConnection()

        self.split = split
        self.scene = scene

        self.idx = 0
        if self.scene:
            self.episodes = self.load_scene(self.split, self.scene)[0]['episodes']
        else:
            self.episodes = self.load_dict(self.split)['episodes']

        self.metas = []


    def __iter__(self):

        return self


    def __len__(self):
        
        return len(self.episodes)


    def __next__(self):

        episode = self.episodes[self.idx]
        self.idx += 1
        frames = self.fly_by_trajectory(self.split, episode)
        res = self.parse_re(episode)
        return self.convert(episode, frames, res)


    def get_rand_episode(self, idx):

        frames = []
        print('Rand episode idx: {}'.format(idx))
        return self.convert(self.episodes[idx], frames)
        

    def get_episodes(self):
        return self.episodes


    def convert(self, o_episode, frames, res):

        n_episode = dict()
        n_episode['episode_id'] = o_episode['episode_id']
        n_episode['trajectory_id'] = o_episode['trajectory_id']
        n_episode['scene_id']  = o_episode['scene_id']
        n_episode['instruction'] = o_episode['instruction']['instruction_text']
        n_episode['imgs'] = frames
        n_episode['res'] = res
        return n_episode


    def load_dict(self, split):

        data_path = self.anno_path / (split + '.json')
        with data_path.open() as f:
             data_dict = json.load(f)
        return data_dict


    def save_scenes(self, split, data_dict):

        print('{} scene division started'.format(split))
        print('processing episodes')
        scene_map = dict()
        epis = data_dict['episodes']
        for epi in epis:
            if epi['scene_id'] not in scene_map:
                scene_map[epi['scene_id']] = []
            scene_map[epi['scene_id']].append(epi)
        print('process end')

        print('mkdir doing')
        split_dir = self.anno_path / split
        try:
            split_dir.mkdir(parents=True)   
        except OSError:
            if not split_dir.isdir():
                raise
        print('mkdir end')

        print('saving to path')
        for sce_id, sce_data in scene_map.items():
            data_dict = {'episodes': sce_data}
            jsonstr = json.dumps(data_dict)
            with (split_dir / (str(sce_id) + '.json')).open(mode='w') as f:
                f.write(jsonstr)
        print('save to {} end'.format(split_dir))
        print()


    def load_scene(self, split, scene):

        split_dir = self.anno_path / split
        json_list = os.listdir(str(split_dir))
        if scene is not None:
            assert scene not in json_list
            json_list = [scene + '.json']
        data_list = []
        for json_file in json_list:
            with (split_dir / json_file).open() as f:
                data_list.append(json.load(f))
        return data_list


    def get_frame(self):

        responses = self.client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, False, False), 
                airsim.ImageRequest("0", airsim.ImageType.Segmentation, False, False)])
        imgs = []
        for idx, response in enumerate(responses):
            if response.pixels_as_float:
                #print("Type %d, size %d" % (response.image_type, len(response.image_data_float)))
                #airsim.write_pfm(os.path.normpath(filename + '.pfm'), airsim.get_pfm_array(response))
                img = airsim.get_pfm_array(response)
            elif response.compress: #png format
                #print("Type %d, size %d" % (response.image_type, len(response.image_data_uint8)))
                #airsim.write_file(os.path.normpath(filename + '.png'), response.image_data_uint8)
                img = response.image_data_uint8
            else: #uncompressed array - numpy demo
                #print("Type %d, size %d" % (response.image_type, len(response.image_data_uint8)))
                img = np.fromstring(response.image_data_uint8, dtype=np.uint8) #get numpy array
                img = img.reshape(response.height, response.width, 3) #reshape array to 3 channel image array H X W X 3
                # cv2.imwrite(os.path.normpath(filename + '.png'), img_rgb) # write to png
            imgs.append(img)
        return imgs


    def parse_re(self, episode, props=None):

        def dfs_traverse(tree, RES):
            if type(tree) == str:
                return
            if tree.label() == 'NP':
                res = []
                dfs_print_leaf(tree, res)
                RE = ''
                for i in res:
                    RE += i + ' '
                # RE.replace(',', '')
                RES.add(RE[:-1])
                # print(RE[:-1])
                return
            for i in range(len(tree)):
                dfs_traverse(tree[i], RES)

        def dfs_print_leaf(tree, res):
            if type(tree) == str:
                res.append(tree)
                return
            for i in range(len(tree)):
                dfs_print_leaf(tree[i], res)


        instruction = episode['instruction']['instruction_text']
        nlp = StanfordCoreNLP(r'/home/B/xiezc/stanford-corenlp-4.4.0')
        nsents = nltk.sent_tokenize(instruction) 
        RES = set()
        try: 
            for i, sent in enumerate(nsents):
                print('Sentence_{}: {}'.format(i+1, sent))
                if props is None:
                    # print('Tokenize:', nlp.word_tokenize(instruction), end='\n\n')
                    # print('Part of Speech:', nlp.pos_tag(instruction), end='\n\n')
                    # print('Constituency Parsing:', nlp.parse(instruction), end='\n\n')
                    # print('Dependency Parsing:', nlp.dependency_parse(instruction), end='\n\n')
                    # print('Sentence Splitting', nlp.ssplit(instruction), end='\n\n')
                    # print('Named Entities:', nlp.ner(instruction), end='\n\n')
                    res = nlp.parse(sent)
                else:
                    res = nlp.annotate(sent, properties=props)

                tree = Tree.fromstring(res)
                dfs_traverse(tree, RES)

            print()
            print('Traverse referring expression:')
            print(RES)
            nlp.close()
        except:
            nlp.close() # Do not forget to close! The backend server will consume a lot memery.

        return RES


    def fly_by_trajectory(self, split, episode, save_path, filt):
        split_dir = Path(save_path) / split / 'JPEGImages'
        epi_id = episode['episode_id']
        tra_id = episode['trajectory_id']
        sce_id = episode['scene_id']
        opath = episode['reference_path']
        instruction = episode['instruction']['instruction_text']
        save_dir = split_dir / '{:02d}_{}_{}'.format(sce_id, tra_id, epi_id)
        if not save_dir.exists():
            try:
                save_dir.mkdir(parents=True)
            except OSError:
                if not save_dir.is_dir():
                    raise

        if len(opath) <= 40 or not filt:
            print('------------------------------------------')
            print('episode_id: {} of trajectory_id: {} in scene_id: {} for distance: {} with {} steps'\
                .format(epi_id, tra_id, sce_id, episode['info']['geodesic_distance'], len(opath)))
            print('------------------------------------------')
            print(instruction)
            npath = []
            for p in opath:
                npath.append(airsim.Pose(airsim.Vector3r(*p[:3]), airsim.to_quaternion(*p[3:])))

            # fly through given path and action, get corresponding frames
            # airsim.wait_key('press any key for move according to given trajectory')

            frames = []
            RES = self.parse_re(episode)
            for i, pos in enumerate(npath):
                frame_name = save_dir / "{:03d}.jpg".format(i)
                frame_seg_dir = save_dir / 'segmentation' 
                if not frame_seg_dir.exists():
                    try:
                        frame_seg_dir.mkdir(parents=True)
                    except OSError:
                        if not frame_seg_dir.is_dir():
                            raise
                frame_name_seg = frame_seg_dir / "{:03d}.jpg".format(i)

                self.client.simSetVehiclePose(pos, True)
                frame = self.get_frame()
                frames.append(frame_name.name[:-4])
                if save_path:
                    airsim.write_png(os.path.normpath(str(frame_name)), frame[0]) 
                    airsim.write_png(os.path.normpath(str(frame_name_seg)), frame[1]) 

            print('Over!!!')
            return frames, RES, save_dir.name
        else:
            return None, None, None

        # feed these pictures and corresponding instructions into SoTA REC model, and filter out pictures which contains
        # referring object by threshing the attention score

        # save filtered pictures into fixed folder for subsequent REC annotations


    def run(self, split, oneturn, save_path, filt): # for local main run, __next__ for global iteration

        length = len(self.episodes)
        metas = dict()
        metas['videos'] = dict()
        if oneturn:
            episode = self.episodes[random.randint(0, length-1)]
            self.fly_by_trajectory(self.split, episode, save_path=save_path, filt=filt)
        else:
            for episode in self.episodes:
                FRAMES, RES, vid_name = self.fly_by_trajectory(self.split, episode, save_path=save_path, filt=filt)
                instruction = episode['instruction']['instruction_text']
                if FRAMES is None:
                    continue
                res = dict()
                for i, RE in enumerate(RES):
                    res[str(i)] = dict()
                    res[str(i)]['exp'] = RE
                metas['videos'][vid_name] = dict()
                metas['videos'][vid_name]['instruction'] = instruction
                metas['videos'][vid_name]['expressions'] = res
                metas['videos'][vid_name]['frames'] = FRAMES
        
        if save_path:
           with (Path(save_path) / split / 'expressions.json').open(mode='a+') as f:
               f.write(json.dumps(metas))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate given trajectory image frames and save to pics.')
    parser.add_argument('-s', '--split', type=str, choices=['train', 'val_seen', 'val_unseen', 'test'],\
            default='train', help='Select split for loading json')
    parser.add_argument('-e', '--scene', type=str, help='Choose scene id for given mode directory, if not given, default first accesible scene id chosen')
    parser.add_argument('-o', '--oneturn', action='store_true',\
        help='Choose episode, all episodes(false) or just the first one to demostrate(true is default)')
    parser.add_argument('-S', '--save_path', type=str, help="save root path for JPEGImages and meta_expressions.json")
    parser.add_argument('-f', '--filt', action='store_true', help="filt by 40 frames or not(default)")
    parser.add_argument('-j', '--json', action='store_true', help="load just json annotation data or additionally load images\
        which means you need to run scenario and connect to airim(default)")

    args = parser.parse_args()
    episodes = Episodes(args.split, args.scene, args.json)
    episodes.run(args.split, args.oneturn, args.save_path, args.filt)

