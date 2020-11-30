#$ -cwd
#$ -A  weizhe.li
#$ -l h_rt=002:00:00
#$ -S /bin/sh
#$ -j y
#$ -pe thread 7
#                           $ -N process_array  comes from process_main.sh

# $QSUB -pe thread -t $ST-$EN -o $SYSOUT_DIR $ARRAY_SCRIPT $SPLIT_BASE_DIR $HDF5_FILE

echo "Running $SGE_TASK_ID of job $JOB_ID on $HOSTNAME"

BASENAME=$(( $SGE_TASK_ID - $SGE_TASK_FIRST + 1 ))      # data set suffix

source /projects/mikem/UserSupport/weizhe.li/split_wsi/set_env.sh

# Get params
# source ./config.txt 
source $5

DIR=$1
HDF5_FILE=$2            # one HDF5 file may contain many datasets
HEATMAP_DIR=$3
export LOG_DIR=$4

export PYTHONUNBUFFERED=TRUE
export HDF5_USE_FILE_LOCKING=FALSE

# PROG=process_images_grp.py 
PROG=process_images_grp_normalization_wli.py
time python $PROG $DIR $HDF5_FILE $BASENAME $HEATMAP_DIR
