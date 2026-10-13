from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from .models import (
    Tresorerie,
    BudgetExercice,
    OrdreRecette,
    SoldeOuvertureExercice,
)
from .forms import (
    BudgetExerciceForm,
    OrdreRecetteForm,
    SoldeOuvertureExerciceForm,
    TresorerieForm,
)

# Create your views here.
# Call the template created in the templates folder to display the table of the Tresorerie model


class TresorerieListView(ListView):
    model = Tresorerie
    template_name = "tr_tableau/tresorerie_table.html"
    context_object_name = "tresorerie_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("add_form", TresorerieForm())
        context.setdefault("open_add_modal", False)
        context.setdefault("modal_mode", "add")
        return context

    def post(self, request, *args, **kwargs):
        edit_id = request.POST.get("edit_id")
        instance = get_object_or_404(Tresorerie, pk=edit_id) if edit_id else None
        form = TresorerieForm(request.POST, instance=instance)
        if form.is_valid():
            tresorerie = form.save()
            action = "modifié" if instance else "ajouté"
            messages.success(
                request,
                f"L'OP {tresorerie.op}/{tresorerie.exercice} a été {action} avec succès.",
            )
            return redirect("tresorerie_table")

        self.object_list = self.get_queryset()
        return self.render_to_response(
            self.get_context_data(
                add_form=form,
                open_add_modal=True,
                modal_mode="edit" if instance else "add",
                edit_instance=instance,
            )
        )


