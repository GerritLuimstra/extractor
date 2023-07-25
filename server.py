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

# HACK FOR NOW
args = {}
args["file"] = "heuristics.txt"

UPLOAD_FOLDER = './uploads/'
ALLOWED_EXTENSIONS = {'pdf'}

heuristics = parse_heuristics_file(args["file"])

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

        votes = {k: 0 for k, v in heuristics.items() if len(v) != 0}
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

        # Perform exact matching first
        for supplier, h in heuristics.items():
            for heuristic in h:
                votes[supplier] += cleaned_content.count(heuristic)

        # Compute the prediction
        prediction = find_max(votes)

        # Did we find a candidate?
        if prediction != "N/A":
            os.remove(filepath)
            return prediction

        # Perform partial matching if exact matching fails
        for supplier, h in heuristics.items():
            for heuristic in h:
                votes[supplier] += partial_match(cleaned_content, heuristic, MAX_DISTANCE) > 0

        # Compute the prediction again
        prediction = find_max(votes)

        # Did we find a candidate?
        if prediction != "N/A":
            os.remove(filepath)
            return prediction

        os.remove(filepath)
        return "N/A"

    # if request.method == 'POST':
    #     # check if the post request has the file part
    #     if 'file' not in request.files:
    #         flash('No file part')
    #         return redirect(request.url)
    #     file = request.files['file']
    #     # If the user does not select a file, the browser submits an
    #     # empty file without a filename.
    #     if file.filename == '':
    #         flash('No selected file')
    #         return redirect(request.url)
    #     if file and allowed_file(file.filename):
    #         filename = secure_filename(file.filename)
    #         file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    #         return redirect(url_for('download_file', name=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''