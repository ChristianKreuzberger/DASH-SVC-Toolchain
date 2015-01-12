#!/usr/bin/env python

# H264 / SVC Bitstream analyzer/demultiplexer which also splits the SVC bitstream into DASH-compliable chunks, one per layer.
# Note: SVC bitstreams must have constant IDR rate (e.g., IDR Frames must be at the beginning of each segment).
# Parameters: 1: stream, 2: segment size, 3: outputFolder for DASH Files, 4: frames per second (relevant for generating the MPD)
# omitting parameters 3 and 4 will only analyse the stream, and not create any output on the hard disk
# This work is based on the SVC Demux/Mux Tool of Michael Grafl, see http://www-itec.uni-klu.ac.at/dash/?page_id=1366
# or http://sourceforge.net/projects/svc-demux-mux/
# This work was partly funded by the Austrian Science Fund (FWF) under the CHIST-ERA project CONCERT (A Context-Adaptive Content Ecosystem Under Uncertainty), project number \textit{I1402}.\\


# Usage Example 1: Analyze SVC Stream:
#                  python demultiplex.py MySVCStream.264 48
# Usage Example 2: Convert MainConcept SVC Stream to DASH Stream
#                  python demultiplex.py MySVCStream.264 48 outputFolder/ 24
# Usage Example 3: Convert JSVM SVC Stream to DASH Stream (need to set the 5th parameter (skipFrames), as JSVM
#                  fails to encode the first couple of frames properly, namely the 2nd I-Frame is at the wrong
#                  position and does not allow to segmentize the first n frames.
#                  python demultplex.py MySVCStream-jsvm.264 48 outputfolder/ 24 43


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



import sys, struct, os;
import H264Parser


# Handle commandline parameters
if len(sys.argv) < 3:
    sys.stderr.write("SVC Stream Multiplexer\r\n")
    sys.stderr.write("Usage: \r\n\tpython " + sys.argv[0] + " stream framesPerSegment [outputFolder frameRate] [skipFrames] [baseURL]\r\n")
    quit()
if len(sys.argv) > 3 and len(sys.argv) < 5:
    sys.stderr.write("SVC Stream Multiplexer\r\n")
    sys.stderr.write("Usage: \r\n\tpython " + sys.argv[0] + " stream framesPerSegment [outputFolder frameRate] [skipFrames] [baseURL]\r\n")
    sys.stderr.write("\tExpected outputFolder and frameRate, but only got outputFolder.\r\n")
    quit()
if len(sys.argv) >= 8:
    sys.stderr.write("SVC Stream Multiplexer\r\n")
    sys.stderr.write("Usage: \r\n\tpython " + sys.argv[0] + " stream framesPerSegment [outputFolder frameRate] [skipFrames] [baseURL]\r\n")
    sys.stderr.write("\tToo many parameters supplied.\r\n")
    quit()

# parse parameters
outputFolder = ""  # defines the output folder for DASH content (if selected)
writeDASHOutput = False  # defines whether or not DASH content is created (if false, it is just analysed)
frameRate = 0  # defines the video framerate (necessary for creating a MPD file)
skipFrames = 0

if len(sys.argv) >= 5:  # if there are exactly 5 parameters, it is for writing DASH output
    outputFolder = sys.argv[3]
    frameRate = int(sys.argv[4])
    writeDASHOutput = True

    # check if output folder exists, if not, create it
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)

if len(sys.argv) == 6:  # 6 parameters --> skip the first couple of frames
    skipFrames = int(sys.argv[5])

baseURL = "./"

if len(sys.argv) == 7: # 7 parameters --> get baseURL
    baseURL = sys.argv[6]

framesPerSeg = int(sys.argv[2])  # specify the number of frames per segment

# get base name of the input file ($base$.264)
base = os.path.splitext(os.path.basename(sys.argv[1]))[0]
print "Analyzing SVC Stream of " + str(sys.argv[1])


