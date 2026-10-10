import argparse
import csv
import os
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MP_Manager.settings")

import django

django.setup()

from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction
from marche.models import FicheMarche, Nantissement, Penalite
from tresorerie.models import BudgetExercice, OrdreRecette, Tresorerie


MODELES = {
    "1": {
        "nom": "Tresorerie",
        "modele": Tresorerie,
        "cles": ("op", "exercice"),
        "template": "tresorerie.csv",
    },
    "2": {
        "nom": "BudgetExercice",
        "modele": BudgetExercice,
        "cles": ("exercice",),
        "template": "budget_exercice.csv",
    },
    "3": {
        "nom": "OrdreRecette",
        "modele": OrdreRecette,
        "cles": ("num_ordre", "exercice"),
        "template": "ordre_recette.csv",
    },
    "4": {
        "nom": "FicheMarche",
        "modele": FicheMarche,
        "cles": ("num_marche",),
        "template": "fiche_marche.csv",
    },
    "5": {
        "nom": "Nantissement",
        "modele": Nantissement,
        "cles": ("num_acte",),
        "template": "nantissement.csv",
    },
    "6": {
        "nom": "Penalite",
        "modele": Penalite,
        "cles": ("num_penalite",),
        "template": "penalite.csv",
    },
}

CHAMPS_AUTOMATIQUES = {"id", "created_at", "updated_at"}
FORMAT_DATE = "%Y-%m-%d"


def valeur_vide(valeur):
    return valeur is None or not valeur.strip()


