import os
import django
import pandas as pd
from decimal import Decimal

# 1. Configuration de l'environnement Django
# Remplacez 'mon_projet.settings' par le chemin exact vers vos settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mon_projet.settings")
django.setup()

# 2. Import de votre modèle Django
# Remplacez 'votre_app' et 'MonModele' par les vrais noms de votre application et classe
from votre_app.models import MonModele


def nettoyer_montant(valeur):
    """Nettoie et convertit les valeurs monétaires (ex: '122,45' -> Decimal('122.45'))"""
    if pd.isna(valeur) or valeur == "" or valeur is None:
        return None

    if isinstance(valeur, str):
        # Retire les espaces insécables/normaux et remplace la virgule par un point
        valeur = valeur.replace(" ", "").replace("\xa0", "").replace(",", ".")

    try:
        return Decimal(str(valeur))
    except Exception:
        return None


def importer_excel(chemin_fichier):
    print("Lecture du fichier Excel...")
    # Charger le fichier Excel
    df = pd.read_excel(chemin_fichier)

    # Convertir les NaN/cellules vides d'Excel en None pour Django
    df = df.where(pd.notnull(df), None)

    # 1. Traitement de la colonne décimale 'montant'
    if "montant" in df.columns:
        df["montant"] = df["montant"].apply(nettoyer_montant)

    # 2. Conversion sécurisée des dates (au format AAAA-MM-JJ)
    colonnes_dates = ["date_rejet", "date_visa", "date_decaissement"]
    for date_col in colonnes_dates:
        if date_col in df.columns:
            # Convertit en datetime pandas puis extrait la date seule (YYYY-MM-DD)
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.date
            # Remplacement des valeurs invalides/vides par None
            df[date_col] = df[date_col].apply(lambda x: None if pd.isna(x) else x)

    # 3. Préparation des objets pour insertion bulk
    objets_a_creer = []

    for _, row in df.iterrows():
        instance = MonModele(
            op=row.get("op"),
            ov=row.get("ov"),
            exercice=row.get("exercice"),
            budget=row.get("budget"),
            ligne_budgetaire=row.get("ligne_budgetaire"),
            code=row.get("code"),
            nature=row.get("nature"),
            marche=row.get("marche"),
            reference_document=row.get("reference_document"),
            beneficiaires=row.get("beneficiaires"),
            montant=row.get("montant"),
            date_rejet=row.get("date_rejet"),
            num_rejet=row.get("num_rejet"),
            date_visa=row.get("date_visa"),
            date_decaissement=row.get("date_decaissement"),
            # created_at et updated_at sont ignorés car alimentés automatiquement par Django
        )
        objets_a_creer.append(instance)

    # 4. Enregistrement en masse dans SQLite
    print(f"Insertion de {len(objets_a_creer)} lignes dans la base de données...")
    MonModele.objects.bulk_create(objets_a_creer)
    print("Importation terminée avec succès !")


if __name__ == "__main__":
    # Indiquez le nom ou chemin réel de votre fichier Excel
    FICHIER_EXCEL = "donnees.xlsx"
    importer_excel(FICHIER_EXCEL)


# import os
# import django
# import pandas as pd
# from decimal import Decimal

# # 1. Configurer l'environnement Django
# os.environ.setdefault(
#     "DJANGO_SETTINGS_MODULE", "MP_Manager.settings"
# )  # Remplacez par le nom de votre projet
# django.setup()

# # 2. Importer votre modèle Django
# from tresorerie.models import Produit  # Remplacez par votre application et votre modèle


# def nettoyer_et_convertir(valeur):
#     """
#     Convertit la valeur en Float ou Decimal en remplaçant la virgule par un point si c'est une chaîne.
#     """
#     if pd.isna(valeur):
#         return None

#     # Si c'est du texte avec une virgule (ex: "122,45")
#     if isinstance(valeur, str):
#         # On retire les espaces de milliers éventuels et on remplace la virgule
#         valeur = valeur.replace(" ", "").replace(",", ".")

#     return float(valeur)
#     # Ou return Decimal(str(valeur)) si votre modèle utilise un DecimalField


# def importer_excel(chemin_fichier):
#     print("Lecture du fichier Excel...")
#     df = pd.read_excel(chemin_fichier)

#     # Nettoyage des colonnes décimales
#     # Remplacez 'prix' par le nom exact de votre colonne dans Excel
#     df["prix"] = df["prix"].apply(nettoyer_et_convertir)

#     objets_a_creer = []

#     for index, row in df.iterrows():
#         produit = Produit(
#             nom=row["nom_produit"],  # Colonne Excel -> Champ du modèle
#             prix=row["prix"],  # Colonne Excel -> Champ du modèle
#         )
#         objets_a_creer.append(produit)

#     # 3. Insertion en masse dans SQLite (très rapide)
#     Produit.objects.bulk_create(objets_a_creer)
#     print(f"Succès ! {len(objets_a_creer)} lignes ont été importées dans SQLite.")


# if __name__ == "__main__":
#     # Indiquez le chemin vers votre fichier Excel
#     importer_excel("donnees.xlsx")
