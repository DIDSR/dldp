"""
Parameter_Extraction_For_Random Forest_Batch
============================================

Purpose:
--------
This module is used to extract parameters from the heatmaps of Normal, Tumor and Test slides
based on different thresholds (0.5, 0.6, 0.7, 0.8, 0.9).

Description:
------------
The input files:

- A directory:
- A csv file: it has the slide name and its label as normal or tumor, which serves as
              ground truth.

The output files:

- A csv file: it included the following parameters for whole-slide image classification task:

::

    global features

    1. The ratio between the area of metastatic regions and the tissue area.
    2. The sum of all cancer metastases probailities detected in the metastasis identification task, divided by the
    tissue area. caculate them at 5 different thresholds (0.5, 0.6, 0.7, 0.8, 0.9), so the total 10 global features

    local features

    Based on 2 largest metastatic candidate regions (select them based on a threshold of 0.5). 9 features were extracted
    from the 2 largest regions:

    1. Area: the area of connected region
    2. Eccentricity: The eccentricity of the ellipse that has the same second-moments as the region
    3. Extend: The ratio of region area over the total bounding box area
    4. Bounding box area
    5. Major axis length: the length of the major axis of the ellipse that has the same normalized second central
    moments as the region
    6. Max/mean/min intensity: The max/mean/minimum probability value in the region
    7. Aspect ratio of the bounding box
    8. Solidity: Ratio of region area over the surrounding convex area

"""

import csv
import glob
import os
import random

import cv2
import numpy as np
import scipy.stats.stats as st
from skimage.measure import label
from skimage.measure import regionprops
from skimage.segmentation import clear_border
from skimage.morphology import closing, square
from matplotlib import cm
from tqdm import tqdm
from skimage.filters import threshold_otsu
from keras.models import load_model
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os.path as osp
import openslide
from pathlib import Path
from skimage.filters import threshold_otsu
import glob
import math
# before importing HDFStore, make sure 'tables' is installed by pip3 install tables
from pandas import HDFStore
from openslide.deepzoom import DeepZoomGenerator
from sklearn.model_selection import StratifiedShuffleSplit
from keras.utils.np_utils import to_categorical


import os.path as osp
import openslide
from pathlib import Path
import numpy as np
import skimage.io as io
import skimage.transform as trans
import re


################################################################################################
# for global features
# ##############################################################################################


