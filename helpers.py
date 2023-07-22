import re
import string
import argparse
from Levenshtein import distance


def get_args_parser():
    parser = argparse.ArgumentParser('OCR Text Extractor', add_help=False)
    parser.add_argument('--file', required=True, help="Path to the heuristics file.")
    return parser


def clean_text(inp):

    # First convert to tokens
    tokens = inp.strip().lower()
    tokens = tokens.translate(str.maketrans('', '', string.punctuation))

    # Remove unnecessary characters
    remove_chars = list(string.punctuation) + ["`", "‘", "“", "’"]
    for char in remove_chars:
        tokens = tokens.replace(char, "")
    tokens = tokens.replace("\n", " ")

    # Remove numbers (TODO: is this too aggressive?)
    tokens = re.sub(r'[0-9]+', "", tokens)

    # Split on space
    tokens = tokens.split(" ")

    # Remove words smaller than 2
    tokens = [w for w in tokens if len(w) > 1]

    return " ".join(tokens)


def find_max(votes):
    votes = [(k, v) for k, v in votes.items()]
    votes = list(sorted(votes, key=lambda x: x[1], reverse=True))
    if votes[0][1] == votes[1][1]:  # tie
        return "N/A"
    return votes[0][0]


def partial_match(full_string, key, max_distance, verbose=False):
    full_string = full_string.replace(" ", "")
    key = key.replace(" ", "")
    N, M = len(full_string), len(key)
    hits = 0
    for i in range(N - M + 1):
        window = full_string[i: i + M]
        if distance(window, key, score_cutoff=max_distance) <= max_distance:
            if verbose:
                print(window)
            hits += 1
    return hits


def parse_heuristics_file(file):

    # Obtain the file contents
    with open(file) as f:
        contents = f.read()

    # Extract the lines
    lines = contents.split("\n")

    # Parse the file contents
    # and extract the heuristics
    heuristics = {}
    last = ""
    for line in lines:
        if "    " in line:
            heuristics[last].append(line.replace("-", "").strip())
        else:
            last = line.strip()
            heuristics[last] = []

    return heuristics


