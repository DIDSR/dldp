#$ -cwd
#$ -A  weizhe.li
#$ -l h_rt=001:00:00
#$ -S /bin/sh
#$ -j y
#$ -o sysout_heatmap
#$ -N heatmap_main

echo "Running job $JOB_ID on $HOSTNAME"

QSUB=/opt/sge_root/bin/lx-amd64/qsub
ARRAY_SCRIPT=heatmap_ar.sh

declare -A dimensions
dimensions[normal]="/home/weizhe.li/li-code4hpc/pred_dim_0314/training-updated/normal/dimensions"
dimensions[tumor]="/home/weizhe.li/li-code4hpc/pred_dim_0314/training-updated/tumor/dimensions"
dimensions[test]="/home/weizhe.li/li-code4hpc/pred_dim_0314/testing/dimensions"

declare -A index_paths
index_paths[normal]="/home/weizhe.li/li-code4hpc/pred_dim_0314/training-updated/normal/patch_index"
index_paths[tumor]="/home/weizhe.li/li-code4hpc/pred_dim_0314/training-updated/tumor/patch_index"
index_paths[test]="/home/weizhe.li/li-code4hpc/pred_dim_0314/testing/patch_index"

slide_category=$1       # expects normal, tumor or test
Folder_dimension=${dimensions[$slide_category]}
slide_path=${slide_paths[$slide_category]}
index_path=${index_paths[$slide_category]}

Folder_Prediction_Results=$2
# expect like this: "/scratch/mikem/UserSupport/weizhe.li/runs_process_cn_True/normal_wnorm_448_400_7690666"

listfile="$slide_category"_preds_list     
ls -1 "$Folder_Prediction_Results" | grep $slide_category > $listfile

num=`ls -1 "$Folder_Prediction_Results" | grep $slide_category | wc -l`

SYSOUT_DIR="$Folder_Prediction_Results"/heatmap_sysout
mkdir -p $SYSOUT_DIR 

# test
# num=2

ARRAY_SCRIPT=heatmap_arr.sh
$QSUB -pe thread 1 -t 1-"$num" -o $SYSOUT_DIR  $ARRAY_SCRIPT  $listfile $Folder_Prediction_Results $Folder_dimension $index_path
