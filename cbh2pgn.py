import numpy as np
from binascii import hexlify
import game
import header
import player
import tournament
import argparse
import sys
from tqdm import tqdm
import chess.pgn

CBH_RECORD_SIZE = 46
CBH_HEADER_SIZE = 46


def to_hex(ls):
    x = str(hexlify(ls))
    return x[2:-1]


parser = argparse.ArgumentParser(
    description='convert a .cbh + .cbg with chess games into a .pgn file')
parser.add_argument('-i', '--input', help='filename of .cbh')
parser.add_argument('-o', '--output', help='filename of output .pgn')

args = parser.parse_args()

if args.input is None or args.output is None:
    parser.print_usage()
    sys.exit(1)

filename_cbh = args.input
filename_out = args.output

if filename_cbh.endswith(".cbh"):
    filename_cbh = filename_cbh[:-4]
if not filename_out.endswith(".pgn"):
    filename_out += ".pgn"

print("input file...: "+str(filename_cbh))
print("output file..: "+str(filename_out))

DB_ROOT = filename_cbh

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
print("")
print("header id: " + to_hex(header_id))
if to_hex(header_id) == "00002c002e01":
    print("created by Chessbase9+?!")
if to_hex(header_id) == "000024002e01":
    print("created by Fritz/CB Light?!")
print("")
pgn_out = open(filename_out, 'w', encoding="utf-8")
exporter = chess.pgn.FileExporter(pgn_out)

nr_records = (len(cbh_file) // 46)

#for i in tqdm(range(1, nr_records)):
for i in tqdm(range(2, 8)):
    cbh_record = cbh_file[46*i:46*(i+1)]

    # get player names
    offset_white = header.get_whiteplayer_offset(cbh_record)
    white_player_name = player.get_name(cbp_file, offset_white)

    offset_black = header.get_blackplayer_offset(cbh_record)
    black_player_name = player.get_name(cbp_file, offset_black)

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

    # get result
    pgn_res = header.get_result(cbh_record)

    # get tournament info
    tournament_offset = header.get_tournament_offset(cbh_record)
    place, site = tournament.get_event_site_totalrounds(cbt_file, tournament_offset)

    # get round + subround
    round,subround = header.get_round_subround(cbh_record)

    w_elo, b_elo = header.get_ratings(cbh_record)

    # get game offset
    game_offset = header.get_game_offset(cbh_record)

    #if header.is_game(cbh_record):
    #    print("game bit is set")
    #else:
    #    print("game bit is NOT set (not a game?)")

    #if header.is_marked_as_deleted(cbh_record):
    #    print("game is marked for deletion")
    #else:
    #    print("game is NOT marked for deletion")

    not_initial, not_encoded, is_960, game_len = game.get_info_gamelen(cbg_file, game_offset)

    pgn_game = None
    if header.is_game(cbh_record) and (not header.is_marked_as_deleted(cbh_record)) \
        and (not_encoded == False) and not is_960:
        # cbg header is 26, after that game starts
        if not_initial:
            fen, cb_position, piece_list = game.decode_start_position(cbg_file, game_offset)
            pgn_game = game.decode(cbg_file[game_offset+4 + 28:game_offset+game_len], cb_position, piece_list, fen=fen)

        else:
            # number denotes the 0th, the 1st, 2nd ... piece of one kind (e.g. 0th white rook in upper left corner
            # 1st white rook in lower left corner
            cb_position = [
             [(game.W_ROOK, 0), (game.W_PAWN, None), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, None), (game.B_ROOK, 0)],
             [(game.W_KNIGHT, 0), (game.W_PAWN, None), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, None), (game.B_KNIGHT, 0)],
             [(game.W_BISHOP, 0), (game.W_PAWN, None), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, None), (game.B_BISHOP, 0)],
             [(game.W_QUEEN, 0), (game.W_PAWN, None), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, None), (game.B_QUEEN, 0)],
             [(game.W_KING, None), (game.W_PAWN, None), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, None), (game.B_KING, None)],
             [(game.W_BISHOP, 1), (game.W_PAWN, None), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, None), (game.B_BISHOP, 1)],
             [(game.W_KNIGHT, 1), (game.W_PAWN, None), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, None), (game.B_KNIGHT, 1)],
             [(game.W_ROOK, 1), (game.W_PAWN, None), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, None), (game.B_ROOK, 1)]
            ]
            piece_list = [None,
             [(3, 0), None, None, None, None, None, None, None],     # white queen on (3,0)
             [(1, 0), (6, 0), None, None, None, None, None, None],   # first white knight on (1,0), second one on (6,0)
             [(2, 0), (5, 0), None, None, None, None, None, None],   # white bishops
             [(0, 0), (7, 0), None, None, None, None, None, None],   # white rooks
             [(3, 7), None, None, None, None, None, None, None],     # black queens
             [(1, 7), (6, 7), None, None, None, None, None, None],   # black knights
             [(2, 7), (5, 7), None, None, None, None, None, None],   # black bishops
             [(0, 7), (7, 7), None, None, None, None, None, None],   # black rooks
             [(4, 0)],                                               # white king
             [(4, 7)],                                               # black king
             [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)], # white pawns
             [(0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6)]] # black pawns
            pgn_game = game.decode(cbg_file[game_offset+4:game_offset+game_len], cb_position, piece_list)
    if pgn_game is not None:
        pgn_game.headers["White"] = white_player_name
        pgn_game.headers["Black"] = black_player_name
        pgn_game.headers["Date"] = pgn_yymmdd
        pgn_game.headers["Result"] = pgn_res
        pgn_game.headers["Place"] = place
        pgn_game.headers["Site"] = site
        if subround != 0:
            pgn_game.headers["Round"] = str(round)+"("+str(subround)+")"
        else:
            pgn_game.headers["Round"] = str(round)
        if w_elo != 0:
            pgn_game.headers["WhiteElo"] = str(w_elo)
        if b_elo != 0:
            pgn_game.headers["BlackElo"] = str(b_elo)
        pgn_game.accept(exporter)
    