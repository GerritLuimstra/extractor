from flask import Flask
import pytesseract
import helpers
import routes

UPLOAD_FOLDER = './uploads/'


DPI = 100
MAX_DISTANCE = 1

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Point to the tesseract executable
# pytesseract.pytesseract.tesseract_cmd = r'C:\Apps\tesseract\tesseract'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

config = helpers.Config(DPI, MAX_DISTANCE, UPLOAD_FOLDER)


@app.route('/cleaned', methods=['POST'])
def cleaned():
    return routes.cleaned(app, config)


@app.route('/classify', methods=['POST'])
def classify():
    return routes.classify(app, config)


@app.route('/classify_all', methods=['POST'])
def classify_all():
    return routes.classify_all(app, config)