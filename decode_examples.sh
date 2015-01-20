# 640x360 @ 6 fps
python decode/svc_merge.py factory-L0.264 factory-temporal/factory-IV.init.svc factory-temporal/factory-IV.seg0-L0.svc 

H264AVCDecoderLibTestStatic factory-L0.264 factory-L0.yuv

mplayer -demuxer rawvideo -rawvideo w=640:h=360:format=i420:fps=6 factory-L0.yuv


# 1280x720 @ 6 fps
python decode/svc_merge.py factory-L16.264 factory-temporal/factory-IV.init.svc factory-temporal/factory-IV.seg0-L0.svc factory-temporal/factory-IV.seg0-L16.svc 

H264AVCDecoderLibTestStatic factory-L16.264 factory-L16.yuv

mplayer -demuxer rawvideo -rawvideo w=1280:h=720:format=i420:fps=6 factory-L16.yuv


# 1920x1080 @ 6 fps
python decode/svc_merge.py factory-L32.264 factory-temporal/factory-IV.init.svc factory-temporal/factory-IV.seg0-L0.svc factory-temporal/factory-IV.seg0-L16.svc factory-temporal/factory-IV.seg0-L32.svc

H264AVCDecoderLibTestStatic factory-L32.264 factory-L32.yuv

mplayer -demuxer rawvideo -rawvideo w=1920:h=1080:format=i420:fps=6 factory-L32.yuv


# 1920x1080 @ 6 fps - HQ
python decode/svc_merge.py factory-L48.264 factory-temporal/factory-IV.init.svc factory-temporal/factory-IV.seg0-L0.svc factory-temporal/factory-IV.seg0-L16.svc factory-temporal/factory-IV.seg0-L32.svc factory-temporal/factory-IV.seg0-L48.svc 

H264AVCDecoderLibTestStatic factory-L48.264 factory-L48.yuv

mplayer -demuxer rawvideo -rawvideo w=1920:h=1080:format=i420:fps=6 factory-L48.yuv








# 640x360 @ 12 fps
python decode/svc_merge.py factory-L1.264 factory-temporal/factory-IV.init.svc factory-temporal/factory-IV.seg0-L0.svc -1 factory-temporal/factory-IV.seg0-L1.svc

H264AVCDecoderLibTestStatic factory-L1.264 factory-L1.yuv

mplayer -demuxer rawvideo -rawvideo w=640:h=360:format=i420:fps=12 factory-L1.yuv


# 1280x720 @ 12 fps
python decode/svc_merge.py factory-L17.264 factory-temporal/factory-IV.init.svc factory-temporal/factory-IV.seg0-L0.svc factory-temporal/factory-IV.seg0-L16.svc -1 factory-temporal/factory-IV.seg0-L1.svc factory-temporal/factory-IV.seg0-L17.svc

H264AVCDecoderLibTestStatic factory-L17.264 factory-L17.yuv

mplayer -demuxer rawvideo -rawvideo w=1280:h=720:format=i420:fps=12 factory-L17.yuv


# 1920x1080 @ 12 fps
python decode/svc_merge.py factory-L33.264 factory-temporal/factory-IV.init.svc factory-temporal/factory-IV.seg0-L0.svc factory-temporal/factory-IV.seg0-L16.svc factory-temporal/factory-IV.seg0-L32.svc -1 factory-temporal/factory-IV.seg0-L1.svc factory-temporal/factory-IV.seg0-L17.svc factory-temporal/factory-IV.seg0-L33.svc

H264AVCDecoderLibTestStatic factory-L33.264 factory-L33.yuv

mplayer -demuxer rawvideo -rawvideo w=1920:h=1080:format=i420:fps=12 factory-L33.yuv


# 1920x1080 @ 12 fps - HQ
python decode/svc_merge.py factory-L49.264 factory-temporal/factory-IV.init.svc factory-temporal/factory-IV.seg0-L0.svc factory-temporal/factory-IV.seg0-L16.svc factory-temporal/factory-IV.seg0-L32.svc factory-temporal/factory-IV.seg0-L48.svc -1 factory-temporal/factory-IV.seg0-L1.svc factory-temporal/factory-IV.seg0-L17.svc factory-temporal/factory-IV.seg0-L33.svc factory-temporal/factory-IV.seg0-L49.svc

H264AVCDecoderLibTestStatic factory-L49.264 factory-L49.yuv

mplayer -demuxer rawvideo -rawvideo w=1920:h=1080:format=i420:fps=12 factory-L49.yuv





# TODO (problems exist here)
# 640x360 @ 24 fps
python decode/svc_merge.py factory-L2.264 factory-temporal/factory-IV.init.svc factory-temporal/factory-IV.seg0-L0.svc -1 factory-temporal/factory-IV.seg0-L1.svc -2 factory-temporal/factory-IV.seg0-L2.svc

H264AVCDecoderLibTestStatic factory-L2.264 factory-L2.yuv

mplayer -demuxer rawvideo -rawvideo w=640:h=360:format=i420:fps=24 factory-L2.yuv



# TODO (problems exist here)
# 1280x720 @ 24 fps
python decode/svc_merge.py factory-L18.264 factory-temporal/factory-IV.init.svc factory-temporal/factory-IV.seg0-L0.svc factory-temporal/factory-IV.seg0-L16.svc -1 factory-temporal/factory-IV.seg0-L1.svc factory-temporal/factory-IV.seg0-L17.svc -2 factory-temporal/factory-IV.seg0-L2.svc factory-temporal/factory-IV.seg0-L18.svc

H264AVCDecoderLibTestStatic factory-L18.264 factory-L18.yuv

mplayer -demuxer rawvideo -rawvideo w=1280:h=720:format=i420:fps=24 factory-L18.yuv



