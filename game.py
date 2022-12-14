import struct

# import chess
import chess.pgn
import numpy as np

MASK_START_WITH_INITIAL = 0x40000000
MASK_IS_ENCODED = 0x80000000
# MASK_GAME_LEN = 0x3FFFFFFF
MASK_GAME_LEN = 0x00FFFFFF
MASK_IS_960 = 0x00A000000


def decode_start(cbg_file, offset):
    size_info = struct.unpack(">I", cbg_file[offset:offset + 4])
    if len(size_info) > 0:
        # print(bin(size_info[0]))
        # print(hex(cbg_file[offset+32]))
        not_initial = (size_info[0] & MASK_START_WITH_INITIAL) >> 30
        not_encoded = (size_info[0] & MASK_IS_ENCODED) >> 31
        if (size_info[0] & MASK_IS_960) > 0:
            is_960 = 1
        else:
            is_960 = 0
        game_len = (size_info[0] & MASK_GAME_LEN)
        # print("game len: "+str(game_len))
        return not_initial, not_encoded, is_960, (game_len - 1)
        # print("res: ")
        # print(str(res))
    else:
        raise ValueError("Unable to extract size info from game file")


MASK_EP_FILE = 0x7
MASK_TURN = 0x10

MASK_WHITE_CASTLE_LONG = 1
MASK_WHITE_CASTLE_SHORT = 2
MASK_BLACK_CASTLE_LONG = 4
MASK_BLACK_CASTLE_SHORT = 8


W_QUEEN = 1
W_KNIGHT = 2
W_BISHOP = 3
W_ROOK = 4

B_QUEEN = 5
B_KNIGHT = 6
B_BISHOP = 7
B_ROOK = 8

W_KING = 9
B_KING = 10
W_PAWN = 11
B_PAWN = 12



SQN = [
    ["a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8"],
    ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8"],
    ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"],
    ["d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8"],
    ["e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8"],
    ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8"],
    ["g1", "g2", "g3", "g4", "g5", "g6", "g7", "g8"],
    ["h1", "h2", "h3", "h4", "h5", "h6", "h7", "h8"]
]


def decode_position_bitstream(s):
    board = np.zeros(64, dtype=np.uint8)
    s_idx = 0
    b_idx = 0
    while s_idx < len(s) and b_idx < 64:
        if s[s_idx] == '0':
            s_idx += 1
            b_idx += 1
        else:
            if len(s) - s_idx < 5:
                raise ValueError("Error decoding position: " + str(s))
            else:
                piece = s[s_idx:s_idx + 5]
                if piece == '10001':
                    board[b_idx] = W_KING
                elif piece == '10010':
                    board[b_idx] = W_QUEEN
                elif piece == '10011':
                    board[b_idx] = W_KNIGHT
                elif piece == '10100':
                    board[b_idx] = W_BISHOP
                    # print("w bishop")
                elif piece == '10101':
                    board[b_idx] = W_ROOK
                elif piece == '10110':
                    board[b_idx] = W_PAWN
                elif piece == '11001':
                    board[b_idx] = B_KING
                elif piece == '11010':
                    board[b_idx] = B_QUEEN
                elif piece == '11011':
                    board[b_idx] = B_KNIGHT
                elif piece == '11100':
                    board[b_idx] = B_BISHOP
                elif piece == '11101':
                    board[b_idx] = B_ROOK
                    # print("b rook")
                elif piece == '11110':
                    board[b_idx] = B_PAWN
                else:
                    raise ValueError(
                        "Error parsing position setup, piece: " + str(piece) + "@pos " + str(s_idx) + " from " + str(s))
                s_idx += 5
                b_idx += 1
    return board.reshape(8, 8)


def convert_pos_to_cb(position):
    w_queens = []
    w_rooks = []
    w_bishops = []
    w_knights = []
    w_kings = [None]  # always 1
    w_pawns = [None for x in range(0, 8)]
    b_queens = []
    b_rooks = []
    b_bishops = []
    b_knights = []
    b_kings = [None]  # always 1
    b_pawns = [None for x in range(0, 8)]

    # put the piece lists into another list, so that we can index them
    # by constants W_KING, W_QUEEN, etc.
    piece_list = [None,
                  w_queens, w_knights, w_bishops, w_rooks, b_queens, b_knights, \
                  b_bishops, b_rooks, w_kings, b_kings, w_pawns, b_pawns ]
    cb_position = [[(0, None) for x in range(0, 8)] for y in range(0, 8)]
    for i in range(0, 8):
        for j in range(0, 8):
            if position[i][j] == W_QUEEN:
                l = len(w_queens)  # becomes the l queen, zero-indexed (len 0 -> 0th queen)
                cb_position[i][j] = (W_QUEEN, l)
                piece_list[W_QUEEN].append((i, j))
            if position[i][j] == W_ROOK:
                l = len(w_rooks)
                cb_position[i][j] = (W_ROOK, l)
                piece_list[W_ROOK].append((i, j))
            if position[i][j] == W_BISHOP:
                l = len(w_bishops)
                cb_position[i][j] = (W_BISHOP, l)
                piece_list[W_BISHOP].append((i, j))
            if position[i][j] == W_KNIGHT:
                l = len(w_knights)
                cb_position[i][j] = (W_KNIGHT, l)
                piece_list[W_KNIGHT].append((i, j))
            if position[i][j] == W_PAWN:
                cb_position[i][j] = (W_PAWN, None)
                piece_list[W_PAWN][i] = (i, j)
            if position[i][j] == W_KING:
                cb_position[i][j] = (W_KING, None)
                piece_list[W_KING][0] = (i, j)
            if position[i][j] == B_QUEEN:
                l = len(b_queens)
                cb_position[i][j] = (B_QUEEN, l)
                piece_list[B_QUEEN].append((i, j))
            if position[i][j] == B_ROOK:
                l = len(b_rooks)
                cb_position[i][j] = (B_ROOK, l)
                piece_list[B_ROOK].append((i, j))
            if position[i][j] == B_BISHOP:
                l = len(b_bishops)
                cb_position[i][j] = (B_BISHOP, l)
                piece_list[B_BISHOP].append((i, j))
            if position[i][j] == B_KNIGHT:
                l = len(b_knights)
                cb_position[i][j] = (B_KNIGHT, l)
                piece_list[B_KNIGHT].append((i, j))
            if position[i][j] == B_PAWN:
                cb_position[i][j] = (B_PAWN, None)
                piece_list[B_PAWN][i] = (i, j)
            if position[i][j] == B_KING:
                cb_position[i][j] = (B_KING, None)
                piece_list[B_KING][0] = (i, j)
            if position[i][j] == 0:
                cb_position[i][j] = (0, None)
    # make sure that all piece lists have 8 elements
    # will make replacing piece nr down later easier
    for i in range(W_QUEEN, B_ROOK+1):
        l = len(piece_list[i])
        for j in range(l, 8):
            piece_list[i].append(None)
    return cb_position, piece_list