# Configuration Part (do not change unless you know what you are doing)
configSvcExtension = ".svc"
configInitSegFilenameTemplate = "{base}.init{svcExtension}"
configMpdfilenameTemplate = "{base}.mpd"
configChunkFilenameTemplate = "{base}.seg{seg}-L{layerId}{svcExtension}"

# create name for init-segment
initFilename = configInitSegFilenameTemplate.format(base=base, svcExtension=configSvcExtension)
mpdFilename = configMpdfilenameTemplate.format(base=base)


if writeDASHOutput:
    # remove existing initfilename (just in case)
    if os.path.isfile(os.path.join(outputFolder, initFilename)):
        os.remove(os.path.join(outputFolder, initFilename))

# split input binary data by using a binary separator 0001
sep = struct.pack("BBBB", 0, 0, 0, 1)
nalus = [] # this array contains all NAL-Units and needs to be parsed
with open(sys.argv[1], 'rb') as fpIn:
    nalus = fpIn.read().split(sep)[1:]
tid = 0

# some variables for parsing
oldSeg = -1
extraText = ""
framesInThisSegment=0
warnings=0
firstHeader = True
frm, last, init, segmentNumberChanged = 0, 0, True, True
segmentFileName=""
header = False
svc_extension_active = False
lastNaluType = -1
naluTypeSixCount = 0

# layer dictionary, containing all relevant info for creating the MPD
layerDashInfo = []

# array for buffering the segment output (per layer)
segmentOutputBuffer = []

