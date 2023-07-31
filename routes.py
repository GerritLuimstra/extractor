from flask import request
from helpers import allowed_file, ALLOWED_EXTENSIONS, find_max, partial_match, parse_heuristics_file, \
    extract_ocr_content


def cleaned(app, config):

    # Obtain the file
    if 'file' not in request.files:
        return "NO FILE UPLOADED. ABORTING."

    if 'heuristics' not in request.files:
        return "NO HEURISTICS FILE UPLOADED. ABORTING."

    # Obtain the file and heuristics contents
    file = request.files['file']
    heuristics = request.files['heuristics']

    if file.filename == '':
        return "NO FILE SELECTED. ABORTING."
    if heuristics.filename == '':
        return "NO HEURISTICS SELECTED. ABORTING."

    if not allowed_file(file.filename):
        return "FILE TYPE NOT SUPPORTED. MUST BE ONE OF: " + str(ALLOWED_EXTENSIONS)

    if not heuristics.filename.endswith(".txt"):
        return "HEURISTICS TYPE NOT SUPPORTED. MUST BE A .TXT FILE."

    return extract_ocr_content(file, app, config)


def classify(app, config):

    # Obtain the file
    if 'file' not in request.files:
        return "NO FILE UPLOADED. ABORTING."

    if 'heuristics' not in request.files:
        return "NO HEURISTICS FILE UPLOADED. ABORTING."

    # Obtain the file and heuristics contents
    file = request.files['file']
    heuristics = request.files['heuristics']

    if file.filename == '':
        return "NO FILE SELECTED. ABORTING."
    if heuristics.filename == '':
        return "NO HEURISTICS SELECTED. ABORTING."

    if not allowed_file(file.filename):
        return "FILE TYPE NOT SUPPORTED. MUST BE ONE OF: " + str(ALLOWED_EXTENSIONS)

    if not heuristics.filename.endswith(".txt"):
        return "HEURISTICS TYPE NOT SUPPORTED. MUST BE A .TXT FILE."

    # Obtain the OCR content
    cleaned_content = extract_ocr_content(file, app, config)

    # Extract the heuristics content
    # TODO: It this smart from a memory perspective?
    heuristics = str(heuristics.stream.read(), encoding="utf-8")
    heuristics = parse_heuristics_file(heuristics)

    votes = {k: 0 for k, v in heuristics.items() if len(v) != 0}

    # Perform exact matching first
    for supplier, h in heuristics.items():
        for heuristic in h:
            votes[supplier] += cleaned_content.count(heuristic)

    # Compute the prediction
    prediction = find_max(votes)

    # Did we find a candidate?
    if prediction != "N/A":
        return prediction

    # Perform partial matching if exact matching fails
    for supplier, h in heuristics.items():
        for heuristic in h:
            votes[supplier] += partial_match(cleaned_content, heuristic, config.max_distance) > 0

    # Compute the prediction again
    prediction = find_max(votes)

    # Did we find a candidate?
    if prediction != "N/A":
        return prediction

    return "N/A"
