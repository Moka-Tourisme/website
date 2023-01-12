{
    "name": "Website Geonames",
    "summary": "Website Geonames",
    "author": "Moka Tourisme",
    "website": "https://www.mokatourisme.fr",
    "category": "Website",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "data": [
        # views
        "views/website_sale_views.xml",
    ],

    "assets": {
        "web.assets_frontend": [
            "website_geonames/static/src/js/**/*",
            "website_geonames/static/lib/choices.css"
        ],
        "web.assets_common": [
            "website_geonames/static/lib/choices.js",
        ],
    },
    "depends": [
        "website",
        "base_location"
    ],
}
