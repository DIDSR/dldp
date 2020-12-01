# Deep Learning for Digital Pathology (DLDP) - Camelyon 2016 dataset

    Weizhe Li, Weijie Chen
    
## ![Project Overview](https://github.com/3dimaging/Accessory/blob/master/workflow2.png "Project Overview")

## Code Overview

<img align="left" width="500" src="https://github.com/3dimaging/Accessory/blob/master/pipeline.png">

&nbsp;

Code link: [Training image extraction](https://github.com/DIDSR/dldp/tree/master/dldp/patch_extract "image patch extraction")

Code link: [Image processing](https://github.com/DIDSR/dldp/tree/master/dldp/image_process "image processing")

Code link: [Neural network training](https://github.com/DIDSR/dldp/tree/master/dldp/cnn_train "cnn training")

Code link: [Heatmap construction](https://github.com/DIDSR/dldp/tree/master/dldp/heatmap_pred "heatmap")

Code link: [Slide-based prediction](https://github.com/DIDSR/dldp/tree/master/dldp/model_eva/roc "ROC")

Code link: [Lesion-based prediction](https://github.com/DIDSR/dldp/tree/master/dldp/model_eva/froc "FROC")

Code link: [WSI-heatmap visualization](https://github.com/DIDSR/dldp/tree/master/dldp/wsi_visu)

[Code Documentation](https://github.com/DIDSR/dldp/blob/master/docs/build/html/index.html)
&nbsp;

- Note: The codes were developed on python 3.5, but also work for python 3.6

&nbsp;

## 0 - Preparation
### 0.1 Set up deep learning environment.

- [Setup Python Environment](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/requirements.txt)
  
- [Package Installation for Color Normalization](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/utils/Color_Normalization.md) 

	Note: SPAMS doesn't need to be installed mannually from source anymore since it can be installed through pip.
        
- Tensorflow and Keras version

	The code here was based on Keras 2.0.0 and Tensorflow 1.9. The compatibility between Tensorflow and Keras, and between Tensorflow and CUDA, are important, especially when the code runs on different machines. Certain machinse can only run some low version of Tensorflow that is compatible with a low version of Keras. When loading a model trained with higher version of Tensorflow and Keras to such a machine, the weights of the trained model would not be fully loaded, but it still works for testing (however, not for training, e.g., transfer learning). The code would need some changes if Keras with a version higher than 2.0.0 is used for model training (see the comments in the code for model training). 
  

### 0.2 ASAP installation and image display

#### OpenSlide

- [OpenSlide Installation](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/utils/OpenSlide_Installation.md)

- OpenSlide can serve as a backend for a web viewer of WSI. 

![alt text](https://github.com/3dimaging/Accessory/blob/master/webserver.png)

![alt text](https://github.com/3dimaging/Accessory/blob/master/webserver-enlarged.png)

#### ASAP

- [ASAP Installation](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/utils/ASAP_installation.txt)
   
### 0.3 Mask image generation

- Mask images can be generated from the xml files that store the pathologist's annotation of tumor contours and serve as ground truth for model training. The mask image is a binary image with normal tissue coded as ‘0’ and tumor tissue coded as ‘1’ for each corresponding pixel of a WSI image. To directly display the masks, the code here use 255 (rather than 1) for tumor pixels. See update for mask file generation on [Camelyon 17 website](https://camelyon17.grand-challenge.org/Data/).
- **Note**:
	- The mask file has a pyramid structure corresponding to multiple levels of magnification. Except for the 40x 		magnification at which the xml annotation was made, the mask size may be slightly different from the corresponding 	   WSI because the method used for creating the pyramid structure in the mask file may be different from that used for 		WSI.

	- The code below for the CAMELYON16 training slides is based on ASAP code, but we found that it did not work for testing slides. We therefore wrote our own mask generation code for the testing slides.


- [Code for Mask file generation - for training (tumor) WSIs](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/utils/mask_generation_asap.py)

- [Code for Mask file generation - for testing (tumor) WSIs](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/utils/xml_to_mask.py)
  
- Time consuming

- WSI and Mask file (Example): tumor_026

<img src="https://github.com/3dimaging/Accessory/blob/master/389e2c0cd56cf3ea1356fd03a2af35cc-94048Vj0.png" width="500">


### 0.4 Data Description (Important)

[CAMELYON16 Data Set](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/utils/Camelyon16_dataset_description.md)

- Note: Some tumor slides were not fully annotated. Normal_86: Originally misclassified, renamed to Tumor_111.
Test_049: Duplicate slide. Test_114: Does not have exhaustive annotations. Test_049 was removed (by the organizer) for slide based and lesion based tasks; Test_114 was removed (by the organizer) from lesion based tasks. 

### 0.5 - WSI Visulization with Annotation
#### Annotation Visulization

- Annotation Visulization Over Image Base on xml file

 <img src="https://github.com/3dimaging/Accessory/blob/master/annotation%20over%20wsi.png" width="250">


## 2 - Image processing

### 2.1 Image Segmentation 

To reduce computation, the blank regions (no tissue) on slide will be excluded.

- Color space switch to HSV

- Tissue region segmentation (Otsu’s method of foreground segmentation)

(code embedded in Patch Extraction)


### 2.2 Patch Extraction

[Extract normal image patches from normal slides](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/patch_extract/Extract_Normal_Patches_From_Normal_Slides.py)

[Extract normal and tumor image patches from tumor slides](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/patch_extract/Extract_Normal_and_Tumor_Patches_From_Tumor_Slides.py)

- Note: The codes for the following procedures are part of the modules for CNN training. 

#### Step 0 : tumor training images and normal training images were randomly divided into training and validation data set.

	          80% for training data set;
		  20% for validation data set. 
		  images for validation data set: 
		  tumor: tumor_002.tif, tumor_008.tif, tumor_010.tif, tumor_019.tif, tumor_022.tif, tumor_024.tif, tumor_025.tif, 
		         tumor_031.tif, tumor_040.tif, tumor_045.tif, tumor_049.tif, tumor_069.tif, tumor_076.tif, tumor_083.tif,
			 tumor_084.tif, tumor_085.tif, tumor_088.tif, tumor_091.tif, tumor_101.tif, tumor_102.tif, tumor_108.tif, 
			 tumor_109.tif
			 
		  normal: normal_003.tif, normal_013.tif, normal_021.tif, normal_023.tif, normal_024.tif, normal_030.tif, normal_031.tif
		  	  normal_040.tif, normal_045.tif, normal_057.tif, normal_062.tif, normal_066.tif, normal_068.tif,normal_075.tif,
			  normal_076.tif, normal_080.tif, normal_087.tif, normal_099.tif, normal_100.tif, normal_102.tif, normal_106.tif
			  normal_112.tif, normal_117.tif, normal_127.tif, normal_132.tif, normal_139.tif, normal_141.tif, normal_149.tif
			  normal_150.tif, normal_151.tif, normal_152.tif, normal_156.tif

#### Step 1 : Randomly extract patches (256 x 256) on the tissue region at the level of 40x
               
		Tumor slide : 1K positive and 1K negative from each slide. So total patches for tumor tissue: 111k

		Normal slide: 1K negative from each slide. So total patches for normal tissue: 111k + 159k = 270k
            

#### Step 2 : Crop 224x224 patches and conduct image augmentation

- Method I: [flip, rotation and cropping](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/image_process/patch_aug.py)

	 	For a 256x256 image patch from step 1, it was flipped,rotated 3 times. The original 256x256 image patch became 4 image patches. Then based on the 4 256x256 image patches, 2 224x224 image patches were randomly cropped from them. So I had total 8 224x224 image patches derived from 1 256x256 image patch. However, for normal image patches, only 1 224x224 image patches were randomly cropped from them.
		
		So, I have total image patches for tumor tissue: 111 x 8 = 888k, for normal tissue: 270 x 4 = 1080k
		
		
![Crop and Flip](https://github.com/3dimaging/Accessory/blob/master/crop%20and%20flip.png "crop and flip")

- Method II: stain (color) normalization and adding color noise

	      For method II, I will have 2 millions of 224x224 image patches for training model. Because, all the previous 224x224 image patches will be color-normalized, then be added color noise. The orginal image patch with color-normalization, plus the one with color noise will give me two 224 x 224 images from 1 224 x 224 images. So I will have total 888 x 2 = 1776k for tumor; 1080 x 2 = 2160k for normal tissue.

- [Stain (color) normalization](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/image_process/color_normalization.py)
	   
  The color variety among patches
	   
<p align="center">
 <img src="https://github.com/3dimaging/Accessory/blob/master/color%20variety.png" width="500">
</p>
	   
  The patches before and after stain normalization

<p align="center">
 <img src="https://github.com/3dimaging/Accessory/blob/master/color_norm2.png" width="500">
</p>

 
 - [Adding color noise](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/image_process/patch_aug.py)
 
 
 Dayong Wang's method (PathAI) (Based on HSV image patches):
 
 <img src="https://github.com/3dimaging/Accessory/blob/master/dayong_addingcolornoise_HSV.png" width="500">
 
 If the image patches were added by a big value that will cause the some pixel values larger than 255, the image patches after adding color noise will look like this (not preferred):
 
  <img src="https://github.com/3dimaging/Accessory/blob/master/dayong_addingcolornoise_rgb.png" width="500">
 
 Yun Liu's method (Google) (also called color perturbation):
 
 <img src="https://github.com/3dimaging/Accessory/blob/master/color_pertubation_liu_yun_1.png" width="500">
 <img src="https://github.com/3dimaging/Accessory/blob/master/color_perturbation_liu_yun_2.png" width="500">

		
#### Step 3 : [Image Generator](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/cnn_train/Training_Patch_Pre.py)

 Patches:
 
 <img src="https://github.com/3dimaging/Accessory/blob/master/patches.png" width="500">
 
 
 Ground Truth:
 
 <img src="https://github.com/3dimaging/Accessory/blob/master/patche%20ground%20truth.png" width="500">



## 3 - Training Neural Network

### Flowchart for Model Training and Prediction

<img src="https://github.com/3dimaging/Accessory/blob/master/workflow%20for%20model%20training.png" width="900">

### GoogleNet (Inception V1) Training

#### Step 1: Network Training

[Training GoogleNet](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/cnn_train/main.py)

- Optimization method: Stochastic gradient descent

- Weight initialization: Random sampling from a Gaussian distribution

- Batch size: 32

- Batch normalization: No

- Regularization: L2-regularization (0.0005) and 50% dropout

- Learning rate: 0.01, multiplied by 0.5 every 50,000 iterations (0.01, multiplied by 0.1 per epoch)

- Activation function: ReLu

- Loss function: Cross-entropy

- Number of training epochs/iterations: 300,000 iterations

#### Step 2: Hard Negative Mining

    Details (11-06-18): 120k 224x224 image patches were extracted based on the predicted; then augmentation were performed by using rotation and horizontal flip. For example, 1 224x224 image patch was rotated 3 times, and get 4 image patches. Then the 4 image patches were flipped horizontal and get total 8 different patches. So, total about 1 million of patches were used for hard negative mining. 
    To get a model with hard negative mining, googlenet v1 was retrained by adding the above mentioned 1 million of patches to my original training patches (1 million of normal 224 patches and 1 million of tumor 224 patches). 

##### [Extract False Positive Patches](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/image_process/main_pred_hnm_workstation.py)

 - Prerequest
 
	 A: a trained CNN model
	 B: [patch_index.py in utils](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/utils/patch_index.py needs to be run first to get postion information of images patches to be predicted.

 - [A HPC version is available](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/heatmap_pred/main_pred_hnm_hpc.py)

 - False positive patches
 
  <img src="https://github.com/3dimaging/Accessory/blob/master/false%20positive%20patches.png" width="900">
  
 - Some false positive patches from partially annotated tumor slides are real positive and will be excluded. 
 
   <img src="https://github.com/3dimaging/Accessory/blob/master/wrong%20predicted%20patches.png" width="900">
   
##### Neural Network Training with False Positive Patches

 The training will use [the same code](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/cnn_train/main.py), but with the folder (hnm_dir) for false positive patches included. 
 
#### Step 3: Neural Network Training with False Positive Patches and Normal Patches Near Tumor Regions

##### [Extract Normal Patches Near Tumor Regions](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/image_process/patches_near_tumor.py)

##### Neural Network Training with False Positive Patches and Normal Patches Near Tumor Regions

The training will use [the same code](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/cnn_train/main.py), but with the folder ("hnm_dir") for false positive patches and the folder ("pnt_dir") for normal patches near tumor regions included. 


## 4 - Prediction and Evaluation

### 4.1 Make predictions and Heatmap stitching

![prediction on HPC](https://github.com/3dimaging/Accessory/blob/master/HPC_new.png "Prediction on HPC")

Test images were divided into non-overlapping small patches; each patch will get a predicted image for each pixel assigned by probability.

Heatmap Generation 
 
 - Prerequrest: [patch_index.py in utils](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/utils/patch_index.py) needs to be run first to get image patch information like location in WSI. 
 
 - [Code for prediction - slide window - googlenet - HPC version](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/heatmap_pred/Pred_Slide_Window_For_Heatmap_main.py)
 
 - [Code for prediction - slide window - googlenet - Workstation version](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/heatmap_pred/Pred_Slide_Window_For_Heatmap_main_workstation.py)

 - Put all the patches together and get prediction for the whole slide ([code for heatmap stitching - HPC version](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/heatmap_pred/Heat_Map_Build0319_betsy.py)). 
 
 - Put all the patches together and get prediction for the whole slide ([code for heatmap stitching - Workstation version](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/heatmap_pred/Heat_Map_Build0319_workstation.py)).

#### Heatmap Examples (From GoogleNet Prediction Only)

the heatmap for test_075 (the part with score < 0.5 is not shown here)

![test_075](https://github.com/3dimaging/Accessory/blob/master/test_075.png "test_075")


the heatmap for test_073 (the part with score < 0.5 is not shown here)

![test_073](https://github.com/3dimaging/Accessory/blob/master/test_073.png "test_073")

Comparison of predicted with ground truth for tumor_005:

![alt text](https://github.com/3dimaging/Accessory/blob/master/49285XZv.png)

#### If some tasks on HPC fail

##### Step 1: [find the failed tasks](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/heatmap_pred/task_id_remained.py)

##### Step 2: [redo the failed tasks](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/heatmap_pred/task_id_makeup.py)

##### Step 3: [copy the results](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/heatmap_pred/copy_makeup_files.py)
    
### 4.2a Slide-based Classification


#### [Extracting Features from Heatmaps for Whole-slide Image Classification](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/model_eva/roc/Parameter_Extraction_For_Random_Forest_Batch.py)

##### Global Features Extraction

1. The ratio between the area of metastatic regions and the tissue area.
2. The sum of all cancer metastases probailities detected in the metastasis identification task, divided by the tissue area. 
caculate them at 5 different thresholds (0.5, 0.6, 0.7, 0.8, 0.9), so the total 10 global features

##### Local Features Extraction 

Based on 2 largest metastatic candidate regions (select them based on a threshold of 0.5).

10 features were extracted from the 2 largest regions:

1. Area: the area of connected region
2. Eccentricity: The eccentricity of the ellipse that has the same second-moments as the region
3. Extend: The ratio of region area over the total bounding box area
4. Bounding box area
5. Major axis length: the length of the major axis of the ellipse that has the same normalized second central moments as the region
6. Max/mean/min intensity: The max/mean/minimum probability value in the region
7. Aspect ratio of the bounding box
8. Solidity: Ratio of region area over the surrounding convex area

#### Results

 <img src="https://github.com/3dimaging/Accessory/blob/master/feature%20extraction.png" width="1000">
 
#### [Random Forest Training and Testing](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/model_eva/roc/RF_training_batch.py)

##### Important Features

<img src="https://github.com/3dimaging/Accessory/blob/master/important%20features.png" width="1000">


### 4.2b Lesion-based Detection

- Combine the prediction results from Model-1 and Model-2

Model-1 is the model from step 2 (with hard negative mining) in section 3 - "Training Neural Netowrk";

Model-2 is the model from step 3 (with hard negative mining patches and normal patches near tumor regions) in section 3 - "Training Neural Netowrk".

The x, y coordinates of predicted tumor lesion come from Model-1; The scores of predicted tumor lesion are the average of scores from Model-1 and Model-2.

- [Lesion-based detection](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/model_eva/froc/FROC_csv_0604.py)


### 4.3 ROC and FROC Generation
#### ROC
 
 - Results
 
![ROC curves](https://github.com/3dimaging/Accessory/blob/master/ROC.png "roc") 

 - Note: ROC curve is generated in the [python script](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/model_eva/roc/RF_training_batch.py) as mentioned above.
 
 - [Code for AUC](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/model_eva/roc/script_auc.R)

#### FROC
 
 - [Code for FROC](https://github.com/DIDSR/DeepLearningCamelyon/blob/master/dldp/dldp/model_eva/froc/FROC_Calcu_with_home_made_mask.py)
 
 - Result
 
 ![FROC](https://github.com/3dimaging/Accessory/blob/master/FROC.png "FROC")


# References
-  Wang, D., et al., Deep learning for identifying metastatic breast cancer
https://arxiv.org/abs/1606.05718

-  Diagnostic Assessment of Deep Learning Algorithms for Detection of Lymph Node Metastases in Women With Breast Cancer.
https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5820737/?report=reader#!po=59.4340

- Litjens G., et al., 1399 H&E-stained sentinel lymph node sections of breast cancer patients: the CAMELYON dataset
https://academic.oup.com/gigascience/article/7/6/giy065/5026175
