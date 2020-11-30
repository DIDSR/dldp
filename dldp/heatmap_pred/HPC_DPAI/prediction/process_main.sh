#$ -cwd
#$ -A  weizhe.li
#$ -l h_rt=001:00:00
#$ -S /bin/sh
#$ -j y
#$ -o sysout_main
#$ -N process_main

echo "Running job $JOB_ID on $HOSTNAME"

QSUB=/opt/sge_root/bin/lx-amd64/qsub
ARRAY_SCRIPT=process_array.sh

# Get params
# source ./config.txt 
CNFG_FILE=$1
source $CNFG_FILE

BASE_RUN=/scratch/mikem/UserSupport/weizhe.li/runs_process_cn_V2_"$COLOR_NORM"
mkdir -p $BASE_RUN
BASE_DIR=$BASE_RUN/"$TYPE"_wnorm_"$PATCH_SIZE"_"$SPLIT_SIZE"_"$JOB_ID"

{ read; # skip the first (title) line
    while read LINE; do
        echo "$LINE"
        ST=$(echo $LINE | awk -F' ' '{printf $1}' )
        EN=$(echo $LINE | awk -F' ' '{printf $2}' )
        SUBDIR=$(echo $LINE | awk -F' ' '{printf $3}' )
        HDF5_FILE="$SUBDIR"".h5"
        IMG_DIR="$BASE_DIR"/"$SUBDIR"
        SYSOUT_DIR="$IMG_DIR"/sysout
        mkdir -p $SYSOUT_DIR 
        HEATMAP_DIR="$IMG_DIR"/preds
        mkdir -p $HEATMAP_DIR 
        
        # LOG_DIR=/home/weizhe.li/log_files
        LOG_DIR="$IMG_DIR"/log_files
        mkdir -p $LOG_DIR 
        
        echo "$QSUB -pe thread -t "$ST"-"$EN" -o $SYSOUT_DIR $ARRAY_SCRIPT $SPLIT_BASE_DIR $HDF5_FILE"
        $QSUB -t "$ST"-"$EN" -o $SYSOUT_DIR -N "$SUBDIR"_"$TYPE" $ARRAY_SCRIPT $SPLIT_BASE_DIR $HDF5_FILE $HEATMAP_DIR $LOG_DIR $CNFG_FILE
    done
} < $LOOKUP_FILE