# go through all NAL units
for n in nalus:
    # local variables for the loop
    layerId = 0
    did = qid = tid = -1
    extraText = ""

    # NALU Structure (Bit): forbidden zero bit (u1), nal_ref_idc (u3), nalu_type (u5)
    # read NAL-Unit-Type and the Nal-REF-IDC
    nal_ref_idc = struct.unpack_from("B", n)[0] >> 5 # get the leftmost 3 bit
    naluType = struct.unpack_from("B", n)[0] & 0x1f # get the rightmost 5 bit

    if naluType == 6: # header or new AU
        naluTypeSixCount += 1

    # NaluType 14 --> Prefix NAL Unit, NaluType 20 --> Coded Slice Extension;
    # both contain depency id, quality id and temporal id --> read them
    if naluType in [14,20] and len(n) >= 4:
        hdr = struct.unpack_from("BBBB", n)
        did = ( hdr[2] >> 4 ) & 0x7
        qid = hdr[2] & 0xF
        tid = (hdr[3] >> 5)
        layerId = did  # other way of calculating layerId is possible, though we are sticking to spatial and snr scalability

    # End of sequence / end of stream
    if naluType in [10, 11]:
        layerId = last  # Write EOS NALU to same layer as previous NALU

    # new frame / new access unit
    if naluType == 14:
        # we found a frame, so anything after this can obviously not be the first header
        firstHeader = False
        header = False
        # increase number of frames
        # type 6 --> new AU
        # type 20 --> last frame was an EL, now we are back to BL --> increase frame number
        # type 8 --> last was picture parmaeter set, meaning header info
        # type -1 --> no header provided, still need to start somewhere
        # type 1 --> non-IDR frame was last
        # type 5 --> IDR frame was last
        if lastNaluType == 6 or lastNaluType == 20 or lastNaluType == 8 or lastNaluType == -1\
                or (naluTypeSixCount == 1 and (lastNaluType == 1 or lastNaluType == 5)):

            if skipFrames > 0:
                skipFrames -= 1
            if skipFrames == 0:
                frm += 1
                framesInThisSegment += 1
        # end if

        # calculate the new (current) segment number and detect if it changed
        newSeg = int((frm-1) / framesPerSeg)
        segmentNumberChanged = (oldSeg != newSeg)

        if segmentNumberChanged:
            if newSeg > 0: # segment number changed and it was not the first segment
                # check number of frames in this segment (should be equal to framesPerSeg)
                print "--- SEGMENT", seg, "ENDED WITH " + str(framesInThisSegment) + " FRAMES"
                if framesInThisSegment != framesPerSeg:
                    # invalid number of frames found in this segment
                    print "----- WARNING: Segment", seg, "contains", framesInThisSegment, ", not", framesPerSeg, "!!!"
                    warnings += 1
                    sys.stderr.write("----- WARNING: Segment " + str(seg) + "contains " + str(framesInThisSegment) +  ", not" + str(framesPerSeg) +  " as specified!!!")
                # end if segment frame check

                if writeDASHOutput:
                    # write buffered output
                    print "---- Writing Buffer to File ----"
                    for tmpLayerId in range(0,len(segmentOutputBuffer)):
                        tmpSegmentFileName = configChunkFilenameTemplate.format(base=base, seg=seg, layerId = tmpLayerId, svcExtension=configSvcExtension)
                        # write old segment to file
                        print "Writing" , tmpSegmentFileName
                        with open(os.path.join(outputFolder, tmpSegmentFileName), 'wb') as fpOut:
                            fpOut.write(segmentOutputBuffer[tmpLayerId])
                            segmentOutputBuffer[tmpLayerId] = ""
                            fpOut.close()
                    # end for
                # end if
            # new segment is starting, reset framesInThisSegment
            print "--- NEW SEGMENT " + str(newSeg) + " (Frame " + str(frm) + ") ----"
            framesInThisSegment = 0
        
        extraText = "NEW FRAME (Frame Number: " + str(frm) + ")"
    elif naluType == 5: # IDR Frame found, check if it is at the beginning of the segment
        extraText = ">!   IDR FRAME   !<"
        if framesInThisSegment > 0 and seg >= 0:
            extraText = extraText, " - WARNING: IDR FRAME NOT AT BEGINNING OF SEGMENT!!!"
            warnings += 1
            sys.stderr.write("WARNING: IN SEGMENT " + str(seg) + ": IDR FRAME FOUND IN THE MIDDLE OF SEGMENT!!!\r\n")
    elif naluType == 1: # NON-IDR Frame, check if it is at the beginning of the segment
        extraText = "(Normal Frame)"
        if framesInThisSegment == 0 and seg >= 0:
            extraText = extraText, " - WARNING: SEGMENT STARTED WITHOUT IDR FRAME!!!"
            sys.stderr.write("WARNING: SEGMENT " + str(seg) + " STARTED WITHOUT IDR FRAME!!!\r\n")
            warnings += 1
    elif naluType == 6 and nal_ref_idc == 0: # detect new header information
        print "----- H.264 HEADER INFORMATION -----"
        header = True
        if naluTypeSixCount > 2: # detect whether this is still the first header or a new AU
            firstHeader = False
            if len(n) == 5:  # this is an AU delimiter, not a header
                header = False
    elif naluType == 10: # detect end of sequence
        extraText = "end of sequenece"
    elif naluType == 11: # end of stream
        extraText = "end of stream"
    elif naluType == 7:
        extraText = "Sequence Parameter Set (SPS)"
    elif naluType == 15:
        extraText = "Sub-Sequence Parameter Set (Sub-SPS)"
    elif naluType == 8:
        extraText = "Picture Parameter Set"

    # calculate old segment number
    oldSeg = seg = int((frm-1) / framesPerSeg)

    # chose the filename - if it is not a header, use the chunk filename template
    if not header:
        segmentFileName = configChunkFilenameTemplate.format(base=base, seg=seg, layerId = layerId, svcExtension=configSvcExtension)
    else: # if it is the first header, use the init-segment, else just skip it
        if firstHeader:
            segmentFileName = initFilename
        else:
            segmentFileName = "skip"
        # end if
    # end if

    mode = None
    length = len(sep+n)   

    # print some information, and count the segment sizes etc...
    if did != -1:
        if skipFrames == 0:
            print "NALU-T:", naluType, "; nal_ref_idc:", nal_ref_idc,",\tlen=" + str(len(n)).rjust(7) + "\t--> seg:", str(seg).zfill(3), ", layer="+ str(layerId), " (Depency = ", did, ", Quality=", qid, ", Tid=", tid, ")", extraText, " --> ", segmentFileName
            if len(layerDashInfo) > 0:
                layerDashInfo[layerId]['Bytes'] += length
                if not segmentFileName in layerDashInfo[layerId]['Segments']:
                    layerDashInfo[layerId]['Segments'].append(segmentFileName)
    elif not header:
        if skipFrames == 0:
            if layerId != -1 and len(layerDashInfo) > 0:
                layerDashInfo[layerId]['Bytes'] += length
                if not segmentFileName in layerDashInfo[layerId]['Segments']:
                    layerDashInfo[layerId]['Segments'].append(segmentFileName)
                # end if
            # end if
            print "NALU-T:", naluType, "; nal_ref_idc:", nal_ref_idc,",\tlen=" + str(len(n)).rjust(7) + "\t--> seg:", str(seg).zfill(3), ", layer="+ str(layerId), extraText, " --> ", segmentFileName
    else: # if header
        print "NALU-T:", naluType, "; nal_ref_idc:", nal_ref_idc,",\tlen=" + str(len(n)).rjust(7) + "\t\t",  extraText, " --> ", segmentFileName
        
    if writeDASHOutput and segmentFileName != "skip":
        if not header:
            if skipFrames == 0:
                segmentOutputBuffer[layerId] += (sep + n)
        else:  # write header immediately
            with open(os.path.join(outputFolder, initFilename), 'ab') as fpOut:
                fpOut.write(sep + n)
                fpOut.close()
    # end if

    # parse SPS if this is the first time the header information appears
    if firstHeader and (naluType == 15 or naluType == 7): # subset sequence parameter set (for svc)
        metaData = H264Parser.sps_extract_width_height(n)


        # set a dummy layerid
        metaData["LayerId"] = len(layerDashInfo)
        sys.stderr.write("MetaData=" + str(metaData) + "\r\n")

        metaData["Segments"] = []
        metaData["Bytes"] = 0
        # append to layerDashInfo
        layerDashInfo.append(metaData)

        # create a new entry in segmentOutputBuffer
        segmentOutputBuffer.append("")
    # end if

    # reset segmentNumberChanged, and set the last layerId
    segmentNumberChanged = False
    last = layerId
    lastNaluType = naluType