# when game is not in starting position decode it
# offset for starting position is usually cbg game offset + 4
def decode_position(cbg_file, offset):
    print("cbg offset: " + str(cbg_file[offset:offset + 4]))
    ep_file = cbg_file[offset + 1] & MASK_TURN
    black_to_move = (cbg_file[offset + 1] & MASK_EP_FILE) >> 4
    w_castle_long = cbg_file[offset + 2] & MASK_WHITE_CASTLE_LONG
    w_castle_short = (cbg_file[offset + 2] & MASK_WHITE_CASTLE_SHORT) >> 1
    b_castle_long = (cbg_file[offset + 2] & MASK_BLACK_CASTLE_LONG) >> 2
    b_castle_short = (cbg_file[offset + 2] & MASK_BLACK_CASTLE_SHORT) >> 3
    next_move_no = cbg_file[offset + 3]
    print("next_move_no: " + str(next_move_no))
    # print("odd bits: ")
    # print(cbg_file[offset+4:offset+8])
    # for i in range(0,4):
    #    print(bin(cbg_file[offset+4+i]))
    setup_bitstream = cbg_file[offset + 4:offset + 4 + 24]
    # print([hex(i) for i in setup_bitstream])
    # turn into FEN
    # print("ep file: "+str(ep_file))
    # print("white castles long: " + str(w_castle_long == 1))
    # print("white castles short: " + str(w_castle_short == 1))
    # print("black castles long: " + str(b_castle_long == 1))
    # print("black castles short: " + str(b_castle_short == 1))
    # print("next move no: " + str(next_move_no))
    # print("bitstream: " + str(setup_bitstream))
    setup_bits = ""
    for i in (range(0, len(setup_bitstream))):
        setup_bits += format(setup_bitstream[i], '08b')
        # print(format(setup_bitstream[i], '08b'))
    # print(setup_bits)
    first_byte = format(setup_bitstream[0], '08b')
    snd_byte = format(setup_bitstream[1], '08b')
    last_byte = format(setup_bitstream[len(setup_bitstream) - 1], '08b')
    last_byte1 = format(setup_bitstream[len(setup_bitstream) - 2], '08b')
    # print("byte0: "+str(first_byte))
    # print("byte1: " + str(snd_byte))
    # print("byteN: " + str(last_byte))
    # print("byteN1: " + str(last_byte1))

    position = decode_position_bitstream(setup_bits)
    # print(position)
    # create FEN, we currently support standard chess only (no 960/X-FEN)
    # board is in form [ [a1,...,a8], [b1,...,b8], ... ]
    FEN = ""
    for i in reversed(range(0, 8)):
        square_counter = 0;
        for j in range(0, 8):
            piece = position[j, i]
            if piece == 0:
                square_counter += 1
            else:
                if square_counter > 0:
                    FEN += str(square_counter)
                    square_counter = 0
                if piece == W_KING:
                    FEN += "K"
                if piece == W_QUEEN:
                    FEN += "Q"
                if piece == W_ROOK:
                    FEN += "R"
                if piece == W_BISHOP:
                    FEN += "B"
                if piece == W_KNIGHT:
                    FEN += "N"
                if piece == W_PAWN:
                    FEN += "P"
                if piece == B_KING:
                    FEN += "k"
                if piece == B_QUEEN:
                    FEN += "q"
                if piece == B_ROOK:
                    FEN += "r"
                if piece == B_BISHOP:
                    FEN += "b"
                if piece == B_KNIGHT:
                    FEN += "n"
                if piece == B_PAWN:
                    FEN += "p"
        if square_counter > 0:
            FEN += str(square_counter)
            square_counter = 0
        FEN += "/"
    FEN = FEN[:-1]  # remove last '/'
    if black_to_move:
        FEN += " b"
    else:
        FEN += " w"
    if w_castle_long or w_castle_short or b_castle_long or b_castle_short:
        FEN += " "
        if w_castle_short:
            FEN += "K"
        if w_castle_long:
            FEN += "Q"
        if b_castle_short:
            FEN += "k"
        if b_castle_long:
            FEN += "q"
    else:
        FEN += " -"
    if ep_file > 0:
        FEN += " "
        if ep_file == 1:
            FEN += "a"
        elif ep_file == 2:
            FEN += "b"
        elif ep_file == 3:
            FEN += "c"
        elif ep_file == 4:
            FEN += "d"
        elif ep_file == 5:
            FEN += "e"
        elif ep_file == 6:
            FEN += "f"
        elif ep_file == 7:
            FEN += "g"
        elif ep_file == 8:
            FEN += "h"
        if black_to_move:
            FEN += "3"
        else:
            FEN += "6"
    else:
        FEN += " - "
    FEN += "0 "
    FEN += str(next_move_no)
    # after FEN conversion, we also convert the position
    # representation into the CB one with both the board
    # and piece lists
    cb_pos, piece_list = convert_pos_to_cb(position)
    return FEN, position, cb_pos, piece_list


