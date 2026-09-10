from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Tresorerie

# Create your views here.
# Call the template created in the templates folder to display the table of the Tresorerie model


class TresorerieListView(ListView):
    model = Tresorerie
    template_name = "tr_tableau/tresorerie_table.html"
    context_object_name = "tresorerie_list"


class TresorerieCreateView(CreateView):
    model = Tresorerie
    template_name = "tresorerie_form.html"
    fields = "__all__"
    success_url = reverse_lazy("tresorerie_list")


class TresorerieUpdateView(UpdateView):
    model = Tresorerie
    template_name = "tresorerie_form.html"
    fields = "__all__"
    success_url = reverse_lazy("tresorerie_list")


class TresorerieDeleteView(DeleteView):
    model = Tresorerie
    template_name = "tresorerie_confirm_delete.html"
    success_url = reverse_lazy("tresorerie_list")


# from django.shortcuts import render
# from .models import Tresorerie


# # # Create your views here.
# # # Call the template created in the templates folder to display the table of the Tresorerie model
# def tresorerie_table(request):
#     tresorerie_list = Tresorerie.objects.all()
#     return render(
#         request,
#         "tr_tableau/tresorerie_table.html",
#         {"tresorerie_list": tresorerie_list},
#     )
