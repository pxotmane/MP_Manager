from decimal import Decimal
from django.contrib import messages
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from .models import Tresorerie, BudgetExercice
from .forms import BudgetExerciceForm

# Create your views here.
# Call the template created in the templates folder to display the table of the Tresorerie model


class TresorerieListView(ListView):
    model = Tresorerie
    template_name = "tr_tableau/tresorerie_table.html"
    context_object_name = "tresorerie_list"


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

