### DASH-SVC-Toolchain
A Dynamic Adaptive Streaming over HTTP (DASH) toolchain for Scalable Video Coding (SVC).
==================
### Description
This toolchain provides python scripts for converting videos of the H.264/SVC extension into several segments and several layers, allowing Dynamic Adaptive Streaming over HTTP.

### Current features and restrictions
* Testing JSVM
* Decoding a DASH/SVC segment


==================
### Download and Tests

This section describes the scripts for downloading and testing. Create a directory, e.g., SVCDemo, switch to this directory and follow the steps below:

	# Requires: python (2.7), cvs, git
	# libdash requires:
	sudo apt-get install git-core build-essential cmake libxml2-dev libcurl4-openssl-dev

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
		echo TESTING JSVM (TEST 1) FAILED!
		exit -2 
	fi
	
	# try decoding it
	$JSVMPATH/H264AVCDecoderLibTestStatic bluesky-II-360p.264 bluesky-II-360p.yuv > bluesky_decode_test.txt
	diff bluesky_decode_test.txt tests/decode_bluesky_II_360p.txt
	
	if [ $? -ne 0 ] ; then 
		echo TESTING JSVM (TEST 2) FAILED!
		exit -2 
	fi

	# remove the files that we just created
	rm bluesky_test.txt
	rm bluesky_decode_test.txt
	rm bluesky-II-360p.264
	rm bluesky-II-360p.yuv
	
	
	echo TESTS DONE!!!

==================
### Decoding a DASH/SVC Segment

Assuming you are in the DASH-SVC-Toolchain directory, follow these steps:

	cd decode
	# Download init segment
	wget http://concert.itec.aau.at/SVCDataset/dataset/bluesky/II/segs/720p/bluesky-II-720p.init.svc
	# Download segment 0, Base Layer
	wget http://concert.itec.aau.at/SVCDataset/dataset/bluesky/II/segs/720p/bluesky-II-720p.seg0-L0.svc
	# Download segment 0, EL 1
	wget http://concert.itec.aau.at/SVCDataset/dataset/bluesky/II/segs/720p/bluesky-II-720p.seg0-L1.svc
	# Download segment 0, EL 2
	wget http://concert.itec.aau.at/SVCDataset/dataset/bluesky/II/segs/720p/bluesky-II-720p.seg0-L2.svc

	# call svc_merge.py and create the yuv files for the segments
	# svc_merge.py for base layer only:
	python svc_merge.py bluesky-II-720p.seg0-BL.264 bluesky-II-720p.init.svc bluesky-II-720p.seg0-L0.svc
	../$JSVMPATH/H264AVCDecoderLibTestStatic bluesky-II-720p.seg0-BL.264 bluesky-II-720p.seg0-BL.yuv

	# svc_merge.py for base layer + EL 1:
	python svc_merge.py bluesky-II-720p.seg0-EL1.264 bluesky-II-720p.init.svc bluesky-II-720p.seg0-L0.svc bluesky-II-720p.seg0-L1.svc
	../$JSVMPATH/H264AVCDecoderLibTestStatic bluesky-II-720p.seg0-EL1.264 bluesky-II-720p.seg0-EL1.yuv


	# svc_merge.py for base layer + EL 1 + EL 2:
	python svc_merge.py bluesky-II-720p.seg0-EL2.264 bluesky-II-720p.init.svc bluesky-II-720p.seg0-L0.svc bluesky-II-720p.seg0-L1.svc bluesky-II-720p.seg0-L2.svc
	../$JSVMPATH/H264AVCDecoderLibTestStatic bluesky-II-720p.seg0-EL2.264 bluesky-II-720p.seg0-EL2.yuv

	# use mplayer to playback the three yuv files
	mplayer -demuxer rawvideo -rawvideo w=1280:h=720:format=i420 bluesky-II-720p.seg0-BL.yuv -loop 0
	mplayer -demuxer rawvideo -rawvideo w=1280:h=720:format=i420 bluesky-II-720p.seg0-EL1.yuv -loop 0
	mplayer -demuxer rawvideo -rawvideo w=1280:h=720:format=i420 bluesky-II-720p.seg0-EL2.yuv -loop 0
	
	# remove the files we created
	rm *.yuv
	rm *.svc
	rm *.264
	
	cd ..
	


