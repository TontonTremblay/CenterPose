# Copyright (c) 2021 NVIDIA Corporation. All rights reserved.
# This work is licensed under the NVIDIA Source Code License - Non-commercial.
# Full text can be found in LICENSE.md

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import cv2

from lib.opts import opts
from lib.detectors.detector_factory import detector_factory
import glob
import numpy as np

image_ext = ['jpg', 'jpeg', 'png', 'webp']
video_ext = ['mp4', 'mov', 'avi', 'mkv']
time_stats = ['tot', 'load', 'pre', 'net', 'dec', 'post', 'merge', 'pnp', 'track']


def demo(opt, meta):
    os.environ['CUDA_VISIBLE_DEVICES'] = opt.gpus_str
    opt.debug = max(opt.debug, 1)
    Detector = detector_factory[opt.task]
    detector = Detector(opt)

    if opt.use_pnp == True and 'camera_matrix' not in meta.keys():
        raise RuntimeError('Error found. Please give the camera matrix when using pnp algorithm!')

    if opt.demo == 'webcam' or \
            opt.demo[opt.demo.rfind('.') + 1:].lower() in video_ext:
        cam = cv2.VideoCapture(0 if opt.demo == 'webcam' else opt.demo)
        detector.pause = False

        # Check if camera opened successfully
        if (cam.isOpened() == False):
            print("Error opening video stream or file")

        idx = 0
        while(cam.isOpened()):
            _, img = cam.read()
            try:
                cv2.imshow('input', img)
            except:
                exit(1)

            filename = os.path.splitext(os.path.basename(opt.demo))[0] + '_' + str(idx).zfill(
                                   4) + '.png'
            ret = detector.run(img, meta_inp=meta,
                               filename=filename)
            idx = idx + 1

            time_str = ''
            for stat in time_stats:
                time_str = time_str + '{} {:.3f}s |'.format(stat, ret[stat])
            print(f'Frame {str(idx).zfill(4)}|' + time_str)
            if cv2.waitKey(1) == 27:
                break
    else:

        # # Option 1: only for XX_test with a lot of sub-folders
        # image_names = []
        # for ext in image_ext:
        #     file_name=glob.glob(os.path.join(opt.demo,f'**/*.{ext}'))
        #     if file_name is not []:
        #         image_names+=file_name

        # Option 2: if we have images just under a folder, uncomment this instead
        if os.path.isdir(opt.demo):
            image_names = []
            ls = os.listdir(opt.demo)
            for file_name in sorted(ls):
                ext = file_name[file_name.rfind('.') + 1:].lower()
                if ext in image_ext:
                    image_names.append(os.path.join(opt.demo, file_name))
        else:
            image_names = [opt.demo]

        detector.pause = False
        for idx, image_name in enumerate(image_names):
            # Todo: External GT input is not enabled in demo yet
            ret = detector.run(image_name, meta_inp=meta)
            time_str = ''
            for stat in time_stats:
                time_str = time_str + '{} {:.3f}s |'.format(stat, ret[stat])
            print(f'Frame {idx}|' + time_str)

if __name__ == '__main__':

    # Default params with commandline input
    opt = opts().parser.parse_args()

    # Local machine configuration
    # opt.c = 'cup'
    # opt.demo = "../images/CenterPose/cup.mp4"
    opt.demo = 'webcam'
    opt.arch = 'dlav1_34'
    # opt.load_model = f"../models/CenterPose/cup_mug_v1_140.pth"
    opt.load_model = "/home/jtremblay/code/centerpose_yunzhi/exp/object_pose/objectron_bike_dlav1_34_2022-05-11-10-08/bike_best.pth"
    opt.show_axes = True

    # Default setting
    opt.nms = True
    opt.obj_scale = True

    # Tracking stuff
    if opt.tracking_task == True:
        print('Running tracking')
        opt.pre_img = True
        opt.pre_hm = True
        opt.tracking = True
        opt.pre_hm_hp = True
        opt.tracking_hp = True
        opt.track_thresh = 0.1

        opt.obj_scale_uncertainty = True
        opt.hps_uncertainty = True
        opt.kalman = True
        opt.scale_pool = True

        opt.vis_thresh = max(opt.track_thresh, opt.vis_thresh)
        opt.pre_thresh = max(opt.track_thresh, opt.pre_thresh)
        opt.new_thresh = max(opt.track_thresh, opt.new_thresh)

        # opt.max_age = 2
        # opt.vis_thresh = 0.5

        print('Using tracking threshold for out threshold!', opt.track_thresh)

    # PnP related
    meta = {}
    if opt.cam_intrinsic is None:
        meta['camera_matrix'] = np.array(
            [[663.0287679036459, 0, 300.2775065104167], [0, 663.0287679036459, 395.00066121419275], [0, 0, 1]])
        opt.cam_intrinsic = meta['camera_matrix']
    else:
        meta['camera_matrix'] = np.array(opt.cam_intrinsic).reshape(3,3)

    opt.use_pnp = False

    # Update default configurations
    opt = opts().parse(opt)

    # Update dataset info/training params
    opt = opts().init(opt)
    demo(opt, meta)
