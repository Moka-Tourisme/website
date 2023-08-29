# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import uuid
from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, _
from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.exceptions import AccessError
from odoo.osv import expression
from odoo.tools import is_html_empty

_logger = logging.getLogger(__name__)
class ChannelInherit(models.Model):
    """ A channel is a container of slides. """
    _inherit = 'slide.channel'

    nbr_audio = fields.Integer(compute='_compute_slides_statistics', string='Number of audio', store=True, compute_sudo=False)

