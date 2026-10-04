from django import forms
from .models import BudgetExercice


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
