import logging
import json
from odoo import SUPERUSER_ID, _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

_logger = logging.getLogger(__name__)


class WebsiteGeonames(http.Controller):

    @http.route('/city/get_zip', type='http', auth="public", methods=['GET'], website=True, sitemap=False)
    def get_zip(self, query='', limit=25, **post):
        domain = [('display_name', '=ilike', "%" + (query or '') + "%")]
        data = request.env['res.city.zip'].search_read(
            domain=domain,
            fields=['id', 'display_name', 'name', 'city_id', 'country_id', 'state_id'],
            limit=int(limit)
        )
        return request.make_response(
            json.dumps(data),
            headers=[("Content-Type", "application/json")]
        )
