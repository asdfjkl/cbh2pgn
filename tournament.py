import numpy as np


def get_event_site_totalrounds(cbt_file, tournament_no):
    if cbt_file[0x18] == 4:
        record_offset = 32 + (tournament_no * 99)
    elif cbt_file[0x18] == 0:
        record_offset = 28 + (tournament_no * 99)
    else:
        raise ValueError("unknown CBT file version")

    record = cbt_file[record_offset:record_offset+99]

    title_bytes = record[9:9+40]
    #print("title bytes: " + str(title_bytes))
    terminator_idx = np.where(title_bytes == 0)[0]
    if len(terminator_idx) > 0:
        title_len = terminator_idx[0]
    else:
        title_len = 40
    title_bytes = title_bytes[0:title_len]
    title = title_bytes.tobytes().decode("iso-8859-1")

    place_bytes = record[49:49 + 30]
    #print("place bytes: " + str(place_bytes))
    terminator_idx = np.where(place_bytes == 0)[0]
    if len(terminator_idx) > 0:
        place_len = terminator_idx[0]
    else:
        place_len = 30
    place_bytes = place_bytes[0:place_len]
    place = place_bytes.tobytes().decode("iso-8859-1")

    return title, place
