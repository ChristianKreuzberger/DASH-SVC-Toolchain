#!/usr/bin/env python

# multiplex svc files and the Merge multiplexed svc files

import sys, os, struct;
import re;

if(len(sys.argv) < 4):
    print("Usage: \n  python", sys.argv[0], "stream_out initsegment bl0_seg_x_in [el1_seg_x_in el2_seg_x_in ... ]")
    print("Merge an ordered list of DASH/SVC files into a decodeable segment. (Hint: do not try to merge independent segments, decode might fail)")
    print("If you do not have an initsegment, write NULL instead of a filename.")
    quit()

# bitstream separator 0001
sep = struct.pack("BBBB", 0, 0, 0, 1)

def countNalus(inFileName, type=20):
    stream = []
    cnt = 0
    with open(inFileName, 'rb') as fpIn:
        stream = fpIn.read().split(sep)[1:]
    for i in range(len(stream)):
        n = stream[i]
        hdr = struct.unpack_from("BBBB", n)
        naluType = hdr[0] & 0x1f
        if naluType == type:
            cnt = cnt + 1
    return cnt
    

def mux(fpOut, fileList, sepNaluType):
    nLayers = len(fileList)
    naluStreams = [None]*nLayers
    positions = [None]*nLayers

    print "Step 1: Reading all input files into memory..."
    for i in range(nLayers):
        with open(fileList[i]['Filename'], 'rb') as fpIn:
            print "Parsing ", fileList[i]['Filename']
            naluStreams[i] = fpIn.read().split(sep)[1:]
            positions[i] = 0
    print "/////////"
    active = True

    baseLayerAUCount = fileList[0]['naluCount']
    
    frm = 0
    while active:
        active = False
        
        for i in range(nLayers):

            # calculate nalu per AU (relevant for enhancement layers)
            naluPerAU = fileList[i]['naluCount'] / baseLayerAUCount
            eos, found = False, False
            
            first = True
            
            if i == 0: # base layer
                # read until we find nalu type 14 (= new AU)
                print "Reading ", fileList[i]['Filename'] , " in Base Layer Mode (len=", len(naluStreams[i]), "): Frame " + str(frm)
                
                while (not eos) and (not found):
                    pos = positions[i]
                    
                    if pos >= len(naluStreams[i]):
                        eos = True
                    else:
                        n = naluStreams[i][pos]
                        if (len(n) > 0): # NALU long enough
                            hdr = struct.unpack_from("BBBB", n)
                            naluType = hdr[0] & 0x1f
                            
                            print "pos=", pos, ", naluType=", naluType, ", len=", len(n)


                            if naluType == sepNaluType:  # make sure to skip first nalutype 14
                                if not first:
                                    found = True
                                    active = True
                            # end if
                            first = False
                        if not found:  # write as long as we did not find another nalu type 14
                            fpOut.write(sep+n)
                            positions[i] +=  1
                        else:
                            print "Info: Possible layer upswitch coming, skipping last NALU (type 14) for now, and continuing with EL 1"
                        # end if not found
                    # end if Check for EOS
                # end while not eos and not found
                frm += 1
                            
            else: # EL
                # read naluPerAU nalus
                print "Reading ", fileList[i]['Filename'] , " in Enhancement Layer Mode (naluPerAU=", naluPerAU, ",len=", len(naluStreams[i]), ")"
                cnt = 0
                while (not eos) and cnt < naluPerAU: # copy NALUs until we find type 1, 5, or 20.
                    pos = positions[i]
                    print "cnt=", cnt, ", pos=", pos
                    
                    if pos >= len(naluStreams[i]):
                        print "end of stream"
                        eos = True
                        active = False
                    else:
                        n = naluStreams[i][pos]
                        cnt += 1
                        
                        hdr = struct.unpack_from("BBBB", n)
                        naluType = hdr[0] & 0x1f
                            
                        print "cnt=", cnt,", pos=", pos, ", naluType=", naluType, ", len=", len(n)
                        
                        fpOut.write(sep+n)
                        positions[i]+= 1
                        active = True
            # end if
            
            
            

# get commandline parmaeters
outFile = sys.argv[1]
initSegment = sys.argv[2]

initSegmentContent = None

if initSegment == "NULL":
    initSegment = None
else:
    print "InitSegment = ", initSegment
    # read initsegment
    fpInit = open(initSegment, 'rb')
    initSegmentContent = fpInit.read()
    fpInit.close()

# determine number of files to merge
nFiles = len(sys.argv)-3

files = {}

separatorNaluType = 6  # type 6 = new AU

for i in range(nFiles):
    curFile = sys.argv[i+3]

    naluCount = 0
    if i == 0:
        print "Processing " + curFile + " as BaseLayer"
        naluCount = countNalus(curFile, 6) # count Nalu Type 6 = new Access Unit
        if naluCount == 0:
            print curFile, "does not have AU delimiters. Trying NaluType 14 instead."
            naluCount = countNalus(curFile, 14)  # count Access Units in Base Layer (NaluType 14)
            separatorNaluType = 14
    else:
        print "Processing " + curFile + " as Enhancement Layer " + str(i)
        naluCount = countNalus(curFile, 20)  # count NaluType 20 (= new SVC frame data)
    print naluCount

    files[i] = {'Filename': curFile, 'naluCount': naluCount}


# open output file
fpOut = open(outFile, 'wb')


# write initSegmentContent
if initSegmentContent is not None:
    fpOut.write(initSegmentContent)
    print "Writing initsegment..."


print files

# Merge/multiplex the other files
mux(fpOut, files, separatorNaluType)


fpOut.close()
