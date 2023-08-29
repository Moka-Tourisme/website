# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import datetime
import io
import re

import requests
import PyPDF2
import json

from dateutil.relativedelta import relativedelta
from PIL import Image
from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import UserError, AccessError
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import url_for
from odoo.tools import html2plaintext, sql


class SlideInherit(models.Model):
    _inherit = [
        'slide.slide',
    ]

    # Add audio to slide_type
    slide_type = fields.Selection(
        selection_add=[
            ('audio', 'Audio'),
        ],
        ondelete={'audio': 'set document'},
    )

    audio_file = fields.Binary(
        string='Audio File',
        attachment=True,
        help='Audio File',
    )

    audio_embed_code = fields.Html(
        string='Audio Embed Code',
        help='Audio Embed Code',
        compute='_compute_audio_embed_code',
        sanitize=False,
    )

    nbr_audio = fields.Integer(
        string='Number of Audio',
        compute='_compute_slides_statistics',
        store=True,
        compute_sudo=False,
    )

    @api.depends('slide_type', 'mime_type', 'audio_file')
    def _compute_audio_embed_code(self):
        for record in self:
            if record.slide_type == 'audio' and record.audio_file:
                # Convert the audio_file binary data to base64
                audio_base64 = record.audio_file.decode('utf-8')
                # Create the audio tag like
                audio_tag = f'<audio controls style="min-width: 100%" src="data:audio/mpeg;base64,{audio_base64}"></audio>'
                record.audio_embed_code = audio_tag
            else:
                record.audio_embed_code = False

    @api.onchange('audio_file')
    def _on_change_audio_file(self):
        if self.audio_file:
            data = base64.b64decode(self.audio_file)

    def _search_render_results(self, fetch_fields, mapping, icon, limit):
        icon_per_type = {
            'infographic': 'fa-file-picture-o',
            'webpage': 'fa-file-text',
            'presentation': 'fa-file-pdf-o',
            'document': 'fa-file-pdf-o',
            'video': 'fa-play-circle',
            'quiz': 'fa-question-circle',
            'link': 'fa-file-code-o',  # appears in template "slide_icon"
            'audio': 'fa-file-audio-o',
        }
        results_data = super()._search_render_results(fetch_fields, mapping, icon, limit)
        for slide, data in zip(self, results_data):
            data['_fa'] = icon_per_type.get(slide.slide_type, 'fa-file-pdf-o')
            data['url'] = slide.website_url
            data['course'] = _('Course: %s', slide.channel_id.name)
            data['course_url'] = slide.channel_id.website_url
        return results_data
