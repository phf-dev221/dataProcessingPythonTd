import pandas as pd
import io

def detect_boolean_column(data):
    """Détecte si une colonne est booléenne"""
    valid = data.dropna()
    bool_values = {'true', 'false', '0', '1', 'yes', 'no', 'oui', 'non'}
    return all(str(v).strip().lower() in bool_values for v in valid)

def normalize_boolean(val):
    if pd.isna(val):
        return None
    return str(val).strip().lower() in {'true', '1', 'yes', 'oui'}

def detect_column_type(data, average=0.7):
    total = len(data)

    numeric = pd.to_numeric(data, errors='coerce')
    num_ratio = numeric.notna().sum() / total

    dates = pd.to_datetime(data, errors='coerce', infer_datetime_format=True)
    date_ratio = dates.notna().sum() / total

    if num_ratio >= average:
        return "numeric", numeric
    elif date_ratio >= average:
        return "datetime", dates
    else:
        return "text", data


def process_dataframe(df):
    df = df.drop_duplicates().copy()

    total_rows_cleaned = 0

    for col in df.columns:

        # 1. Détection booléenne en priorité
        if detect_boolean_column(df[col]):
            null_count = int(df[col].isna().sum())
            total_rows_cleaned += null_count
            df.loc[:, col] = df[col].apply(normalize_boolean)
            df.loc[df[col].isna(), col] = False  # valeur par défaut booléen
            continue

        col_type, converted = detect_column_type(df[col])

        if col_type == "numeric":
            # Détection des valeurs aberrantes via IQR avant de calculer la moyenne
            q1 = converted.quantile(0.25)
            q3 = converted.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            # Moyenne sans les outliers pour le fillna
            filtered = converted[(converted >= lower) & (converted <= upper)]
            fill_value = round(filtered.mean(), 2) if not filtered.empty else round(converted.mean(), 2)

            null_count = int(converted.isna().sum())
            total_rows_cleaned += null_count
            df.loc[:, col] = converted.fillna(fill_value)

        elif col_type == "datetime":
            null_count = int(converted.isna().sum())
            total_rows_cleaned += null_count
            df.loc[:, col] = converted.fillna(pd.Timestamp("1900-01-01"))

        else:
            null_count = int(df[col].isna().sum())
            total_rows_cleaned += null_count
            df.loc[:, col] = df[col].fillna("Unknown")  # plus lisible que "vide"

    return df, int(total_rows_cleaned)


def load_file(file):
    extension = file.filename.split('.')[-1].lower()

    if extension == 'csv':
        return pd.read_csv(file)
    elif extension == 'xlsx':
        return pd.read_excel(file, engine="openpyxl")
    elif extension == 'json':
        return pd.read_json(file)
    else:
        raise ValueError("Unsupported file format")


def convert_file(file, conversion_type):
    extension = file.filename.split('.')[-1].lower()

    # Chargement selon l'extension source
    if extension == 'csv':
        df = pd.read_csv(file)
    elif extension == 'xlsx':
        df = pd.read_excel(file, engine="openpyxl")
    elif extension == 'json':
        df = pd.read_json(file)
    else:
        raise ValueError("Unsupported input file format")

    output = io.BytesIO()

    # Conversion selon le type demandé
    if conversion_type == 'csv-to-excel' or conversion_type == 'json-to-excel':
        df.to_excel(output, index=False, engine="openpyxl")
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "converted.xlsx"

    elif conversion_type == 'excel-to-csv' or conversion_type == 'json-to-csv':
        df.to_csv(output, index=False)
        mimetype = "text/csv"
        filename = "converted.csv"

    elif conversion_type in ('excel-to-json', 'csv-to-json'):
        json_str = df.to_json(orient="records", indent=2)
        output.write(json_str.encode("utf-8"))
        mimetype = "application/json"
        filename = "converted.json"

    else:
        raise ValueError(f"Unsupported conversion type: {conversion_type}")

    output.seek(0)
    return output, mimetype, filename