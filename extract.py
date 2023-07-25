import pytesseract
from pdf2image import convert_from_path
import tqdm
import pandas as pd
from helpers import clean_text, find_max, partial_match, get_args_parser, parse_heuristics_file
import argparse

# Parse the arguments from the CLI
parser = argparse.ArgumentParser('OCR Text Extractor', parents=[get_args_parser()])
args = parser.parse_args()

# Point to the tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'D:\tesseract\tesseract'

heuristics = parse_heuristics_file(args.file)

INPUTS_DIR = "./inputs/"
DPI = 100
MAX_DISTANCE = 1

# Read in the meta file
dataset = pd.read_csv("inputs/meta.csv")

correct = 0
for i, row in tqdm.tqdm(dataset.iterrows(), total=len(dataset)):

    # Convert the PDF to images
    pages = convert_from_path(INPUTS_DIR + row["file"], DPI, poppler_path=r"D:\popper\poppler-23.07.0\Library\bin")

    votes = {k: 0 for k, v in heuristics.items() if len(v) != 0}
    cleaned_content = ""
    for page in tqdm.tqdm(pages):

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

    # Perform exact matching first
    for supplier, h in heuristics.items():
        for heuristic in h:
            votes[supplier] += cleaned_content.count(heuristic)

    # Compute the prediction
    prediction = find_max(votes)

    # Did we find a candidate?
    if prediction != "N/A":
        correct += prediction.lower() == row["supplier"]
        continue

    # Perform partial matching if exact matching fails
    for supplier, h in heuristics.items():
        for heuristic in h:
            votes[supplier] += partial_match(cleaned_content, heuristic, MAX_DISTANCE) > 0

    # Compute the prediction again
    prediction = find_max(votes)

    # Did we find a candidate?
    if prediction != "N/A":
        correct += prediction.lower() == row["supplier"]
        continue

    print(row["file"], votes)
    # Perform partial matching if exact matching fails
    for supplier, h in heuristics.items():
        for heuristic in h:
            partial_match(cleaned_content, heuristic, MAX_DISTANCE, verbose=True)

print(correct / len(dataset))
