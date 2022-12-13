import struct
import numpy as np
from binascii import hexlify

import game
import header
import player
import tournament

# 7 Tag Roster + FEN
# [DONE] Event
# [DONE] Site
# [DONE] Date
# [DONE] Round
# [DONE] White
# [DONE] Black
# [DONE] Result
# [DONE] Rating White
# [DONE] Rating Black
# FEN
CBH_RECORD_SIZE = 46
CBH_HEADER_SIZE = 46


def to_hex(ls):
    x = str(hexlify(ls))
    return x[2:-1]


#DB_ROOT = "/home/user/MyFiles/workspace/test_databases/Fritz7/database"
#DB_ROOT = "/home/user/MyFiles/workspace/test_databases/Fritz17/Database 2020"
#DB_ROOT = "/home/user/MyFiles/workspace/test_databases/umlaut"
#DB_ROOT = "/home/user/MyFiles/workspace/test_databases/yymmdd"
#DB_ROOT = "/home/user/MyFiles/workspace/test_databases/start_pos"
#DB_ROOT = "/home/user/MyFiles/workspace/test_databases/f8_simple_game"
#DB_ROOT = "/home/user/MyFiles/workspace/test_databases/f8_simple_game_capture"
DB_ROOT = "/home/user/MyFiles/workspace/test_databases/f8_d1d2d3d4"
#DB_ROOT = "/media/user/28CE7A31CE79F800/Users/Domin/Desktop/db_compare/f7_standard_custom"
#DB_ROOT = "/media/user/28CE7A31CE79F800/Users/Domin/Desktop/db_compare/f13_960_init"

CBH = DB_ROOT + ".cbh" # index
CBG = DB_ROOT + ".cbg" # games
CBP = DB_ROOT + ".cbp" # players
CBT = DB_ROOT + ".cbt" # tournaments
CBE = DB_ROOT + ".cbe" # teams

cbh_file = np.memmap(CBH, dtype=np.uint8)
cbp_file = np.memmap(CBP, dtype=np.uint8)
cbt_file = np.memmap(CBT, dtype=np.uint8)
cbg_file = np.memmap(CBG, dtype=np.uint8)

header_bytes = cbh_file[0:46]
header_id = header_bytes[0:6]
print("header id: " + to_hex(header_id))
if to_hex(header_id) == "00002c002e01":
    print("created by Chessbase9+")
if to_hex(header_id) == "000024002e01":
    print("created by Fritz/CB Light")

cbh_record = cbh_file[46*1:46*2]

# get player names
offset_white = header.get_whiteplayer_offset(cbh_record)
white_player_name = player.get_name(cbp_file, offset_white)
print("White: "+str(white_player_name))

offset_black = header.get_blackplayer_offset(cbh_record)
black_player_name = player.get_name(cbp_file, offset_black)
print("Black: "+str(black_player_name))

# get date
yy,mm,dd = header.get_yymmdd(cbh_record)
pgn_yymmdd = ""
if yy != 0:
    pgn_yymmdd += "{:04d}".format(yy)
else:
    pgn_yymmdd += "????"
pgn_yymmdd += "."
if mm != 0:
    pgn_yymmdd += "{:02d}".format(mm)
else:
    pgn_yymmdd += "??"
pgn_yymmdd += "."
if dd != 0:
    pgn_yymmdd += "{:02d}".format(dd)
else:
    pgn_yymmdd += "??"
print("Date:")
print(yy,mm,dd)
print(pgn_yymmdd)

# get result
pgn_res = header.get_result(cbh_record)
print("Result: "+str(pgn_res))

# get tournament info
tournament_offset = header.get_tournament_offset(cbh_record)
place, site = tournament.get_event_site_totalrounds(cbt_file, tournament_offset)
print("Place, Site:")
print(place,site)

# get round + subround
round,subround = header.get_round_subround(cbh_record)
print("round, subround: "+str(round) + ", "+str(subround))

w_elo, b_elo = header.get_ratings(cbh_record)
print("Elo White: "+str(w_elo))
print("Elo Black: "+str(b_elo))

# get game offset
game_offset = header.get_game_offset(cbh_record)
print("game offset (in cbg): "+str(game_offset))
print("game offset (in cbg): "+str(hex(game_offset))+" h")

if header.is_game(cbh_record):
    print("game bit is set")
else:
    print("game bit is NOT set (not a game?)")

if header.is_marked_as_deleted(cbh_record):
    print("game is marked for deletion")
else:
    print("game is NOT marked for deletion")

not_initial, not_encoded, is_960, game_len = game.decode_start(cbg_file, game_offset)
print("Starting FEN: "+str(not_initial == 1))
print("Not a Game: "+str(not_encoded == 1))
print("Is 960: "+str(is_960 == 1))
print("Game Length: "+str(game_len))

cb_position = None
fen = None
# cbg header is 26, after that game starts
if not_initial:
    fen, position, cb_position, piece_list = game.decode_position(cbg_file, game_offset+4)
    print(fen)
    print(position)
    print(cb_position)
    print("cbg initial position:")
    print([ hex(i) for i in cbg_file[game_offset + 4 :game_offset + 4 + 28]])
    print("cbg game bytes:")
    print([ hex(i) for i in cbg_file[game_offset + 4 + 24:game_offset + game_len]])
    game = game.decode(cbg_file[game_offset+4 + 28:game_offset+game_len], cb_position, piece_list, fen=fen)
    print(game)
else:
    initial_position = [
        [ game.W_ROOK, game.W_PAWN, 0, 0, 0, 0, game.B_PAWN, game.B_ROOK ],
        [ game.W_KNIGHT, game.W_PAWN, 0, 0, 0, 0, game.B_PAWN, game.B_KNIGHT ],
        [ game.W_BISHOP, game.W_PAWN, 0, 0, 0, 0, game.B_PAWN, game.B_BISHOP ],
        [ game.W_QUEEN, game.W_PAWN, 0, 0, 0, 0, game.B_PAWN, game.B_QUEEN ],
        [ game.W_KING, game.W_PAWN, 0, 0, 0, 0, game.B_PAWN, game.B_KING ],
        [ game.W_BISHOP, game.W_PAWN, 0, 0, 0, 0, game.B_PAWN, game.B_BISHOP ],
        [ game.W_KNIGHT, game.W_PAWN, 0, 0, 0, 0, game.B_PAWN, game.B_KNIGHT ],
        [ game.W_ROOK, game.W_PAWN, 0, 0, 0, 0, game.B_PAWN, game.B_ROOK ]
    ]
    cb_position, piece_list = game.convert_pos_to_cb(initial_position)
    print("cbg game bytes:")
    print([ hex(i) for i in cbg_file[game_offset + 4:game_offset + game_len]])
    game = game.decode(cbg_file[game_offset+4:game_offset+game_len], cb_position, piece_list, fen=fen)
    print(game)