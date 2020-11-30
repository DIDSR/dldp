# DIR=/scratch/mikem/UserSupport/weizhe.li/runs_process_cn_False/normal_wnorm_448_400_7691563
# DIR=/scratch/mikem/UserSupport/weizhe.li/runs_process_cn_V2_False/testing_wnorm_448_400_7694088

# DIR=/scratch/mikem/UserSupport/weizhe.li/runs_process_cn_V2_True/testing_wnorm_448_400_7694222
# PREFIX=test

# DIR=/scratch/mikem/UserSupport/weizhe.li/runs_process_cn_V2_True/tumor_wnorm_448_400_7694290
# PREFIX=tumor

DIR=/scratch/mikem/UserSupport/weizhe.li/runs_process_cn_V2_True/normal_wnorm_448_400_7694229
PREFIX=normal

SUBDIRS=`ls -1 $DIR | grep $PREFIX`

STAT_FILE="$PREFIX"_timing_all.txt
rm -f $STAT_FILE

ALL_GROUPS="$PREFIX"_all_groups.txt
rm -f $ALL_GROUPS

DP=details
rm -rf $DP
mkdir -p $DP

for SD in $SUBDIRS
do
  echo "Processing $SD subdirectory..."
  echo $SD
  PREFIX1=$SD
  find "$DIR"/"$SD"/sysout -name "$PREFIX1"* | xargs grep -e user -e sys > "$DP"/"$SD"_timing.txt
  awk '{ print $2 }' "$DP"/"$SD"_timing.txt > "$DP"/"$SD"_timing_2nd.txt
  sed 's/m/ /g; s/s//g' "$DP"/"$SD"_timing_2nd.txt > "$DP"/"$SD"_timing_2nd_no_ms.txt
  awk -v sd="$SD" '{mult+=$1*60+$2;} END {printf ("%.18f %s\n", mult, sd);}' "$DP"/"$SD"_timing_2nd_no_ms.txt >> $STAT_FILE
  awk '{ printf ("%.18f\n", $1 * 60 + $2) }' "$DP"/"$SD"_timing_2nd_no_ms.txt > "$DP"/"$SD"_timing_secs.txt
  awk 'NR%2 { split($0, a) ; next }  { for (i=1; i<=NF; i++) printf (" %.18f", a[i]+$i) ; print "" }' "$DP"/"$SD"_timing_secs.txt >> $ALL_GROUPS
done

sort -k1 -n $STAT_FILE > "$STAT_FILE"_sorted.txt
awk '{sum+=$1;} END {printf ("%.18f", sum);}' "$STAT_FILE"_sorted.txt > "$STAT_FILE"_total_seconds.txt

sort -k1 -n $ALL_GROUPS > "$ALL_GROUPS"_sorted
