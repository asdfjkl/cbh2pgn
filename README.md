# cbh2pgn

## About

A small python script that converts chess databases
stored in the `.cbh` file format to `.pgn`. The tool is currently very limited:

- converts only standard games - no `Chess960`
- only the moves (including variations) of a game plus the following meta-info is converted:
  - Event
  - Site
  - Date
  - Round (plus subround if exists)
  - White player name
  - Black player name
  - Result
  - White Elo
  - Black Elo
- in particular, as of now, *no* game annotations are converted

## Installation and Use (on Ubuntu)

As python is quite slow, I recommend using `pypy` instead of `cpython`.
Even with `pypy`, a database with 9 million games takes approximately 8 hours to convert
in single-threaded mode.

For comparison (reading and writing from/to SSD):
- with `pypy` 300 to 400 games per second (after a few seconds, when JIT kicks in)
- with `cpython` 20 to 60 games per second

### Using `pypy`

Install `python`, `pypy`, `pip`, and `python-chess`:

- `sudo apt install pypy3`
- `sudo apt install python3-pip`
- `pypy3 -mpip install -U pip wheel`
- `pypy3 -mpip install python-chess`

Download `cbh2pgn` [here](https://github.com/asdfjkl/cbh2pgn/releases)
and unzip to `myfolder`, then

- `cd myfolder`
- `pypy3 cbh2pgn.py -i your_database.cbh -o output.pgn`

This will create `output.pgn`

### Using `cpython`

Note that this will be too slow for large databases.

Install `python`, `pip`, and `python-chess`:

- `sudo apt install python3`
- `sudo apt install python3-pip`
- `pip3 install python-chess`

Download `cbh2pgn` [here](https://github.com/asdfjkl/cbh2pgn/releases)
and unzip to `myfolder`, then

- `cd myfolder`
- `python3 cbh2pgn.py -i your_database.cbh -o output.pgn`

This will create `output.pgn`

## Parallel Conversion

For large databases (millions of games), use the `-p` flag to enable parallel
conversion using multiple CPU cores:

```
pypy3 cbh2pgn.py -i your_database.cbh -o output.pgn -p
```

This automatically uses all available CPU cores (minus 2, to leave headroom for
the OS). You can also specify an exact number of workers:

```
pypy3 cbh2pgn.py -i your_database.cbh -o output.pgn -p 8
```

### How it works

The `.cbh` index file uses fixed-size 46-byte records with direct offset
pointers into the `.cbg` game data file. Since each game can be decoded
independently, the record range is split across multiple worker processes that
each write to a temporary file. After all workers finish, the temp files are
concatenated in order to produce the final PGN, preserving the original game
ordering.

### Performance

On a multi-core system with `pypy`, parallel conversion scales nearly linearly
with the number of cores. A 9 million game database that takes ~8 hours
single-threaded can finish in under 30 minutes with 20+ cores.

| Mode | Cores | Mega Database (11.7M games) |
|------|-------|-----------------------------|
| Sequential | 1 | ~8-9 hours |
| Parallel (`-p 4`) | 4 | ~2-3 hours |
| Parallel (`-p 16`) | 16 | ~35-45 min |
| Parallel (`-p`) | all | scales accordingly |

Without the `-p` flag, the original single-threaded behavior with `tqdm`
progress bar is preserved.

## License

Copyright (c) 2022 Dominik Klein. Licensed under MIT (see file LICENSE)
