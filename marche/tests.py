"""Tests de l'application Marché : tableau (design + options) et fiche.

Reprend les vérifications de non-régression déjà faites pour la Trésorerie
(`tresorerie/tests.py`) : structure « carte + conteneur défilant », ligne de
filtres par colonne, colonne Actions isolée, pills sans icône, et langue
française embarquée dans le JS.
"""

from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from marche.models import FicheMarche, Nantissement
from marche.templatetags import marche_extras

# NOTE : les montants sont passés en Decimal et non en chaîne, car
# `FicheMarche.save()` appelle `calculer_ttc()` AVANT que Django ne convertisse
# les champs : une chaîne y arriverait telle quelle (Decimal * str -> TypeError).


class PillsMarcheTests(TestCase):
    """Tests unitaires des filtres de template « pills » du tableau marchés."""

    def test_type_budget_badge(self):
        self.assertEqual(marche_extras.type_budget_badge("INV"), "badge-matte-blue")
        self.assertEqual(marche_extras.type_budget_badge("EXP"), "badge-matte-green")
        # Valeur inconnue / absente => couleur neutre (jamais de classe vide).
        self.assertEqual(marche_extras.type_budget_badge("XXX"), "badge-matte-slate")
        self.assertEqual(marche_extras.type_budget_badge(None), "badge-matte-slate")

    def test_type_marche_toutes_valeurs_mappees(self):
        """Toute valeur du modèle doit être mappée, jamais laissée à « slate »
        (qui se confondrait visuellement avec « non renseigné »)."""
        for valeur in FicheMarche.TypesMarche.values:
            with self.subTest(type_marche=valeur):
                self.assertEqual(
                    marche_extras.type_marche_badge(valeur),
                    marche_extras._TYPE_MARCHE_BADGES[valeur],
                )

    def test_aucune_icone_sur_les_badges(self):
        """Choix de design : les pills ne portent aucune icône."""
        for nom in ("type_budget_icon", "mode_passation_icon", "type_marche_icon"):
            with self.subTest(filtre=nom):
                self.assertFalse(hasattr(marche_extras, nom))

    def test_statut_priorise_le_resilie(self):
        """Un marché résilié ET soldé doit s'afficher « Résilié »."""
        marche = FicheMarche(marche_solde=True, marche_resilie=True)
        self.assertEqual(marche_extras.statut_libelle(marche), "Résilié")
        self.assertEqual(marche_extras.statut_badge(marche), "badge-matte-red")
        self.assertEqual(
            marche_extras.statut_libelle(FicheMarche(marche_solde=True)), "Soldé"
        )
        self.assertEqual(
            marche_extras.statut_badge(FicheMarche(marche_solde=True)),
            "badge-matte-green",
        )
        self.assertEqual(marche_extras.statut_libelle(FicheMarche()), "En cours")
        self.assertEqual(
            marche_extras.statut_badge(FicheMarche()), "badge-matte-amber"
        )

    def test_nantissement_exploite_l_annotation(self):
        self.assertEqual(marche_extras.nantissement_libelle(True), "Nanti")
        self.assertEqual(marche_extras.nantissement_badge(True), "badge-matte-teal")
        self.assertEqual(marche_extras.nantissement_libelle(False), "Non nanti")
        self.assertEqual(
            marche_extras.nantissement_badge(False), "badge-matte-slate"
        )