def glob_features(slide_path, heatmap):
    """
    The function is used to generate global features based on heatmap.

    :param slide_path: The path for individual WSI, not the path for WSIs folder.
    :type slide_path: str
    :param heatmap: the heatmap created by the trained model during the prediction. The heatmap here
                    is the final assembled array from many small arrays.
    :type heatmap: array
    :return: global features
    :rtype: list
    """

    # make the heatmap path the same as slide path
    with openslide.open_slide(slide_path) as slide:
        dtotal = (slide.dimensions[0] / 16, slide.dimensions[1] / 16)
        thumbnail = slide.get_thumbnail((dtotal[0], dtotal[1]))
        thum = np.array(thumbnail)
        ddtotal = thum.shape
        # dimensions.extend(ddtotal)
        hsv_image = cv2.cvtColor(thum, cv2.COLOR_RGB2HSV)
        #hsv_image = cv2.cvtColor(thum, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv_image)
        hthresh = threshold_otsu(h)
        sthresh = threshold_otsu(s)
        #vthresh = threshold_otsu(v)

    # be min value for v can be changed later
        minhsv = np.array([hthresh, sthresh, 0], np.uint8)
        #maxhsv = np.array([180, 255, vthresh], np.uint8)
        maxhsv = np.array([180, 255, 255], np.uint8)
        thresh = [minhsv, maxhsv]

    # extraction the countor for tissue

        rgbbinary = cv2.inRange(hsv_image, thresh[0], thresh[1])
        rgbbinaryarea = cv2.countNonZero(rgbbinary)

        predthreshold50 = heatmap > 0.5
        predthreshold60 = heatmap > 0.6
        predthreshold70 = heatmap > 0.7
        predthreshold80 = heatmap > 0.8
        predthreshold90 = heatmap > 0.9

        ratio_cancer_tissue50 = cv2.countNonZero(
            predthreshold50*1)/rgbbinaryarea
        ratio_cancer_tissue60 = cv2.countNonZero(
            predthreshold60*1)/rgbbinaryarea
        ratio_cancer_tissue70 = cv2.countNonZero(
            predthreshold70*1)/rgbbinaryarea
        ratio_cancer_tissue80 = cv2.countNonZero(
            predthreshold80*1)/rgbbinaryarea
        ratio_cancer_tissue90 = cv2.countNonZero(
            predthreshold90*1)/rgbbinaryarea

        predthreshold250 = heatmap - 0.5
        predthreshold260 = heatmap - 0.6
        predthreshold270 = heatmap - 0.7
        predthreshold280 = heatmap - 0.8
        predthreshold290 = heatmap - 0.9
        predthreshold250 = predthreshold250.clip(min=0)
        predthreshold260 = predthreshold260.clip(min=0)
        predthreshold270 = predthreshold270.clip(min=0)
        predthreshold280 = predthreshold280.clip(min=0)
        predthreshold290 = predthreshold290.clip(min=0)

        ratio_sum_tissue50 = predthreshold250.sum()/rgbbinaryarea
        ratio_sum_tissue60 = predthreshold260.sum()/rgbbinaryarea
        ratio_sum_tissue70 = predthreshold270.sum()/rgbbinaryarea
        ratio_sum_tissue80 = predthreshold280.sum()/rgbbinaryarea
        ratio_sum_tissue90 = predthreshold290.sum()/rgbbinaryarea

        globalfeatures = [ratio_cancer_tissue50, ratio_cancer_tissue60, ratio_cancer_tissue70, ratio_cancer_tissue80,
                          ratio_cancer_tissue90,  ratio_sum_tissue50,  ratio_sum_tissue60,  ratio_sum_tissue70,
                          ratio_sum_tissue80, ratio_sum_tissue90]

    return globalfeatures

# ##########################################################################################
# for local features
# ##########################################################################################


def get_region_props(heatmapbinary, heatmap):
    """
    This is the most fundamental function for local feature extraction.
    :param heatmapbinary: the binary array generated by a threshold, for example, 0.5.
    :type heatmapbinary: array
    :param heatmap: The heatmap created by the trained model during the prediction. The heatmap here
                    is the final assembled array from many small arrays.
    :type heatmap: array
    :return: region properties
    :rtype: dataframe
    """
    #heatmapbinary = closing(heatmapbinary, square[3])
    heatmapbinary = clear_border(heatmapbinary)
    labeled_img = label(heatmapbinary)
    return regionprops(labeled_img, intensity_image=heatmap)


#   1. Area: the area of connected region

def get_largest_tumor_index_area(region_props):
    """
    The function is used to find the largest tumor region.

    :param region_props: the results from get_region_props.
    :type region_props: dataframe
    :return: the largest tumor region with its area and index.
    :rtype: tuple
    """
    largest_tumor_index = -1

    largest_tumor_area = -1

    n_regions = len(region_props)
    for index in range(n_regions):
        if region_props[index]['area'] > largest_tumor_area:
            largest_tumor_area = region_props[index]['area']
            largest_tumor_index = index

    return (largest_tumor_index, largest_tumor_area)


def get_second_largest_tumor_index_area(region_props, largest_index):
    """
    The function is used to find the second largest tumor region.

    :param region_props: the results from get_region_props.
    :type region_props: dataframe
    :param largest_index: the index of the largest region
    :type int
    :return: the second largest tumor region with its area and index.
    :rtype: tuple
    """
    second_largest_tumor_index = -1

    second_largest_tumor_area = -1

    n_regions = len(region_props)
    for index in range(n_regions):
        if region_props[index]['area'] > second_largest_tumor_area and region_props[index]['area'] < region_props[largest_index]['area']:
            second_largest_tumor_area = region_props[index]['area']
            second_largest_tumor_index = index

    return (second_largest_tumor_index, second_largest_tumor_area)


