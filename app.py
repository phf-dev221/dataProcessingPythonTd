from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import traceback

# Configuration de l'application Flask
app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
app.config['SECRET_KEY'] = 'votre_cle_secrete_ici_123'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CLEANED_FOLDER'] = 'cleaned'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['ALLOWED_EXTENSIONS'] = {'csv', 'xlsx', 'xls', 'json', 'xml'}

# Créer les dossiers
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CLEANED_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def convert_numpy_types(obj):
    """
    Convertit récursivement les types numpy en types Python natifs
    pour permettre la sérialisation JSON
    """
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


def read_file(filepath):
    """Lit un fichier et retourne un DataFrame pandas"""
    try:
        ext = filepath.rsplit('.', 1)[1].lower()

        if ext == 'csv':
            # Tenter différents encodages
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
                try:
                    return pd.read_csv(filepath, encoding=encoding)
                except UnicodeDecodeError:
                    continue
            raise ValueError("Impossible de lire le fichier CSV avec les encodages standards")

        elif ext in ['xlsx', 'xls']:
            return pd.read_excel(filepath)

        elif ext == 'json':
            # Tenter différentes orientations JSON
            try:
                return pd.read_json(filepath)
            except ValueError:
                # Si échec, essayer de lire comme liste de dictionnaires
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return pd.DataFrame(data)

        elif ext == 'xml':
            return pd.read_xml(filepath)

        else:
            raise ValueError(f"Format de fichier non supporté: {ext}")

    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture du fichier: {str(e)}")


def save_file(df, filepath):
    """Sauvegarde un DataFrame dans le format approprié"""
    try:
        ext = filepath.rsplit('.', 1)[1].lower()

        if ext == 'csv':
            df.to_csv(filepath, index=False, encoding='utf-8')

        elif ext in ['xlsx', 'xls']:
            df.to_excel(filepath, index=False, engine='openpyxl')

        elif ext == 'json':
            df.to_json(filepath, orient='records', indent=2, force_ascii=False)

        elif ext == 'xml':
            df.to_xml(filepath, index=False)

        else:
            # Par défaut, sauvegarder en CSV
            df.to_csv(filepath, index=False, encoding='utf-8')

    except Exception as e:
        raise ValueError(f"Erreur lors de la sauvegarde du fichier: {str(e)}")