CB_KING_ENC = {
    0x49: (0, 1),
    0x39: (1, 1),
    0xD8: (1, 0),
    0x5D: (1, 7),
    0xC2: (0, 7),
    0xB1: (7, 7),
    0xB2: (7, 0),
    0x47: (7, 1),
    0x76: (2, 0),  # castles short
    0xB5: (-2, 0)  # castles long
}

CB_QUEEN_1_ENC = {
    0xA5: (0, 2),
    0xB8: (0, 2),
    0xCB: (0, 3),
    0x53: (0, 4),
    0x7F: (0, 5),
    0x6B: (0, 6),
    0x8D: (0, 7),
    0x79: (1, 0),
    0xBE: (2, 0),
    0xEB: (3, 0),
    0x21: (4, 0),
    0x99: (5, 0),
    0xD2: (6, 0),
    0x57: (7, 0),
    0x4D: (1, 1),
    0xB4: (2, 2),
    0xBF: (3, 3),
    0x62: (4, 4),
    0xBD: (5, 5),
    0x24: (6, 6),
    0x96: (7, 7),
    0xA7: (1, 7),
    0x48: (2, 6),
    0x28: (3, 5),
    0x6E: (4, 4),
    0x2F: (5, 3),
    0x5A: (6, 2),
    0x18: (7, 1)
}

CB_QUEEN_2_ENC = {
    0xE5: (0, 1),
    0x94: (0, 2),
    0x50: (0, 3),
    0x11: (0, 4),
    0xEA: (0, 5),
    0x31: (0, 6),
    0x01: (0, 7),
    0x5C: (1, 0),
    0x95: (2, 0),
    0xCA: (3, 0),
    0xD3: (4, 0),
    0x1D: (5, 0),
    0x7E: (6, 0),
    0xEF: (7, 0),
    0x44: (1, 1),
    0x80: (2, 2),
    0xA0: (3, 3),
    0x1F: (4, 4),
    0x83: (5, 5),
    0x00: (6, 6),
    0x4B: (7, 7),
    0x67: (1, 7),
    0x20: (2, 6),
    0x5B: (3, 5),
    0x2A: (4, 4),
    0x92: (5, 3),
    0xB6: (6, 2),
    0x60: (7, 1)
}

CB_QUEEN_3_ENC = {
    0x1A: (0, 1),
    0x42: (0, 2),
    0x0F: (0, 3),
    0x0D: (0, 4),
    0xB0: (0, 5),
    0xD1: (0, 6),
    0x23: (0, 7),
    0xF0: (1, 0),
    0x7A: (2, 0),
    0x54: (3, 0),
    0x4F: (4, 0),
    0xF4: (5, 0),
    0xA8: (6, 0),
    0x72: (7, 0),
    0xE7: (1, 1),
    0x40: (2, 2),
    0x38: (3, 3),
    0x59: (4, 4),
    0x87: (5, 5),
    0xE8: (6, 6),
    0x6C: (7, 7),
    0x86: (1, 7),
    0x04: (2, 6),
    0xF1: (3, 5),
    0x8C: (4, 4),
    0xCE: (5, 3),
    0x6A: (6, 2),
    0xDB: (7, 1)
}

CB_ROOK_1_ENC = {
    0x4E: (0, 1),
    0xF8: (0, 2),
    0x43: (0, 3),
    0xD7: (0, 4),
    0x63: (0, 5),
    0x9C: (0, 6),
    0xE6: (0, 7),
    0x2E: (1, 0),
    0xC6: (2, 0),
    0x26: (3, 0),
    0x88: (4, 0),
    0x30: (5, 0),
    0x61: (6, 0),
    0x6F: (7, 0)
}

CB_ROOK_2_ENC = {
    0x14: (0, 1),
    0xA9: (0, 2),
    0x68: (0, 3),
    0xEE: (0, 4),
    0xFB: (0, 5),
    0x77: (0, 6),
    0xE2: (0, 7),
    0xA6: (1, 0),
    0x05: (2, 0),
    0x8B: (3, 0),
    0xA1: (4, 0),
    0x98: (5, 0),
    0x32: (6, 0),
    0x52: (7, 0)
}

CB_ROOK_3_ENC = {
    0x81: (0, 1),
    0x82: (0, 2),
    0x9A: (0, 3),
    0x1B: (0, 4),
    0x9D: (0, 5),
    0x0A: (0, 6),
    0x2B: (0, 7),
    0x8F: (1, 0),
    0xCD: (2, 0),
    0xED: (3, 0),
    0x10: (4, 0),
    0x74: (5, 0),
    0x69: (6, 0),
    0xD6: (7, 0)
}

