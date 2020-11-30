
# input params
# source ./config.txt
source $1


num_files=0
begin=0
end=0

echo "Start End Name" > "$LOOKUP_FILE"

for file in "$SPLIT_BASE_DIR"/*.csv        # list files
do
    num=`awk 'NR==1{print $1}' $file`
    
    begin=$((num_files+1))
    end=$(( $num_files + $num ))
    
    base=`basename "$file"`
    
    row="$begin  $end ${base%.*}"
    
    echo  "$row" >> $LOOKUP_FILE
    
    num_files=$(( $num_files + $num ))
done

echo  "$end" > "$NUM_HDF5_DS"
