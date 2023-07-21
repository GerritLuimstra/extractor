from PIL import Image
import os
import glob
import pytesseract
from pdf2image import convert_from_path
import string
import matplotlib.pyplot as plt
import re
import tqdm
import pandas as pd
from helpers import clean_text, find_max

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

INPUTS_DIR = "./inputs/"
DPI = 100  # TODO: how much does this affect the output?

# Read in the meta file
dataset = pd.read_csv("inputs/meta.csv")
print(dataset.head())

print(dataset.columns)

heuristics = {
    "ADHD Noord": [],
    "AtHomeFirst": ["athomefirst"],
    "De Buinerhof": [],
    "Cosis": ["cosis"],
    "CuraXL": [],
    "Dokter": ["schoonmaakorganisatie", "dokter"],  # TODO: dokter = FP?
    "Eigen Pad": [],
    "Leger Des Heils": [],
    "Scilla Andante": [],
    "Thalia": ["thalia"],
    "De Toegang": ["advies om mee te doen", "de toegang", "hulp en ondersteuning"],
    "Treant": [],
    "VNN": [],
    "Wender (Kopland)": [],
    "Zorggroep Vitez": [],
    "De Zorgzaak": [],
    "ZaZaDi": ["zazadi"],  # TODO: moeten deze ook?
    "FMJ Zorg": ["fmj", "fmj zorg"],
    "B-Point": ["bpoint"]
}

correct = 0
for i, row in tqdm.tqdm(dataset.iterrows(), total=len(dataset)):

    # Convert the PDF to images
    pages = convert_from_path(INPUTS_DIR + row["file"], DPI)
    # print("Done converting to images. Found ", len(pages))

    votes = {k: 0 for k in heuristics}

    for page in tqdm.tqdm(pages):

        # Extract the OCR content
        page_ocr_content = pytesseract.image_to_string(page)

        # Clean the output
        cleaned_text = clean_text(page_ocr_content)

        for supplier, h in heuristics.items():
            for heuristic in h:
                if heuristic in cleaned_text:
                    votes[supplier] += 1

    prediction = find_max(votes)
    correct += prediction.lower() == row["supplier"]

print(correct / len(dataset))
