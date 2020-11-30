
import sys
import time

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
import cv2
from keras.utils.np_utils import to_categorical

import os.path as osp
import os 
import openslide
from pathlib import Path
from keras.models import Sequential
from keras.layers import Lambda, Dropout
from keras.layers.convolutional import Convolution2D, Conv2DTranspose
from keras.layers.pooling import MaxPooling2D
from keras.models import model_from_json
import numpy as np
import sys
import skimage.io as io
import skimage.transform as trans
import numpy as np
from keras.models import *
from keras.layers import *
from keras.optimizers import *
from keras.callbacks import ModelCheckpoint, LearningRateScheduler
from keras import backend as keras
import re
import staintools
#############################################
import h5py
from keras.utils import HDF5Matrix
import stain_utils as utils
import stainNorm_Reinhard
import stainNorm_Macenko
import stainNorm_Vahadane

from datetime import datetime

cores = int(os.environ['NSLOTS'])
keras.set_session(keras.tf.Session(config=keras.tf.ConfigProto(intra_op_parallelism_threads=cores, inter_op_parallelism_threads=cores)))

pred_size = int(os.environ['PRED_SIZE'])
stride = 16

mcn = os.environ['MCN']
model = load_model(mcn, compile=False)
        # '/home/weizhe.li/Training/googlenetmainmodel1119HNM-02-0.92.hdf5')
        # '/home/weizhe.li/Training/googlenetmainmodel1119HNM-02-0.92.hdf5', compile=False)
#    '/home/weizhe.li/Training/HNM_models/no_noise_no_norm/googlenetv1_no_noise_no_norm_0210_hnm_transfer_learn_02.10.20_09:31_original_256_patches-03-0.91.hdf5', compile=False)

# /home/weizhe.li/Training/googlenetmainmodel1119HNM-02-0.92.hdf5

def main():
    ''' Four command line arguments:
        - $DIR           Directory where HDF5 is located
        - $HDF5_FILE     HDF5 file name, like test_001.h5
        - $BASENAME      subgroup suffix, like 1, 2, ... 
        - $HEATMAP_DIR   heatmap directory name
    '''

    # print command line arguments
    for arg in sys.argv[1:]:
        print (arg)

    print (os.environ['HOSTNAME'])
    print (os.environ['SGE_TASK_ID'])
    
    x = int(os.environ['SGE_TASK_ID'])
    print ("x = ", x)

    dir = sys.argv[1] 
    hdf5_file = sys.argv[2] 
    grp_suffix = sys.argv[3]
    heatmap_dir = sys.argv[4] 

    print ("dir = " + dir)
    print ("hdf5_file = " + hdf5_file)
    print ("grp_suffix = " + grp_suffix)
    print ("heatmap_dir = " + heatmap_dir)
     
    # patches, coords = [], [] 
     
    start_time = time.time()
     
    # patches, coords = get_patches( dir,
    get_patches( dir, hdf5_file, grp_suffix, heatmap_dir, verbose=True)
    
    print("--- %s seconds ---" % (time.time() - start_time))
    
# end of main () 

###########################################################################
#                HDF5-specific helper functions                           #
###########################################################################

def get_patches(db_location, file_name, grp_suffix, heatmap_dir, verbose=False):
    """ Loads the numpy patches from HDF5 files.
    """
    patches, coords = [], []
    
    # Now load the images from H5 file.
    file = h5py.File(db_location + "/" + file_name,'r+')
    grp='t'+grp_suffix
    # dataset = file['/' + ds]
    group = file['/' + grp]
    
    for key, value in group.items():
        if key == 'img':
            dataset=value
        if key == 'coord':
            dataset2=value    
    
    new_patches = np.array(dataset).astype('uint8')
    # for patch in new_patches:
    #    patches.append(patch)
    print ("COLOR_NORM on line # 133 is: ", color_norm)
    output_preds_final_grp = []
    for patch in new_patches:
        ################################################color normalization##############################
        if color_norm:
            patch_normalized = color_norm_pred(patch, fit, log_file, current_time)
        else:
            patch_normalized = patch
        output_preds_final = patch_pred_collect_from_slide_window(pred_size, patch_normalized, model, stride)
        output_preds_final_grp.append(output_preds_final)
    output_preds_final_grp = np.array(output_preds_final_grp)
    np.save(osp.join(heatmap_dir, '%s_%s' % (file_name[:-3], grp)), output_preds_final_grp)
       
    print ("Group " + grp)
        
    # dataset2 = group['/' + "coord"]
    new_coords = np.array(dataset2).astype('int64') 
    for coord in new_coords:
        coords.append(coord)
    
    file.close()

    # output_preds_final_160 = []
    # for i in range(len(patches)): 
    #    output_preds_final = patch_pred_collect_from_slide_window(pred_size, patches[i], model, stride)
    #    output_preds_final_160.append(output_preds_final)
    # output_preds_final_160 = np.array(output_preds_final_160)
    # np.save(osp.join(heatmap_dir, '%s_%s' % (file_name[:-3], grp)), output_preds_final_160)

    if verbose:
        print("[py-wsi] loaded from", file_name, grp)

    # return patches, coords

