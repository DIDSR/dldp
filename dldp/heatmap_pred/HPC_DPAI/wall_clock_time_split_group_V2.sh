# timing for splitting and grouping 

D="$2"/sysout

PREFIX=sg_testing

case "$1" in
   "normal") PREFIX=split_grp 
   ;;
   "test") PREFIX=sg_testing 
   ;;
   "tumor") PREFIX=split_grp 
   ;;
esac

DIR=wall_clock_time_details_"$1"
SUFFIX=`date '+%Y%m%d%H%M%S'`
mv $DIR "$DIR"_"$SUFFIX" 2>/dev/null
mkdir -p $DIR

FN_PR=$DIR/time

find $D -name "$PREFIX"* | xargs grep "real" > "$FN_PR".txt

awk -F ' ' '{print $2}' "$FN_PR".txt > "$FN_PR"_nums.txt 
sed 's/m/ /g; s/s//g' "$FN_PR"_nums.txt > "$FN_PR"_nums2.txt # remove all "m" "s"
sort -k1 -k2 -n -r "$FN_PR"_nums2.txt > "$FN_PR"_nums2_sorted.txt
awk '{ printf ("%.18f\n", $1 * 60 + $2) }' "$FN_PR"_nums2_sorted.txt > wall_clock_final_"$SUFFIX".txt

