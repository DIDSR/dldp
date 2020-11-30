#!/home/wli/env python3
# -*- coding: utf-8 -*-
"""
Title: main_pred_hnm_workstation
================================
Created: 10-31-2019
Python-Version: 3.5, 3.6

Description:
------------

This module is used to extract image patches for hard negative mining
on workstation.

Inputs:
*******

1. model = load_model() : specify which model to load;

2. slide_category = slide_categories[1] : tumor slides or normal slides

3. ground_truth_path = '/raidb/wli/Final_Results/Display/train_masking':
   This is the mask files generated by utils/mask_generation_asap.py

4. color_norm = False : if color normalization method will be used; if
   yes, specifly : color_norm_method = color_norm_methods[2]
                 : template_image_path = '/home/wli/DeepLearningCamelyon/dldp/data/tumor_st.png'
                 : log_path = '/raidb/wli/testing_1219/hnm/log_files'

5. IIIdhistech_only = False : if only extract patches for the slides
   from 3D histch scanner.

Output:
*******

The folders to store the extracted image patches:
     path_for_results = '/raidb/wli/testing_1219/hnm/%s_%s' % (slide_category, color_norm_method)


Request:
********

this module relys on (if color normalization is used):
         https://github.com/wanghao14/Stain_Normalization
         https://github.com/Peter554/StainTools

Please also put the above folders to PYTHONPATH.

patch_index.py needs to be run first to generate the postion information of
image patches to be predicted.


"""


from keras.models import load_model
import pandas as pd
import os.path as osp
from datetime import datetime
import sys
# sys.path.append('/home/wli/Stain_Normalization-master')
#############################################
from dldp.heatmap_pred import Pred_Slide_Window_For_Heatmap as pswh
from dldp.utils import fileman as fm


if __name__ == "__main__":

    current_time = datetime.now().strftime("%d-%m-%Y_%I-%M-%S_%p")
    slide_categories = ['normal', 'tumor', 'test']
    slide_category = slide_categories[1]
    batch_size = 32
    crop_size = [224, 224]
    pred_size = 224
    NUM_CLASSES = 2  # not_tumor, tumor
    stride = 224
    thresh_hold = 0.6

    # SGE_TASK_ID will not be used here.
    # origin_taskid = int(os.environ['SGE_TASK_ID'])
    color_norm_methods = ['Vahadane', 'Reinhard', 'Macenko']
    template_image_path = '/home/wli/DeepLearningCamelyon/dldp/data/tumor_st.png'
    color_norm = False
    if color_norm:
        color_norm_method = color_norm_methods[2]
        fit = pswh.color_normalization(template_image_path, color_norm_method)
    else:
        color_norm_method = 'baseline'
        fit = None
    path_for_results = '/raidb/wli/testing_1219/hnm/%s_%s' % (
        slide_category, color_norm_method)
    log_path = '/raidb/wli/testing_1219/hnm/log_files'
    fm.creat_folder(log_path)
    log_file = open('%s/%s.txt' % (log_path, color_norm_method), 'w')
    IIIdhistech_only = False
    # the WSI images from Camelyon16 challenge.
    slide_paths = {
        "normal": '/raida/wjc/CAMELYON16/training/normal/',
        "tumor": '/raida/wjc/CAMELYON16/training/tumor/',
        "test": '/raida/wjc/CAMELYON16/testing/images'
    }

    # the index_path is place to store all the coordinate of tiled patches
    ####################################################################################################
    # the slide and dimension information retrievaled based on the name of index_paths to make sure all
    # dimension, index_paths, slide are all matched
    ####################################################################################################
    index_paths = {
        "normal": '/raidb/wli/Final_Results/Display/pred_dim_0314/training-updated/normal/patch_index',
        "tumor": '/raidb/wli/Final_Results/Display/pred_dim_0314/training-updated/tumor/patch_index',
    }

    # the slide and dimension information retrievaled based on the name of index_paths to make sure all
    # dimension, index_paths, slide are all matched
    patch_numbers = {

        "normal": '/home/wli/DeepLearningCamelyon/dldp/data/PatchNumberForHPC_normal.pkl',
        "tumor": '/home/wli/DeepLearningCamelyon/dldp/data/PatchNumberForHPC_tumor.pkl',
        "test": '/home/wli/DeepLearningCamelyon/dldp/data/PatchNumberForHPC_test0314.pkl'
    }

    exclude_normal_list = ['tumor_010', 'tumor_015', 'tumor_018', 'tumor_020',
                           'tumor_025', 'tumor_029', 'tumor_033', 'tumor_034',
                           'tumor_044', 'tumor_046', 'tumor_051', 'tumor_054',
                           'tumor_055', 'tumor_056', 'tumor_067', 'tumor_079',
                           'tumor_085', 'tumor_092', 'tumor_095', 'tumor_110']

    ground_truth_path = '/raidb/wli/Final_Results/Display/train_masking'
    ground_truth_paths = False
    # collect all the information
    slide_path_pred = pswh.list_file_in_dir(slide_paths[slide_category], 'tif')
    index_path_pred = pswh.list_file_in_dir(index_paths[slide_category], 'pkl')
    patch_number = pd.read_pickle(patch_numbers[slide_category])
    if slide_category == 'tumor':
        ground_truth_paths = pswh.list_file_in_dir(ground_truth_path, 'tif')

    print(slide_path_pred)
    print(ground_truth_paths)
    # load the model for prediction
    model = load_model(
        '/raidb/wli/googlenetv1_Total_Patch_Retrain_10.04.19 09:06_Origin-06-0.95.hdf5')

    # modify task_id and decide the number of patches to be predicted for one task id from HPC

    for origin_taskid in range(1, 150001):

        # print(origin_taskid)

        task_id, patches_per_task = pswh.modify_task_id(
            origin_taskid, slide_category)
        # identify the slide and patches index
        i, j, j_dif = pswh.slide_patch_index(
            task_id, patches_per_task, patch_number)
        # select slides from 3dhistech scanner
        if IIIdhistech_only:
            pswh.exit_program(i, slide_category)

        if ground_truth_paths:
            all_samples, n_samples, slide, new_slide_path, ground_truth = pswh.slide_level_info_hnm(
                i, index_path_pred, slide_path_pred, ground_truth_paths)

            # print('tumor_path for pred: %s' % new_slide_path)
        else:
            all_samples, n_samples, slide, new_slide_path = pswh.slide_level_info_hnm(
                i, index_path_pred, slide_path_pred)
        if osp.splitext(osp.basename(new_slide_path))[0] in exclude_normal_list:
            print("Not fully annotated WSI, Skip")
            continue

        path_to_create = pswh.creat_folder(new_slide_path, path_for_results)

        sub_samples, range_right = pswh.patches_for_pred(
            i, j, j_dif, patch_number, patches_per_task, all_samples)

        pswh.batch_pred_per_taskid_hnm(pred_size, stride, sub_samples, slide, fit, model, range_right, path_to_create,
                                       task_id, patch_number, i, j, current_time, log_file, new_slide_path, thresh_hold, ground_truth, color_norm)