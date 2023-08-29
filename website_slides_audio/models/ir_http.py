import base64
import hashlib
import io
import mimetypes
import json

import odoo
from odoo import api, http, models
from odoo.http import content_disposition, request
from odoo.tools import file_open, image_process, ustr
import inspect

from odoo.addons.web.controllers.main import HomeStaticTemplateHelpers


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    @api.model
    def _get_content_common(self, xmlid=None, model='ir.attachment', res_id=None, field='datas',
                            unique=None, filename=None, filename_field='name', download=None, mimetype=None,
                            access_token=None, token=None):
        if model == 'slide.slide':
            if field == 'audio_file':
                # Search the slide and get the audio file
                slide = request.env['slide.slide'].sudo().search([('id', '=', res_id)])
                if slide:
                    if slide.audio_file:
                        print("Slide audio file: ", slide.audio_file)
                        #         Guess the mimetype from audio_file using mimetypes.guess_type
                        # Get the extension from mimetype and add it to the filename
                        filename = 'slide.slide-'
                        filename += str(slide.id)
                        filename += '-' + field
                        filename += '.mp3'

        status, headers, content = self.binary_content(
            xmlid=xmlid, model=model, id=res_id, field=field, unique=unique, filename=filename,
            filename_field=filename_field, download=download, mimetype=mimetype, access_token=access_token
        )

        if status != 200:
            return self._response_by_status(status, headers, content)
        else:
            content_base64 = base64.b64decode(content)
            headers.append(('Content-Length', len(content_base64)))
            response = request.make_response(content_base64, headers)
        return response
