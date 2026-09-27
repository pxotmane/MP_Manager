"""Tests de l'application Trésorerie : pills Budget/Nature + actions CRUD."""

from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tresorerie.models import Tresorerie
from tresorerie.templatetags import ui_extras


class BadgesFiltresTests(TestCase):
    """Tests unitaires des filtres de template « pills » (Budget / Nature)."""

    def test_budget_badge(self):
        attendus = {
            "RAM EXP": "badge-matte-green",
            "RAM INV": "badge-matte-blue",
            "BUDGET EXP": "badge-matte-green-solid",
            "BUDGET INV": "badge-matte-blue-solid",
            "": "badge-matte-slate",
            None: "badge-matte-slate",
        }
        for valeur, classe in attendus.items():
            with self.subTest(valeur=valeur):
                self.assertEqual(ui_extras.budget_badge(valeur), classe)

    def test_nature_badge(self):
        self.assertEqual(ui_extras.nature_badge("MARCHE"), "badge-matte-blue")
        self.assertEqual(ui_extras.nature_badge("CONVENTION"), "badge-matte-teal")
        self.assertEqual(ui_extras.nature_badge("INCONNUE"), "badge-matte-slate")
        self.assertEqual(ui_extras.nature_badge(None), "badge-matte-slate")

    def test_aucune_icone_sur_les_badges(self):
        """Choix de design : les pills Budget / Nature ne portent aucune icône."""
        self.assertFalse(hasattr(ui_extras, "budget_icon"))
        self.assertFalse(hasattr(ui_extras, "nature_icon"))


class TresorerieVuesTests(TestCase):
    """Tests d'intégration : liste (DataTables), formulaire et suppression."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testeur",
            password="MotDePasseTresSolide123",
        )
        cls.tresorerie = Tresorerie.objects.create(
            op=1,
            ov="260001",
            exercice=2026,
            budget="RAM EXP",
            ligne_budgetaire="980.912.31.21",
            code=6563,
            nature="MARCHE",
            beneficiaires="TEST s.a.r.l",
            montant=Decimal("12520.00"),
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_liste_affiche_les_pills_et_les_icones(self):
        response = self.client.get(reverse("tresorerie_table"))
        self.assertEqual(response.status_code, 200)

        # Pills Budget / Nature : couleur mate, libellé lisible, AUCUNE icône,
        # libellé complet conservé dans l'attribut title
        self.assertContains(response, 'class="badge-matte badge-matte-green"')
        self.assertContains(response, 'title="RAM Exploitation"')
        self.assertContains(response, 'class="badge-matte badge-matte-blue"')
        self.assertContains(response, 'title="Marché"')
        self.assertNotContains(response, "bi-cash-stack")
        self.assertNotContains(response, "bi-file-earmark-text")

        # Actions : icônes + suppression en POST (CSRF) + confirmation JS
        self.assertContains(response, "bi-pencil-square")
        self.assertContains(response, "bi-trash3")
        self.assertContains(response, "js-delete-form")
        self.assertContains(response, "csrfmiddlewaretoken")

        # Thème : Bootstrap Icons + JS externalisé, ancien filtre supprimé
        self.assertContains(response, "bootstrap-icons@1.13.1")
        self.assertContains(response, "JS/tresorerie-table.js")
        self.assertNotContains(response, "filterRow")

    def test_footer_non_fixe_et_structure_html_valide(self):
        response = self.client.get(reverse("tresorerie_table"))
        contenu = response.content.decode()

        # base.html est désormais un document HTML valide
        self.assertTrue(contenu.lstrip().startswith("<!DOCTYPE html>"))
        self.assertIn("d-flex flex-column min-vh-100", contenu)
        self.assertIn('class="app-footer mt-auto', contenu)
        # Plus aucune règle inline de footer fixe
        self.assertNotIn("position: fixed", contenu)

    def test_tableau_dans_un_conteneur_defilant(self):
        """Le tableau large reste DANS la carte grâce à .table-responsive."""
        response = self.client.get(reverse("tresorerie_table"))
        contenu = response.content.decode()

        self.assertIn('<div class="table-card">', contenu)
        self.assertIn('<div class="table-responsive">', contenu)
        # Colonne Actions : classe dédiée (colonne figée via CSS) + nom filtrée
        self.assertIn('class="text-center text-nowrap actions-col"', contenu)
        self.assertIn('class="actions-col" data-filter="off"', contenu)

    def test_colonne_actions_exclue_des_filtres(self):
        response = self.client.get(reverse("tresorerie_table"))
        contenu = response.content.decode()
        ligne_filtres = contenu.split('<tr class="filters">')[1].split("</tr>")[0]

        self.assertEqual(ligne_filtres.count("<th"), 14)
        self.assertEqual(ligne_filtres.count("data-placeholder="), 9)
        self.assertEqual(ligne_filtres.count('data-filter="off"'), 5)

    def test_formulaires_creation_et_modification(self):
        URLs = (
            reverse("tresorerie_add"),
            reverse("tresorerie_edit", args=[self.tresorerie.pk]),
        )
        for url in URLs:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "btn-matte-primary")

    def test_page_de_confirmation_de_suppression(self):
        url = reverse("tresorerie_delete", args=[self.tresorerie.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Confirmer la suppression")
        self.assertContains(response, "btn-matte-danger")

    def test_suppression_effective_en_post(self):
        url = reverse("tresorerie_delete", args=[self.tresorerie.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("tresorerie_table"))
        self.assertFalse(Tresorerie.objects.filter(pk=self.tresorerie.pk).exists())

    def test_creation_puis_redirection(self):
        response = self.client.post(
            reverse("tresorerie_add"),
            {
                "op": 2,
                "ov": "260002",
                "exercice": 2026,
                "budget": "BUDGET INV",
                "ligne_budgetaire": "980.912.41.21",
                "code": 6527,
                "nature": "BON COMMANDE",
                "beneficiaires": "SOLA s.a.r.l",
                "montant": "25360.78",
                "date_rejet": "",
                "num_rejet": "",
                "date_visa": "",
                "date_decaissement": "",
                "marche": "",
                "reference_document": "001/26",
            },
        )
        self.assertRedirects(response, reverse("tresorerie_table"))
        self.assertTrue(Tresorerie.objects.filter(op=2, exercice=2026).exists())



class DataTablesLangueTests(TestCase):
    """Garde-fou : la langue de DataTables doit être française ET embarquée.

    Aucun dictionnaire distant : si le CDN (i18n/fr-FR.json) était
    inaccessible, DataTables retomberait silencieusement en anglais.
    """

    def setUp(self):
        self.chemin_js = (
            Path(settings.BASE_DIR) / "MP_Manager" / "static" / "JS" / "tresorerie-table.js"
        )

    def test_aucune_dependance_a_un_dictionnaire_distant(self):
        contenu = self.chemin_js.read_text(encoding="utf-8")
        self.assertNotIn("cdn.datatables.net/plug-ins", contenu)
        self.assertNotIn("i18n/fr-FR.json", contenu)

    def test_libelles_francais_embarques(self):
        contenu = self.chemin_js.read_text(encoding="utf-8")
        libelles = (
            "Aucune donnée disponible dans le tableau",
            "Aucune entrée correspondante trouvée",
            "Affichage de _START_ à _END_ sur _TOTAL_ entrées",
            "Affichage de 0 à 0 sur 0 entrées",
            "Afficher _MENU_ lignes",
            "Rechercher :",
            "Première",
            "Dernière",
            "Suivante",
            "Précédente",
        )
        for libelle in libelles:
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