# stream ended, we still have stuff to write in buffer:
if writeDASHOutput:
    # write buffered output
    print "---- Writing Buffer to File ----"
    for tmpLayerId in range(0, len(segmentOutputBuffer)):
        tmpSegmentFileName = configChunkFilenameTemplate.format(base=base, seg=seg, layerId = tmpLayerId, svcExtension=configSvcExtension)
        # write old segment to file
        print "Writing" , tmpSegmentFileName
        with open(os.path.join(outputFolder, tmpSegmentFileName), 'wb') as fpOut:
            fpOut.write(segmentOutputBuffer[tmpLayerId])
            segmentOutputBuffer[tmpLayerId] = ""
            fpOut.close()
    # end for
# end if


if writeDASHOutput:
    print "----------------------------------"
    print "Generating MPD ..."
    #############################################
    # Write MPD                                 #
    #############################################
    mpdHeader = """<?xml version="1.0" encoding="UTF-8"?>
    <MPD xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns="urn:mpeg:DASH:schema:MPD:2011"
         xsi:schemaLocation="urn:mpeg:DASH:schema:MPD:2011"
         profiles="urn:mpeg:dash:profile:isoff-main:2011"
         type="static"
         mediaPresentationDuration="PT{duration}S"
         minBufferTime="PT2.0S">
              <BaseURL>{baseURL}</BaseURL>
              <Period start="PT0S">
    """

    mpdAdaptationSetStart = """
     <AdaptationSet bitstreamSwitching="true" mimeType="video/svc" startWithSAP="1" maxWidth="{maxWidth}" maxHeight="{maxHeight}" maxFrameRate="{maxFps}" par="16:9">
                    <SegmentBase>
                        <Initialization sourceURL="{initFile}"/>
                    </SegmentBase>
    """

    mpdAdaptationSegmentsAVC = """
     <Representation id="{representationId}" codecs="AVC" mimeType="video/svc"
                                width="{width}" height="{height}" frameRate="{fps}" sar="1:1" bandwidth="{bandwidth}">
                       <SegmentList duration="{framesSegment}" timescale="{fps}">
{SegmentList}
                       </SegmentList>
                    </Representation>
    """


    mpdAdaptationSegmentsSVC = """
     <Representation id="{representationId}" dependencyId="{dependencyId}" codecs="SVC" mimeType="video/svc"
                                width="{width}" height="{height}" frameRate="{fps}" sar="1:1" bandwidth="{bandwidth}">
                       <SegmentList duration="{framesSegment}" timescale="{fps}">
    {SegmentList}
                       </SegmentList>
                    </Representation>
    """

    mpdAdaptationSegmentURL = """                     <SegmentURL media="{SegmentFileName}"/>
    """


    mpdAdaptationSetClosing = """
     </AdaptationSet>
        </Period>
    </MPD>
    """

    videoLength = round(float(frm) / float(frameRate),3)


    mpd = mpdHeader.format(duration=str(videoLength), baseURL=os.path.join(baseURL,outputFolder))
    # determine max width / height
    maxHeight = maxWidth = 0

    for layer in layerDashInfo:
        if layer['Width'] > maxWidth:
            maxWidth = layer['Width']
        if layer['Height'] > maxHeight:
            maxHeight = layer['Height']

    # start new adaptation set
    mpd += mpdAdaptationSetStart.format(maxHeight = maxHeight, maxWidth = maxWidth, maxFps = frameRate, initFile = initFilename)

    lastLayerId=-1
    # append each layer
    for layer in layerDashInfo:
        segmentList = ""
        for segment in layer['Segments']:
            segmentList += mpdAdaptationSegmentURL.format(SegmentFileName = segment)

        # calculate bitrate
        bitrate = float(layer['Bytes']) / float(len(layer['Segments']))
        bitrate = int(bitrate / float(framesPerSeg / frameRate) * 8)

        if layer['LayerId'] == 0: # base layer
            mpd += mpdAdaptationSegmentsAVC.format(width=layer['Width'], height=layer['Height'], fps=frameRate,bandwidth=bitrate,
                                                   framesSegment=framesPerSeg, SegmentList=segmentList,
                                                representationId=layer['LayerId'])
        else:
            mpd += mpdAdaptationSegmentsSVC.format(width=layer['Width'], height=layer['Height'], fps=frameRate,bandwidth=bitrate,
                                                   framesSegment=framesPerSeg, SegmentList=segmentList,
                                                representationId=layer['LayerId'],dependencyId=lastLayerId)
        lastLayerId = layer['LayerId']

    # close adaptation set and mpd file
    mpd += mpdAdaptationSetClosing

    with open(mpdFilename, "w") as mpdOut:
        mpdOut.write(mpd)
        mpdOut.close()
    print mpd
# end writing MPD

# print frame count and number of segments, just to verify everything works!
print "FrameCount=" + str(frm) + ", Segments=" + str(seg+1)

# check if there were any warnings - and print the number of warnings to stderr
sys.stderr.write("Warnings:" + str(warnings) + "\r\n")
if warnings > 0:
    sys.stderr.write("Warning: Segment borders are not proper!\r\n")
sys.stderr.write("FrameCount=" + str(frm) + ", Segments=" + str(seg+1) + "\r\n")


exit(warnings)


