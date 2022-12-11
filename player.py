import numpy as np


def get_name(cbp_file, player_no):
    if cbp_file[0x18] == 4:
        record_offset = 32 + (player_no * 67)
    elif cbp_file[0x18] == 0:
        record_offset = 28 + (player_no * 67)
    else:
        raise ValueError("unknown CBP file version")
    last_name_bytes = cbp_file[record_offset + 9:record_offset + 9 + 30]
    terminator_idx = np.where(last_name_bytes == 0)[0]
    if len(terminator_idx) > 0:
        last_name_len = terminator_idx[0]
    else:
        last_name_len = 30
    last_name_bytes = last_name_bytes[0:last_name_len]
    last_name = last_name_bytes.tobytes().decode("iso-8859-1")

    first_name_bytes = cbp_file[record_offset + 39:record_offset + 39 + 20]
    terminator_idx = np.where(first_name_bytes == 0)[0]
    if len(terminator_idx) > 0:
        first_name_len = terminator_idx[0]
    else:
        first_name_len = 30
    first_name_bytes = first_name_bytes[0:first_name_len]
    first_name = first_name_bytes.tobytes().decode("iso-8859-1")

    return last_name + ", " + first_name
