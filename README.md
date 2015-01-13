# DASH-SVC-Toolchain
- - -

A _Dynamic Adaptive Streaming over HTTP_ (DASH) toolchain for _Scalable Video Coding_ (SVC). This open source toolkit 
provides scripts for demultiplexing and re-multiplexing video content which has been encoded according to the 
**H.264/SVC** extension. It can be used together with the DASH/SVC Dataset provided 
[here](http://concert.itec.aau.at/SVCDataset/) ([http://concert.itec.aau.at/SVCDataset/](http://concert.itec.aau.at/SVCDataset/)).

## Description
This toolchain provides python scripts for converting videos encoded according to the **H.264/SVC** extension into 
several segments and several layers (spatial and quality scalability), allowing Dynamic Adaptive Streaming over HTTP
for Scalable Video Coding.
This toolchain is based on the SVC Demux/Mux Tool of Michael Grafl (see 
[http://www-itec.uni-klu.ac.at/dash/?page_id=1366]() for more information).
This work was partly funded by the **Austrian Science Fund (FWF)** under the CHIST-ERA project **CONCERT** 
(A Context-Adaptive Content Ecosystem Under Uncertainty), project number _I1402_ (see [http://www.concert-project]()
for more details).

This README file will cover downloading, building and executing the scripts and programs provided within this
github repository.

### Current features:
* Testing JSVM
* Analysing an H.264/SVC compatible stream
* De-Multiplexing an H.264/SVC compatible stream into DASH/SVC segments
* Re-Multiplexing DASH/SVC segments into an H.264/SVC compatible segment
* Supports spatial and coarse-grain quality scalability
* Parsing SVC MPD file and extracting the URLs of all segments and layers

### Known Restrictions:

* Temporal Scalability is not supported yet.
* Only coarse-grain Quality Scalability is supported.
* JSVM might not compile on all platforms.

### Multiplexing
![Multiplexing](https://raw.githubusercontent.com/ChristianKreuzberger/DASH-SVC-Toolchain/master/doc/dash_svc.png "Multiplexing SVC Content")

### Dependencies
* Python 2.7
* Python easy_install
* Python module: bitstring
* CVS (required for downloading JSVM)
* build-essentials and cmake
* [JSVM](http://www.hhi.fraunhofer.de/de/kompetenzfelder/image-processing/research-groups/image-video-coding/svc-extension-of-h264avc/jsvm-reference-software.html) Reference Encoder
* [libdash](https://github.com/bitmovin/libdash) library for parsing MPD files (included in this github project, required for MPD parsing)

- - -

## Download, Build and Test

This section describes the scripts for downloading and testing. Create a directory, e.g., SVCDemo, switch to this 
directory and follow the steps below:

Install required packages and download this git repository:

	# Requires: python (2.7), cvs, git
	# libdash requires:
	sudo apt-get install cvs git-core build-essential cmake libxml2-dev libcurl4-openssl-dev
	# python setup-tools (easy install)
	sudo apt-get install python-setuptools
	# python module bitstring
	sudo easy_install bitstring
	
    # if you want to play yuv files, you need mplayer or any other player that can play yuv files
    sudo apt-get install mplayer
    # get this repository
	git clone --recursive git://github.com/ChristianKreuzberger/DASH-SVC-Toolchain.git
    cd DASH-SVC-Toolchain


Let's **build libdash** or just call the script `build_scripts/buildLibDash.sh`:
(Note: libdash is required for parsing MPD files; if you don't intend to do that, you don't need to build libdash)

	cd libdash/libdash
	mkdir build
	cd build
	cmake ../
	make
	if [ $? -ne 0 ] ; then
		echo "Failed building libdash";
		exit -3
	fi
	
	# go back to the main directory
	cd ../../../

**Download and build** the **JSVM** reference software or just call the script `build_scripts/buildJsvm.sh`:
(Note: JSVM might not compile on all platforms. We have successfully compiled JSVM under Ubuntu 12.04.)

	# get JSVM reference software
	cvs -d :pserver:jvtuser:jvt.Amd.2@garcon.ient.rwth-aachen.de:/cvs/jvt login
	cvs -d :pserver:jvtuser@garcon.ient.rwth-aachen.de:/cvs/jvt checkout jsvm

	cd jsvm/JSVM/H264Extension/build/linux
	make
	if [ $? -ne 0 ]; then 
		echo "BUILDING JSVM FAILED!"
		exit -1
	fi


	# see if the JSVM tools exist
	cd ../../../../bin/
	ls

	# test bitstream extractor static
	./BitStreamExtractorStatic
	
	# go back to the main directory
	cd ../../


Test JSVM by **decoding a H.264/SVC video** from our dataset:


	# let's test JSVM by downloading a H.264/SVC video from our dataset (svcseqs subfolder)
	JSVMPATH=$(pwd)/jsvm/bin
	export PATH=$PATH:$JSVMPATH

	# download a video
	wget http://concert.itec.aau.at/SVCDataset/svcseqs/II/bluesky-II-360p.264
	BitStreamExtractorStatic bluesky-II-360p.264 > bluesky_test.txt
	diff bluesky_test.txt tests/bluesky_II_360p.txt

	if [ $? -ne 0 ] ; then 
		echo "TESTING JSVM (TEST 1) FAILED!"
		exit -2 
	fi
	
	# try decoding it
	H264AVCDecoderLibTestStatic bluesky-II-360p.264 bluesky-II-360p.yuv > bluesky_decode_test.txt
	diff bluesky_decode_test.txt tests/decode_bluesky_II_360p.txt
	
	if [ $? -ne 0 ] ; then 
		echo "TESTING JSVM (TEST 2) FAILED!"
		exit -2 
	fi

	# remove the files that we just created
	rm bluesky_test.txt
	rm bluesky_decode_test.txt
	rm bluesky-II-360p.264
	rm bluesky-II-360p.yuv
	
	
	echo "TESTS DONE!!!"


Congratulations! You have successfully downloaded and built libdash and the JSVM reference encoder. In the next
subsections you will try to decode a DASH/SVC segment with our toolchain.

- - -

## Decoding a DASH/SVC Segment

Assuming you are in the DASH-SVC-Toolchain directory, follow these steps:
(Note: This step requires JSVM binaries)

	# make sure JSVM is in PATH
	JSVMPATH=$(pwd)/jsvm/bin
	export PATH=$PATH:$JSVMPATH
	
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
	H264AVCDecoderLibTestStatic bluesky-II-720p.seg0-BL.264 bluesky-II-720p.seg0-BL.yuv

	# svc_merge.py for base layer + EL 1:
	python svc_merge.py bluesky-II-720p.seg0-EL1.264 bluesky-II-720p.init.svc bluesky-II-720p.seg0-L0.svc bluesky-II-720p.seg0-L1.svc
	H264AVCDecoderLibTestStatic bluesky-II-720p.seg0-EL1.264 bluesky-II-720p.seg0-EL1.yuv


	# svc_merge.py for base layer + EL 1 + EL 2:
	python svc_merge.py bluesky-II-720p.seg0-EL2.264 bluesky-II-720p.init.svc bluesky-II-720p.seg0-L0.svc bluesky-II-720p.seg0-L1.svc bluesky-II-720p.seg0-L2.svc
	H264AVCDecoderLibTestStatic bluesky-II-720p.seg0-EL2.264 bluesky-II-720p.seg0-EL2.yuv

	# use mplayer to playback the three yuv files
	mplayer -demuxer rawvideo -rawvideo w=1280:h=720:format=i420 bluesky-II-720p.seg0-BL.yuv -loop 0
	mplayer -demuxer rawvideo -rawvideo w=1280:h=720:format=i420 bluesky-II-720p.seg0-EL1.yuv -loop 0
	mplayer -demuxer rawvideo -rawvideo w=1280:h=720:format=i420 bluesky-II-720p.seg0-EL2.yuv -loop 0
	
	# remove the files we created
	rm *.yuv
	rm *.svc
	rm *.264
	
	cd ..
	

- - -


## Parsing MPD using libdash
This section details on how to parse the MPD using libdash, assuming we are in the main directory (DASH-SVC-Toolchain) again.

parseMPD uses libdash to parse the MPD files of our dataset, and prints all segments and layers. This tool can be used
for testing our dataset, e.g., downloading a full set of segments and layers, and then decoding them using the tools
described in the Decoding section.

	LIBDASHPATH=$(pwd)/libdash/libdash/build/bin
	LIBDASH=$LIBDASHPATH/libdash.so
	cd parseMPD
	make
	# example 1: Print segments of any MPD file (in this case: http://concert.itec.aau.at/SVCDataset/dataset/mpd/factory-I-720p.mpd)
	LD_LIBRARY_PATH=$LIBDASHPATH/ ./parseMPD
	# example 2: Print segments of a specified MPD file
	LD_LIBRARY_PATH=$LIBDASHPATH/ ./parseMPD http://concert.itec.aau.at/SVCDataset/dataset/mpd/rushhour-I-360p.mpd
	# example 3: Print only a specific layer of the specified MPD file
	LD_LIBRARY_PATH=$LIBDASHPATH/ ./parseMPD http://concert.itec.aau.at/SVCDataset/dataset/mpd/rushhour-I-360p.mpd 0
	# Layer 1
	LD_LIBRARY_PATH=$LIBDASHPATH/ ./parseMPD http://concert.itec.aau.at/SVCDataset/dataset/mpd/rushhour-I-360p.mpd 1
	# Layer 2
	LD_LIBRARY_PATH=$LIBDASHPATH/ ./parseMPD http://concert.itec.aau.at/SVCDataset/dataset/mpd/rushhour-I-360p.mpd 2
	

The output will contain a list of SVC segment files.


## Analyzing a H.264/SVC File

Assuming you are in the DASH-SVC-Toolchain directory, follow these steps:

## Demultiplexing a H.264/SVC File into multiple segments and layers

Assuming you are in the DASH-SVC-Toolchain directory, follow these steps:
