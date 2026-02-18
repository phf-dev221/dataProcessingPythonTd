
from flask import Flask, request, jsonify
import pandas as pd
from config import Config
from data_cleaner import clean_data

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        fileExtension = file.filename.split('.')[-1]
        print(fileExtension)
        if fileExtension == 'csv':
            df = pd.read_csv(file)
        elif fileExtension == 'xlsx':
            df = pd.read_excel(file)
        elif fileExtension == 'json':
            df = pd.read_json(file)
        elif fileExtension == 'pkl':
            df = pd.read_pickle(file)
        elif fileExtension == 'sql':
            df = pd.read_sql(file)
        elif fileExtension == 'html':
            df = pd.read_html(file)
        else:
            return jsonify({'error': 'File extension not supported'}), 400
        
        missing_values_before = df.isnull().sum().to_dict()

        column_to_correct = request.form.get('column_to_correct')
        
        cleaned_df = clean_data(df, df.isnull().any().any())
        print(cleaned_df)

        cleaned_head = cleaned_df.head().to_dict(orient='records')
        data_summary = cleaned_df.describe().to_dict()

        return jsonify({
            'message': 'File processed successfully',
            'original_missing_values': missing_values_before,
            'cleaned_data_head': cleaned_head,
            'data_summary': data_summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