CB_BISHOP_1_ENC = {
    0x02: (1, 1),
    0x97: (2, 2),
    0xE1: (3, 3),
    0x41: (4, 4),
    0xC3: (5, 5),
    0x7C: (6, 6),
    0xE4: (7, 7),
    0x06: (1, 7),
    0xB7: (2, 6),
    0x55: (3, 5),
    0xD9: (4, 4),
    0x2C: (5, 3),
    0xAE: (6, 2),
    0x37: (7, 1)
}

CB_BISHOP_2_ENC = {
    0xF6: (1, 1),
    0x3F: (2, 2),
    0x08: (3, 3),
    0x93: (4, 4),
    0x73: (5, 5),
    0x5E: (6, 6),
    0x78: (7, 7),
    0x35: (1, 7),
    0xF2: (2, 6),
    0x6D: (3, 5),
    0x71: (4, 4),
    0xA2: (5, 3),
    0xF3: (6, 2),
    0x16: (7, 1)
}

CB_BISHOP_3_ENC = {
    0x51: (1, 1),
    0xB9: (2, 2),
    0x45: (3, 3),
    0x3B: (4, 4),
    0x56: (5, 5),
    0x91: (6, 6),
    0xFD: (7, 7),
    0xAB: (1, 7),
    0x66: (2, 6),
    0x3E: (3, 5),
    0x46: (4, 4),
    0xB3: (5, 3),
    0xFC: (6, 2),
    0xC8: (7, 1)
}

CB_KNIGHT_1_ENC = {
    0x58: (2, 1),
    0x3D: (1, 2),
    0xFA: (-1, 2),
    0xE9: (-2, 1),
    0xBA: (-2, -1),
    0xD4: (-1, -2),
    0xDD: (1, -2),
    0x4A: (2, -1)
}

CB_KNIGHT_2_ENC = {
    0xC4: (2, 1),
    0x0E: (1, 2),
    0xFE: (-1, 2),
    0x5F: (-2, 1),
    0x75: (-2, -1),
    0x07: (-1, -2),
    0x89: (1, -2),
    0x34: (2, -1)
}

CB_KNIGHT_3_ENC = {
    0x9B: (2, 1),
    0xC0: (1, 2),
    0xE3: (-1, 2),
    0xA3: (-2, 1),
    0xAC: (-2, -1),
    0xC9: (-1, -2),
    0xEC: (1, -2),
    0x27: (2, -1)
}

CB_PAWN_A_ENC = {
    0x2D: (0, 1),
    0xC1: (0, 2),
    0x8E: (1, 1),
    0xF5: (-1, 1)
}

CB_PAWN_B_ENC = {
    0x64: (0, 1),
    0x17: (0, 2),
    0x70: (1, 1),
    0xA4: (-1, 1)
}

CB_PAWN_C_ENC = {
    0x7B: (0, 1),
    0xDA: (0, 2),
    0xE0: (1, 1),
    0x85: (-1, 1)
}

CB_PAWN_D_ENC = {
    0xC5: (0, 1),
    0x0B: (0, 2),
    0x90: (1, 1),
    0xF9: (-1, 1)
}

CB_PAWN_E_ENC = {
    0x84: (0, 1),
    0xFF: (0, 2),
    0x15: (1, 1),
    0x36: (-1, 1)
}

CB_PAWN_F_ENC = {
    0x09: (0, 1),
    0x9E: (0, 2),
    0x7D: (1, 1),
    0xDE: (-1, 1)
}

CB_PAWN_G_ENC = {
    0xBB: (0, 1),
    0xDF: (0, 2),
    0xBC: (1, 1),
    0x3A: (-1, 1)
}

CB_PAWN_H_ENC = {
    0x12: (0, 1),
    0x33: (0, 2),
    0x13: (1, 1),
    0x19: (-1, 1)
}


LOOKUP_2B = [
    (0,0), (0,1), (0,2), (0,3), (0,4), (0,5), (0,6), (0,7),  # a1 ... a8
    (1,0), (1,1), (1,2), (1,3), (1,4), (1,5), (1,6), (1,7),  # b1 ... b8
    (2,0), (2,1), (2,2), (2,3), (2,4), (2,5), (2,6), (2,7),  # c1 ... c8
    (3,0), (3,1), (3,2), (3,3), (3,4), (3,5), (3,6), (3,7),  # d1 ... d8
    (4,0), (4,1), (4,2), (4,3), (4,4), (4,5), (4,6), (4,7),  # e1 ... e8
    (5,0), (5,1), (5,2), (5,3), (5,4), (5,5), (5,6), (5,7),  # f1 ... f8
    (6,0), (6,1), (6,2), (6,3), (6,4), (6,5), (6,6), (6,7),  # g1 ... g8
    (7,0), (7,1), (7,2), (7,3), (7,4), (7,5), (7,6), (7,7)   # h1 ... h8
]


def decrease_piece_nr(piece_list, cb_position, target_piece_type, target_nr):
    for nr in range(target_nr, 7):
        piece_list[target_piece_type][nr] = piece_list[target_piece_type][nr + 1]
    piece_list[target_piece_type][7] = None
    # now update position
    for x in range(0, 8):
        for y in range(0, 8):
            p, t = cb_position[x][y]
            if p == target_piece_type:
                cb_position[x][y] = (p, t - 1)


