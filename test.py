import pytesseract
from pytesseract import Output
from pdf2image import convert_from_path
import tqdm
import pandas as pd
from helpers import clean_text, find_max, partial_match, get_args_parser, parse_heuristics_file
import argparse
import cv2
import numpy as np
import matplotlib.pyplot as plt

# Point to the tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

files = [
    "./inputs/36.pdf",
    "./inputs/37.pdf",
    "./inputs/38.pdf",
    "./inputs/39.pdf"
]

# Load in the model
from flair.data import Sentence
from flair.models import SequenceTagger
#
import flair, torch
flair.device = torch.device('cuda')
#
# load tagger
tagger = SequenceTagger.load("flair/ner-dutch-large")

for file in files:

    # Convert the PDF to images
    pages = convert_from_path(file, 100)

    texts = []
    for page in pages:
        results = pytesseract.image_to_data(page, lang="nld", output_type=Output.DICT)
        page = np.asarray(page)

        full_text = " ".join(list(filter(None, results["text"])))
        # texts.append(full_text)
        #
        # sentences = [
        #     Sentence(text) for text in texts
        # ]

        # predict NER tags
        sentence = Sentence(full_text)
        tagger.predict(sentence)

        # iterate over entities and print
        entities = []
        for entity in sentence.get_spans('ner'):
            if entity.tag == "PER" and entity.score > 0.75:
                entities.append(entity.text)

        for i in range(0, len(results["text"])):

            # extract the bounding box coordinates of the text region from
            # the current result
            x = results["left"][i]
            y = results["top"][i]
            w = results["width"][i]
            h = results["height"][i]
            # extract the OCR text itself along with the confidence of the
            # text localization
            text = results["text"][i]
            conf = int(results["conf"][i])

            if len(text.strip()) == 0:
                continue

            if conf < 50:
                continue

            # filter out weak confidence text localizations
            if ("@" in text and len(text) > 2) or any([text in entity for entity in entities]):
                # display the confidence and text to our terminal
                print("Confidence: {}".format(conf))
                print("Text: {}".format(text))
                # strip out non-ASCII text so we can draw the text on the image
                # using OpenCV, then draw a bounding box around the text along
                # with the text itself
                text = "".join([c if ord(c) < 128 else "" for c in text]).strip()
                cv2.rectangle(page, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # cv2.putText(page, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                #             0.5, (0, 0, 255), 3)

        # show the output image
        plt.imshow(page)
        plt.show()

    # print("start pred")
    # sentences = [
    #     Sentence(text) for text in texts
    # ]
    #
    # # predict NER tags
    # tagger.predict(sentences)
    #
    # # iterate over entities and print
    # entities = []
    # for i, sentence in enumerate(sentences):
    #     for entity in sentence.get_spans('ner'):
    #         if entity.tag == "PER" and entity.score > 0.8:
    #             entities.append((i, entity.text))
    #
    # print(entities)
        # # import spacy
        # # from spacy.lang.nl.examples import sentences
        # #
        # # nlp = spacy.load("nl_core_news_lg")
        # # doc = nlp(full_text)
        # # print(doc.text)
        # # # print(doc.ents)
        # # print([(ent.text, ent.label_) for ent in doc.ents])
        # # exit(0)
        # # # import nltk
        # # # from nltk import word_tokenize, pos_tag
        # #
        # # from flair.data import Sentence
        # # from flair.models import SequenceTagger
        # #
        # # # import flair, torch
        # # # flair.device = torch.device('cuda')
        # #
        # # # load tagger
        # # tagger = SequenceTagger.load("flair/ner-dutch-large")
        # # #@tagger = SequenceTagger.load("flair/ner-dutch")
        # #
        # # make example sentence
        # sentence = Sentence(full_text)
        # #
        # # predict NER tags
        # tagger.predict(sentence)


        #



