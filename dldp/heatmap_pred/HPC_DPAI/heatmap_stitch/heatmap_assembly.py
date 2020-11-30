####################################################################################################
""" 
Heatmap assembly
=================
After prediction, each patch from a WSI image has one prediction matrix (for example, 14x14). This script is
used to put all these small matrix into a big map corresponding to a rectangle tissue region of a
WSI image.

How to use
----------
The following variables needed to be set:

: param Folder_Prediction_Results: the location of the prediction for individual patches
: type Folder_Prediction_results: str
: param slide_category: the category of the slide, for example, 'tumor', 'normal', 'test'
: type slide_category: str
: param Folder_Heatmap: the folder to stoe the stitched heatmap
: type Folder_Heatmap: str
: param Stride: the skipped pixels when prediction, for example, 16, 64 
: type Stride: int

Note
----
The following files are necessary to perform the task:
'/home/weizhe.li/li-code4hpc/pred_dim_0314/training-updated/normal/dimensions',
'/home/weizhe.li/li-code4hpc/pred_dim_0314/training-updated/tumor/dimensions',
'/home/weizhe.li/li-code4hpc/pred_dim_0314/testing/dimensions' 

These files store the dimension of the heatmap and location of the heatmap in the WSI image.

"""
####################################################################################################
import os
import os.path as osp
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import glob
#import multiprocess as mlp
import re
####################################################################################################


def pred_collect(pred_folder):
    
    files = glob.glob(osp.join(pred_folder, '*.npy'))
    files.sort(key=lambda f: int(f.split('_t')[1].split('.')[0]))
    # create a empty list to store all the small heatmap files (160, 14, 14) list. 
    heat_map = []
    for file in files:
        regions = np.load(file)
        heat_map.extend(regions)


    heat_map_array = np.array(heat_map)
    
    return heat_map_array


def stitch_preded_patches(dim, index, pred_folder, Folder_Heatmap, Stride):
    
    """
    stitching the prediction based on each small patches to a big heatmap
    
    :param dimension_files: a list of all the dimension files for one category of slides, foe example, 'tumor' 
    :type dimension_files: list
    :param pred_folder: the folder having all the patch prediction results for a single WSI image.
    :type pred_folder: str
    :param Folder_Heatmap: the folder to store the big stitched heatmap.
    :type Folder_Heatmap: str
    :param stride: the stride during prediction
    :type stride: int
    
    :return: no return
    
    :note: two files will saved to the Folder_Heatmap:
            1. the stitched heatmap in npy format
            2. the heatmap picture in png format
    """
    
    num_of_pred_per_patch = int(224/Stride)

    # heat_map_big = np.zeros([dim[7]*num_of_pred_per_patch, dim[8]*num_of_pred_per_patch], dtype=np.float32)
    
    # generate a list of all npy files inside one folder.

    heat_map_array = pred_collect(pred_folder)
    heat_map_array_iter = iter(heat_map_array)
    
    # construct the full heat_map array
    no_tissue_region = np.zeros([int(224/Stride), int(224/Stride)], dtype = np.float32)
    # no_tissue_region = np.zeros([12, 12], dtype=np.float32)
    heat_map_all = []
    for _, item in index.iterrows():
        
        if item.is_tissue:
            patch_pred = next(heat_map_array_iter)
            heat_map_all.extend(patch_pred)
            #print(patch_pred)
        else:
            heat_map_all.extend(no_tissue_region)

        
    heat_map_all = np.array(heat_map_all)
    print(heat_map_all.shape)
        
    # These are critical steps to construct heatmap in a time saving manner. 
    heat_map_reshape = heat_map_all.reshape(dim[7], dim[8], num_of_pred_per_patch, num_of_pred_per_patch)
    
    b = heat_map_reshape.transpose((0, 2, 1, 3))

    # c = b.reshape(heat_map_big.shape[0], heat_map_big.shape[1])
    # c = b.reshape(heat_map_big.shape[0], heat_map_big.shape[1])
    c = b.reshape(dim[7]*num_of_pred_per_patch, dim[8]*num_of_pred_per_patch)
    
    np.save('%s/%s_oldmodel_test_001n' % (Folder_Heatmap, osp.basename(pred_folder)), c)

    matplotlib.image.imsave('%s/%s_oldmodel_test_001n.png' % (Folder_Heatmap, osp.basename(pred_folder)), c)

 
if __name__ == "__main__":
    
    taskid = int(os.environ['SGE_TASK_ID'])
    
    # Here is the folder for prediction results.The prediction results are organized into folders. Each folder corresponds to a WSI image.
    # Folder_Prediction_Results = '/scratch/mikem/UserSupport/weizhe.li/runs_process_cn_True/normal_wnorm_448_400_7690666'
    Folder_Prediction_Results = os.environ['Folder_Prediction_Results']

    Folder_dimension = os.environ['Folder_dimension']
    index_path = os.environ['index_path']

    dimension_files = glob.glob(osp.join(Folder_dimension, '*.npy'))
    dimension_files.sort()
    
    print(dimension_files)

    index_files = glob.glob(osp.join(index_path, '*.pkl'))
    index_files.sort()

    # Folder_Heatmap = '/scratch/weizhe.li/heat_map/HPC/test'
    Folder_Heatmap = os.environ['Folder_Heatmap']
    
    Stride = 16

    i = taskid - 1
    
    dir = os.environ['dir']
    pred_folder = osp.join(Folder_Prediction_Results, dir, 'preds')
    dimension_file = dimension_files[i]
    dimension = np.load(dimension_file)
    print(dimension[7])
    index_file = index_files[i]
    index = np.load(index_file)

    print(pred_folder)
    stitch_preded_patches(dimension, index, pred_folder, Folder_Heatmap, Stride)