# piece_list  : w_queens, w_rooks, ...
# cb_position : game position
# piece_type  : W_KING, W_QUEEN, B_KING, B_QUEEN...
# piece_nr    : number, denotes e.g. first queen (0), second queen (1), ...
# cb_enc_arr  : one of e.g. CB_QUEENS_1_ENC ...
# node        : game node of python chess tree
# tkn         : encoding byte
# pawn_flip   : true for black pawns (need to consider direction from black's perspective
#               for pawns, all other pieces have absolute directions
def do_move(piece_list, piece_type, piece_nr, cb_position, cb_enc_arr, node, tkn, pawn_flip=False):
    print("piece list do move")
    print(piece_list[piece_type])
    (i, j) = piece_list[piece_type][piece_nr]
    cb_position[i][j] = (0, None)
    (add_x, add_y) = cb_enc_arr[tkn]
    if pawn_flip:
        add_x = -add_x  # revert direction as pawn moves are always encoded
        add_y = -add_y  # from own perspective
    i1 = (i + add_x) % 8
    j1 = (j + add_y) % 8
    # check what's on target square
    # and manipulate position accordingly
    target_piece_type, target_nr = cb_position[i1][j1]
    print("target piece type: "+str(target_piece_type))
    if target_piece_type != 0 and target_piece_type != W_KING and target_piece_type != B_KING \
            and target_piece_type != W_PAWN and target_piece_type != B_PAWN:
        decrease_piece_nr(piece_list, cb_position, target_piece_type, target_nr)
    cb_position[i1][j1] = (piece_type, piece_nr)
    piece_list[piece_type][piece_nr] = (i1, j1)
    # if we have castles, move the rook, too
    if piece_type == W_KING and tkn == 0x76: # castle short
        print("CASTLES W SHORT!!!!!")
        cb_position[7][0] = (0, None)
        for idx in range(0, len(piece_list[W_ROOK])):
            if piece_list[W_ROOK][idx] == (7,0):
                print("setting rook")
                piece_list[W_ROOK][idx] = (5,0)
                cb_position[5][0] = (W_ROOK, idx)
                break
    if piece_type == B_KING and tkn == 0x76:  # castle short
        print("CASTLES B SHORT!!!!!")
        cb_position[7][7] = (0, None)
        for idx in range(0, len(piece_list[B_ROOK])):
            if piece_list[B_ROOK][idx] == (7, 7):
                piece_list[B_ROOK][idx] = (5, 7)
                cb_position[5][7] = (B_ROOK, idx)
                break
    if piece_type == W_KING and tkn == 0xB5:  # castle long
        print("CASTLES W LONG!!!!!")
        cb_position[0][0] = (0, None)
        for idx in range(0, len(piece_list[W_ROOK])):
            if piece_list[W_ROOK][idx] == (0, 0):
                piece_list[W_ROOK][idx] = (3, 0)
                cb_position[3][0] = (W_ROOK, idx)
                break
    if piece_type == B_KING and tkn == 0xB5:  # castle long
        print("CASTLES B LONG!!!!!")
        cb_position[0][7] = (0, None)
        for idx in range(0, len(piece_list[B_ROOK])):
            if piece_list[B_ROOK][idx] == (0, 7):
                piece_list[B_ROOK][idx] = (3, 7)
                cb_position[3][7] = (B_ROOK, idx)
                break
    m = chess.Move.from_uci(SQN[i][j] + SQN[i1][j1])
    print(SQN[i][j] + SQN[i1][j1])
    node = node.add_variation(m)
    return node


def do_2b_move(piece_list, i, j, i1, j1, cb_position, node, cb_promotion_code):
    piece_type, piece_nr = cb_position[i][j]
    cb_position[i][j] = (0, None)
    # check what's on target square
    # and manipulate position accordingly
    target_piece_type, target_nr = cb_position[i1][j1]
    print("target piece type: "+str(target_piece_type))
    if target_piece_type != 0 and target_piece_type != W_KING and target_piece_type != B_KING \
            and target_piece_type != W_PAWN and target_piece_type != B_PAWN:
        decrease_piece_nr(piece_list, cb_position, target_piece_type, target_nr)
    promotion_str = ""
    promoted_piece_type = 0
    if piece_type != W_PAWN and piece_type != B_PAWN:
        # we just assume that two byte encodings never happen for
        # pawn moves, except it's a promotion (check if this is true?!)
        cb_position[i1][j1] = (piece_type, piece_nr)
        print("piece type: "+str(piece_type))
        print("piece nr: " + str(piece_nr))
        piece_list[piece_type][piece_nr] = (i1, j1)
    else:
        # 2b move should usually never be castles -> nothing to be done
        # 2b moves are used for promotions
        if piece_type == W_PAWN and j1 == 7:
            if cb_promotion_code == 0:
                promoted_piece_type = W_QUEEN
                promotion_str += "q"
            elif cb_promotion_code == 1:
                promoted_piece_type = W_ROOK
                promotion_str += "r"
            elif cb_promotion_code == 2:
                promoted_piece_type = W_BISHOP
                promotion_str += "b"
            elif cb_promotion_code == 3:
                promoted_piece_type = W_KNIGHT
                promotion_str += "n"
            else:
                raise ValueError("unknown promotion piece type")
        if piece_type == B_PAWN and j1 == 0:
            if cb_promotion_code == 0:
                promoted_piece_type = B_QUEEN
                promotion_str += "q"
            elif cb_promotion_code == 1:
                promoted_piece_type = B_ROOK
                promotion_str += "r"
            elif cb_promotion_code == 2:
                promoted_piece_type = B_BISHOP
                promotion_str += "b"
            elif cb_promotion_code == 3:
                promoted_piece_type = B_KNIGHT
                promotion_str += "n"
            else:
                raise ValueError("unknown promotion piece type")
    if promoted_piece_type != 0:
        # find first free piece nr
        for free_idx in range(0,8):
            if piece_list[promoted_piece_type][free_idx] == (0, None):
                break
        piece_list[promoted_piece_type][free_idx] = (i1,j1)
        cb_position[i1][j1] = (promoted_piece_type, free_idx)
    m = chess.Move.from_uci(SQN[i][j] + SQN[i1][j1] + promotion_str)
    print(SQN[i][j] + SQN[i1][j1] + promotion_str)
    node = node.add_variation(m)
    return node





