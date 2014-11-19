### DASH-SVC-Toolchain
A Dynamic Adaptive Streaming over HTTP (DASH) toolchain for Scalable Video Coding (SVC).
==================
### Description
This toolchain provides python scripts for converting videos of the H.264/SVC extension into several segments and several layers, allowing Dynamic Adaptive Streaming over HTTP.

### Current features and restrictions
* TODO

==================
### Download and Tests

This section describes the scripts for downloading and testing.

# Requires: python (2.7), cvs, git
# libdash requires:
# sudo apt-get install git-core build-essential cmake libxml2-dev libcurl4-openssl-dev

	# get this repository
	git clone git://github.com/ChristianKreuzberger/DASH-SVC-Toolchain.git

	# get libdash
	git clone git://github.com/bitmovin/libdash.git
	cd libdash/libdash
	mkdir build
	cd build
	cmake ../
	make
	if [ $? -ne 0 ] ; then
		echo "Failed building libdash";
		exit -3
	fi
	LIBDASHPATH=../../libdash/libdash/build/bin
	LIBDASH=$LIBDASHPATH/libdash.so
	cd ../../../



	# get JSVM reference software ( http://www.hhi.fraunhofer.de/de/kompetenzfelder/image-processing/research-groups/image-video-coding/svc-extension-of-h264avc/jsvm-reference-software.html ) 
	cvs -d :pserver:jvtuser:jvt.Amd.2@garcon.ient.rwth-aachen.de:/cvs/jvt login
	cvs -d :pserver:jvtuser@garcon.ient.rwth-aachen.de:/cvs/jvt checkout jsvm

	cd jsvm/JSVM/H264Extension/build/linux
	make
	if [ $? -ne 0 ]; then 
		echo BUILDING JSVM FAILED!
		exit -1
	fi


	# see if the JSVM tools exist
	cd ../../../../bin/
	ls

	# test bitstream extractor static
	./BitStreamExtractorStatic
	cd ../../

	# go back to the main directory
	cd DASH-SVC-Toolchain

	# let's test JSVM by downloading a H.264/SVC video from our dataset (svcseqs subfolder)
	JSVMPATH=../jsvm/bin

	# download a video
	wget http://concert.itec.aau.at/SVCDataset/svcseqs/II/bluesky-II-360p.264
	$JSVMPATH/BitStreamExtractorStatic bluesky-II-360p.264 > bluesky_test.txt
	diff bluesky_test.txt tests/bluesky_II_360p.txt

	if [ $? -ne 0 ] ; then 
		echo TESTING JSVM FAILED!
		exit -2 
	fi

	# remove the files that we just created
	rm bluesky_test.txt
	rm bluesky-II-360p.264