def clean_data(input_file, output_file):
    """
    Nettoie les données avec une approche robuste et efficace

    Opérations:
    1. Suppression des doublons
    2. Gestion des valeurs manquantes (intelligente)
    3. Nettoyage du texte (espaces, casse)
    4. Détection et traitement des valeurs aberrantes (optionnel)
    """

    stats = {
        'rows_before': 0,
        'rows_after': 0,
        'rows_removed': 0,
        'duplicates_removed': 0,
        'missing_values_handled': 0,
        'outliers_removed': 0,
        'columns_cleaned': 0,
        'processing_time': 0,
        'errors': []
    }

    start_time = datetime.now()

    try:
        # ============================================
        # ÉTAPE 1 : LECTURE DU FICHIER
        # ============================================
        print("📖 Lecture du fichier...")
        df = read_file(input_file)
        stats['rows_before'] = len(df)
        print(f"   ✅ {len(df)} lignes, {len(df.columns)} colonnes")

        # ============================================
        # ÉTAPE 2 : SUPPRESSION DES DOUBLONS
        # ============================================
        print("\n🔍 Suppression des doublons...")
        duplicates_before = df.duplicated().sum()

        if duplicates_before > 0:
            df = df.drop_duplicates(keep='first')
            stats['duplicates_removed'] = duplicates_before
            print(f"   ✅ {duplicates_before} doublons supprimés")
        else:
            print(f"   ℹ️  Aucun doublon détecté")

        # ============================================
        # ÉTAPE 3 : SUPPRESSION DES LIGNES VIDES
        # ============================================
        print("\n🧹 Suppression des lignes complètement vides...")
        empty_rows = df.isnull().all(axis=1).sum()

        if empty_rows > 0:
            df = df.dropna(how='all')
            print(f"   ✅ {empty_rows} lignes vides supprimées")

        # ============================================
        # ÉTAPE 4 : GESTION DES VALEURS MANQUANTES
        # ============================================
        print("\n📊 Gestion des valeurs manquantes...")
        missing_before = df.isnull().sum().sum()

        if missing_before > 0:
            for col in df.columns:
                missing_count = df[col].isnull().sum()

                if missing_count > 0:
                    # Calculer le pourcentage de valeurs manquantes
                    missing_pct = (missing_count / len(df)) * 100

                    # Si plus de 70% de valeurs manquantes, supprimer la colonne
                    if missing_pct > 70:
                        df = df.drop(columns=[col])
                        print(f"   🗑️  {col}: colonne supprimée ({missing_pct:.1f}% manquant)")
                        continue

                    # Pour les colonnes numériques
                    if df[col].dtype in ['int64', 'float64']:
                        # Utiliser la médiane (plus robuste que la moyenne)
                        median_val = df[col].median()
                        df[col].fillna(median_val, inplace=True)
                        print(f"   ✅ {col}: {missing_count} valeurs remplacées par la médiane ({median_val:.2f})")
                        stats['missing_values_handled'] += missing_count

                    # Pour les colonnes textuelles
                    elif df[col].dtype == 'object':
                        # Utiliser le mode ou 'Unknown'
                        if not df[col].mode().empty:
                            mode_val = df[col].mode()[0]
                            df[col].fillna(mode_val, inplace=True)
                            print(f"   ✅ {col}: {missing_count} valeurs remplacées par '{mode_val}'")
                        else:
                            df[col].fillna('Unknown', inplace=True)
                            print(f"   ✅ {col}: {missing_count} valeurs remplacées par 'Unknown'")
                        stats['missing_values_handled'] += missing_count
        else:
            print(f"   ℹ️  Aucune valeur manquante détectée")

        # ============================================
        # ÉTAPE 5 : NETTOYAGE DU TEXTE
        # ============================================
        print("\n✂️  Nettoyage du texte...")
        text_columns = df.select_dtypes(include=['object']).columns

        if len(text_columns) > 0:
            for col in text_columns:
                try:
                    # Supprimer les espaces en début et fin
                    df[col] = df[col].astype(str).str.strip()

                    # Remplacer les espaces multiples par un seul
                    df[col] = df[col].str.replace(r'\s+', ' ', regex=True)

                    # Remplacer les chaînes vides par NaN puis gérer
                    df[col] = df[col].replace(['', 'nan', 'None'], np.nan)

                    stats['columns_cleaned'] += 1
                except Exception as e:
                    print(f"   ⚠️  Erreur sur {col}: {str(e)}")
                    stats['errors'].append(f"Nettoyage de {col}: {str(e)}")

            print(f"   ✅ {len(text_columns)} colonnes textuelles nettoyées")

        # ============================================
        # ÉTAPE 6 : DÉTECTION DES VALEURS ABERRANTES (IQR)
        # ============================================
        print("\n🎯 Détection des valeurs aberrantes...")
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns

        rows_before_outliers = len(df)

        if len(numeric_columns) > 0:
            for col in numeric_columns:
                try:
                    # Calculer Q1, Q3 et IQR
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1

                    # Définir les limites
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR

                    # Compter les aberrations
                    outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()

                    if outliers > 0:
                        # Ne supprimer que si moins de 10% de la colonne
                        outlier_pct = (outliers / len(df)) * 100

                        if outlier_pct < 10:
                            df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
                            print(f"   ✅ {col}: {outliers} valeurs aberrantes supprimées")
                        else:
                            # Remplacer par les limites au lieu de supprimer
                            df.loc[df[col] < lower_bound, col] = lower_bound
                            df.loc[df[col] > upper_bound, col] = upper_bound
                            print(f"   ⚠️  {col}: {outliers} valeurs aberrantes plafonnées (trop nombreuses)")

                except Exception as e:
                    print(f"   ⚠️  Erreur sur {col}: {str(e)}")
                    stats['errors'].append(f"Aberrations de {col}: {str(e)}")

            stats['outliers_removed'] = rows_before_outliers - len(df)
            if stats['outliers_removed'] > 0:
                print(f"   📉 Total: {stats['outliers_removed']} lignes supprimées")

        # ============================================
        # ÉTAPE 7 : RÉINITIALISER L'INDEX
        # ============================================
        df.reset_index(drop=True, inplace=True)

        # ============================================
        # ÉTAPE 8 : SAUVEGARDER LE FICHIER
        # ============================================
        print("\n💾 Sauvegarde du fichier nettoyé...")
        save_file(df, output_file)

        # Statistiques finales
        stats['rows_after'] = len(df)
        stats['rows_removed'] = stats['rows_before'] - stats['rows_after']
        stats['processing_time'] = (datetime.now() - start_time).total_seconds()

        print(f"\n✅ NETTOYAGE TERMINÉ !")
        print(f"   📊 Lignes avant: {stats['rows_before']}")
        print(f"   📊 Lignes après: {stats['rows_after']}")
        print(f"   📉 Lignes supprimées: {stats['rows_removed']}")
        print(f"   ⏱️  Temps de traitement: {stats['processing_time']:.2f}s")

        return stats

    except Exception as e:
        print(f"\n❌ ERREUR : {str(e)}")
        traceback.print_exc()
        stats['errors'].append(str(e))
        raise


