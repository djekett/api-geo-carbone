"""
Constantes du projet API.GEO.Carbone.
Nomenclatures, palettes de couleurs, coefficients de carbone.

Données réelles des forêts classées du département d'Oumé.
"""

ANNEE_CHOICES = [
    (1986, '1986'),
    (2003, '2003'),
    (2023, '2023'),
]

ANNEES_VALIDES = [1986, 2003, 2023]

COLOR_MAP = {
    'FORET_DENSE': '#006400',
    'FORET_CLAIRE': '#32CD32',
    'FORET_DEGRADEE': '#9ACD32',
    'JACHERE': '#FFFF00',
    'CACAO': '#FFA500',
    'CAFE': '#8B4513',
    'HEVEA': '#FFB6C1',
    'CULTURE_HERBACEE': '#DA70D6',
    'SOL_NU': '#E0FFFF',
}

# ======= Valeurs de référence Biomasse / Carbone / CO2 =======

BIOMASSE_REFERENCE = {
    'FORET_DENSE': 1739.16,
    'FORET_CLAIRE': 1804.16,
    'FORET_DEGRADEE': 1062.09,
    'JACHERE': 1671.98,
    'CACAO': 0,
    'CAFE': 0,
    'HEVEA': 0,
    'CULTURE_HERBACEE': 0,
    'SOL_NU': 0,
}

CARBONE_TOTAL_REFERENCE = {
    'FORET_DENSE': 869.10,
    'FORET_CLAIRE': 902.08,
    'FORET_DEGRADEE': 531.04,
    'JACHERE': 792.66,
    'CACAO': 0,
    'CAFE': 0,
    'HEVEA': 0,
    'CULTURE_HERBACEE': 0,
    'SOL_NU': 0,
}

STOCK_CARBONE_REFERENCE = {
    'FORET_DENSE': 3186.70,
    'FORET_CLAIRE': 3307.62,
    'FORET_DEGRADEE': 1947.15,
    'JACHERE': 2906.42,
    'CACAO': 0,
    'CAFE': 0,
    'HEVEA': 0,
    'CULTURE_HERBACEE': 0,
    'SOL_NU': 0,
}

# ======= Nomenclature complète avec biomasse + carbone + CO2 =======

NOMENCLATURE_DATA = [
    {
        'code': 'FORET_DENSE',
        'libelle_fr': 'Forêt dense',
        'biomasse_t_ha': 1739.16,
        'carbone_tc_ha': 869.10,
        'stock_carbone_reference': 3186.70,
        'couleur_hex': '#006400',
        'ordre_affichage': 1,
    },
    {
        'code': 'FORET_CLAIRE',
        'libelle_fr': 'Forêt claire',
        'biomasse_t_ha': 1804.16,
        'carbone_tc_ha': 902.08,
        'stock_carbone_reference': 3307.62,
        'couleur_hex': '#32CD32',
        'ordre_affichage': 2,
    },
    {
        'code': 'FORET_DEGRADEE',
        'libelle_fr': 'Forêt dégradée',
        'biomasse_t_ha': 1062.09,
        'carbone_tc_ha': 531.04,
        'stock_carbone_reference': 1947.15,
        'couleur_hex': '#9ACD32',
        'ordre_affichage': 3,
    },
    {
        'code': 'JACHERE',
        'libelle_fr': 'Jachère / Reboisement jeune',
        'biomasse_t_ha': 1671.98,
        'carbone_tc_ha': 792.66,
        'stock_carbone_reference': 2906.42,
        'couleur_hex': '#FFFF00',
        'ordre_affichage': 4,
    },
    {
        'code': 'CACAO',
        'libelle_fr': 'Cacao',
        'biomasse_t_ha': 0,
        'carbone_tc_ha': 0,
        'stock_carbone_reference': 0,
        'couleur_hex': '#FFA500',
        'ordre_affichage': 5,
    },
    {
        'code': 'CAFE',
        'libelle_fr': 'Café',
        'biomasse_t_ha': 0,
        'carbone_tc_ha': 0,
        'stock_carbone_reference': 0,
        'couleur_hex': '#8B4513',
        'ordre_affichage': 6,
    },
    {
        'code': 'HEVEA',
        'libelle_fr': 'Hévéa',
        'biomasse_t_ha': 0,
        'carbone_tc_ha': 0,
        'stock_carbone_reference': 0,
        'couleur_hex': '#FFB6C1',
        'ordre_affichage': 7,
    },
    {
        'code': 'CULTURE_HERBACEE',
        'libelle_fr': 'Culture annuelle / Herbacée',
        'biomasse_t_ha': 0,
        'carbone_tc_ha': 0,
        'stock_carbone_reference': 0,
        'couleur_hex': '#DA70D6',
        'ordre_affichage': 8,
    },
    {
        'code': 'SOL_NU',
        'libelle_fr': 'Sol nu',
        'biomasse_t_ha': 0,
        'carbone_tc_ha': 0,
        'stock_carbone_reference': 0,
        'couleur_hex': '#E0FFFF',
        'ordre_affichage': 9,
    },
]

# ======= Superficies RÉELLES des forêts classées (ha) =======

FORETS_DATA = {
    'TENE': {
        'nom': 'Forêt Classée de TENÉ',
        'superficie_legale_ha': 29549,
    },
    'DOKA': {
        'nom': 'Forêt Classée de DOKA',
        'superficie_legale_ha': 10945,
    },
    'SANGOUE': {
        'nom': 'Forêt Classée de SANGOUÉ',
        'superficie_legale_ha': 27360,
    },
    'LAHOUDA': {
        'nom': 'Forêt Classée de LAHOUDA',
        'superficie_legale_ha': 3300,
    },
    'ZOUEKE_1': {
        'nom': 'Forêt Classée de ZOUÉKÉ Bloc I',
        'superficie_legale_ha': 6825,
    },
    'ZOUEKE_2': {
        'nom': 'Forêt Classée de ZOUÉKÉ Bloc II',
        'superficie_legale_ha': 3077,
    },
}

SUPERFICIE_TOTALE_HA = 81056
