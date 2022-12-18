# cbh2pgn

## About

`cbh2pgn` is a small python script that converts chess databases 
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
Even with `pypy`, a database with 9 million games takes approximately 8 hours to convert.

For comparison (reading and writing from/to SSD):
- with `pypy3` 300 to 400 games per second (after a few seconds, when JIT kicks in)
- with `cpython` 20 to 60 games per second

### Using `pypy`

Install `python3`, `pypy`, `pip`, and `python-chess`

- `sudo apt install pypy3`
- `pypy3 -m ensurepip`
- `pypy -mpip install -U pip wheel`
- `pypy -mpip install python-chess`

Download `cbh2pgn` [here](https://github.com/asdfjkl/cbh2pgn/releases)
and unzip to `myfolder`, then

- `cd myfolder`
- `pypy3 cbh2pgn.py -i your_database.cbh -o output.pgn`

This will create `output.pgn`

### Using `cpython`

Note that this will be too slow for large databases

Install `python3`, `pypy`, `pip`, and `python-chess`

- `sudo apt install python3`
- `sudo apt install python3-pip`
- `pip3 install python-chess`

- Download `cbh2pgn` [here](https://github.com/asdfjkl/cbh2pgn/releases)
and unzip to `myfolder`, then

- `cd myfolder`
- `python3 cbh2pgn.py -i your_database.cbh -o output.pgn`

This will create `output.pgn`

## License

Copyright (c) 2022 Dominik Klein. Licensed under MIT (see file LICENSE)