class TableauMarcheTests(TestCase):
    """Tests d'intégration de la page « liste des marchés »."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testeur", password="MotDePasseTresSolide123"
        )
        cls.marche = FicheMarche.objects.create(
            num_marche="1/2026",
            type_budget="INV",
            imputation_budgetaire="980.912.32.41",
            objet="Construction",
            titulaire="B_build",
            mode_passation="AOO",
            type_marche="MARCHE_ALLOTIS",
            exercice_budgetaire=2026,
            rib="212324343556575812204198",
            dom_bancaire="BP",
            date_notif_appro="2026-02-01",
            delai_execution=24,
            montant_ht=Decimal("2000000.00"),
            avenant=Decimal("40000.00"),
        )
        Nantissement.objects.create(
            marche=cls.marche,
            num_acte="NANT-001",
            date_nant="2026-03-01",
            mtt_nant=Decimal("50000.00"),
            entite_nant="Banque Populaire",
            rib="212324343556575812204198",
            dom_banc="BP",
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_liste_charge_les_marches_avec_le_statut_de_nantissement(self):
        """La vue annote `nantissement_existe` (sinon la pill serait « non nanti »)."""
        response = self.client.get(reverse("tableau_marche"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["marches"]), [self.marche])
        self.assertTrue(response.context["marches"][0].nantissement_existe)
        self.assertContains(response, "Nanti")

    def test_design_identique_a_la_tresorerie(self):
        contenu = self.client.get(reverse("tableau_marche")).content.decode()
        self.assertIn('<div class="table-card">', contenu)
        self.assertIn('<div class="table-responsive">', contenu)
        self.assertIn('id="marcheTable"', contenu)
        self.assertIn('class="table table-striped table-hover"', contenu)
        # Colonne Actions : classe dédiée (figée via CSS) + jamais filtrée.
        self.assertIn('class="text-center text-nowrap actions-col"', contenu)
        self.assertIn('class="actions-col" data-filter="off"', contenu)
        # Ligne de filtres par colonne + script DataTables externalisé.
        self.assertIn('<tr class="filters">', contenu)
        self.assertIn("JS/marche-table.js", contenu)
        self.assertIn("dataTables.bootstrap5.min.css", contenu)

    def test_colonne_actions_exclue_des_filtres(self):
        contenu = self.client.get(reverse("tableau_marche")).content.decode()
        ligne_filtres = contenu.split('<tr class="filters">')[1].split("</tr>")[0]
        # 14 colonnes, dont 2 sans filtre (date de notification et Actions).
        self.assertEqual(ligne_filtres.count("data-placeholder"), 12)
        self.assertEqual(ligne_filtres.count('data-filter="off"'), 2)

    def test_aucune_regression_les_pills_de_la_tresorerie(self):
        """Le template marchés ne doit pas casser les filtres existants."""
        from tresorerie.templatetags import ui_extras

        self.assertEqual(ui_extras.budget_badge("RAM EXP"), "badge-matte-green")
        self.assertEqual(ui_extras.nature_badge("MARCHE"), "badge-matte-blue")

    def test_etat_vide(self):
        # Les nantissements protègent le marché (on_delete=PROTECT) : il faut les
        # supprimer d'abord, ce qui vérifie au passage que la protection est active.
        with self.assertRaises(ProtectedError):
            FicheMarche.objects.all().delete()
        Nantissement.objects.all().delete()
        FicheMarche.objects.all().delete()

        response = self.client.get(reverse("tableau_marche"))
        self.assertEqual(list(response.context["marches"]), [])
        self.assertContains(response, "Aucun marché enregistré")

    def test_montant_nul_affiche_zero_et_non_un_tiret(self):
        """`|default:"-"` ne doit pas masquer un montant réellement nul."""
        self.marche.montant_global_ttc = Decimal("0.00")
        self.marche.save()
        contenu = self.client.get(reverse("tableau_marche")).content.decode()
        # « 0,00 » (format français) présent, et aucune cellule vide à sa place.
        self.assertIn("0,00", contenu)

    def test_acces_refuse_aux_anonymes(self):
        self.client.logout()
        response = self.client.get(reverse("tableau_marche"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


class FicheMarcheTests(TestCase):
    """Tests de la fiche détaillée (bouton « Actions » du tableau)."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testeur", password="MotDePasseTresSolide123"
        )
        cls.marche = FicheMarche.objects.create(
            num_marche="2/2026",
            type_budget="EXP",
            imputation_budgetaire="980.912.50.53",
            objet="Fournitures de bureau",
            titulaire="SOLA s.a.r.l",
            mode_passation="AOS",
            type_marche="MARCHE_CADRE",
            exercice_budgetaire=2026,
            rib="212324343556575812204198",
            dom_bancaire="CIH",
            delai_execution=12,
            montant_ht=Decimal("10000.00"),
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_fiche_affiche_le_marche(self):
        response = self.client.get(reverse("fiche_marche", args=[self.marche.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2/2026")
        self.assertContains(response, "Fournitures de bureau")
        self.assertContains(response, "SOLA s.a.r.l")
        # Lien de retour vers le tableau.
        self.assertContains(response, reverse("tableau_marche"))

    def test_fiche_sans_document_rie_n_affiche_le_message_d_vidage(self):
        response = self.client.get(reverse("fiche_marche", args=[self.marche.pk]))
        self.assertContains(
            response, "Aucun nantissement ni pénalité rattaché à ce marché"
        )

    def test_fiche_inexistante_renvoie_404(self):
        response = self.client.get(reverse("fiche_marche", args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_acces_refuse_aux_anonymes(self):
        self.client.logout()
        response = self.client.get(reverse("fiche_marche", args=[self.marche.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


class DataTablesLangueMarcheTests(TestCase):
    """Garde-fou : la langue de DataTables doit être française ET embarquée.

    Aucun dictionnaire distant : si le CDN (i18n/fr-FR.json) était
    inaccessible, DataTables retomberait silencieusement en anglais.
    """

    def setUp(self):
        self.chemin_js = (
            Path(settings.BASE_DIR) / "MP_Manager" / "static" / "JS" / "marche-table.js"
        )

    def test_aucune_dependance_a_un_dictionnaire_distant(self):
        contenu = self.chemin_js.read_text(encoding="utf-8")
        self.assertNotIn("cdn.datatables.net/plug-ins", contenu)
        self.assertNotIn("i18n/fr-FR.json", contenu)

    def test_libelles_francais_embarques(self):
        contenu = self.chemin_js.read_text(encoding="utf-8")
        for libelle in (
            "Aucune donnée disponible dans le tableau",
            "Aucune entrée correspondante trouvée",
            "Affichage de _START_ à _END_ sur _TOTAL_ entrées",
            "Afficher _MENU_ lignes",
            "Rechercher :",
            "Première",
            "Dernière",
            "Suivante",
            "Précédente",
        ):
            with self.subTest(libelle=libelle):
                self.assertIn(libelle, contenu)

    def test_aucun_libelle_anglais_de_datatables(self):
        contenu = self.chemin_js.read_text(encoding="utf-8")
        for libelle in (
            "Show _MENU_ entries",
            "Search:",
            "Previous",
            "Next",
            "No matching records found",
            "No data available in table",
        ):
            with self.subTest(libelle=libelle):
                self.assertNotIn(libelle, contenu)
