# cbh2pgn converter
# Copyright (c) 2022 Dominik Klein.
# Licensed under MIT (see file LICENSE)

def get_event_site_totalrounds(cbt_file, tournament_no):
    if cbt_file[0x18] == 4:
        record_offset = 32 + (tournament_no * 99)
    elif cbt_file[0x18] == 0:
        record_offset = 28 + (tournament_no * 99)
    else:
        raise ValueError("unknown CBT file version")

    record = cbt_file[record_offset:record_offset+99]

    title_bytes = record[9:9+40]
    tmp = title_bytes.decode("utf-8", errors="replace").split('\x00')
    if len(tmp) > 0:
        title = tmp[0]

    place_bytes = record[49:49 + 30]
    tmp = place_bytes.decode("utf-8", errors="replace").split('\x00')
    if len(tmp) > 0:
        place = tmp[0]

    return title, place
