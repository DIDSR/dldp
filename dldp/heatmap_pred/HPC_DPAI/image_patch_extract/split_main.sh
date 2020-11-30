#$ -cwd
#$ -A  weizhe.li
#$ -l h_rt=001:00:00
#$ -S /bin/sh
#$ -j y
#$ -o sysout_main
#$ -N split_main

echo "Running job $JOB_ID on $HOSTNAME"

QSUB=/opt/sge_root/bin/lx-amd64/qsub
ARRAY_SCRIPT=split_grp.sh

# Get params
# source ./config.txt 
# CNFG_FILE="./config_normal.txt"
CNFG_FILE=$1
source $CNFG_FILE 

ls -1 $FILE_DIR > $LISTFILE

mv $SPLIT_BASE_DIR "$SPLIT_BASE_DIR"_"$JOB_ID" 2>/dev/null
mkdir -p $SPLIT_BASE_DIR

SG_DIR=/scratch/mikem/UserSupport/weizhe.li/runs_split_group
mkdir -p $SG_DIR
BASE_DIR="$TYPE"_"$SG_DIR"/"$PATCH_SIZE"_"$SPLIT_SIZE"_"$JOB_ID"

ST=1
EN=`cat $LISTFILE | wc -l`
SYSOUT_DIR="$BASE_DIR"/sysout
mkdir -p $SYSOUT_DIR 


# test
# ST=1
# EN=3

echo "$QSUB -pe thread -t "$ST"-"$EN" -o $SYSOUT_DIR $ARRAY_SCRIPT"
$QSUB -pe thread 1 -t "$ST"-"$EN" -o $SYSOUT_DIR -N sg_"$TYPE" $ARRAY_SCRIPT $CNFG_FILE
