#$ -cwd
#$ -A  weizhe.li
#$ -l h_rt=048:00:00
#$ -l h_vmem=10G
#$ -S /bin/sh
#$ -j y
#$ -N heatmap_arr

# $listfile $Folder_Prediction_Results $Folder_dimension $index_path

echo "Running task $SGE_TASK_ID of job $JOB_ID on $HOSTNAME"

source /projects/mikem/UserSupport/weizhe.li/split_wsi/set_env.sh

listfile=$1

export dir=$(awk "NR==$SGE_TASK_ID" $listfile)

export Folder_Prediction_Results=$2
export Folder_dimension=$3
export index_path=$4
export Folder_Heatmap="$Folder_Prediction_Results"/"$dir"/heatmap
mkdir -p $Folder_Heatmap

# debug
echo "Folder_dimension = $Folder_dimension"
echo "index_path = $index_path"


PROG=heatmap_assembly.py
time python $PROG 
