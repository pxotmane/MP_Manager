# Architecture du projet Django
## ERP de Gestion des Marchés Publics

Cette architecture suit les bonnes pratiques Django afin de rendre le projet maintenable, évolutif et facile à tester.

```


MP_Manager/
│
├── config/
│
├── apps/
│   ├── accounts/
│   ├── marches/
│   ├── tresorerie/
│   ├── decomptes/
│   ├── revision_prix/
│   ├── rapprochement/
│   ├── dashboard/
│   ├── documents/
│   ├── rapports/
│   └── core/
│       ├── models.py
│       ├── mixins.py
│       ├── validators.py
│       ├── choices.py
│       └── utils.py
│
├── templates/
│   ├── base.html
│   ├── includes/
│   ├── registration/
│   └── dashboard/
├── static/
├── media/
├── docs/
├── requirements/
└── manage.py

```

---

# Description des applications

## 1. accounts

Accés au dashboard de l'application.

---

## 2. marches

Application principale.

Contient notamment :

- FicheMarché
- Ordres de Service
- Réceptions
- Délais
- Avenants

Toutes les autres applications sont liées à cette application.

---

## 3. nantissements

Gestion de :

- Nantissements
- Mainlevées
- Banques
- Dates
- Montants

Relation :

```
FicheMarché
    ↓
Nantissement
```

---

## 4. penalites

Gestion de :

- Retards
- Calcul automatique
- Pénalités
- Exonérations

---

## 5. Tresorerie

Contient toutes les données de référence :

- Entreprises
- Titulaires
- Banques
- Administrations
- Maîtres d'ouvrage

---

## 6. tableaux_bord

Dashboard général :

- Nombre de marchés
- Marchés en cours
- Marchés terminés
- Pénalités
- Nantissements
- Graphiques

---

## 7. rapports

Toutes les impressions :

- PDF
- Excel
- CSV
- Statistiques

---

## 8. core

Application très importante.

Contient :

- Classes abstraites
- Fonctions utilitaires
- Validators
- Choix (Choices)
- Mixins
- Fonctions communes

Aucune logique métier ne doit être dupliquée dans les autres applications.

---

# Flux général

```
Utilisateur
      │
      ▼
Accounts
      │
      ▼
Marchés
      │
 ┌────┼───────────────┐
 ▼    ▼               ▼
Nantissements   Pénalités   Entreprises
      │
      ▼
Rapports
      │
      ▼
Dashboard
```

---

# Objectifs de cette architecture

- Code propre
- Faible couplage
- Forte cohésion
- Facilité de maintenance
- Réutilisation maximale du code
- Évolutivité
- Tests unitaires simplifiés
- Respect des bonnes pratiques Django

---

# Convention de développement

- Une application = une responsabilité.
- Les modèles ne contiennent que la logique métier.
- Les traitements complexes sont placés dans `services.py`.
- Les fonctions communes sont placées dans `core`.
- Les vues restent les plus légères possible.
- Les formulaires sont centralisés dans `forms.py`.
- Les URLs sont propres et organisées par application.
- Les templates sont regroupés par fonctionnalité.

---

# Vision du projet

Construire un ERP spécialisé dans la gestion des marchés publics marocains, modulaire, évolutif et conforme aux bonnes pratiques Django, permettant la gestion complète des marchés, des entreprises, des nantissements, des pénalités, des tableaux de bord et des rapports.