#   Major axis length: the length of the major axis of the ellipse that has the same normalized second central moments
#   as the region

# def get_longest_axis_in_largest_tumor_region(region_props, tumor_region_index):
#    tumor_region = region_props[tumor_region_index]
#    return max(tumor_region['major_axis_length'], tumor_region['minor_axis_length'])


def local_features(heatmap, threshold):
    """
    The function is to be used for generation of local_features from heatmap

    :param heatmap: The heatmap created by the trained model during the prediction. The heatmap here
                    is the final assembled array from many small arrays.
    :type heatmap: array
    :param threshold: the threshold set for generating binary arrays.
    :type threshold: float
    :return: local features
    :rtype: list
    """

    # I used 0.5 as threshold here, but Dayong may use another value, for example 0.9
    heatmapbinary = (heatmap > threshold)*1
    #heatmapbinary = (heatmap > 0.5)*1

    features = []

    # extract parameters from regionprops function of scikit-image

    region_props_largest = get_region_props(heatmapbinary, heatmap)

    number_tumor_region = len(region_props_largest)

    if number_tumor_region == 0:
        return [0.00] * N_FEATURES

    # else:
    #   1. Area: the area of connected region

    # the area and index of largest lesion:

    largest_lesion = get_largest_tumor_index_area(region_props_largest)

    largest_area = largest_lesion[1]

    largest_index = largest_lesion[0]

    # print(largest_area)

    # features.append(largest_area)

    #   2. Eccentricity: The eccentricity of the ellipse that has the same second-moments as the region
    eccentricity_largest = region_props_largest[largest_index]['eccentricity']

    # features.append(eccentricity_largest)

    #   3. Extend: The ratio of region area over the total bounding box area
    extend_largest = region_props_largest[largest_index]['extent']

    # features.append(extent_largest)

    #   4. Bounding box area
    area_bbox_largest = region_props_largest[largest_index]['bbox_area']

    # features.append(area_bbox_largest)

    #   5. Major axis length: the length of the major axis of the ellipse that has the same normalized second central
    #   moments as the region
    major_axis_length_largest = region_props_largest[largest_index]['major_axis_length']

    features.append(major_axis_length_largest)

    #   6. Max/mean/min intensity: The max/mean/minimum probability value in the region

    maxprob_largest = region_props_largest[largest_index]['max_intensity']
    minprob_largest = region_props_largest[largest_index]['min_intensity']
    aveprob_largest = region_props_largest[largest_index]['mean_intensity']

    #features.append(maxprob_largest, minprob_largest, aveprob_largest)

    #   7. Aspect ratio of the bounding box
    coordinates_of_bbox_largest = region_props_largest[largest_index]['bbox']
    aspect_ratio_bbox_largest = (coordinates_of_bbox_largest[2]-coordinates_of_bbox_largest[0])/(
        coordinates_of_bbox_largest[3]-coordinates_of_bbox_largest[1])

    # features.append(aspect_ratio_bbox_largest)

    #   8. Solidity: Ratio of region area over the surrounding convex area
    solidity_largest = region_props_largest[largest_index]['solidity']

    # features.append(solidity_largest)

    #   1. Area: the area of connected region

    # the area and index of largest lesion:

    second_largest_lesion = get_second_largest_tumor_index_area(
        region_props_largest, largest_index=largest_lesion[0])

    second_largest_area = second_largest_lesion[1]

    second_largest_index = second_largest_lesion[0]

    # features.append(second_largest_area)

    #   2. Eccentricity: The eccentricity of the ellipse that has the same second-moments as the region
    eccentricity_second_largest = region_props_largest[second_largest_index]['eccentricity']

    # features.append(eccentricity_second_largest)

    #   3. Extend: The ratio of region area over the total bounding box area
    extend_second_largest = region_props_largest[second_largest_index]['extent']

    # features.append(extent_second_largest)

    #   4. Bounding box area
    area_bbox_second_largest = region_props_largest[second_largest_index]['bbox_area']

    # features.append(area_bbox_second_largest)

    #   5. Major axis length: the length of the major axis of the ellipse that has the same normalized second central
    #   moments as the region
    major_axis_length_second_largest = region_props_largest[
        second_largest_index]['major_axis_length']

    # features.append(major_axis_length_second_largest)

    #   6. Max/mean/min intensity: The max/mean/minimum probability value in the region

    maxprob_second_largest = region_props_largest[second_largest_index]['max_intensity']
    minprob_second_largest = region_props_largest[second_largest_index]['min_intensity']
    aveprob_second_largest = region_props_largest[second_largest_index]['mean_intensity']

    #features.append(maxprob_second_largest, minprob_second_largest, aveprob_second_largest)

    #   7. Aspect ratio of the bounding box
    coordinates_of_bbox_second_largest = region_props_largest[second_largest_index]['bbox']
    aspect_ratio_bbox_second_largest = (coordinates_of_bbox_second_largest[2]-coordinates_of_bbox_second_largest[0])/(
        coordinates_of_bbox_second_largest[3]-coordinates_of_bbox_second_largest[1])

    # features.extend(aspect_ratio_bbox_second_largest)

    #   8. Solidity: Ratio of region area over the surrounding convex area
    solidity_second_largest = region_props_largest[second_largest_index]['solidity']

    # features.append(solidity_second_largest)

    localfeatures = [largest_area, eccentricity_largest, extend_largest, area_bbox_largest, major_axis_length_largest,
                     maxprob_largest, minprob_largest, aveprob_largest, aspect_ratio_bbox_largest, solidity_largest,
                     second_largest_area, eccentricity_second_largest, extend_second_largest, area_bbox_second_largest,
                     major_axis_length_second_largest, maxprob_second_largest, minprob_second_largest,
                     aveprob_second_largest, aspect_ratio_bbox_second_largest, solidity_second_largest]

    return localfeatures


