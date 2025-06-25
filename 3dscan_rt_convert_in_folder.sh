MYPATH="/data/3dscan/data_files/"

TNAME=$2
echo "Tile name: "$TNAME
cat $1 | while read LINE;
do
	FNAME=${LINE: -24}
	FULLPATH="$MYPATH$TNAME$FNAME"
	echo "Converting "$FNAME
	/home/lhep/soft/AFIViewer_new_hardware_FSDI/adc64-tlv/AFIViewer/build/ADC64Viewer  -g 0 -f $FULLPATH -m x > /dev/null
	#/home/lhep/soft/AFIViewer/ADC64Viewer -g 0 -f $FULLPATH -m x > /dev/null
	#/home/analysis/soft/AFIViewer/build/ADC64Viewer -g 0 -f $FULLPATH -m x > /dev/null

	INNAME=${FNAME: -21}
	echo "INNAME "$INNAME
	OUTNAME=$(ls -rt | tail -n 1)
	echo "OUTNAME "$OUTNAME
	while ! [[ "$OUTNAME" == *"$INNAME"* ]];
	do
  		echo "File not converted, retry."
		/home/lhep/soft/AFIViewer_new_hardware_FSDI/adc64-tlv/AFIViewer/build/ADC64Viewer  -g 0 -f $FULLPATH -m x > /dev/null
		#/home/lhep/soft/AFIViewer/ADC64Viewer -g 0 -f $FULLPATH -m x -w > /dev/null
		#/home/analysis/soft/AFIViewer/build/ADC64Viewer -g 0 -f $FULLPATH -m x > /dev/null
		OUTNAME=$(ls -rt | tail -n 1)	
	done
	if ! [[ "$OUTNAME" == *"$FNAME"* ]]; then
		mv $OUTNAME "rlog_$FNAME.root"
	fi
done