class JournalTresorerieView(TemplateView):
    template_name = "tr_tableau/journal_tresorerie.html"

    def get_selected_exercise(self, raw_value=None):
        value = raw_value if raw_value is not None else self.request.GET.get("exercice")
        try:
            year = int(value) if value else timezone.localdate().year
        except (TypeError, ValueError):
            year = timezone.localdate().year
        return year if 1 <= year <= 9999 else timezone.localdate().year

    def get_selected_month(self, raw_value=None):
        value = raw_value if raw_value is not None else self.request.GET.get("mois")
        try:
            month = int(value) if value else None
        except (TypeError, ValueError):
            return None
        return month if month is not None and 1 <= month <= 12 else None

    def get_exercise_options(self, selected_exercise):
        years = {selected_exercise}
        years.update(
            SoldeOuvertureExercice.objects.values_list("exercice", flat=True)
        )
        years.update(Tresorerie.objects.values_list("exercice", flat=True))
        years.update(OrdreRecette.objects.values_list("exercice", flat=True))
        years.update(
            year
            for year in Tresorerie.objects.values_list(
                "date_decaissement__year", flat=True
            ).distinct()
            if year
        )
        years.update(
            year
            for year in OrdreRecette.objects.values_list(
                "date_encaissement__year", flat=True
            ).distinct()
            if year
        )
        return sorted((year for year in years if year), reverse=True)

    def get_journal_entries(self, exercice):
        mouvements = []
        for recette in OrdreRecette.objects.filter(
            date_encaissement__year=exercice
        ):
            mouvements.append(
                {
                    "date": recette.date_encaissement,
                    "type_order": 0,
                    "number": recette.num_ordre,
                    "or_number": recette.num_ordre,
                    "op_number": None,
                    "reference": recette.num_decision,
                    "debit": None,
                    "credit": recette.montant,
                }
            )

        for paiement in Tresorerie.objects.filter(
            date_decaissement__year=exercice
        ):
            mouvements.append(
                {
                    "date": paiement.date_decaissement,
                    "type_order": 1,
                    "number": paiement.op,
                    "or_number": None,
                    "op_number": paiement.op,
                    "reference": paiement.ov or "",
                    "debit": paiement.montant,
                    "credit": None,
                }
            )

        mouvements.sort(
            key=lambda mouvement: (
                mouvement["date"],
                mouvement["type_order"],
                mouvement["number"],
            )
        )

        cumul_debit = Decimal("0.00")
        cumul_credit = Decimal("0.00")
        opening_balance = SoldeOuvertureExercice.objects.filter(
            exercice=exercice
        ).first()
        solde = opening_balance.montant if opening_balance else None
        for mouvement in mouvements:
            debit = mouvement["debit"]
            credit = mouvement["credit"]
            if debit is not None:
                cumul_debit += debit
            if credit is not None:
                cumul_credit += credit
            if solde is not None:
                solde += (credit or Decimal("0.00")) - (debit or Decimal("0.00"))
            mouvement["cumul_debit"] = cumul_debit
            mouvement["cumul_credit"] = cumul_credit
            mouvement["solde"] = solde

        return mouvements

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_exercise = kwargs.get(
            "selected_exercise", self.get_selected_exercise()
        )
        selected_month = kwargs.get(
            "selected_month", self.get_selected_month()
        )
        opening_balance = SoldeOuvertureExercice.objects.filter(
            exercice=selected_exercise
        ).first()
        all_journal_entries = self.get_journal_entries(selected_exercise)
        journal_entries = (
            [
                entry
                for entry in all_journal_entries
                if entry["date"].month == selected_month
            ]
            if selected_month is not None
            else all_journal_entries
        )
        total_debits = sum(
            (entry["debit"] or Decimal("0.00") for entry in journal_entries),
            Decimal("0.00"),
        )
        total_credits = sum(
            (entry["credit"] or Decimal("0.00") for entry in journal_entries),
            Decimal("0.00"),
        )
        entries_through_period = (
            [
                entry
                for entry in all_journal_entries
                if entry["date"].month <= selected_month
            ]
            if selected_month is not None
            else all_journal_entries
        )
        cumulative_debits = sum(
            (
                entry["debit"] or Decimal("0.00")
                for entry in entries_through_period
            ),
            Decimal("0.00"),
        )
        cumulative_credits = sum(
            (
                entry["credit"] or Decimal("0.00")
                for entry in entries_through_period
            ),
            Decimal("0.00"),
        )
        closing_balance = None
        if opening_balance:
            closing_balance = (
                entries_through_period[-1]["solde"]
                if entries_through_period
                else opening_balance.montant
            )
        month_names = (
            "Janvier",
            "Février",
            "Mars",
            "Avril",
            "Mai",
            "Juin",
            "Juillet",
            "Août",
            "Septembre",
            "Octobre",
            "Novembre",
            "Décembre",
        )
        context.update(
            {
                "selected_exercise": selected_exercise,
                "selected_month": selected_month,
                "selected_month_name": (
                    month_names[selected_month - 1] if selected_month else None
                ),
                "months": list(enumerate(month_names, start=1)),
                "exercise_options": self.get_exercise_options(selected_exercise),
                "opening_balance": opening_balance,
                "opening_balance_form": kwargs.get(
                    "opening_balance_form",
                    SoldeOuvertureExerciceForm(
                        instance=opening_balance,
                        initial={"exercice": selected_exercise},
                    ),
                ),
                "open_balance_modal": kwargs.get("open_balance_modal", False),
                "journal_entries": journal_entries,
                "total_debits": total_debits,
                "total_credits": total_credits,
                "cumulative_debits": cumulative_debits,
                "cumulative_credits": cumulative_credits,
                "closing_balance": closing_balance,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        balance_id = request.POST.get("opening_balance_id")
        instance = (
            get_object_or_404(SoldeOuvertureExercice, pk=balance_id)
            if balance_id
            else None
        )
        form = SoldeOuvertureExerciceForm(request.POST, instance=instance)
        selected_exercise = self.get_selected_exercise(
            request.POST.get("exercice")
        )
        selected_month = self.get_selected_month(request.POST.get("mois"))
        if form.is_valid():
            solde = form.save()
            messages.success(
                request,
                f"Le solde d'ouverture de l'exercice {solde.exercice} a été enregistré.",
            )
            redirect_url = f"{reverse_lazy('journal_tresorerie')}?exercice={solde.exercice}"
            if selected_month is not None:
                redirect_url += f"&mois={selected_month}"
            return redirect(redirect_url)

        return self.render_to_response(
            self.get_context_data(
                opening_balance_form=form,
                open_balance_modal=True,
                selected_exercise=selected_exercise,
                selected_month=selected_month,
            )
        )


class TresorerieCreateView(CreateView):
    model = Tresorerie
    template_name = "tr_tableau/tresorerie_form.html"
    fields = "__all__"
    # Le nom d'URL de la liste est "tresorerie_table" (et non "tresorerie_list")
    success_url = reverse_lazy("tresorerie_table")


class TresorerieUpdateView(UpdateView):
    model = Tresorerie
    template_name = "tr_tableau/tresorerie_form.html"
    fields = "__all__"
    success_url = reverse_lazy("tresorerie_table")


class TresorerieDeleteView(DeleteView):
    model = Tresorerie
    template_name = "tr_tableau/tresorerie_confirm_delete.html"
    success_url = reverse_lazy("tresorerie_table")


class SuiviPaiementView(TemplateView):
    """
    Tableau récapitulatif 'Suivi de paiement' selon le modèle table_canvas/suivi_paiement.md.
    Confronte les crédits budgétaires alloués et les décaissements réels par exercice.
    """
    template_name = "tr_tableau/suivi_paiement.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        filtre_statut = self.request.GET.get("statut", "decaisse")

        # 1. Requête filtrée sur la trésorerie
        paiements_qs = Tresorerie.objects.filter(exercice__isnull=False).exclude(exercice=0)
        if filtre_statut == "decaisse":
            # Uniquement les OP ayant fait l'objet d'un décaissement bancaire
            paiements_qs = paiements_qs.filter(date_decaissement__isnull=False)

        # 2. Agrégation des paiements par exercice et ventilation Exploitation vs Investissement
        paiements_agg = (
            paiements_qs
            .values("exercice")
            .annotate(
                exp=Coalesce(
                    Sum(
                        "montant",
                        filter=Q(budget__in=[
                            Tresorerie.TypeBudget.RAM_EXP,
                            Tresorerie.TypeBudget.BUDGET_EXP,
                        ]),
                    ),
                    Decimal("0.00"),
                ),
                inv=Coalesce(
                    Sum(
                        "montant",
                        filter=Q(budget__in=[
                            Tresorerie.TypeBudget.RAM_INV,
                            Tresorerie.TypeBudget.BUDGET_INV,
                        ]),
                    ),
                    Decimal("0.00"),
                ),
            )
        )

        paiements_dict = {}
        for p in paiements_agg:
            try:
                ex_int = int(p["exercice"])
                if ex_int > 0:
                    paiements_dict[ex_int] = p
            except (ValueError, TypeError):
                continue

        # 3. Récupération des crédits budgétaires par exercice
        budgets_dict = {
            b.exercice: b for b in BudgetExercice.objects.all() if b.exercice
        }

        # 4. Détermination de la liste complète des exercices
        exercices_connus = {
            ex for ex in (set(paiements_dict.keys()) | set(budgets_dict.keys()))
            if isinstance(ex, int) and ex > 0
        }
        canvas_min = 2011
        canvas_max = max(list(exercices_connus) + [2026])
        exercices_all = sorted(
            set(range(canvas_min, canvas_max + 1)) | exercices_connus,
            reverse=True,
        )

        lignes = []
        totaux = {
            "credit_exp": Decimal("0.00"),
            "paiement_exp": Decimal("0.00"),
            "credit_inv": Decimal("0.00"),
            "paiement_inv": Decimal("0.00"),
            "total_credit": Decimal("0.00"),
            "total_paiement": Decimal("0.00"),
        }

        for ex in exercices_all:
            b = budgets_dict.get(ex)
            p = paiements_dict.get(ex, {})

            c_exp = b.credit_exploitation if b else Decimal("0.00")
            c_inv = b.credit_investissement if b else Decimal("0.00")
            p_exp = p.get("exp", Decimal("0.00"))
            p_inv = p.get("inv", Decimal("0.00"))

            tot_c = c_exp + c_inv
            tot_p = p_exp + p_inv

            totaux["credit_exp"] += c_exp
            totaux["paiement_exp"] += p_exp
            totaux["credit_inv"] += c_inv
            totaux["paiement_inv"] += p_inv
            totaux["total_credit"] += tot_c
            totaux["total_paiement"] += tot_p

            taux = (tot_p / tot_c * 100) if tot_c > Decimal("0.00") else None

            lignes.append({
                "exercice": ex,
                "credit_exp": c_exp,
                "paiement_exp": p_exp,
                "credit_inv": c_inv,
                "paiement_inv": p_inv,
                "total_credit": tot_c,
                "total_paiement": tot_p,
                "taux": taux,
                "budget_obj": b,
            })

        totaux["taux"] = (
            (totaux["total_paiement"] / totaux["total_credit"] * 100)
            if totaux["total_credit"] > Decimal("0.00")
            else None
        )

        context.update({
            "lignes": lignes,
            "totaux": totaux,
            "filtre_statut": filtre_statut,
            "budget_form": BudgetExerciceForm(),
        })
        return context

    def post(self, request, *args, **kwargs):
        """Ajout ou mise à jour rapide des crédits d'un exercice via formulaire modal."""
        exercice = request.POST.get("exercice")
        instance = BudgetExercice.objects.filter(exercice=exercice).first() if exercice else None
        form = BudgetExerciceForm(request.POST, instance=instance)
        if form.is_valid():
            b = form.save()
            messages.success(
                request,
                f"Crédits budgétaires pour l'exercice {b.exercice} enregistrés avec succès.",
            )
        else:
            messages.error(
                request,
                "Erreur lors de l'enregistrement des crédits budgétaires. Vérifiez les données saisies.",
            )
        return redirect("suivi_paiement")


class BudgetExerciceDeleteView(DeleteView):
    model = BudgetExercice
    template_name = "tr_tableau/budget_confirm_delete.html"
    success_url = reverse_lazy("suivi_paiement")


class SituationRecettesView(TemplateView):
    """
    Tableau de situation des ordres de recette dans la trésorerie
    selon le modèle table_canvas/situation_recettes.md.
    """
    template_name = "tr_tableau/situation_recettes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filtre exercice optionnel
        exercice_param = self.request.GET.get("exercice")
        recettes_qs = OrdreRecette.objects.all()

        exercices_disponibles = set(
            list(OrdreRecette.objects.values_list("exercice", flat=True).distinct())
        )

        exercice_actuel = None
        if exercice_param:
            try:
                exercice_actuel = int(exercice_param)
                recettes_qs = recettes_qs.filter(exercice=exercice_actuel)
            except ValueError:
                pass

        # Total des recettes (pour l'exercice sélectionné ou global)
        total_recettes = (
            recettes_qs.aggregate(
                total=Coalesce(Sum("montant"), Decimal("0.00"))
            )["total"]
        )

        context.update({
            "recettes_list": recettes_qs,
            "total_recettes": total_recettes,
            "exercices_disponibles": exercices_disponibles,
            "exercice_actuel": exercice_actuel,
            "recette_form": OrdreRecetteForm(),
        })
        return context

    def post(self, request, *args, **kwargs):
        """Ajout ou modification rapide d'un ordre de recette via fenêtre modale."""
        recette_id = request.POST.get("recette_id")
        instance = None
        if recette_id:
            instance = get_object_or_404(OrdreRecette, pk=recette_id)

        form = OrdreRecetteForm(request.POST, instance=instance)
        if form.is_valid():
            recette = form.save()
            action_label = "mis à jour" if instance else "créé"
            messages.success(
                request,
                f"L'ordre de recette N°{recette.num_ordre}/{recette.exercice} ({recette.debiteur}) a été {action_label} avec succès.",
            )
        else:
            messages.error(
                request,
                "Erreur lors de l'enregistrement de l'ordre de recette. Veuillez vérifier les données saisies.",
            )
        redirect_url = reverse_lazy("situation_recettes")
        exercice = request.POST.get("exercice")
        if exercice:
            return redirect(f"{redirect_url}?exercice={exercice}")
        return redirect(redirect_url)


class OrdreRecetteDeleteView(DeleteView):
    model = OrdreRecette
    success_url = reverse_lazy("situation_recettes")

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        label = f"N°{obj.num_ordre}/{obj.exercice} — {obj.debiteur}"
        response = super().post(request, *args, **kwargs)
        messages.success(request, f"L'ordre de recette {label} a été supprimé avec succès.")
        return response
