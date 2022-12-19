# cbh2pgn converter
# Copyright (c) 2022 Dominik Klein.
# Licensed under MIT (see file LICENSE)

def get_name(cbp_file, player_no):
    if cbp_file[0x18] == 4:
        record_offset = 32 + (player_no * 67)
    elif cbp_file[0x18] == 0:
        record_offset = 28 + (player_no * 67)
    else:
        raise ValueError("unknown CBP file version")
    last_name_bytes = cbp_file[record_offset + 9:record_offset + 9 + 30]
    tmp = last_name_bytes.decode("iso-8859-1").split('\x00')
    if len(tmp) > 0:
        last_name = tmp[0]

    first_name_bytes = cbp_file[record_offset + 39:record_offset + 39 + 20]
    tmp = first_name_bytes.decode("iso-8859-1").split('\x00')
    if len(tmp) > 0:
        first_name = tmp[0]

    return last_name + ", " + first_name