# deobfuscation of 2 byte encoded moves
# actually also used for 1 byte moves, but
# we can just operate on the obfuscated values directly
DEOBFUSCATE_2B = [
    0XA2, 0X95, 0X43, 0XF5, 0XC1, 0X3D, 0X4A, 0X6C,	#   0 -   7
    0X53, 0X83, 0XCC, 0X7C, 0XFF, 0XAE, 0X68, 0XAD,	#   8 -  15
    0XD1, 0X92, 0X8B, 0X8D, 0X35, 0X81, 0X5E, 0X74,	#  16 -  23
    0X26, 0X8E, 0XAB, 0XCA, 0XFD, 0X9A, 0XF3, 0XA0,	#  24 -  31
    0XA5, 0X15, 0XFC, 0XB1, 0X1E, 0XED, 0X30, 0XEA,	#  32 -  39
    0X22, 0XEB, 0XA7, 0XCD, 0X4E, 0X6F, 0X2E, 0X24,	#  40 -  47
    0X32, 0X94, 0X41, 0X8C, 0X6E, 0X58, 0X82, 0X50,	#  48 -  55
    0XBB, 0X02, 0X8A, 0XD8, 0XFA, 0X60, 0XDE, 0X52,	#  56 -  63
    0XBA, 0X46, 0XAC, 0X29, 0X9D, 0XD7, 0XDF, 0X08,	#  64 -  71
    0X21, 0X01, 0X66, 0XA3, 0XF1, 0X19, 0X27, 0XB5,	#  72 -  79
    0X91, 0XD5, 0X42, 0X0E, 0XB4, 0X4C, 0XD9, 0X18,	#  80 -  87
    0X5F, 0XBC, 0X25, 0XA6, 0X96, 0X04, 0X56, 0X6A,	#  88 -  95
    0XAA, 0X33, 0X1C, 0X2B, 0X73, 0XF0, 0XDD, 0XA4,	#  96 - 103
    0X37, 0XD3, 0XC5, 0X10, 0XBF, 0X5A, 0X23, 0X34,	# 104 - 111
    0X75, 0X5B, 0XB8, 0X55, 0XD2, 0X6B, 0X09, 0X3A,	# 112 - 119
    0X57, 0X12, 0XB3, 0X77, 0X48, 0X85, 0X9B, 0X0F,	# 120 - 127
    0X9E, 0XC7, 0XC8, 0XA1, 0X7F, 0X7A, 0XC0, 0XBD,	# 128 - 135
    0X31, 0X6D, 0XF6, 0X3E, 0XC3, 0X11, 0X71, 0XCE,	# 136 - 143
    0X7D, 0XDA, 0XA8, 0X54, 0X90, 0X97, 0X1F, 0X44,	# 144 - 151
    0X40, 0X16, 0XC9, 0XE3, 0X2C, 0XCB, 0X84, 0XEC,	# 152 - 159
    0X9F, 0X3F, 0X5C, 0XE6, 0X76, 0X0B, 0X3C, 0X20,	# 160 - 167
    0XB7, 0X36, 0X00, 0XDC, 0XE7, 0XF9, 0X4F, 0XF7,	# 168 - 175
    0XAF, 0X06, 0X07, 0XE0, 0X1A, 0X0A, 0XA9, 0X4B,	# 176 - 183
    0X0C, 0XD6, 0X63, 0X87, 0X89, 0X1D, 0X13, 0X1B,	# 184 - 191
    0XE4, 0X70, 0X05, 0X47, 0X67, 0X7B, 0X2F, 0XEE,	# 192 - 199
    0XE2, 0XE8, 0X98, 0X0D, 0XEF, 0XCF, 0XC4, 0XF4,	# 200 - 207
    0XFB, 0XB0, 0X17, 0X99, 0X64, 0XF2, 0XD4, 0X2A,	# 208 - 215
    0X03, 0X4D, 0X78, 0XC6, 0XFE, 0X65, 0X86, 0X88,	# 216 - 223
    0X79, 0X45, 0X3B, 0XE5, 0X49, 0X8F, 0X2D, 0XB9,	# 224 - 231
    0XBE, 0X62, 0X93, 0X14, 0XE9, 0XD0, 0X38, 0X9C,	# 232 - 239
    0XB2, 0XC2, 0X59, 0X5D, 0XB6, 0X72, 0X51, 0XF8,	# 240 - 247
    0X28, 0X7E, 0X61, 0X39, 0XE1, 0XDB, 0X69, 0X80,	# 248 - 255
]

SPECIAL_CODES = [
    0x29, # two byte move follows
    0xDC, # start of variation
    0x0C, # end of variation
    0x9F  # just skip and continue
]


