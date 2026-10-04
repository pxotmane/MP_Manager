from django import forms
from .models import BudgetExercice, OrdreRecette


class BudgetExerciceForm(forms.ModelForm):
    class Meta:
        model = BudgetExercice
        fields = [
            "exercice",
            "credit_exploitation",
            "credit_investissement",
            "observation",
        ]
        widgets = {
            "exercice": forms.NumberInput(
                attrs={"placeholder": "Ex: 2026", "class": "form-control"}
            ),
            "credit_exploitation": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "placeholder": "0.00",
                    "class": "form-control",
                }
            ),
            "credit_investissement": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "placeholder": "0.00",
                    "class": "form-control",
                }
            ),
            "observation": forms.TextInput(
                attrs={
                    "placeholder": "Notes facultatives",
                    "class": "form-control",
                }
            ),
        }


class OrdreRecetteForm(forms.ModelForm):
    class Meta:
        model = OrdreRecette
        fields = [
            "exercice",
            "num_ordre",
            "date_decision",
            "num_decision",
            "debiteur",
            "nature",
            "budget",
            "date_encaissement",
            "montant",
            "etat",
            "observation",
        ]
        widgets = {
            "exercice": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Ex: 2026"}
            ),
            "num_ordre": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Ex: 1", "min": "1"}
            ),
            "date_decision": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "num_decision": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "N° de décision"}
            ),
            "debiteur": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nom / Organisme débiteur"}
            ),
            "nature": forms.Select(
                attrs={"class": "form-select"}
            ),
            "budget": forms.Select(
                attrs={"class": "form-select"}
            ),
            "date_encaissement": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "montant": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}
            ),
            "etat": forms.Select(
                attrs={"class": "form-select"}
            ),
            "observation": forms.Textarea(
                attrs={"class": "form-control", "rows": "2", "placeholder": "Notes facultatives"}
            ),
        }
