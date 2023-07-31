from flask import request, jsonify
from helpers import allowed_file, ALLOWED_EXTENSIONS, find_max, partial_match, parse_heuristics_file, \
    extract_ocr_content, match_exact, match_partial


def check_if_valid_upload(file_name, allowed_extensions):

    # Obtain the file
    if file_name not in request.files:
        return f"File '{file_name}' is missing from the request.", 422

    # Obtain the file and heuristics contents
    file = request.files[file_name]

    if file.filename == '':
        return f"File '{file_name}' header is present, but does not contain a file.", 422

    if not allowed_file(file.filename, allowed_extensions):
        return f"File '{file_name}' does not have the correct extension. Must be one of {allowed_extensions}", 422

    return file, 200


def cleaned(app, config):

    # Obtain the files
    file, status = check_if_valid_upload("file", ALLOWED_EXTENSIONS)
    if status != 200:
        return file, status
    heuristics, status = check_if_valid_upload("heuristics", ["txt"])
    if status != 200:
        return heuristics, status

    return extract_ocr_content(file, app, config)


def classify(app, config):

    # Obtain the files
    file, status = check_if_valid_upload("file", ALLOWED_EXTENSIONS)
    if status != 200:
        return file, status
    heuristics, status = check_if_valid_upload("heuristics", ["txt"])
    if status != 200:
        return heuristics, status

    # Obtain the OCR content
    cleaned_content = extract_ocr_content(file, app, config)

    # Extract the heuristics content
    heuristics = str(heuristics.stream.read(), encoding="utf-8")
    heuristics = parse_heuristics_file(heuristics)

    # Obtain the exact votes
    votes_exact = match_exact(cleaned_content, heuristics)

    # Compute the prediction
    prediction = find_max(votes_exact)

    # Did we find a candidate?
    if prediction != "N/A":
        return prediction

    # Obtain the partial votes
    # and then combine the votes
    votes_partial = match_partial(cleaned_content, heuristics, config.max_distance)
    votes_combined = {k: v + votes_exact[k] for k, v in votes_partial.items()}

    # Compute the prediction again
    prediction = find_max(votes_combined)

    # Did we find a candidate?
    if prediction != "N/A":
        return prediction

    return "N/A"


def classify_all(app, config):

    # Obtain the files
    file, status = check_if_valid_upload("file", ALLOWED_EXTENSIONS)
    if status != 200:
        return file, status
    heuristics, status = check_if_valid_upload("heuristics", ["txt"])
    if status != 200:
        return heuristics, status

    # Obtain the OCR content
    cleaned_content = extract_ocr_content(file, app, config)

    # Extract the heuristics content
    heuristics = str(heuristics.stream.read(), encoding="utf-8")
    heuristics = parse_heuristics_file(heuristics)

    # Obtain the votes
    votes_exact = match_exact(cleaned_content, heuristics)
    votes_partial = match_partial(cleaned_content, heuristics, config.max_distance)
    votes_combined = {k: v + votes_exact[k] for k, v in votes_partial.items()}

    return jsonify(votes_combined)


def fetch(app, config):

    # Obtain the files
    file, status = check_if_valid_upload("file", ALLOWED_EXTENSIONS)
    if status != 200:
        return file, status
    match_file, status = check_if_valid_upload("match", ["txt"])

    if status != 200:
        return match_file, status

    # Obtain the OCR content
    cleaned_content = extract_ocr_content(file, app, config)

    # Extract the terms to match
    terms_to_match = str(match_file.stream.read(), encoding="utf-8").split(" ")

    # Keep track of the terms that match
    matched_terms = []

    # Perform exact matching
    for term in terms_to_match:
        if term in cleaned_content.split(" "):
            matched_terms.append(term)

    # Perform partial matching
    for term in terms_to_match:
        if partial_match(cleaned_content, term, config.max_distance) > 0:
            matched_terms.append(term)

    # De-duplicate
    matched_terms = list(set(matched_terms))

    return jsonify(matched_terms)
