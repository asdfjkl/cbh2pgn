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
import os
import time
import tempfile
from tqdm import tqdm
import chess.pgn

CBH_RECORD_SIZE = 46
CBH_HEADER_SIZE = 46

# Standard initial position and piece list used for games starting from
# the default chess position (not_initial == False).
INITIAL_CB_POSITION = [
    [(game.W_ROOK, 0), (game.W_PAWN, 0), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 0), (game.B_ROOK, 0)],
    [(game.W_KNIGHT, 0), (game.W_PAWN, 1), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 1), (game.B_KNIGHT, 0)],
    [(game.W_BISHOP, 0), (game.W_PAWN, 2), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 2), (game.B_BISHOP, 0)],
    [(game.W_QUEEN, 0), (game.W_PAWN, 3), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 3), (game.B_QUEEN, 0)],
    [(game.W_KING, None), (game.W_PAWN, 4), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 4), (game.B_KING, None)],
    [(game.W_BISHOP, 1), (game.W_PAWN, 5), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 5), (game.B_BISHOP, 1)],
    [(game.W_KNIGHT, 1), (game.W_PAWN, 6), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 6), (game.B_KNIGHT, 1)],
    [(game.W_ROOK, 1), (game.W_PAWN, 7), (0, None), (0, None), (0, None), (0, None), (game.B_PAWN, 7), (game.B_ROOK, 1)]
]

INITIAL_PIECE_LIST = [None,
    [(3, 0), None, None, None, None, None, None, None],
    [(1, 0), (6, 0), None, None, None, None, None, None],
    [(2, 0), (5, 0), None, None, None, None, None, None],
    [(0, 0), (7, 0), None, None, None, None, None, None],
    [(3, 7), None, None, None, None, None, None, None],
    [(1, 7), (6, 7), None, None, None, None, None, None],
    [(2, 7), (5, 7), None, None, None, None, None, None],
    [(0, 7), (7, 7), None, None, None, None, None, None],
    [(4, 0)],
    [(4, 7)],
    [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)],
    [(0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6)]]


def to_hex(ls):
    x = str(hexlify(ls))
    return x[2:-1]


def format_date(cbh_record):
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
    return pgn_yymmdd


def convert_record(i, cbh_file, cbg_file, cbp_file, cbt_file):
    """Convert a single CBH record to a PGN game. Returns (pgn_game, error) or (None, error)."""
    cbh_record = cbh_file[46 * i:46 * (i + 1)]

    offset_white = header.get_whiteplayer_offset(cbh_record)
    white_player_name = player.get_name(cbp_file, offset_white)

    offset_black = header.get_blackplayer_offset(cbh_record)
    black_player_name = player.get_name(cbp_file, offset_black)

    pgn_yymmdd = format_date(cbh_record)
    pgn_res = header.get_result(cbh_record)

    tournament_offset = header.get_tournament_offset(cbh_record)
    event, site = tournament.get_event_site_totalrounds(cbt_file, tournament_offset)

    rnd, subround = header.get_round_subround(cbh_record)
    w_elo, b_elo = header.get_ratings(cbh_record)
    game_offset = header.get_game_offset(cbh_record)

    not_initial, not_encoded, is_960, special_encoding, game_len = game.get_info_gamelen(cbg_file, game_offset)

    err = None
    if special_encoding:
        err = (i, hex(cbg_file[game_offset]), "ignored: special encoding flag")

    pgn_game = None
    if header.is_game(cbh_record) and (not header.is_marked_as_deleted(cbh_record)) \
            and (not_encoded == 0) and not is_960 and not special_encoding:
        if not_initial:
            fen, cb_position, piece_list = game.decode_start_position(cbg_file, game_offset)
            pgn_game, err_string = game.decode(cbg_file[game_offset + 4 + 28:game_offset + game_len], cb_position,
                                               piece_list, fen=fen)
            if not (err_string is None):
                err = (i, hex(cbg_file[game_offset]), err_string)
        else:
            import copy
            cb_position = copy.deepcopy(INITIAL_CB_POSITION)
            piece_list = copy.deepcopy(INITIAL_PIECE_LIST)
            pgn_game, err_string = game.decode(cbg_file[game_offset + 4:game_offset + game_len], cb_position, piece_list)
            if not (err_string is None):
                err = (i, hex(cbg_file[game_offset]), err_string)

    if pgn_game is not None:
        pgn_game.headers["White"] = white_player_name
        pgn_game.headers["Black"] = black_player_name
        pgn_game.headers["Date"] = pgn_yymmdd
        pgn_game.headers["Result"] = pgn_res
        pgn_game.headers["Event"] = event
        pgn_game.headers["Site"] = site
        if subround != 0:
            pgn_game.headers["Round"] = str(rnd) + "(" + str(subround) + ")"
        else:
            pgn_game.headers["Round"] = str(rnd)
        if w_elo != 0:
            pgn_game.headers["WhiteElo"] = str(w_elo)
        if b_elo != 0:
            pgn_game.headers["BlackElo"] = str(b_elo)

    return pgn_game, err


