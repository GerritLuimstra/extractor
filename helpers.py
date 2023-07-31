import re
import string
import argparse
from Levenshtein import distance
import os
from flask import Flask, flash, request, redirect, url_for
from pdf2image import convert_from_path
from werkzeug.utils import secure_filename
import pytesseract

ALLOWED_EXTENSIONS = ['pdf']


class Config:
    def __init__(self, dpi, max_distance, upload_folder):
        self.dpi = dpi
        self.max_distance = max_distance
        self.upload_folder = upload_folder

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


def parse_heuristics_file(contents):

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


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_ocr_content(file, app, config):

    # Store the file (temporarily)
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Convert the PDF to images
    pages = convert_from_path(filepath, config.dpi)
    # poppler_path=r"C:\Apps\popper\poppler-23.07.0\Library\bin")

    cleaned_content = ""
    for page in pages:

        # Check if the image is in landscape mode
        if page.size[0] > page.size[1]:
            # Check which rotation of 90 degrees produces more content
            # since we cannot easily check which version is correct
            rot_90_content = pytesseract.image_to_string(page.rotate(90), lang="nld")

            rot_90_rev_content = pytesseract.image_to_string(page.rotate(-90), lang="nld")
            content = rot_90_content if len(rot_90_content) > len(rot_90_rev_content) else rot_90_rev_content
        else:
            content = pytesseract.image_to_string(page, lang="nld")

        # Extract the cleaned content
        cleaned_content = cleaned_content + " " + clean_text(content)

    # Remove the file
    os.remove(filepath)

    return cleaned_content


