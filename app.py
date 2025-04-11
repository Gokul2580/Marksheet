from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
import numpy as np
import cv2
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route('/api/extract-marks', methods=['POST'])
def extract_marks():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400

        file = request.files['image']
        npimg = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

        records = []
        n_boxes = len(data['level'])
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if text in map(str, range(1, 16)):
                q_no = text
                row_marks = []
                for j in range(i+1, i+10):
                    if j < n_boxes:
                        val = data['text'][j].strip()
                        if val:
                            row_marks.append(val)
                part_a = row_marks[0] if len(row_marks) > 0 else ''
                part_b_a = row_marks[1] if len(row_marks) > 1 else ''
                part_b_b = row_marks[2] if len(row_marks) > 2 else ''
                total = row_marks[-1] if len(row_marks) > 1 else ''
                records.append({
                    'Question No': q_no,
                    'Part A Marks': part_a,
                    'Part B Marks (a)': part_b_a,
                    'Part B Marks (b)': part_b_b,
                    'Total': total
                })

        df = pd.DataFrame(records)

        def parse_mark(val):
            try:
                return float(val.replace('½', '.5').replace('¼', '.25').replace('¾', '.75')
                             .replace('1½', '1.5').replace('2½', '2.5').replace('⅓', '0.33')
                             .replace('⅔', '0.66').replace('⅛', '0.125').replace('⅜', '0.375'))
            except:
                return 0

        df['Part A Marks'] = df['Part A Marks'].apply(parse_mark)
        df['Part B Marks (a)'] = df['Part B Marks (a)'].apply(parse_mark)
        df['Part B Marks (b)'] = df['Part B Marks (b)'].apply(parse_mark)
        df['Total'] = df['Total'].apply(parse_mark)

        return jsonify({
            'marks': df.to_dict(orient='records'),
            'summary': {
                'Total Part A': df['Part A Marks'].sum(),
                'Total Part B': df['Part B Marks (a)'].sum() + df['Part B Marks (b)'].sum(),
                'Overall Total': df['Total'].sum()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Only for local testing:
if __name__ == '__main__':
    app.run(debug=True)
