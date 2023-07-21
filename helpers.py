import string
import re


def clean_text(input):

    # First convert to tokens
    tokens = input.strip().lower()
    tokens = tokens.translate(str.maketrans('', '', string.punctuation))

    # Remove unnecessary characters
    remove_chars = list(string.punctuation) + ["`", "‘", "“", "’"]
    for char in remove_chars:
        tokens = tokens.replace(char, "")
    tokens = tokens.replace("\n", " ")

    # Remove numbers (TODO: is this too aggresive?)
    tokens = re.sub(r'[0-9]+', "", tokens)

    # Split on space
    tokens = tokens.split(" ")

    # Remove words smaller than 2
    tokens = [w for w in tokens if len(w) > 1]

    return " ".join(tokens)


def find_max(votes):
    max_ = 0
    key_ = "N/A"
    for k, v in votes.items():
        if v > max_:
            max_ = v
            key_ = k
    return key_