# end of get_patches ()


def patch_pred_collect_from_slide_window(pred_size, fullimage, model, stride):
    """
    create a nxn matrix that includes all the patches extracted from one big patch by slide window sampling.
    
    :param integer pred_size: the size of patches to be extracted and predicted as tumor or normal patch.
    :param nxn matrix fullimage: the image used for slide window prediction, which is larger than the patch to be predicted to avoid side effect.
    :param object model: the trained network to predict the patches.
    
    :return a nxn matrix for one patch to be predicted by slide window method
    """
    
    output_preds_final = []
    
    for x in tqdm(range(0, pred_size, stride)):
        patchforprediction_batch = []
        
        for y in range(0, pred_size, stride):
            patchforprediction = fullimage[x:x+pred_size, y:y+pred_size]
            patchforprediction_batch.append(patchforprediction)
    
        X_train = np.array(patchforprediction_batch)
        preds = predict_batch_from_model(X_train, model)
        output_preds_final.append(preds)
    
    output_preds_final = np.array(output_preds_final)
    
    return output_preds_final

# end of patch_pred_collect_from_slide_window


def predict_batch_from_model(patches, model):
    """
    There are two values for each prediction: one is for the score of normal patches.
    ; the other one is for the score of tumor patches. The function is used to select
    the score of tumor patches
    :param array patches: a list of image patches to be predicted.
    :param object model: the trained neural network.
    :return lsit predictions: a list of scores for each predicted image patch. 
                              The score here is the probability of the image as a tumor
                              image.
            
    """
    predictions = model.predict(patches)
    predictions = predictions[:, 1]
    return predictions

# end of predict_batch_from_model

def color_normalization(template_image_path, color_norm_method):
    """
    The function put all the color normalization methods together.
    :param string template_image_path: the path of the image used as a template
    :param string color_norm_method: one of the three methods: vahadane, macenko, reinhard.
    :return object 
    """
    template_image = staintools.read_image(template_image_path)
    standardizer = staintools.LuminosityStandardizer.standardize(
        template_image)
    if color_norm_method == 'Reinhard':
        color_normalizer = stainNorm_Reinhard.Normalizer()
        color_normalizer.fit(standardizer)
    elif color_norm_method == 'Macenko':
        color_normalizer = stainNorm_Macenko.Normalizer()
        color_normalizer.fit(standardizer)
    elif color_norm_method == 'Vahadane':
        color_normalizer = staintools.StainNormalizer(method='vahadane')
        color_normalizer.fit(standardizer)
    
    return color_normalizer

def color_norm_pred(image_patch, fit, log_file, current_time):
    """
    To perform color normalization based on the method used.
    :param matrix img: the image to be color normalized
    :param object fit: the initialized method for normalization
    :return matrix img_norm: the normalized images
    :note if the color normalization fails, the original image patches
          will be used. But this event will be written in the log file.
    """
    img = image_patch
    img_norm = img
    try:
        img_standard = staintools.LuminosityStandardizer.standardize(img)
        img_norm = fit.transform(img_standard)
    except Exception as e:
        log_file.write(str(image_patch) + ';' + str(e) + ';' + current_time)
    #print(img_norm)
    return img_norm

# end of color_norm_pred

if __name__ == "__main__":
    current_time = datetime.now().strftime("%d-%m-%Y_%I-%M-%S_%p")
    color_norm_methods = ['Vahadane', 'Reinhard', 'Macenko']
    template_image_path = '/home/weizhe.li/tumor_st.png'
    # log_path = '/home/weizhe.li/log_files'
    # color_norm = True
    cn = os.environ['COLOR_NORM']
    if (cn == "True"): 
        color_norm = True
    else:     
        color_norm = False
    
    if color_norm:
        print ("COLOR_NORM on line # 276 is: ", color_norm)
        color_norm_method = color_norm_methods[0]
        fit = color_normalization(template_image_path, color_norm_method)    
    else:
        print ("COLOR_NORM on Line # 280 is: ", color_norm)
        color_norm_method = 'baseline'
        fit = None
    
    log_path = os.environ['LOG_DIR']
    log_file = open('%s/%s.txt' % (log_path, color_norm_method), 'w')

    main()
