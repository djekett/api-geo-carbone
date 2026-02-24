/**
 * Popup Builder - Formatage des popups d'information
 */
const PopupBuilder = {
    occupation(props) {
        return `
            <div class="popup-header">${props.foret_nom || 'Foret'}</div>
            <div class="popup-body">
                <div class="row"><span class="label">Type</span><span class="value">${props.libelle || props.type_couvert || '-'}</span></div>
                <div class="row"><span class="label">Annee</span><span class="value">${props.annee || '-'}</span></div>
                <div class="row"><span class="label">Superficie</span><span class="value">${props.superficie_ha ? props.superficie_ha.toLocaleString('fr', {maximumFractionDigits: 1}) + ' ha' : '-'}</span></div>
                <div class="row"><span class="label">Stock carbone</span><span class="value">${props.stock_carbone_calcule ? props.stock_carbone_calcule.toLocaleString('fr', {maximumFractionDigits: 0}) + ' tCO2/ha' : '-'}</span></div>
                <div class="row"><span class="label">Source</span><span class="value">${props.source_donnee || '-'}</span></div>
            </div>`;
    },

    foret(props) {
        return `
            <div class="popup-header">${props.nom || 'Foret classee'}</div>
            <div class="popup-body">
                <div class="row"><span class="label">Code</span><span class="value">${props.code || '-'}</span></div>
                <div class="row"><span class="label">Superficie legale</span><span class="value">${props.superficie_legale_ha ? props.superficie_legale_ha.toLocaleString('fr') + ' ha' : '-'}</span></div>
                <div class="row"><span class="label">Gestion</span><span class="value">${props.autorite_gestion || '-'}</span></div>
            </div>`;
    },

    placette(props) {
        return `
            <div class="popup-header">Placette ${props.code_placette || ''}</div>
            <div class="popup-body">
                <div class="row"><span class="label">Foret</span><span class="value">${props.foret_nom || '-'}</span></div>
                <div class="row"><span class="label">Annee</span><span class="value">${props.annee_mesure || '-'}</span></div>
                <div class="row"><span class="label">Biomasse</span><span class="value">${props.biomasse_tonne_ha ? props.biomasse_tonne_ha + ' t/ha' : '-'}</span></div>
                <div class="row"><span class="label">Carbone</span><span class="value">${props.stock_carbone_mesure ? props.stock_carbone_mesure + ' tCO2/ha' : '-'}</span></div>
            </div>`;
    },
};
