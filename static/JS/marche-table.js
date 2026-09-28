/* ==========================================================================
 * MP Manager -- Initialisation du tableau « Marchés » (DataTables 1.13.x)
 * --------------------------------------------------------------------------
 * Miroir de `tresorerie-table.js` : mêmes options, mêmes filtres par colonne,
 * même isolation de la colonne « Actions » (ni triable, ni recherchable, donc
 * exclue de la recherche globale) et mêmes tooltips ré-appliqués après chaque
 * redraw (changement de page, tri, filtre).
 *
 * Seule différence : pas de confirmation de suppression (la fiche marché est
 * en lecture seule), ni de délégation sur `.js-delete-form`.
 * ========================================================================== */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        var tableEl = document.getElementById('marcheTable');
        if (!tableEl || typeof jQuery === 'undefined') {
            return;
        }

        var $ = jQuery;
        var $table = $(tableEl);
        var tooltips = [];

        function refreshTooltips() {
            tooltips.forEach(function (tooltip) {
                tooltip.dispose();
            });
            tooltips = [];
            if (typeof bootstrap === 'undefined' || !bootstrap.Tooltip) {
                return;
            }
            tooltips = Array.prototype.map.call(
                tableEl.querySelectorAll('[data-bs-toggle="tooltip"]'),
                function (element) {
                    // container: 'body' => l'info-bulle n'est pas rognée par le
                    // conteneur défilant (.table-responsive) ni par .table-card.
                    return new bootstrap.Tooltip(element, { container: 'body' });
                }
            );
        }

        // ------------------------------------------------------------------
        // Libellés FRANÇAIS écrits en dur : la langue ne dépend plus d'aucun
        // CDN (si le dictionnaire distant est inaccessible, DataTables
        // basculerait silencieusement en anglais). Reprend les clés utilisées
        // ici du dictionnaire officiel français (DataTables 1.13.x).
        // ------------------------------------------------------------------
        var langueFR = {
            decimal: ',',
            thousands: ' ',
            emptyTable: 'Aucune donnée disponible dans le tableau',
            loadingRecords: 'Chargement...',
            processing: 'Traitement...',
            zeroRecords: 'Aucune entrée correspondante trouvée',
            info: 'Affichage de _START_ à _END_ sur _TOTAL_ entrées',
            infoEmpty: 'Affichage de 0 à 0 sur 0 entrées',
            infoFiltered: '(filtrées depuis un total de _MAX_ entrées)',
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
            // « toutes les » + « lignes » => « Afficher toutes les lignes »
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, 'Toutes']],
            autoWidth: false,
            columnDefs: [
                {
                    // Dernière colonne = Actions : jamais triée, jamais cherchée.
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

                    // Isolation : aucun filtre pour les colonnes non
                    // recherchables (Actions) ou marquées data-filter="off".
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
})();