def create_folder(result_folder, sub_folder):
    """
    To create folders

    :param sub_folder: the folder to be created.
    :type sub_folder: str
    :param result_folder: the folder to store the results
    :return: folder_to_create
    :rtype: str
    """

    folder_to_create = osp.join(result_folder, sub_folder)
    print(folder_to_create)
    try:
        os.makedirs(folder_to_create)
    except:
        print('Folder exists, skip folder creation')

    return folder_to_create


if __name__ == "__main__":

    N_FEATURES = 30
    # heatmap_path = '/home/wli/Downloads/pred/'
    # heatmap_paths = glob.glob(osp.join(heatmap_path, '*.npy'))
    # slide_path = '/home/wli/Downloads/Camelyon16/training/tumor'
    # result_folder = '/home/wzli/Downloads/RF_parameters_64stride'
    result_folder = '/raidb/wli/testing_1219/test_roc'
    cols = ['name', 'tumor', 'ratio_cancer_tissue50', 'ratio_cancer_tissue60', 'ratio_cancer_tissue70', 'ratio_cancer_tissue80', 'ratio_cancer_tissue90',  'ratio_sum_tissue50',  'ratio_sum_tissue60',  'ratio_sum_tissue70',  'ratio_sum_tissue80', 'ratio_sum_tissue90', 'largest_area', 'eccentricity_largest', 'extend_largest', 'area_bbox_largest', 'major_axis_length_largest', 'maxprob_largest',
            'minprob_largest', 'aveprob_largest', 'aspect_ratio_bbox_largest', 'solidity_largest', 'second_largest_area', 'eccentricity_second_largest', 'extend_second_largest', 'area_bbox_second_largest', 'major_axis_length_second_largest', 'maxprob_second_largest', 'minprob_second_largest', 'aveprob_second_largest', 'aspect_ratio_bbox_second_largest', 'solidity_second_largest']

    list_thres = [0.5, 0.6, 0.7, 0.8, 0.9]

    list_slide_path = ['/raida/wjc/CAMELYON16/training/normal/',
                       '/raida/wjc/CAMELYON16/training/tumor/', '/raida/wjc/CAMELYON16/testing/images/']
    #list_heatmap_path = ['/home/wzli/Method_II_Model_I_HNM_no_norm/normal_0425_new', '/home/wzli/Method_II_Model_I_HNM_no_norm/tumor_0425_new', '/home/wzli/Method_II_Model_I_HNM_no_norm/test_0425_new_new']
    list_heatmap_path = ['/raidb/wli/Final_Results/Heat_map/Method_II/color_noise_color_normalization/Method_II_Model_I_norm/normal_0506',
                         '/raidb/wli/Final_Results/Heat_map/Method_II/color_noise_color_normalization/Method_II_Model_I_norm/tumor_0506',
                         '/raidb/wli/Final_Results/Heat_map/Method_II/color_noise_color_normalization/Method_II_Model_I_norm/test_0506']

    list_names = ['normal', 'tumor', 'test']
    for m in list_thres:

        new_folder = create_folder(result_folder, str(m*10))
        print(new_folder)

        for n in [0, 1, 2]:

            slide_paths = glob.glob(osp.join(list_slide_path[n], '*.tif'))
            slide_paths.sort()
            # print(slide_paths)

            heatmap_paths = glob.glob(osp.join(list_heatmap_path[n], '*.npy'))
            heatmap_paths.sort()
            # print(heatmap_paths)

            totalfeatures = []
            for i in range(len(heatmap_paths)):
                try:
                    heatmap = np.load(heatmap_paths[i])
                # the except here will give two same entry in the final table.
                except ValueError:
                    i = i+1
                    heatmap = np.load(heatmap_paths[i])
                # downsample the heatmap by 4, which is equal to stride 56
                heatmap = heatmap[0::4, 0::4]

                new_slide_path = [x for x in slide_paths if re.search(
                    osp.basename(heatmap_paths[i]).replace('.npy', '.tif'), x)]
                slide_path = new_slide_path[0]
                #slide_path = glob.glob(osp.join(slide_path, os.rename(split(basename(heatmap_path[i])))))

                #data_sheet_for_random_forest.at[i, 'name'] = osp.basename(slide_paths[i])

                heatmapbinary_lesion = (heatmap > m)*1
                #heatmapbinary_lesion = (heatmap > 0.5)*1
                number_lesion = len(get_region_props(
                    heatmapbinary_lesion, heatmap))
                if number_lesion == 0:

                    features = [0.00]*N_FEATURES

                else:

                    features = glob_features(
                        slide_path, heatmap) + local_features(heatmap, m)

                slide_contains_tumor = osp.basename(
                    slide_path).startswith('tumor_')
                slide_test = osp.basename(slide_path).startswith('test_')

                if slide_contains_tumor:
                    features = [1] + features
                    #data_sheet_for_random_forest.at[i, 'tumor'] = 1

                elif slide_test:

                    features = [np.nan] + features

                else:

                    features = [0] + features
                    #data_sheet_for_random_forest.at[i, 'tumor'] = 0

                # add file name to the first column.
                features = [osp.basename(slide_path)] + features
                #data_sheet_for_random_forest = data_sheet_for_random_forest.append(features)
                print(features)
                totalfeatures.append(features)
                #data_sheet_for_random_forest.append(pd.Series(features, index=cols[:]), ignore_index=True)
                #data_sheet_for_random_forest = data_sheet_for_random_forest.append(pd.Series(features, index=cols[2:]), ignore_index=True)

                #data_sheet_for_random_forest.at[i, 'name'] = osp.basename(slide_paths[i])

            data_sheet_for_random_forest = pd.DataFrame(
                totalfeatures, columns=cols)

            data_sheet_for_random_forest.to_csv(
                '%s/data_sheet_for_random_forest_56_strike_%s_%d_1023_Method_II_Model_I_norm.csv' % (new_folder, list_names[n], m*10))
