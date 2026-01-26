from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import pandas as pd
import os
from werkzeug.utils import secure_filename

# Configuration de l'application Flask
app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_ici_123'  # Pour les messages flash

# Configuration des dossiers
UPLOAD_FOLDER = 'uploads'
CLEANED_FOLDER = 'cleaned'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json', 'xml'}  # ✅ 5 formats

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CLEANED_FOLDER'] = CLEANED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite 16MB

# Créer les dossiers s'ils n'existent pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLEANED_FOLDER, exist_ok=True)

# Fonction pour vérifier l'extension du fichier
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Fonction de nettoyage des données
def clean_data(input_file, output_file):
    """
    Nettoie automatiquement les données avec 4 opérations :
    1. Traiter les valeurs manquantes
    2. Traiter les valeurs aberrantes
    3. Supprimer les doublons
    4. Normaliser les données
    """
    
    # ============================================
    # ÉTAPE 0 : LIRE LE FICHIER
    # ============================================
    if input_file.endswith('.csv'):
        df = pd.read_csv(input_file)
    elif input_file.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(input_file)
    elif input_file.endswith('.json'):
        df = pd.read_json(input_file)
    elif input_file.endswith('.xml'):
        df = pd.read_xml(input_file)
    else:
        raise ValueError("Format de fichier non supporté")
    
    # Statistiques AVANT nettoyage
    rows_before = len(df)
    
    
    # ============================================
    # TRAITEMENT 1 : VALEURS MANQUANTES
    # ============================================
    print("📊 Traitement 1 : Valeurs manquantes...")
    
    # Pour chaque colonne
    for col in df.columns:
        if df[col].isnull().sum() > 0:  # S'il y a des valeurs manquantes
            
            # Si c'est une colonne numérique (nombres)
            if df[col].dtype in ['int64', 'float64']:
                # Remplacer par la MOYENNE
                moyenne = df[col].mean()
                df[col].fillna(moyenne, inplace=True)
                print(f"   ✅ {col}: valeurs remplacées par la moyenne ({moyenne:.2f})")
            
            # Si c'est une colonne texte (object)
            else:
                # Remplacer par le MODE (la valeur la plus fréquente)
                if not df[col].mode().empty:
                    mode = df[col].mode()[0]
                    df[col].fillna(mode, inplace=True)
                    print(f"   ✅ {col}: Valeurs remplacées par '{mode}'")
    
    
    # ============================================
    # TRAITEMENT 2 : VALEURS ABERRANTES (IQR)
    # ============================================
    print("\n📊 Traitement 2 : Valeurs aberrantes...")
    
    # Sélectionner uniquement les colonnes numériques
    numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
    
    rows_before_outliers = len(df)
    
    for col in numeric_columns:
        # Calculer les quartiles
        Q1 = df[col].quantile(0.25)  # Premier quartile (25%)
        Q3 = df[col].quantile(0.75)  # Troisième quartile (75%)
        IQR = Q3 - Q1                 # Intervalle interquartile
        
        # Définir les limites
        lower_bound = Q1 - 1.5 * IQR  # Limite inférieure
        upper_bound = Q3 + 1.5 * IQR  # Limite supérieure
        
        # Compter les valeurs aberrantes
        outliers_count = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
        
        if outliers_count > 0:
            # Supprimer les lignes avec valeurs aberrantes
            df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
            print(f"   ✅ {col}: {outliers_count} valeurs aberrantes supprimées")
    
    rows_removed_outliers = rows_before_outliers - len(df)
    print(f"   📉 Total: {rows_removed_outliers} lignes supprimées")
    
    
    # ============================================
    # TRAITEMENT 3 : DOUBLONS
    # ============================================
    print("\n📊 Traitement 3 : Doublons...")
    
    duplicates_before = df.duplicated().sum()
    
    if duplicates_before > 0:
        df = df.drop_duplicates()
        print(f"   ✅ {duplicates_before} doublons supprimés")
    else:
        print(f"   ℹ️  Aucun doublon détecté")
    
    
    # ============================================
    # TRAITEMENT 4 : NORMALISATION (0-1)
    # ============================================
    print("\n📊 Traitement 4 : Normalisation...")
    
    from sklearn.preprocessing import MinMaxScaler
    
    # Sélectionner uniquement les colonnes numériques
    numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
    
    if len(numeric_columns) > 0:
        scaler = MinMaxScaler()  # Normalise entre 0 et 1
        df[numeric_columns] = scaler.fit_transform(df[numeric_columns])
        print(f"   ✅ {len(numeric_columns)} colonnes normalisées (valeurs entre 0 et 1)")
    else:
        print(f"   ℹ️  Aucune colonne numérique à normaliser")
    
    
    # ============================================
    # SAUVEGARDER LE FICHIER NETTOYÉ
    # ============================================
    # ✅ CORRECTION : Gérer TOUS les formats (CSV, Excel, JSON, XML)
    if output_file.endswith('.csv'):
        df.to_csv(output_file, index=False)
    elif output_file.endswith(('.xlsx', '.xls')):
        df.to_excel(output_file, index=False)
    elif output_file.endswith('.json'):
        df.to_json(output_file, orient='records', indent=2)
    elif output_file.endswith('.xml'):
        df.to_xml(output_file, index=False)
    else:
        # Par défaut : sauvegarder en CSV
        df.to_csv(output_file, index=False)
    
    # Statistiques APRÈS nettoyage
    rows_after = len(df)
    rows_removed = rows_before - rows_after
    
    print(f"\n✅ NETTOYAGE TERMINÉ !")
    print(f"   📊 Lignes avant: {rows_before}")
    print(f"   📊 Lignes après: {rows_after}")
    print(f"   📉 Lignes supprimées: {rows_removed}")
    
    return {
        'rows_before': rows_before,
        'rows_after': rows_after,
        'rows_removed': rows_removed
    }