def decode(game_bytes, cb_position, piece_list, fen=None):
    position_stack = []
    processed_moves = 0
    game = chess.pgn.Game()
    if fen is not None:
        board = chess.Board(fen)
        game.setup(board)
    node = game
    idx = 0
    while idx < len(game_bytes):
        print("idx: "+str(idx))
        #print(game)
        tkn = (game_bytes[idx] - processed_moves) % 256
        print("tkn: " + str(hex(tkn)))
        if tkn not in SPECIAL_CODES:
            processed_moves += 1
            processed_moves %= 256
        if tkn == 0x9F:
            idx+=1
            continue
            print("white to move")
            print("tkn: "+str(hex(tkn)))
        if tkn == 0xAA:  # null move
            node = node.add_variation(chess.Move.null())
            processed_moves += 1
        if tkn == 0x29: # latch to two byte move
            print("LATCH TO 2B")
            #
            #move_2b = struct.unpack(">H", game_bytes[idx+1:idx+3])
            #print(bin(move_2b[0]))
            #src = move_2b[0] & 0x3F
            #print("latch:")
            #print(bin(game_bytes[idx]))
            #print(bin(game_bytes[idx+1]))
            #print(bin(game_bytes[idx+2]))
            tmp = [None, None]
            print(hex(game_bytes[idx+1]))
            print(hex(game_bytes[idx + 2]))
            tmp[0] = DEOBFUSCATE_2B[game_bytes[idx+1] - processed_moves]
            tmp[1] = DEOBFUSCATE_2B[game_bytes[idx+2] - processed_moves]
            tmp_uint16 = struct.unpack(">H", bytes(tmp))
            if len(tmp_uint16) < 1:
                raise ValueError("Error decoding 2b move: "+str(tmp_uint16))
            move_2b = tmp_uint16[0]
            src = move_2b & 0x3F
            dst = (move_2b >> 6) & 0x3F
            promotion_piece = (move_2b >> 12) & 0x3
            x,y = LOOKUP_2B[src]
            src_san = SQN[x][y]
            x1,y1 = LOOKUP_2B[dst]
            dst_san = SQN[x][y]
            print("promotion: "+str(promotion_piece))

            node = do_2b_move(piece_list, x, y, x1, y1, cb_position, node, promotion_piece)
            processed_moves += 1
            processed_moves %= 256
            idx += 3

            #processed_moves += 1
            #processed_moves %= 256
            continue
            #print("src: "+str(src))
            #print("src_xy: "+str(src_san))
            #print("src_san: "+src_san)
            # a1=0, a2=1, h8=63
            #dst =
            #start
        if node.board().turn == chess.WHITE:
            if tkn in CB_KING_ENC:
                print("w king enc")
                node = do_move(piece_list, W_KING, 0, cb_position, CB_KING_ENC, node, tkn)
            elif tkn in CB_QUEEN_1_ENC:
                print("w queen enc 1")
                node = do_move(piece_list, W_QUEEN, 0, cb_position, CB_QUEEN_1_ENC, node, tkn)
            elif tkn in CB_QUEEN_2_ENC:
                print("w queen enc 2")
                node = do_move(piece_list, W_QUEEN, 1, cb_position, CB_QUEEN_2_ENC, node, tkn)
            elif tkn in CB_QUEEN_3_ENC:
                print("w queen enc 3")
                node = do_move(piece_list, W_QUEEN, 2, cb_position, CB_QUEEN_3_ENC, node, tkn)
            elif tkn in CB_ROOK_1_ENC:
                print("w rook enc")
                node = do_move(piece_list, W_ROOK, 0, cb_position, CB_ROOK_1_ENC, node, tkn)
            elif tkn in CB_ROOK_2_ENC:
                print("w rook enc")
                node = do_move(piece_list, W_ROOK, 1, cb_position, CB_ROOK_2_ENC, node, tkn)
            elif tkn in CB_ROOK_3_ENC:
                print("w rook enc")
                node = do_move(piece_list, W_ROOK, 2, cb_position, CB_ROOK_3_ENC, node, tkn)
            elif tkn in CB_BISHOP_1_ENC:
                print("w bishop enc")
                node = do_move(piece_list, W_BISHOP, 0, cb_position, CB_BISHOP_1_ENC, node, tkn)
            elif tkn in CB_BISHOP_2_ENC:
                print("w bishop enc")
                node = do_move(piece_list, W_BISHOP, 1, cb_position, CB_BISHOP_2_ENC, node, tkn)
            elif tkn in CB_BISHOP_3_ENC:
                print("w bishop enc")
                node = do_move(piece_list, W_BISHOP, 2, cb_position, CB_BISHOP_3_ENC, node, tkn)
            elif tkn in CB_KNIGHT_1_ENC:
                print("w bishop enc")
                node = do_move(piece_list, W_KNIGHT, 0, cb_position, CB_KNIGHT_1_ENC, node, tkn)
            elif tkn in CB_KNIGHT_2_ENC:
                print("w bishop enc")
                node = do_move(piece_list, W_KNIGHT, 1, cb_position, CB_KNIGHT_2_ENC, node, tkn)
            elif tkn in CB_KNIGHT_3_ENC:
                print("w bishop enc")
                node = do_move(piece_list, W_KNIGHT, 2, cb_position, CB_KNIGHT_3_ENC, node, tkn)
            elif tkn in CB_PAWN_A_ENC:
                print("w pawn enc")
                node = do_move(piece_list, W_PAWN, 0, cb_position, CB_PAWN_A_ENC, node, tkn)
            elif tkn in CB_PAWN_B_ENC:
                print("w pawn enc")
                node = do_move(piece_list, W_PAWN, 1, cb_position, CB_PAWN_B_ENC, node, tkn)
            elif tkn in CB_PAWN_C_ENC:
                print("w pawn enc")
                node = do_move(piece_list, W_PAWN, 2, cb_position, CB_PAWN_C_ENC, node, tkn)
            elif tkn in CB_PAWN_D_ENC:
                print("w pawn enc")
                node = do_move(piece_list, W_PAWN, 3, cb_position, CB_PAWN_D_ENC, node, tkn)
            elif tkn in CB_PAWN_E_ENC:
                # print("pawn move e")
                print("w pawn enc")
                node = do_move(piece_list, W_PAWN, 4, cb_position, CB_PAWN_E_ENC, node, tkn)
            elif tkn in CB_PAWN_F_ENC:
                print("w pawn enc")
                node = do_move(piece_list, W_PAWN, 5, cb_position, CB_PAWN_F_ENC, node, tkn)
            elif tkn in CB_PAWN_G_ENC:
                print("w pawn enc")
                node = do_move(piece_list, W_PAWN, 6, cb_position, CB_PAWN_G_ENC, node, tkn)
            elif tkn in CB_PAWN_H_ENC:
                print("w pawn enc")
                node = do_move(piece_list, W_PAWN, 7, cb_position, CB_PAWN_H_ENC, node, tkn)
        else:
            # print("black to move")
            #print("tkn: " + str(hex(tkn)))
            #if tkn == 0xAA:  # null move
            #    node = node.add_variation(chess.Move.null())
            #    processed_moves += 1
            if tkn in CB_KING_ENC:
                node = do_move(piece_list, B_KING, 0, cb_position, CB_KING_ENC, node, tkn)
            elif tkn in CB_QUEEN_1_ENC:
                node = do_move(piece_list, B_QUEEN, 0, cb_position, CB_QUEEN_1_ENC, node, tkn)
            elif tkn in CB_QUEEN_2_ENC:
                node = do_move(piece_list, B_QUEEN, 1, cb_position, CB_QUEEN_2_ENC, node, tkn)
            elif tkn in CB_QUEEN_3_ENC:
                node = do_move(piece_list, B_QUEEN, 2, cb_position, CB_QUEEN_3_ENC, node, tkn)
            elif tkn in CB_ROOK_1_ENC:
                node = do_move(piece_list, B_ROOK, 0, cb_position, CB_ROOK_1_ENC, node, tkn)
            elif tkn in CB_ROOK_2_ENC:
                node = do_move(piece_list, B_ROOK, 1, cb_position, CB_ROOK_2_ENC, node, tkn)
            elif tkn in CB_ROOK_3_ENC:
                node = do_move(piece_list, B_ROOK, 2, cb_position, CB_ROOK_3_ENC, node, tkn)
            elif tkn in CB_BISHOP_1_ENC:
                node = do_move(piece_list, B_BISHOP, 0, cb_position, CB_BISHOP_1_ENC, node, tkn)
            elif tkn in CB_BISHOP_2_ENC:
                node = do_move(piece_list, B_BISHOP, 1, cb_position, CB_BISHOP_2_ENC, node, tkn)
            elif tkn in CB_BISHOP_3_ENC:
                node = do_move(piece_list, B_BISHOP, 2, cb_position, CB_BISHOP_3_ENC, node, tkn)
            elif tkn in CB_KNIGHT_1_ENC:
                node = do_move(piece_list, B_KNIGHT, 0, cb_position, CB_KNIGHT_1_ENC, node, tkn)
            elif tkn in CB_KNIGHT_2_ENC:
                node = do_move(piece_list, B_KNIGHT, 1, cb_position, CB_KNIGHT_2_ENC, node, tkn)
            elif tkn in CB_KNIGHT_3_ENC:
                node = do_move(piece_list, B_KNIGHT, 2, cb_position, CB_KNIGHT_3_ENC, node, tkn)
            elif tkn in CB_PAWN_A_ENC:
                node = do_move(piece_list, B_PAWN, 0, cb_position, CB_PAWN_A_ENC, node, tkn, pawn_flip=True)
            elif tkn in CB_PAWN_B_ENC:
                node = do_move(piece_list, B_PAWN, 1, cb_position, CB_PAWN_B_ENC, node, tkn, pawn_flip=True)
            elif tkn in CB_PAWN_C_ENC:
                node = do_move(piece_list, B_PAWN, 2, cb_position, CB_PAWN_C_ENC, node, tkn, pawn_flip=True)
            elif tkn in CB_PAWN_D_ENC:
                node = do_move(piece_list, B_PAWN, 3, cb_position, CB_PAWN_D_ENC, node, tkn, pawn_flip=True)
            elif tkn in CB_PAWN_E_ENC:
                # print("pawn move e black")
                node = do_move(piece_list, B_PAWN, 4, cb_position, CB_PAWN_E_ENC, node, tkn, pawn_flip=True)
            elif tkn in CB_PAWN_F_ENC:
                node = do_move(piece_list, B_PAWN, 5, cb_position, CB_PAWN_F_ENC, node, tkn, pawn_flip=True)
            elif tkn in CB_PAWN_G_ENC:
                node = do_move(piece_list, B_PAWN, 6, cb_position, CB_PAWN_G_ENC, node, tkn, pawn_flip=True)
            elif tkn in CB_PAWN_H_ENC:
                node = do_move(piece_list, B_PAWN, 7, cb_position, CB_PAWN_H_ENC, node, tkn, pawn_flip=True)
        idx += 1
    return game


"""


Special
-------
29 = multiple byte move to follow
9F = dummy - skip and don't count thi move. Used by earlier CB verions as padding!?
25 = unused
C7 = unused
CC = unused
65 = unused
4C = unused
D5 = unused
1E = unused
CF = unused
03 = unused
8A = unused
AF = unused
F7 = unused
AD = unused
3C = unused
D0 = unused
22 = unused
1C = unused
DC = push position (start of variant)
0C = pop position (end of variant)
"""
