import os
import sys

import numpy as np
from openslide import open_slide  
import openslide

import csv
import time

import tables
import h5py
from datetime import timedelta

import pandas as pd
import numpy as np

def main():
    ''' Six command line arguments:
        - $FILE_DIR      location of WSI, tif files, like /scratch/wxc4/CAMELYON16-testing
        - $FILE          name of WSI, like test_001.tif
        - $PATCH_SIZE
        - $SPLIT_SIZE    number of the sampled patches in one hdf5 file
        - $SPLIT_DIR     output location of split parts/sets, like /projects/mikem/UserSupport/weizhe.li/split_imgs/test_001
            
        Note: patch_size is the dimension of the sampled patches, NOT equivalent to openslide's definition
        of tile_size. This implementation was chosen to allow for more intuitive usage.
    '''
    # print command line arguments
    for arg in sys.argv[1:]:
        print (arg)

    print (os.environ['HOSTNAME'])
    print (os.environ['SGE_TASK_ID'])
    
    x = int(os.environ['SGE_TASK_ID'])
    print ("x = ", x)

    file_dir = sys.argv[1] 
    file = sys.argv[2]
    p_size = int(sys.argv[3]) 
    s_size = int(sys.argv[4]) 
    split_dir = sys.argv[5] 

    print ("file_dir = " + file_dir)
    print ("file = " + file)
    print ("p_size = " + str( p_size))
    print ("s_size = " + str( s_size))
    print ("split_dir = " + split_dir)
     
    ''' - limit_bounds      activates OpenSlide's automatic boundary limits (cuts out some background)
    '''
    patch_count = split_and_store_patches( file,
                                file_dir,
                                patch_size=p_size,
                                split_size=s_size, 
                                db_location=split_dir)
# end of main () 

def split_and_store_patches(file_name,
                             file_dir,
                             patch_size=448,
                             split_size=160, 
                             db_location=''):
    ''' Sample patches of specified size from .tif file.
        - file_name             name of whole slide image to sample from
        - file_dir              directory file is located in
    '''
    pred_size = int(os.environ['PRED_SIZE'])                  # Dimensiuons expand ratio 224 now

    slide_path = file_dir + "/" + file_name
    slide = openslide.open_slide(slide_path)

    index_dir=os.environ['INDEX_DIR']
    index_file_path=index_dir + "/" + file_name[:-4] + '.pkl' 

    index_file = pd.read_pickle(index_file_path)
    
    # Drop the rows with 'is_tissue' is 0. 0 means this image patches is not from a speciman. 
    index_file = index_file[index_file['is_tissue'] > 0] # please pay attention to the index of dataframe
    # num_samples = len(index_file)
    
    hdf5_file = h5py.File(db_location + "/" + file_name[:-4] + '.h5','w')
    
    num_grp = 0 ; 
    count = 0 ;                  # number of subgroups in the h5 file
    patches, coords = [], []
    
    start_time = time.time()

    for _, batch_sample in index_file.iterrows():
        xy = batch_sample.tile_loc[::-1] # the "-1" is very important. It switches the x, y for openslide.

        # This will avoid go outside of WSI image.
        # xylarge = [abs(x * pred_size - pred_size//2) for x in xy]
        
        # if xy[0] == 0 or xy[1] == 0:
        #    xylarge = [x * pred_size for x in xy]
        # else:
        #    xylarge = [x * pred_size - pred_size//2 for x in xy]
        
        xylarge = [x * pred_size for x in xy] # placeholder, this will change
        
        if xy[0] == 0 and xy[1] == 0:
             xylarge = [x * pred_size for x in xy]
        elif xy[0] == 0 and xy[1] != 0:
             xylarge [0] = xy[0] * pred_size
             xylarge [1] = xy[1]  * pred_size - pred_size//2
        elif xy[0] != 0 and xy[1] == 0:
             xylarge [0] = xy[0]  * pred_size - pred_size//2
             xylarge [1] = xy[1] * pred_size
        else:
             xylarge = [x * pred_size - pred_size//2 for x in xy]        
        
        # Please double check
        if xylarge[0]+patch_size > slide.dimensions[0]:
            xylarge[0] = xylarge[0] - (xylarge[0] + patch_size - slide.dimensions[0]-1)
        if xylarge[1]+patch_size > slide.dimensions[1]:
            xylarge[1] = xylarge[1] - (xylarge[1] + patch_size - slide.dimensions[1]-1)

        new_tile = generate_patches(slide, xylarge, patch_size)
        
        # Debug
        # print("Added: ", str (x_inc), " ", str (y_inc), " ", str (x), " ", str (y))
        
        patches.append(new_tile)
        coords.append(np.array([xy[0], xy[1], xylarge[0], xylarge[1], patch_size]))
        count += 1
     
        if ( count % split_size == 0 ) :
            # Write to HDF5 files all in one go.
            save_to_hdf5(db_location, patches, coords, str(count // split_size), hdf5_file)
            num_grp += 1
            
            print("Group " + str(num_grp ) + ": --- %s seconds ---" % (time.time() - start_time))
            start_time = time.time()    # restart timer
            
            # debug 
            print ("len(coords) = " + str(len(coords))) 
            print ("count = " + str(count)) 
            print ("num_grp = " + str(num_grp)) 

            del patches
            del coords
            patches, coords = [], [] # Reset right away.
                

    if count % split_size != 0:
        # Write to HDF5 files all in one go.
        save_to_hdf5(db_location, patches, coords, str(count // split_size + 1), hdf5_file)
        num_grp += 1

        print("Group " + str(num_grp ) + ": --- %s seconds ---" % (time.time() - start_time))
       
        # debug 
        print ("len(coords) = " + str(len(coords))) 
        print ("count = " + str(count)) 
        print ("num_grp = " + str(num_grp)) 
 

    row = [ num_grp, file_name[:-4] ]
    # writing to csv file 
    with open(db_location + "/" + file_name[:-4] + '.csv', 'w') as csvfile: 
        csvwriter = csv.writer(csvfile, delimiter = ' ')     # creating a csv writer object 
        csvwriter.writerow(row)           # writing the data rows    
    
    return count

# end of split_and_store_patches()

def generate_patches(slide, xylarge, ps):
    """
    To extract 448x448 patches from WSI for prediction
    :param object slide: slide object from OpenSlide
    :param list xylarge: the x, y coordinates for the position where the patch
                          should be extracted
    :return array img: a 448x448 patch, only 3 channels (R, G, B)
    """
    img = slide.read_region(xylarge, 0, (ps, ps))
    img = np.array(img)
    img = img[:, :, :3]
    
    return img


###########################################################################
#                Option 2: store to HDF5 files                            #
###########################################################################

def save_to_hdf5(db_location, patches, coords, file_name, hdf5_file):
    """ Saves the numpy arrays to HDF5 files. A sub-group of patches from a single WSI will be saved
        to the same HDF5 file
        - db_location       folder to save images in
        - patches           numpy images
        - coords            x, y tile coordinates
        - file_name         number, like 1, 2,  
        - hdf5_file        one hdf5 wil contain many datasets
    """
    # Save patches into hdf5 file.
    subgrp='t'+file_name
    grp = hdf5_file.create_group(subgrp) ;
    dataset = grp.create_dataset("img", np.shape(patches), 
                                dtype=np.uint8, data=patches)
                                # dtype=np.uint8, data=patches, compression="szip")
                                # , compression_opts=9)
                                
    dataset2 = grp.create_dataset("coord", np.shape(coords), 
                                  dtype=np.int64, data=coords)
    
# end of save_to_hdf5 ()



if __name__ == "__main__":
    main()
    
    
