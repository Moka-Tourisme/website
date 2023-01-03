{
    "name": "Website Geonames",
    "summary": "Website Geonames",
    "author": "Moka Tourisme",
    "website": "https://www.mokatourisme.fr",
    "category": "Website",
    "version": "15.0.1",
    "license": "AGPL-3",
    "data": [
        # views
        "views/website_sale_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_geonames/static/src/js/**/*",
        ],
    },
    "depends": [
        "website",
        "base_location_geonames_import",
        "base_location"
    ],
}
