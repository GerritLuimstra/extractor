import os
from flask import Flask, flash, request, redirect, url_for
from pdf2image import convert_from_path
from werkzeug.utils import secure_filename
import pytesseract
from helpers import parse_heuristics_file, get_args_parser, clean_text, find_max, partial_match
import argparse

# # Parse the arguments from the CLI
# parser = argparse.ArgumentParser('OCR Text Extractor', parents=[get_args_parser()])
# args = parser.parse_args()

UPLOAD_FOLDER = './uploads/'
ALLOWED_EXTENSIONS = {'pdf'}

heuristics = [
    parse_heuristics_file("heuristics.txt"),
    parse_heuristics_file("heuristics_type.txt")
]

DPI = 100
MAX_DISTANCE = 1

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Point to the tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Apps\tesseract\tesseract'

@app.route('/', methods=['GET', 'POST'])
def upload_file():

    if request.method == "POST":
        # Obtain the file
        if 'file' not in request.files:
            return "NO FILE UPLOADED. ABORTING."

        # Obtain the file contents
        file = request.files['file']

        if file.filename == '':
            return "NO FILE SELECTED. ABORTING."

        if not allowed_file(file.filename):
            return "FILE TYPE NOT SUPPORTED. MUST BE ONE OF: " + str(ALLOWED_EXTENSIONS)

        # Store the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Convert the PDF to images
        pages = convert_from_path(filepath, DPI,
                                  poppler_path=r"C:\Apps\popper\poppler-23.07.0\Library\bin")

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

        predictions = []
        for heuristic_dict in heuristics:
            votes = {k: 0 for k, v in heuristic_dict.items() if len(v) != 0}

            # Perform exact matching first
            for supplier, h in heuristic_dict.items():
                for heuristic in h:
                    votes[supplier] += cleaned_content.count(heuristic)

            # Compute the prediction
            prediction = find_max(votes)

            # Did we find a candidate?
            if prediction != "N/A":
                predictions.append(prediction)
                continue

            # Perform partial matching if exact matching fails
            for supplier, h in heuristic_dict.items():
                for heuristic in h:
                    votes[supplier] += partial_match(cleaned_content, heuristic, MAX_DISTANCE) > 0

            # Compute the prediction again
            prediction = find_max(votes)

            # Did we find a candidate?
            if prediction != "N/A":
                predictions.append(prediction)
                continue

            predictions.append("N/A")

        return ";".join(predictions)