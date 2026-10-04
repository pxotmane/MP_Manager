/* ==========================================================================
 * MP Manager -- Initialisation du tableau « Situation des Recettes »
 * --------------------------------------------------------------------------
 * Principes :
 *   - Ligne 2 d'en-tête <tr class="filters"> pour les filtres par colonne ;
 *   - Recherche globale, tri et pagination en français (DataTables 1.13.x) ;
 *   - Colonne « Actions » isolée (sans filtre ni tri) ;
 *   - Gestion de la fenêtre modale rapide pour Ajout et Modification ;
 *   - Confirmation de suppression déléguée.
 * ========================================================================== */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        var tableEl = document.getElementById('recettesTable');
        if (!tableEl || typeof jQuery === 'undefined') {
            return;
        }

        var $ = jQuery;
        var $table = $(tableEl);
        var tooltips = [];

        function refreshTooltips() {
            tooltips.forEach(function (t) {
                t.dispose();
            });
            tooltips = [];
            if (typeof bootstrap === 'undefined' || !bootstrap.Tooltip) {
                return;
            }
            tooltips = Array.prototype.map.call(
                tableEl.querySelectorAll('[data-bs-toggle="tooltip"]'),
                function (el) {
                    return new bootstrap.Tooltip(el, { container: 'body' });
                }
            );
        }

        var langueFR = {
            decimal: ',',
            thousands: ' ',
            emptyTable: 'Aucun ordre de recette disponible dans le tableau',
            loadingRecords: 'Chargement...',
            processing: 'Traitement...',
            zeroRecords: 'Aucun ordre de recette correspondant trouvé',
            info: 'Affichage de _START_ à _END_ sur _TOTAL_ recettes',
            infoEmpty: 'Affichage de 0 à 0 sur 0 recette',
            infoFiltered: '(filtrées depuis un total de _MAX_ recettes)',
            lengthMenu: 'Afficher _MENU_ lignes',
            search: 'Rechercher :',
            paginate: {
                first: 'Première',
                last: 'Dernière',
                next: 'Suivante',
                previous: 'Précédente'
            },
            aria: {
                sortAscending: ' : activer pour trier la colonne par ordre croissant',
                sortDescending: ' : activer pour trier la colonne par ordre décroissant'
            }
        };

        var table = $table.DataTable({
            language: langueFR,
            orderCellsTop: true,
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, 'Toutes']],
            autoWidth: false,
            order: [[0, 'asc']], // Tri par N° d'ordre par défaut
            columnDefs: [
                {
                    // Dernière colonne = Actions : isolée
                    targets: -1,
                    orderable: false,
                    searchable: false,
                    className: 'text-center text-nowrap actions-col'
                }
            ],
            initComplete: function () {
                var api = this.api();
                var $filterCells = $table.find('thead tr.filters th');

                api.columns().every(function (index) {
                    var column = this;
                    var $cell = $filterCells.eq(index);

                    if (!column.searchable() || $cell.data('filter') === 'off') {
                        return;
                    }

                    var placeholder = $cell.data('placeholder') || column.header().textContent.trim();
                    if (!placeholder) {
                        return;
                    }

                    var $input = $('<input>', {
                        type: 'text',
                        class: 'form-control form-control-sm',
                        placeholder: placeholder,
                        'aria-label': 'Filtrer la colonne ' + placeholder
                    });

                    $cell.empty().append($input);

                    $input.on('keyup change clear', function () {
                        if (column.search() !== this.value) {
                            column.search(this.value).draw();
                        }
                    });
                });

                refreshTooltips();
            }
        });

        table.on('draw', refreshTooltips);
    });

    // Confirmation de suppression déléguée
    document.addEventListener('submit', function (event) {
        var form = event.target.closest ? event.target.closest('.js-delete-form') : null;
        if (!form) {
            return;
        }
        var label = form.getAttribute('data-label') || 'cette recette';
        if (!window.confirm('Supprimer définitivement ' + label + ' ?')) {
            event.preventDefault();
        }
    });
})();

// Fonctions d'ouverture de la Modale rapide
function openAddRecetteModal() {
    var modalEl = document.getElementById('recetteModal');
    if (!modalEl) return;

    document.getElementById('recetteModalTitle').textContent = "Ajouter un Ordre de Recette";
    document.getElementById('id_recette_id').value = "";
    
    // Récupérer l'exercice sélectionné dans l'URL ou année en cours
    var currentYear = new Date().getFullYear();
    var urlParams = new URLSearchParams(window.location.search);
    var exUrl = urlParams.get('exercice');

    document.getElementById('id_exercice').value = exUrl || currentYear;
    document.getElementById('id_num_ordre').value = "";
    document.getElementById('id_date_decision').value = "";
    document.getElementById('id_num_decision').value = "";
    document.getElementById('id_debiteur').value = "";
    document.getElementById('id_nature').value = "ALIMENTATION DE LA TRESORERIE";
    document.getElementById('id_budget').value = "EXPLOITATION";
    document.getElementById('id_date_encaissement').value = "";
    document.getElementById('id_montant').value = "";
    document.getElementById('id_etat').value = "NON ETABLI";
    document.getElementById('id_observation').value = "";

    var modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    modal.show();
}

function openEditRecetteModal(data) {
    var modalEl = document.getElementById('recetteModal');
    if (!modalEl) return;

    document.getElementById('recetteModalTitle').textContent = "Modifier l'Ordre de Recette N°" + data.num_ordre;
    document.getElementById('id_recette_id').value = data.id || "";
    document.getElementById('id_exercice').value = data.exercice || "";
    document.getElementById('id_num_ordre').value = data.num_ordre || "";
    document.getElementById('id_date_decision').value = data.date_decision || "";
    document.getElementById('id_num_decision').value = data.num_decision || "";
    document.getElementById('id_debiteur').value = data.debiteur || "";
    document.getElementById('id_nature').value = data.nature || "ALIMENTATION DE LA TRESORERIE";
    document.getElementById('id_budget').value = data.budget || "EXPLOITATION";
    document.getElementById('id_date_encaissement').value = data.date_encaissement || "";
    document.getElementById('id_montant').value = data.montant || "";
    document.getElementById('id_etat').value = data.etat || "NON ETABLI";
    document.getElementById('id_observation').value = data.observation || "";

    var modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    modal.show();
}
