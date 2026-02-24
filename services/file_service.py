import pandas as pd
import io


# ── helpers ───────────────────────────────────────────────────────────────────

def _is_numeric(v):
    """True si la valeur est numérique (helper interne)"""
    try:
        float(str(v))
        return True
    except (ValueError, TypeError):
        return False


def detect_boolean_column(data):
    """
    Détecte si une colonne est à dominante booléenne (>= 80% de valeurs bool valides).
    Tolère les erreurs de saisie minoritaires.
    """
    valid = data.dropna()
    if len(valid) == 0:
        return False
    bool_values = {'true', 'false', '0', '1', 'yes', 'no', 'oui', 'non', 'y', 'n'}
    ratio = sum(str(v).strip().lower() in bool_values for v in valid) / len(valid)
    return ratio >= 0.8


def normalize_boolean(val):
    """Convertit une valeur en True/False. Retourne None si NaN."""
    if pd.isna(val):
        return None
    return str(val).strip().lower() in {'true', '1', 'yes', 'oui', 'y'}


def detect_column_type(data, threshold=0.7):
    """
    Détecte le type dominant : numeric, datetime, ou text.
    threshold : ratio minimum pour déclarer un type.
    """
    total = len(data)
    if total == 0:
        return "text", data

    numeric    = pd.to_numeric(data, errors='coerce')
    num_ratio  = numeric.notna().sum() / total

    dates      = pd.to_datetime(data, errors='coerce', infer_datetime_format=True)
    date_ratio = dates.notna().sum() / total

    if num_ratio >= threshold:
        return "numeric", numeric
    elif date_ratio >= threshold:
        return "datetime", dates
    else:
        return "text", data


def replace_extreme_outliers(series):
    """
    Remplace uniquement les outliers EXTRÊMES :
    - IQR factor x3 (très tolérant)
    - ET Z-score > 4 (seulement les vraiment aberrants)
    Les deux conditions doivent être vraies simultanément.
    Valeur de remplacement : médiane des valeurs normales.
    """
    if series.std() == 0:
        return series

    q1  = series.quantile(0.25)
    q3  = series.quantile(0.75)
    iqr = q3 - q1

    iqr_lower = q1 - 3.0 * iqr
    iqr_upper = q3 + 3.0 * iqr

    mean = series.mean()
    std  = series.std()

    def is_extreme(v):
        if pd.isna(v):
            return False
        iqr_out    = v < iqr_lower or v > iqr_upper
        zscore_out = abs((v - mean) / std) > 4.0
        return iqr_out and zscore_out

    mask        = series.apply(is_extreme)
    normal_vals = series[~mask].dropna()
    fill        = round(normal_vals.median(), 2) if not normal_vals.empty else round(series.median(), 2)

    return series.apply(lambda v: fill if is_extreme(v) else v)


# ── Core ──────────────────────────────────────────────────────────────────────

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


def analyze_dataframe(df):
    """
    Diagnostic complet AVANT nettoyage.
    Retourne les stats globales + détail par colonne.
    Compatible avec DiagnosticPanel dans Clean.jsx.
    """
    total_rows    = len(df)
    total_cols    = len(df.columns)
    total_cells   = total_rows * total_cols
    duplicates    = int(df.duplicated().sum())
    total_missing = 0
    columns_info  = []

    for col in df.columns:
        missing     = int(df[col].isna().sum())
        total_missing += missing
        missing_pct = round(missing / total_rows * 100, 1) if total_rows > 0 else 0

        if detect_boolean_column(df[col]):
            col_type = "boolean"
        else:
            col_type, _ = detect_column_type(df[col])

        col_info = {
            "name":        col,
            "type":        col_type,
            "missing":     missing,
            "missing_pct": missing_pct,
            "unique":      int(df[col].nunique()),
            "outliers":    None,
            "min":         None,
            "max":         None,
            "mean":        None,
        }

        if col_type == "numeric":
            numeric  = pd.to_numeric(df[col], errors='coerce')
            q1       = float(numeric.quantile(0.25))
            q3       = float(numeric.quantile(0.75))
            iqr      = q3 - q1
            std      = numeric.std()
            mean_val = numeric.mean()

            def is_extreme(v):
                if pd.isna(v): return False
                iqr_out    = v < q1 - 3.0 * iqr or v > q3 + 3.0 * iqr
                zscore_out = abs((v - mean_val) / std) > 4.0 if std > 0 else False
                return iqr_out and zscore_out

            col_info["outliers"] = int(numeric.apply(is_extreme).sum())
            col_info["min"]      = round(float(numeric.min()), 2) if not numeric.isna().all() else None
            col_info["max"]      = round(float(numeric.max()), 2) if not numeric.isna().all() else None
            col_info["mean"]     = round(float(mean_val), 2)      if not numeric.isna().all() else None

        columns_info.append(col_info)

    completeness = round((1 - total_missing / total_cells) * 100, 1) if total_cells > 0 else 100

    return {
        "total_rows":    total_rows,
        "total_cols":    total_cols,
        "total_missing": total_missing,
        "duplicates":    duplicates,
        "completeness":  completeness,
        "columns":       columns_info,
    }


