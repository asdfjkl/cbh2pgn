import chess.pgn
from chess.pgn import read_game
from tqdm import tqdm
import os

FILE_IN = "/home/user/MyFiles/workspace/test_databases/millionbase-2.22.pgn"
#FILE_IN = "/media/user/TOSHIBA EXT/mega.pgn"
FILE_OUT = "mb_out.pgn"

# estimate number of games by filesize

FILESIZE_IN = os.path.getsize(FILE_IN)
pbar = tqdm(total=round(FILESIZE_IN))
pgn_in = open(FILE_IN, encoding="latin-1")
pgn_out = open(FILE_OUT, 'w', encoding="utf-8")
exporter = chess.pgn.FileExporter(pgn_out)


def generator():
    while True:
        yield


i = 0
# for _ in tqdm(generator()):
while True:
    game = chess.pgn.read_game(pgn_in)
    if game is None:
        break
    game.accept(exporter)
    i+=1
    if i%1000 == 0:
        currentSize = os.path.getsize(FILE_OUT)
        current = round(currentSize / 1000.)
        percent = round(currentSize/FILESIZE_IN, 2)
        #pbar.update(currentSize-pbar.n)
        pbar.update(pgn_in.tell()-pbar.n)
        #print(str(currentSize)+"/"+str(FILESIZE_IN)+"("+str(percent)+")")

pbar.close()
pgn_in.close()
pgn_out.close()
