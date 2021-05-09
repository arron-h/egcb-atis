import flask
import urllib3
import re

app = flask.Flask(__name__)

ALPHANUMERICS = {
    "A": "Alpha",
    "B": "Bravo",
    "C": "Charlie",
    "D": "Delta",
    "E": "Echo",
    "F": "Foxtrot",
    "G": "Golf",
    "H": "Hotel",
    "I": "India",
    "J": "Juliet",
    "K": "Kilo",
    "L": "Lima",
    "M": "Mike",
    "N": "November",
    "O": "Oscar",
    "P": "Papa",
    "Q": "Quebec",
    "R": "Romeo",
    "S": "Sierra",
    "T": "Tango",
    "U": "Uniform",
    "V": "Victor",
    "W": "Whisky",
    "X": "X-Ray",
    "Y": "Yankee",
    "Z": "Zulu"
}


def expand_alphanumeric(letter):
    return ALPHANUMERICS[letter]


def expand_LR(lr):
    if lr.upper() == 'L':
        return "left"
    elif lr.upper() == 'R':
        return "right"

    raise RuntimeError("Unhandled runway assignment.")


def talkify_runway(runway_code):
    t = runway_code[0] + " " + runway_code[1]
    if len(runway_code) == 3:
        t += " " + expand_LR(runway_code[2])

    return t


def talkify_circuit(cct):
    if cct.upper() == "LH":
        return "left hand"
    elif cct.upper() == "RH":
        return "right hand"

    raise RuntimeError("Unhandled circuit direction.")


def talkify_pressure(pressure):
    t = ""
    for char in pressure:
        t += char + " "

    if int(pressure) <= 999:
        t += "hectopascals"

    return t


def get_atis():
    http = urllib3.PoolManager()
    r = http.request('GET', 'https://www.egcbatis.co.uk/main/index.php')
    if (r.status != 200):
        return None

    html = str(r.data)
    data = {}

    # Time
    timerx = re.compile("<span class=\"style_green_data_text\">\s?([0-9]{4})\s?<\/span>\s?<span class=\"style_headings\">\s?z")
    m = re.search(timerx, html)
    if m:
        data["time"] = str(m.group(1)[0:2]) + " " + str(m.group(1)[2:4]) + " zulu"

    # Information
    inforx = re.compile("INFO:\s?<\/span>\s?<span class=\"style_green_data_text\">\s?([A-Z]{1})\s?<\/span>")
    m = re.search(inforx, html)
    if m:
        data["information"] = expand_alphanumeric(m.group(1))

    # Runway
    rwyrx = re.compile("RWY:\s?<\/span>\s?<span class=\"style_green_data_text\">\s?([0-9LR]{2,3})\s?<\/span>")
    m = re.search(rwyrx, html)
    if m:
        data["runway"] = talkify_runway(m.group(1))

    # Circuit
    cctrx = re.compile("CCT:\s?<\/span>\s?<span class=\"style_green_data_text\">(RH|LH)<\/span>")
    m = re.search(cctrx, html)
    if m:
        data["circuit"] = talkify_circuit(m.group(1))

    # MCR QNH
    qnhrx = re.compile("M\/CR QNH:\s?<\/span>\s?<span class=\"style_green_data_text\">([0-9]+)<\/span>")
    m = re.search(qnhrx, html)
    if m:
        data["qnh"] = talkify_pressure(m.group(1))

    # Barton QFE
    qferx = re.compile("BARTON QFE:\s?<\/span>\s?<span class=\"style_green_data_text\">([0-9]+)<\/span>")
    m = re.search(qferx, html)
    if m:
        data["qfe"] = talkify_pressure(m.group(1))

    return data


def extract_data(key, data):
    body = ""
    try:
        body = f"{key} {data[key.lower()]}.</br>"
    except KeyError:
        body = f"{key} unknown.</br>"

    return body


@app.route('/', methods=['GET'])
def home():
    return "<h1>EGCB ATIS retriever</h1><p>Use /atis/text to retrieve textual atis</p>"


@app.route('/atis/text', methods=['GET'])
def atis_text():
    try:
        atis_data = get_atis()
    except Exception as e:
        return f"Error: {e}."

    if atis_data is None or len(atis_data) == 0:
        return "No data available."

    body = "Barton Information.</br>"
    body += extract_data("Time", atis_data)
    body += extract_data("Information", atis_data)
    body += extract_data("Runway", atis_data)
    body += extract_data("Circuit", atis_data)
    body += extract_data("QNH", atis_data)
    body += extract_data("QFE", atis_data)

    return body


if __name__ == "__main__":
    app.run(host='0.0.0.0')