def convert_chunk(args):
    """Worker function for parallel mode: convert a range of records to a temp PGN file."""
    db_root, start, end, chunk_id, temp_dir = args

    f_cbh = open(db_root + ".cbh", "rb")
    f_cbg = open(db_root + ".cbg", "rb")
    f_cbp = open(db_root + ".cbp", "rb")
    f_cbt = open(db_root + ".cbt", "rb")

    cbh_file = mmap.mmap(f_cbh.fileno(), 0, prot=mmap.PROT_READ)
    cbg_file = mmap.mmap(f_cbg.fileno(), 0, prot=mmap.PROT_READ)
    cbp_file = mmap.mmap(f_cbp.fileno(), 0, prot=mmap.PROT_READ)
    cbt_file = mmap.mmap(f_cbt.fileno(), 0, prot=mmap.PROT_READ)

    out_path = os.path.join(temp_dir, "chunk_{:04d}.pgn".format(chunk_id))
    pgn_out = open(out_path, 'w', encoding='utf-8')
    exporter = chess.pgn.FileExporter(pgn_out)

    errors = []
    games_written = 0

    for i in range(start, end):
        pgn_game, err = convert_record(i, cbh_file, cbg_file, cbp_file, cbt_file)
        if err:
            errors.append(err)
        if pgn_game is not None:
            pgn_game.accept(exporter)
            games_written += 1

    pgn_out.close()
    f_cbh.close()
    f_cbg.close()
    f_cbp.close()
    f_cbt.close()

    return chunk_id, games_written, errors, out_path


def run_parallel(filename_cbh, filename_out, num_workers):
    """Convert using multiple parallel worker processes."""
    from multiprocessing import Pool, cpu_count

    cbh_size = os.path.getsize(filename_cbh + ".cbh")
    nr_records = cbh_size // CBH_RECORD_SIZE

    if num_workers <= 0:
        num_workers = max(1, cpu_count() - 2)

    print("input file...: " + str(filename_cbh))
    print("output file..: " + str(filename_out))
    print("records......: {:,}".format(nr_records))
    print("workers......: {}".format(num_workers))
    print("")

    # Split records into chunks (skip record 0 = file header)
    records_per_chunk = max(1, (nr_records - 1) // num_workers)
    chunks = []
    temp_dir = tempfile.mkdtemp(prefix="cbh2pgn_")

    for chunk_id in range(num_workers):
        start = 1 + chunk_id * records_per_chunk
        if chunk_id == num_workers - 1:
            end = nr_records
        else:
            end = 1 + (chunk_id + 1) * records_per_chunk
        if start < nr_records:
            chunks.append((filename_cbh, start, end, chunk_id, temp_dir))

    print("split into {} chunks of ~{:,} records each".format(len(chunks), records_per_chunk))
    print("")

    t0 = time.time()

    with Pool(processes=num_workers) as pool:
        results = []
        for result in pool.imap_unordered(convert_chunk, chunks):
            chunk_id, games_written, errors, out_path = result
            elapsed = time.time() - t0
            print("  chunk {:4d} done: {:,} games, {} errors  [{:.0f}s elapsed]".format(
                chunk_id, games_written, len(errors), elapsed))
            results.append(result)

    # Sort by chunk_id to maintain original game order
    results.sort(key=lambda x: x[0])

    print("")
    print("concatenating {} chunks...".format(len(results)))

    total_games = 0
    all_errors = []

    with open(filename_out, 'w', encoding='utf-8') as out:
        for chunk_id, games_written, errors, out_path in results:
            total_games += games_written
            all_errors.extend(errors)
            with open(out_path, 'r', encoding='utf-8') as chunk_f:
                for line in chunk_f:
                    out.write(line)
            os.unlink(out_path)

    os.rmdir(temp_dir)

    elapsed = time.time() - t0
    rate = total_games / elapsed if elapsed > 0 else 0

    print("")
    print("done!")
    print("  total games.: {:,}".format(total_games))
    print("  total time..: {:.1f}s ({:,.0f} games/sec)".format(elapsed, rate))
    print("  output size.: {:.2f} GB".format(os.path.getsize(filename_out) / (1024**3)))
    print("  errors logged: {}".format(len(all_errors)))
    for err in all_errors:
        print("  " + str(err))


def run_sequential(filename_cbh, filename_out):
    """Original single-threaded conversion."""
    f_cbh = open(filename_cbh + ".cbh", "rb")
    f_cbp = open(filename_cbh + ".cbp", "rb")
    f_cbt = open(filename_cbh + ".cbt", "rb")
    f_cbg = open(filename_cbh + ".cbg", "rb")

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

    for i in tqdm(range(1, nr_records)):
        pgn_game, err = convert_record(i, cbh_file, cbg_file, cbp_file, cbt_file)
        if err:
            errors_encountered.append(err)
        if pgn_game is not None:
            pgn_game.accept(exporter)

    f_cbh.close()
    f_cbp.close()
    f_cbt.close()
    f_cbg.close()

    print("errors logged: " + str(len(errors_encountered)))
    for err in errors_encountered:
        print(str(err))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='convert a .cbh + .cbg with chess games into a .pgn file')
    parser.add_argument('-i', '--input', help='filename of .cbh', required=True)
    parser.add_argument('-o', '--output', help='filename of output .pgn', required=True)
    parser.add_argument('-p', '--parallel', type=int, nargs='?', const=0, default=None,
                        metavar='N',
                        help='enable parallel conversion. N = number of worker processes '
                             '(default: number of CPU cores minus 2)')

    args = parser.parse_args()

    filename_cbh = args.input
    filename_out = args.output

    if filename_cbh.endswith(".cbh"):
        filename_cbh = filename_cbh[:-4]
    if not filename_out.endswith(".pgn"):
        filename_out += ".pgn"

    if args.parallel is not None:
        run_parallel(filename_cbh, filename_out, args.parallel)
    else:
        print("input file...: " + str(filename_cbh))
        print("output file..: " + str(filename_out))
        run_sequential(filename_cbh, filename_out)
