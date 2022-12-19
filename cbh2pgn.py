# cbh2pgn converter
# Copyright (c) 2022 Dominik Klein.
# Licensed under MIT (see file LICENSE)

import mmap
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

print("input file...: " + str(filename_cbh))
print("output file..: " + str(filename_out))

DB_ROOT = filename_cbh

CBH = DB_ROOT + ".cbh"  # index
CBG = DB_ROOT + ".cbg"  # games
CBP = DB_ROOT + ".cbp"  # players
CBT = DB_ROOT + ".cbt"  # tournaments
CBE = DB_ROOT + ".cbe"  # teams

f_cbh = open(CBH, "rb")
f_cbp = open(CBP, "rb")
f_cbt = open(CBT, "rb")
f_cbg = open(CBG, "rb")

cbh_file = mmap.mmap(f_cbh.fileno(), 0, prot=mmap.PROT_READ)
cbp_file = mmap.mmap(f_cbp.fileno(), 0, prot=mmap.PROT_READ)
cbt_file = mmap.mmap(f_cbt.fileno(), 0, prot=mmap.PROT_READ)
cbg_file = mmap.mmap(f_cbg.fileno(), 0, prot=mmap.PROT_READ)

header_bytes = cbh_file[0:46]
header_id = header_bytes[0:6]
print("")
print("header id: " + to_hex(header_id))
if to_hex(header_id) == "00002c002e01":
    print("created by CB9+?!")
if to_hex(header_id) == "000024002e01":
    print("created by Chess Program X/CB Light?!")
print("")
pgn_out = open(filename_out, 'w', encoding="utf-8")
exporter = chess.pgn.FileExporter(pgn_out)

nr_records = (len(cbh_file) // 46)

errors_encountered = []

# for i in tqdm(range(1, nr_records)):
for i in tqdm(range(1, nr_records)):
    # 3036382 Poppner, Dietmar vs Von Herman, Ulf
    #         corrupted? additional moves at end, no 0c marker...
    # 3036403 Von Herman, Ulf vs Suchin, Dimitry: game starts with 0x40, i.e. Queen2 (2,2)
    #         instead of Nf3, i.e. 0xFE: (-1, 2)
    #         for this, bit 0 in the first byte at the .cbg game offset is set
    cbh_record = cbh_file[46 * i:46 * (i + 1)]

    # get player names
    offset_white = header.get_whiteplayer_offset(cbh_record)
    white_player_name = player.get_name(cbp_file, offset_white)

    offset_black = header.get_blackplayer_offset(cbh_record)
    black_player_name = player.get_name(cbp_file, offset_black)

    # get date
    yy, mm, dd = header.get_yymmdd(cbh_record)
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
    event, site = tournament.get_event_site_totalrounds(cbt_file, tournament_offset)

    # get round + subround
    round, subround = header.get_round_subround(cbh_record)

    w_elo, b_elo = header.get_ratings(cbh_record)

    # get game offset
    game_offset = header.get_game_offset(cbh_record)

    not_initial, not_encoded, is_960, special_encoding, game_len = game.get_info_gamelen(cbg_file, game_offset)

    # cbg_file[game_offset] is the byte that stores various game encoding and setup information
    # which is useful for debugging
    if special_encoding:
        errors_encountered.append((i, hex(cbg_file[game_offset]), "ignored: special encoding flag"))

    pgn_game = None
    if header.is_game(cbh_record) and (not header.is_marked_as_deleted(cbh_record)) \
            and (not_encoded == 0) and not is_960 and not special_encoding:
        # cbg header is 26, after that game starts
        if not_initial:
            fen, cb_position, piece_list = game.decode_start_position(cbg_file, game_offset)
            pgn_game, err_string = game.decode(cbg_file[game_offset + 4 + 28:game_offset + game_len], cb_position,
                                               piece_list, fen=fen)
            if not (err_string is None):
                errors_encountered.append((i, hex(cbg_file[game_offset]), err_string))
        else:
            # number denotes the 0th, the 1st, 2nd ... piece of one kind (e.g. 0th white rook in upper left corner
            # 1st white rook in lower left corner
            cb_position = [
                [(game.W_ROOK, 0), (game.W_PAWN, 0), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 0),
                 (game.B_ROOK, 0)],
                [(game.W_KNIGHT, 0), (game.W_PAWN, 1), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 1),
                 (game.B_KNIGHT, 0)],
                [(game.W_BISHOP, 0), (game.W_PAWN, 2), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 2),
                 (game.B_BISHOP, 0)],
                [(game.W_QUEEN, 0), (game.W_PAWN, 3), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 3),
                 (game.B_QUEEN, 0)],
                [(game.W_KING, None), (game.W_PAWN, 4), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 4),
                 (game.B_KING, None)],
                [(game.W_BISHOP, 1), (game.W_PAWN, 5), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 5),
                 (game.B_BISHOP, 1)],
                [(game.W_KNIGHT, 1), (game.W_PAWN, 6), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 6),
                 (game.B_KNIGHT, 1)],
                [(game.W_ROOK, 1), (game.W_PAWN, 7), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 7),
                 (game.B_ROOK, 1)]
            ]
            piece_list = [None,
                          [(3, 0), None, None, None, None, None, None, None],  # white queen on (3,0)
                          [(1, 0), (6, 0), None, None, None, None, None, None],
                          # first white knight on (1,0), second one on (6,0)
                          [(2, 0), (5, 0), None, None, None, None, None, None],  # white bishops
                          [(0, 0), (7, 0), None, None, None, None, None, None],  # white rooks
                          [(3, 7), None, None, None, None, None, None, None],  # black queens
                          [(1, 7), (6, 7), None, None, None, None, None, None],  # black knights
                          [(2, 7), (5, 7), None, None, None, None, None, None],  # black bishops
                          [(0, 7), (7, 7), None, None, None, None, None, None],  # black rooks
                          [(4, 0)],  # white king
                          [(4, 7)],  # black king
                          [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)],  # white pawns
                          [(0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6)]]  # black pawns
            pgn_game, err_string = game.decode(cbg_file[game_offset + 4:game_offset + game_len], cb_position, piece_list)
            if not (err_string is None):
                errors_encountered.append((i, hex(cbg_file[game_offset]), err_string))
    if pgn_game is not None:
        pgn_game.headers["White"] = white_player_name
        pgn_game.headers["Black"] = black_player_name
        pgn_game.headers["Date"] = pgn_yymmdd
        pgn_game.headers["Result"] = pgn_res
        pgn_game.headers["Event"] = event
        pgn_game.headers["Site"] = site
        if subround != 0:
            pgn_game.headers["Round"] = str(round) + "(" + str(subround) + ")"
        else:
            pgn_game.headers["Round"] = str(round)
        if w_elo != 0:
            pgn_game.headers["WhiteElo"] = str(w_elo)
        if b_elo != 0:
            pgn_game.headers["BlackElo"] = str(b_elo)
        pgn_game.accept(exporter)

f_cbh.close()
f_cbp.close()
f_cbt.close()
f_cbg.close()

print("errors logged: "+str(len(errors_encountered)))
for err in errors_encountered:
    print(str(err))