def process_dataframe(df):
    """
    Nettoyage complet :
    1. Suppression des doublons
    2. Pour chaque colonne :
       - Détection du type dominant
       - Remplacement des valeurs parasites (mauvais type) par None
       - Remplissage des nulls selon le type
       - Remplacement des outliers extrêmes (numeric uniquement)
    """
    df = df.drop_duplicates().copy()
    total_rows_cleaned = 0

    for col in df.columns:

        # ── BOOLEAN ──────────────────────────────────────────────────────────
        if detect_boolean_column(df[col]):
            bool_values = {'true', 'false', '0', '1', 'yes', 'no', 'oui', 'non', 'y', 'n'}

            # Parasites → None
            cleaned = df[col].apply(
                lambda v: v if (pd.isna(v) or str(v).strip().lower() in bool_values) else None
            )

            # Mode sur valeurs valides = valeur de remplacement
            valid_vals = cleaned.dropna()
            mode_raw   = valid_vals.mode()[0] if not valid_vals.empty else 'false'
            fill_bool  = normalize_boolean(mode_raw)

            total_rows_cleaned += int(cleaned.isna().sum())

            df.loc[:, col] = cleaned.apply(
                lambda v: normalize_boolean(v) if not pd.isna(v) else fill_bool
            )
            continue

        col_type, converted = detect_column_type(df[col])

        # ── NUMERIC ──────────────────────────────────────────────────────────
        if col_type == "numeric":
            # Non-numériques déjà NaN via errors='coerce'
            total_rows_cleaned += int(converted.isna().sum())

            # Médiane IQR pour les nulls
            q1       = converted.quantile(0.25)
            q3       = converted.quantile(0.75)
            iqr      = q3 - q1
            filtered = converted[
                (converted >= q1 - 1.5 * iqr) &
                (converted <= q3 + 1.5 * iqr)
            ]
            fill_null = round(
                filtered.median() if not filtered.empty else converted.median(), 2
            )
            converted = converted.fillna(fill_null)

            # Outliers extrêmes → médiane des valeurs normales
            df.loc[:, col] = replace_extreme_outliers(converted)

        # ── DATETIME ─────────────────────────────────────────────────────────
        elif col_type == "datetime":
            total_rows_cleaned += int(converted.isna().sum())

            valid_dates = converted.dropna()
            if not valid_dates.empty:
                median_date = pd.Timestamp(int(valid_dates.astype('int64').median()))
            else:
                median_date = pd.Timestamp("1900-01-01")

            df.loc[:, col] = converted.fillna(median_date)

        # ── TEXT ─────────────────────────────────────────────────────────────
        else:
            non_null  = df[col].dropna()
            num_count = sum(1 for v in non_null if _is_numeric(v))
            num_ratio = num_count / len(non_null) if len(non_null) > 0 else 0

            # < 20% numériques dans un champ texte → parasites → None
            if num_ratio < 0.2:
                cleaned_col = df[col].apply(
                    lambda v: None if (not pd.isna(v) and _is_numeric(v)) else v
                )
            else:
                cleaned_col = df[col]

            total_rows_cleaned += int(cleaned_col.isna().sum())

            mode_val   = cleaned_col.dropna().mode()
            fill_value = mode_val[0] if not mode_val.empty else "Unknown"
            df.loc[:, col] = cleaned_col.fillna(fill_value)

    return df, int(total_rows_cleaned)


# ── Convert ───────────────────────────────────────────────────────────────────

def convert_file(file, conversion_type):
    extension = file.filename.split('.')[-1].lower()

    if extension == 'csv':
        df = pd.read_csv(file)
    elif extension == 'xlsx':
        df = pd.read_excel(file, engine="openpyxl")
    elif extension == 'json':
        df = pd.read_json(file)
    else:
        raise ValueError("Unsupported input file format")

    output = io.BytesIO()

    if conversion_type in ('csv-to-excel', 'json-to-excel'):
        df.to_excel(output, index=False, engine="openpyxl")
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "converted.xlsx"

    elif conversion_type in ('excel-to-csv', 'json-to-csv'):
        df.to_csv(output, index=False)
        mimetype = "text/csv"
        filename = "converted.csv"

    elif conversion_type in ('excel-to-json', 'csv-to-json'):
        output.write(df.to_json(orient="records", indent=2).encode("utf-8"))
        mimetype = "application/json"
        filename = "converted.json"

    else:
        raise ValueError(f"Unsupported conversion type: {conversion_type}")

    output.seek(0)
    return output, mimetype, filename