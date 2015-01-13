from bitstring import ConstBitStream
import binascii


# sps_extract_width_height extracts information from the H.264 bitstream, in particular it processes the
# NAL-unit types 7 and 15 (Sequence Parameter Set and Subsequence Parmaeter Set, resp.).as
def sps_extract_width_height(byte_array):
    s = ConstBitStream("0x" + binascii.hexlify(byte_array))

    # read forbidden_zero_bit, nal_ref_idc and nal_unit_type
    forbidden_zero_bit = s.read('uint:1')
    nal_ref_idc = s.read('uint:2')
    nal_unit_type = s.read('uint:5')

    if nal_unit_type != 15 and nal_unit_type != 7:
        Exception("Error in SPS_extract_width_height: Expected nalu type 7 or 15 (SPS), but got " + str(nal_unit_type))
        return
    # end if

    profile_idc = s.read('uint:8')

    # read constraint set (5 bit)
    constrained_set = s.read('bits:5')

    # read reserved zero 3 bit
    s.read('uint:3') # ignore

    level_idc = s.read('uint:8')

    seq_param_set_id = s.read('ue')

    if profile_idc == 100 or profile_idc == 110 or profile_idc == 122 or profile_idc == 244 or profile_idc == 44 or profile_idc == 83 or profile_idc == 86 or profile_idc == 118:
        chroma_format_idc = s.read('ue')
        separate_colour_plane_flag = 0
        if chroma_format_idc == 3:
            separate_colour_plane_flag = s.read('uint:1')
        # end if
        bit_depth_luma_minus8 = s.read('ue')
        bit_depth_chroma_minus8 = s.read('ue')
        qpprime_y_zero_transform_bypass_flag2 = s.read('uint:1')
        seq_scaling_matrix_present_flag = s.read('uint:1')
    # end if

    log2_max_frame_num_minus4 = s.read('ue')
    pic_order_cnt_type = s.read('ue')
    log2_max_pic_order_cnt_lsb_minus4 = s.read('ue')
    max_num_ref_frames = s.read('ue')
    gaps_in_frame_num_value_allowed_flag = s.read('uint:1')

    pic_width_in_mbs_minus1 = s.read('ue')
    pic_height_in_map_units_minus1 = s.read('ue')

    frame_mbs_only_flag = s.read('uint:1')
    direct_8x8_inference_flag = s.read('uint:1')

    frame_cropping_flag = s.read('uint:1')

    # initialize frame_crop_*_offset
    frame_crop_left_offset = frame_crop_right_offset = frame_crop_top_offset = frame_crop_bottom_offset = 0

    # get offsets
    if frame_cropping_flag == 1:
        frame_crop_left_offset = s.read('ue')
        frame_crop_right_offset = s.read('ue')
        frame_crop_top_offset = s.read('ue')
        frame_crop_bottom_offset = s.read('ue')


    Width = ((pic_width_in_mbs_minus1 + 1) * 16) - (frame_crop_right_offset * 2) - (frame_crop_left_offset * 2)
    Height = ((2 - frame_mbs_only_flag) * (pic_height_in_map_units_minus1 + 1) * 16) - frame_crop_bottom_offset*2 - frame_crop_top_offset*2

    FramesPerSecond = 0

    return {'ProfileIDC': profile_idc, 'LevelIDC': level_idc, 'SPS-ID': seq_param_set_id, 'Width': Width, 'Height': Height, 'FPS': FramesPerSecond}
# end function