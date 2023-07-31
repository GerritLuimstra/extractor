from flask import Flask
import pytesseract
import helpers
import routes
from flasgger import Swagger

UPLOAD_FOLDER = './uploads/'


DPI = 100
MAX_DISTANCE = 1

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
swagger = Swagger(app)

# Point to the tesseract executable
# pytesseract.pytesseract.tesseract_cmd = r'C:\Apps\tesseract\tesseract'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

config = helpers.Config(DPI, MAX_DISTANCE, UPLOAD_FOLDER)


@app.route('/cleaned', methods=['POST'])
def cleaned():
    """
    Endpoint to obtain the cleaned text that is extracted from tesseract.
    Since the output of tesseract can be rather noisy, the following steps are performed:
    1. All the text is lower cased
    2. Punctuation and special characters are removed
    3. Numbers are removed
    4. Words with 1 letter are removed

    ---
    parameters:
    - in: file
      name: file
      type: file
      required: true
      description: The PDF file to extract the text content from.
    responses:
      200:
        description: The words extracted from the PDF, seperated by a space.
    """
    return routes.cleaned(app, config)


@app.route('/classify', methods=['POST'])
def classify():
    """
    Endpoint to perform a classification on a given PDF file.
    In addition to the PDF file, a heuristics file should also be provided.<br>
    The steps to reach a classification are as follows:
    1. The (cleaned) text is extracted from the given PDF.
    2. Exact matching is performed based on the heuristic files given, and each class is given a vote.
    3. If there is a class with a dominant number of votes, this classification is returned. Otherwise, continue.
    4. Partial matching is performed using the Levenshtein distance.
    5. If there is a class with a dominant number of votes, this classification is returned. Otherwise, continue.
    6. No classification could be made. Return N/A

    ---
    parameters:
    - in: file
      name: file
      type: file
      required: true
      description: The PDF file to extract the text content from.
    - in: heuristics
      name: heuristics
      type: file
      required: true
      description: A TXT file in the following format <br><br>
        class1 <br>
        &nbsp;  &nbsp;  - a_term_to_look_for <br>
        &nbsp;  &nbsp;  - a sentence to look for <br>
        class2 <br>
        &nbsp;  &nbsp;  - another_term_to_look_for<br>
        &nbsp;  &nbsp;  - another sentence to look for
      responses:
          200:
            description: The class with the most votes.

    """
    return routes.classify(app, config)


@app.route('/classify_all', methods=['POST'])
def classify_all():
    """
        Endpoint to classify multiple classes.
        This route is exactly the same as the /classify route, except that now exact and partial matching
         are always performed and all classes along with their votes are returned.

        ---
        parameters:
        - in: file
          name: file
          type: file
          required: true
          description: The PDF file to extract the text content from.
        - in: heuristics
          name: heuristics
          type: file
          required: true
          description: A TXT file in the following format <br><br>
            class1 <br>
            &nbsp;  &nbsp;  - a_term_to_look_for <br>
            &nbsp;  &nbsp;  - a sentence to look for <br>
            class2 <br>
            &nbsp;  &nbsp;  - another_term_to_look_for<br>
            &nbsp;  &nbsp;  - another sentence to look for
          responses:
              200:
                description: A json object with the votes for each provided class
        """
    return routes.classify_all(app, config)