# Route principale
@app.route('/')
def index():
    return render_template('index.html')

# Route "À propos"
@app.route('/about')
def about():
    return render_template('about.html')

# Route pour uploader et nettoyer le fichier
@app.route('/upload', methods=['POST'])
def upload_file():
    # Vérifier si un fichier a été envoyé
    if 'file' not in request.files:
        flash('Aucun fichier sélectionné', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    # Vérifier si le fichier a un nom
    if file.filename == '':
        flash('Aucun fichier sélectionné', 'error')
        return redirect(url_for('index'))
    
    # Vérifier si le fichier est autorisé
    if file and allowed_file(file.filename):
        # Sécuriser le nom du fichier
        filename = secure_filename(file.filename)
        
        # Chemins des fichiers
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Créer le nom du fichier nettoyé
        name, ext = os.path.splitext(filename)
        cleaned_filename = f"{name}_cleaned{ext}"
        output_path = os.path.join(app.config['CLEANED_FOLDER'], cleaned_filename)
        
        # Sauvegarder le fichier uploadé
        file.save(input_path)
        
        try:
            # Nettoyer les données
            stats = clean_data(input_path, output_path)
            
            # Message de succès
            flash(f'✅ Fichier nettoyé avec succès ! {stats["rows_removed"]} lignes supprimées.', 'success')
            
            # Télécharger le fichier nettoyé
            return send_file(output_path, as_attachment=True, download_name=cleaned_filename)
        
        except Exception as e:
            flash(f'❌ Erreur lors du nettoyage : {str(e)}', 'error')
            return redirect(url_for('index'))
    else:
        # ✅ CORRECTION : Message mis à jour
        flash('❌ Type de fichier non autorisé. Utilisez CSV, XLSX, XLS, JSON ou XML.', 'error')
        return redirect(url_for('index'))

# Lancer l'application
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
    