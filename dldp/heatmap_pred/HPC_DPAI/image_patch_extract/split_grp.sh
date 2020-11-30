#$ -cwd
#$ -A weizhe.li
#$ -l h_rt=048:00:00
#$ -S /bin/sh
#$ -j y
#                           $ -N split_grp comes from split_main.sh

echo "Running $SGE_TASK_ID of job $JOB_ID on $HOSTNAME"

source /projects/mikem/UserSupport/weizhe.li/split_wsi/set_env.sh

# Get params
# source ./config.txt
source $1

FILE=$(awk "NR==$SGE_TASK_ID" $LISTFILE)

export PYTHONUNBUFFERED=TRUE
PROG=split_grp.py
time python $PROG $FILE_DIR $FILE $PATCH_SIZE $SPLIT_SIZE $SPLIT_BASE_DIR