# ============================================
# ROUTES API
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Vérifier que l'API fonctionne"""
    return jsonify({
        'status': 'healthy',
        'message': 'DataFlow API is running',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload et nettoyage de fichier"""

    # Vérifier si un fichier a été envoyé
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'Aucun fichier fourni'
        }), 400

    file = request.files['file']

    # Vérifier si le fichier a un nom
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'Nom de fichier vide'
        }), 400

    # Vérifier l'extension
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': f'Format non supporté. Utilisez: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'
        }), 400

    try:
        # Sécuriser le nom du fichier
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Créer des noms uniques
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"
        cleaned_filename = f"{name}_cleaned_{timestamp}{ext}"

        # Chemins
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        output_path = os.path.join(app.config['CLEANED_FOLDER'], cleaned_filename)

        # Sauvegarder le fichier uploadé
        file.save(input_path)

        # Nettoyer les données
        stats = clean_data(input_path, output_path)

        # Supprimer le fichier original après traitement
        try:
            os.remove(input_path)
        except:
            pass

        return jsonify({
            'success': True,
            'message': 'Fichier nettoyé avec succès',
            'filename': cleaned_filename,
            'download_url': f'/api/download/{cleaned_filename}',
            'stats': convert_numpy_types(stats)
        }), 200

    except Exception as e:
        # Nettoyer les fichiers en cas d'erreur
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
        except:
            pass

        return jsonify({
            'success': False,
            'error': str(e),
            'details': traceback.format_exc()
        }), 500


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Télécharger un fichier nettoyé"""
    try:
        filepath = os.path.join(app.config['CLEANED_FOLDER'], filename)

        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': 'Fichier introuvable'
            }), 404

        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Obtenir des statistiques sur les fichiers traités"""
    try:
        upload_count = len(os.listdir(app.config['UPLOAD_FOLDER']))
        cleaned_count = len(os.listdir(app.config['CLEANED_FOLDER']))

        return jsonify({
            'success': True,
            'uploads': upload_count,
            'cleaned': cleaned_count,
            'total_processed': cleaned_count
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Route de fallback pour le frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """Renvoie des informations sur l'API"""
    return jsonify({
        'name': 'DataFlow API',
        'version': '2.0',
        'endpoints': {
            'health': '/api/health',
            'upload': '/api/upload (POST)',
            'download': '/api/download/<filename> (GET)',
            'stats': '/api/stats (GET)'
        },
        'supported_formats': list(app.config['ALLOWED_EXTENSIONS']),
        'max_file_size': '16 MB'
    }), 200


# Gestion des erreurs
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'success': False,
        'error': 'Fichier trop volumineux (max 16 MB)'
    }), 413


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'success': False,
        'error': 'Erreur interne du serveur',
        'details': str(error)
    }), 500


# Lancer l'application
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)