def convertir_valeur(champ, valeur):
    valeur = valeur.strip()
    if valeur == "":
        if champ.null:
            return None
        if champ.get_internal_type() in {"CharField", "TextField"} and champ.blank:
            return ""
        if champ.has_default():
            return champ.get_default()
        raise ValueError("valeur obligatoire manquante")

    type_champ = champ.get_internal_type()
    if type_champ in {"CharField", "TextField", "SlugField", "EmailField"}:
        return valeur
    if type_champ == "BooleanField":
        valeurs_vraies = {"1", "true", "oui", "yes"}
        valeurs_fausses = {"0", "false", "non", "no"}
        normalisee = valeur.casefold()
        if normalisee in valeurs_vraies:
            return True
        if normalisee in valeurs_fausses:
            return False
        raise ValueError("utiliser true/false, oui/non ou 1/0")
    if type_champ in {"DecimalField", "FloatField"}:
        normalisee = valeur.replace("\u00a0", "").replace(" ", "")
        if "," in normalisee and "." in normalisee:
            if normalisee.rfind(",") > normalisee.rfind("."):
                normalisee = normalisee.replace(".", "").replace(",", ".")
            else:
                normalisee = normalisee.replace(",", "")
        else:
            normalisee = normalisee.replace(",", ".")
        try:
            nombre = Decimal(normalisee)
        except InvalidOperation as erreur:
            raise ValueError("nombre invalide") from erreur
        if not nombre.is_finite():
            raise ValueError("nombre non fini invalide")
        return nombre
    if type_champ in {
        "AutoField",
        "BigAutoField",
        "IntegerField",
        "PositiveIntegerField",
        "PositiveSmallIntegerField",
        "SmallIntegerField",
        "BigIntegerField",
    }:
        try:
            return int(valeur)
        except ValueError as erreur:
            raise ValueError("entier invalide") from erreur
    if type_champ == "DateField":
        for format_date in (FORMAT_DATE, "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(valeur, format_date).date()
            except ValueError:
                continue
        raise ValueError("date invalide (formats acceptés : AAAA-MM-JJ ou JJ/MM/AAAA)")
    if type_champ == "DateTimeField":
        try:
            return datetime.fromisoformat(valeur)
        except ValueError as erreur:
            raise ValueError("date et heure invalides (format ISO attendu)") from erreur
    return valeur


def obtenir_champs_importables(modele):
    return {
        champ.name: champ
        for champ in modele._meta.concrete_fields
        if champ.name not in CHAMPS_AUTOMATIQUES
        and not champ.primary_key
        and not getattr(champ, "auto_created", False)
    }


def lire_csv(chemin):
    with chemin.open("r", encoding="utf-8-sig", newline="") as fichier:
        echantillon = fichier.read(4096)
        fichier.seek(0)
        try:
            dialecte = csv.Sniffer().sniff(echantillon, delimiters=",;\t")
        except csv.Error:
            dialecte = csv.excel
        lecteur = csv.DictReader(fichier, dialect=dialecte)
        if not lecteur.fieldnames:
            raise ValueError("le fichier CSV ne contient pas de ligne d'en-tête")
        entetes = [entete.strip() if entete else "" for entete in lecteur.fieldnames]
        if len(entetes) != len(set(entetes)):
            raise ValueError("le fichier contient des noms de colonnes en double")
        lecteur.fieldnames = entetes
        return entetes, list(lecteur)


def preparer_ligne(champs, entetes, ligne):
    valeurs = {}
    erreurs = []
    champs_fk = {
        nom: champ
        for nom, champ in champs.items()
        if champ.is_relation and champ.many_to_one
    }

    for nom, champ in champs.items():
        if nom in champs_fk:
            entete = "num_marche" if nom == "marche" else f"{nom}_id"
            if entete not in entetes:
                if not champ.null and not champ.has_default():
                    erreurs.append((entete, "", "colonne requise absente"))
                continue
            brut = ligne.get(entete, "")
            if valeur_vide(brut):
                if champ.null:
                    valeurs[nom] = None
                elif not champ.has_default():
                    erreurs.append((entete, brut, "référence obligatoire manquante"))
                continue
            try:
                if nom == "marche":
                    valeurs[nom] = FicheMarche.objects.get(num_marche=brut.strip())
                else:
                    valeurs[nom] = champ.related_model.objects.get(pk=brut.strip())
            except (FicheMarche.DoesNotExist, champ.related_model.DoesNotExist, ValueError):
                erreurs.append((entete, brut, "référence introuvable"))
            continue

        if nom not in entetes:
            if not champ.blank and not champ.null and not champ.has_default():
                erreurs.append((nom, "", "colonne requise absente"))
            continue

        brut = ligne.get(nom, "")
        try:
            valeurs[nom] = convertir_valeur(champ, brut)
        except (ValueError, TypeError) as erreur:
            erreurs.append((nom, brut, str(erreur)))

    return valeurs, erreurs


def importer_csv(modele_info, chemin):
    modele = modele_info["modele"]
    cles = modele_info["cles"]
    champs = obtenir_champs_importables(modele)

    entetes, lignes = lire_csv(chemin)
    a_fk_marche = any(champ.name == "marche" for champ in champs.values())
    entetes_speciales = {"num_marche"} if a_fk_marche else set()
    champs_inconnus = set(entetes) - set(champs) - entetes_speciales
    if champs_inconnus:
        raise ValueError(
            "colonnes inconnues pour ce modèle : " + ", ".join(sorted(champs_inconnus))
        )
    entetes_requises = {
        "num_marche" if champ.name == "marche" else nom
        for nom, champ in champs.items()
        if not champ.blank and not champ.null and not champ.has_default()
    }
    entetes_requises.update(cles)
    colonnes_manquantes = entetes_requises - set(entetes)
    if colonnes_manquantes:
        raise ValueError(
            "colonnes obligatoires absentes : "
            + ", ".join(sorted(colonnes_manquantes))
        )

    erreurs = []
    crees = 0
    mis_a_jour = 0
    ignores = 0

    for numero, ligne in enumerate(lignes, start=2):
        if None in ligne:
            ignores += 1
            erreurs.append(
                (
                    numero,
                    "colonnes",
                    repr(ligne[None]),
                    "nombre de valeurs supérieur au nombre de colonnes",
                )
            )
            continue
        ligne = {
            nom: valeur if valeur is not None else ""
            for nom, valeur in ligne.items()
        }
        if not any(not valeur_vide(valeur or "") for valeur in ligne.values()):
            continue

        valeurs, erreurs_ligne = preparer_ligne(champs, entetes, ligne)
        for cle in cles:
            if cle not in valeurs or valeurs[cle] in (None, ""):
                erreurs_ligne.append((cle, ligne.get(cle, ""), "clé de mise à jour manquante"))

        if erreurs_ligne:
            ignores += 1
            erreurs.extend((numero, *erreur) for erreur in erreurs_ligne)
            continue

        filtre = {cle: valeurs[cle] for cle in cles}
        defaults = {nom: valeur for nom, valeur in valeurs.items() if nom not in cles}
        try:
            with transaction.atomic():
                instance = modele.objects.filter(**filtre).first()
                if instance is None:
                    instance = modele(**valeurs)
                    instance.full_clean()
                    instance.save()
                    crees += 1
                else:
                    for nom, valeur in defaults.items():
                        setattr(instance, nom, valeur)
                    instance.full_clean()
                    instance.save()
                    mis_a_jour += 1
        except (ValidationError, ValueError, TypeError) as erreur:
            ignores += 1
            if isinstance(erreur, ValidationError):
                if hasattr(erreur, "message_dict"):
                    erreurs.extend(
                        (
                            numero,
                            champ,
                            ligne.get("num_marche" if champ == "marche" else champ, ""),
                            "; ".join(messages),
                        )
                        for champ, messages in erreur.message_dict.items()
                    )
                else:
                    erreurs.append((numero, "ligne", "", "; ".join(erreur.messages)))
            else:
                erreurs.append((numero, "ligne", "", str(erreur)))
        except DatabaseError as erreur:
            ignores += 1
            erreurs.append((numero, "ligne", "", f"erreur de base de données : {erreur}"))

    print(
        f"\nImport de {modele_info['nom']} terminé : "
        f"{crees} créé(s), {mis_a_jour} mis à jour, {ignores} ignoré(s)."
    )
    if erreurs:
        print("\nDétail des erreurs (ligne CSV, colonne, valeur, problème) :")
        for numero, colonne, valeur, message in erreurs:
            print(f"- Ligne {numero} | {colonne} | {valeur!r} | {message}")
    return crees, mis_a_jour, ignores, erreurs


def choisir_modele(argument):
    if argument:
        if argument in MODELES:
            return MODELES[argument]
        for info in MODELES.values():
            if argument.casefold() == info["nom"].casefold():
                return info
        raise ValueError(f"modèle inconnu : {argument}")

    print("Choisis la table à importer :")
    for numero, info in MODELES.items():
        print(f"  {numero}. {info['nom']}")
    while True:
        choix = input("Numéro du modèle : ").strip()
        if choix in MODELES:
            return MODELES[choix]
        print("Choix invalide. Sélectionne un numéro affiché ci-dessus.")


def main():
    parseur = argparse.ArgumentParser(
        description="Importer ou mettre à jour des lignes depuis un fichier CSV."
    )
    parseur.add_argument(
        "--model",
        help="nom ou numéro du modèle (si absent, le script affiche un menu)",
    )
    parseur.add_argument(
        "--csv",
        dest="csv_path",
        help="chemin du fichier CSV (si absent, le script le demande)",
    )
    args = parseur.parse_args()

    try:
        modele_info = choisir_modele(args.model)
        print(
            "CSV modèle : "
            f"{PROJECT_DIR / 'csv_templates' / modele_info['template']}"
        )
        chemin_saisi = args.csv_path or input("Chemin du fichier CSV : ").strip()
        chemin = Path(chemin_saisi).expanduser()
        if not chemin.is_file():
            raise ValueError(f"fichier introuvable : {chemin}")
        _, _, ignores, _ = importer_csv(modele_info, chemin)
    except (OSError, ValueError, csv.Error) as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        return 1
    return 1 if ignores else 0


if __name__ == "__main__":
    raise SystemExit(main())
