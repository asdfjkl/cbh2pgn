# decode header data file
import struct

MASK_IS_GAME = int('00000001', 2)
MASK_MARKED_FOR_DELETION = int('10000000', 2)
MASK_DAY = int('000000000000000000011111', 2)
MASK_MONTH = int('000000000000000111100000', 2)
MASK_YEAR = int('111111111111111000000000', 2)


def get_ratings(cbh_record):
    white_elo = struct.unpack(">H", cbh_record[31:33])
    black_elo = struct.unpack(">H", cbh_record[33:35])
    return white_elo[0], black_elo[0]


def get_round_subround(cbh_record):
    return int(cbh_record[29]), int(cbh_record[30])


def get_result(cbh_record):
    res_code = cbh_record[27]
    if res_code == 2:
        return "1-0"
    if res_code == 1:
        return "1/2-1/2"
    if res_code == 0:
        return "0-1"
    return "*"


def get_yymmdd(cbh_record):
    yymmdd = [ 0 for x in range(0,4) ]
    yymmdd[1:4] = cbh_record[24:27]
    yymmdd_uint32 = struct.unpack(">I", bytearray(yymmdd))[0]
    year = (yymmdd_uint32 & MASK_YEAR) >> 9
    month = (yymmdd_uint32 & MASK_MONTH) >> 5
    day = yymmdd_uint32 & MASK_DAY
    return year, month, day


def get_whiteplayer_offset(cbh_record):
    player_no_white = [0 for x in range(0, 4)]
    player_no_white[1:4] = cbh_record[9:12]
    white_player_int = struct.unpack(">I", bytearray(player_no_white))
    if len(white_player_int) > 0:
        return white_player_int[0]
    else:
        raise ValueError("unable to parse white player offset")


def get_blackplayer_offset(cbh_record):
    player_no_black = [0 for x in range(0, 4)]
    player_no_black[1:4] = cbh_record[12:15]
    black_player_int = struct.unpack(">I", bytearray(player_no_black))
    if len(black_player_int) > 0:
        return black_player_int[0]
    else:
        raise ValueError("unable to parse black player offset")


def get_tournament_offset(cbh_record):
    tournament_no = [0 for x in range(0, 4)]
    tournament_no[1:4] = cbh_record[15:18]
    tournament_int = struct.unpack(">I", bytearray(tournament_no))
    if len(tournament_int) > 0:
        return tournament_int[0]
    else:
        raise ValueError("unable to parse tournament info offset")


def get_game_offset(cbh_record):
    #print([hex(x) for x in cbh_record[1:5]])
    game_offset_int = struct.unpack(">I", bytearray(cbh_record[1:5]))
    if len(game_offset_int) > 0:
        return game_offset_int[0]
    else:
        raise ValueError("unable to parse game offset")


def is_marked_as_deleted(cbh_record):
    marked_for_deletion = (MASK_MARKED_FOR_DELETION & cbh_record[0]) >> 7
    return marked_for_deletion == 1


def is_game(cbh_record):
    return (MASK_IS_GAME & cbh_record[0]) == 1

