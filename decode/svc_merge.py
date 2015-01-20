#!/usr/bin/env python

# multiplex svc files and the Merge multiplexed svc files


'''
The MIT License

Copyright (c) 2014 Christian Kreuzberger

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''



import sys, os, struct;
import argparse # for parsing the commandline



cmdParser = argparse.ArgumentParser(description="SVC DASH Segment Merger")

cmdParser.add_argument('outputStream', help="the output H.264/SVC segment" )
cmdParser.add_argument('initSegment', help="the init-segment for the H.264/SVC stream" )

cmdParser.add_argument('tempLayer0', nargs="+", help="Scalability Group for Temporal Layer 0 (default group)", metavar="SVCInputSegment")
cmdParser.add_argument('-1', '--tempLayer1', nargs="*", help="Scalability Group for Temporal Layer 1 (omit if you dont have temporal scalability)", metavar="SVCTempL1InputSegment")
cmdParser.add_argument('-2', '--tempLayer2', nargs="*", help="Scalability Group for Temporal Layer 2 (omit if you dont have temporal scalability)", metavar="SVCTempL2InputSegment")
cmdParser.add_argument('-3', '--tempLayer3', nargs="*", help="Scalability Group for Temporal Layer 3 (omit if you dont have temporal scalability)", metavar="SVCTempL3InputSegment")
cmdParser.add_argument('-4', '--tempLayer4', nargs="*", help="Scalability Group for Temporal Layer 4 (omit if you dont have temporal scalability)", metavar="SVCTempL4InputSegment")
cmdParser.add_argument('-5', '--tempLayer5', nargs="*", help="Scalability Group for Temporal Layer 5 (omit if you dont have temporal scalability)", metavar="SVCTempL5InputSegment")
cmdParser.add_argument('-6', '--tempLayer6', nargs="*", help="Scalability Group for Temporal Layer 6 (omit if you dont have temporal scalability)", metavar="SVCTempL6InputSegment")

#     print("Merge an ordered list of DASH/SVC files into a decodeable segment. (Hint: do not try to merge independent segments, decode might fail)")
#     print("If you do not have an initsegment, write NULL instead of a filename.")

cmdArgs = cmdParser.parse_args()
tempLayerGroup = []
tempLayerGroup.append(cmdArgs.tempLayer0)

useTemporalScalability = False


if not cmdArgs.tempLayer1 is None:
    tempLayerGroup.append(cmdArgs.tempLayer1)
    useTemporalScalability = True
    if not cmdArgs.tempLayer2 is None:
        tempLayerGroup.append(cmdArgs.tempLayer2)
        if not cmdArgs.tempLayer3 is None:
            tempLayerGroup.append(cmdArgs.tempLayer3)
            if not cmdArgs.tempLayer4 is None:
                tempLayerGroup.append(cmdArgs.tempLayer4)
                if not cmdArgs.tempLayer5 is None:
                    tempLayerGroup.append(cmdArgs.tempLayer5)
                    if not cmdArgs.tempLayer6 is None:
                        tempLayerGroup.append(cmdArgs.tempLayer6)

print "OutputStream = ", cmdArgs.outputStream
print "InitSegment = ", cmdArgs.initSegment
print "Number of temporal layers = ", len(tempLayerGroup)


numTemporalGroups = len(tempLayerGroup)
numSegmentsPerGroup = len(tempLayerGroup[0])
outFile = cmdArgs.outputStream
initSegment = cmdArgs.initSegment

for j in range(len(tempLayerGroup)):
    print "TempLayerGroup" + str(j+1) + ": " + str(tempLayerGroup[j])
    if len(tempLayerGroup[j]) != numSegmentsPerGroup:
        print "ERROR: Each Temporary Scalability Layer Group must have the same amount of segments!"
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
    

def mux(fpOut, layerList, sepNaluType, temporalScalability = False):
    numTemporalLayers = len(layerList)
    naluStreams = {}
    positions = {}


    print "Step 1: Reading all input files into memory..."
    for j in range(numTemporalLayers):
        # init naluStreams and positions
        naluStreams[j] = {}
        positions[j] = {}

        fileList = layerList[j]
        nLayers = len(fileList)
        for i in range(nLayers):
            with open(fileList[i]['Filename'], 'rb') as fpIn:
                print "Parsing ", fileList[i]['Filename']
                naluStreams[j][i] = fpIn.read().split(sep)[1:]
                positions[j][i] = 0
    print "/////////"
    active = True

    # sum up base layer AU count
    #baseLayerAUCount = {}
    #for j in range(numTemporalGroups):
    #    baseLayerAUCount[j] = layerList[j][0]['naluCount']
    baseLayerAUCount = layerList[0][0]['naluCount']

    frm = 0
    nal_ref_idc = 0
    cur_temp_layer = 0



    while active:
        active = False

        # decode the frame for all layers
        if temporalScalability:
            print "Current temporal layer: ", cur_temp_layer
        # end if
        for i in range(nLayers):
            fileList = layerList[cur_temp_layer]
            # calculate nalu per AU (relevant for enhancement layers)
            naluPerAU = fileList[i]['naluCount'] / baseLayerAUCount
            print "naluPerAU=", naluPerAU
            eos, found = False, False
            
            first = True

            probeForTemporalUpswitch = False
            
            if i == 0: # base layer
                # read until we find NALU type 14 (= new AU); if 14 found --> possible upswitch coming
                print "Reading ", fileList[i]['Filename'] , " in Base Layer Mode (len=", len(naluStreams[cur_temp_layer][i]), "): Frame " + str(frm)
                cnt = 0
                while (not eos) and (not found):
                    pos = positions[cur_temp_layer][i]
                    
                    if pos >= len(naluStreams[cur_temp_layer][i]):
                        eos = True
                        #if cur_temp_layer == 0 and numTemporalGroups > 1:
                        #    probeForTemporalUpswitch = True
                        # end if
                    else:
                        n = naluStreams[cur_temp_layer][i][pos]
                        if (len(n) > 0): # NALU long enough
                            nal_ref_idc = struct.unpack_from("B", n)[0] >> 5 # get the leftmost 3 bit
                            naluType = struct.unpack_from("B", n)[0] & 0x1f # get the rightmost 5 bit
                            
                            print "pos=", pos, ", naluType=", naluType, ", nal_ref_idc=", nal_ref_idc, ", len=", len(n)

                            if naluType == sepNaluType:  # make sure to skip first nalutype 14
                                if not first and nLayers > 1:
                                    found = True
                                    active = True
                            # end if
                            first = False

                        if naluType != 14:
                            cnt += 1

                        if not found:  # write as long as we did not find another nalu type 14
                            fpOut.write(sep+n)
                            positions[cur_temp_layer][i] +=  1
                            if nLayers == 1 and naluType == 1 and (nal_ref_idc == 2 or (nal_ref_idc == 0 and cnt >= naluPerAU)):
                                print "Info: Possible temporal layer upswitch coming. Probing..."
                                active = True
                                found = True
                                probeForTemporalUpswitch = True
                        else:
                            print "Info: Possible layer upswitch coming, skipping last NALU (type 14) for now, and continuing with EL 1"
                        # end if not found
                    # end if Check for EOS
                # end while not eos and not found
                frm += 1
                            
            else: # EL
                # read naluPerAU nalus
                print "Reading ", fileList[i]['Filename'] , " in Enhancement Layer Mode (naluPerAU=", naluPerAU, ",len=", len(naluStreams[cur_temp_layer][i]), ")"
                cnt = 0
                while (not eos) and cnt < naluPerAU: # copy NALUs until we find type 1, 5, or 20.
                    pos = positions[cur_temp_layer][i]
                    print "cnt=", cnt, ", pos=", pos
                    
                    if pos >= len(naluStreams[cur_temp_layer][i]):
                        print "end of stream cur_temp_layer=", cur_temp_layer
                        eos = True
                        active = False
                    else:
                        n = naluStreams[cur_temp_layer][i][pos]
                        cnt += 1
                        
                        nal_ref_idc = struct.unpack_from("B", n)[0] >> 5 # get the leftmost 3 bit
                        naluType = struct.unpack_from("B", n)[0] & 0x1f # get the rightmost 5 bit
                            
                        print "cnt=", cnt,", pos=", pos, ", naluType=", naluType, ", nal_ref_idc=", nal_ref_idc, ", len=", len(n)
                        
                        fpOut.write(sep+n)
                        positions[cur_temp_layer][i]+= 1
                        active = True
                    # end if
                # end while
            # end if EL
            # now check for temporal scalability:
            # if last layer AND naluType == 20 and nal_ref_idc == 2 --> next temporal layer
            #print "Temporal=", temporalScalability, ", i=", i, ", nLayers-1=", nLayers-1
            if probeForTemporalUpswitch or (temporalScalability and i == nLayers-1 and ((naluType == 20 and nal_ref_idc == 2) or (nLayers == 1 and naluType == 1 and nal_ref_idc == 2))) :
                # go to next temporal layer
                print "Info: Temporal Upswitch in Progress..."
                probeForTemporalUpswitch = False

                cur_temp_layer += 1
                cur_temp_layer = cur_temp_layer % numTemporalLayers

                if cur_temp_layer != 0:
                    eos = False
                    active = True

                print "New temporal layer=", cur_temp_layer, ", active=", active
            # end if
        # end for (decode current frame)
        # now, start loop at beginning again

    # end while active
# end function mux
            
            



initSegmentContent = None

if initSegment is None or initSegment == "NULL":
    initSegment = None
else:
    print "InitSegment = ", initSegment
    # read initsegment
    fpInit = open(initSegment, 'rb')
    initSegmentContent = fpInit.read()
    fpInit.close()

files = {}

separatorNaluType = 6  # type 6 = new AU


for j in range(numTemporalGroups):
    files[j] = {}
    for i in range(numSegmentsPerGroup):
        curFile = tempLayerGroup[j][i]

        naluCount = 0
        if i == 0:
            print "Processing " + curFile + " as BaseLayer with TID=" + str(j)
            naluCount = countNalus(curFile, 6) # count Nalu Type 6 = new Access Unit
            if naluCount == 0:
                print curFile, "does not have AU delimiters. Trying NaluType 14 instead."
                naluCount = countNalus(curFile, 14)  # count Access Units in Base Layer (NaluType 14)
                separatorNaluType = 14
        else:
            print "Processing " + curFile + " as Enhancement Layer " + str(i) + ",  with TID=" + str(j)
            naluCount = countNalus(curFile, 20)  # count NaluType 20 (= new SVC frame data)
        print naluCount

        files[j][i] = {'Filename': curFile, 'naluCount': naluCount}


# open output file
fpOut = open(outFile, 'wb')


# write initSegmentContent
if initSegmentContent is not None:
    fpOut.write(initSegmentContent)
    print "Writing initsegment..."


print files

# Merge/multiplex the other files
mux(fpOut, files, separatorNaluType, useTemporalScalability)


fpOut.close()
