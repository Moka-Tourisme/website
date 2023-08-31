from odoo import http
from odoo.http import request
import odoo.addons.web.controllers.main as main
import json
from odoo.http import content_disposition, dispatch_rpc, request
from odoo.tools import html_escape, pycompat, ustr, apply_inheritance_specs, lazy_property, osutil
import operator


class Binary(main.Binary):
    @http.route(['/web/content',
                 '/web/content/<string:xmlid>',
                 '/web/content/<string:xmlid>/<string:filename>',
                 '/web/content/<int:id>',
                 '/web/content/<int:id>/<string:filename>',
                 '/web/content/<string:model>/<int:id>/<string:field>',
                 '/web/content/<string:model>/<int:id>/<string:field>/<string:filename>'], type='http', auth="public")
    def content_common(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                       filename=None, filename_field='name', unique=None, mimetype=None,
                       download=None, data=None, token=None, access_token=None, **kw):

        if field == 'datas':
            filename_field = "datas_filename"
        elif field == 'audio_file':
            filename_field = "audio_filename"
        return request.env['ir.http']._get_content_common(xmlid=xmlid, model=model, res_id=id, field=field,
                                                          unique=unique, filename=filename,
                                                          filename_field=filename_field, download=download,
                                                          mimetype=mimetype, access_token=access_token, token=token)


class ExportFormat(main.ExportFormat):
    def base(self, data):
        print("LA web export format nouvelle")
        params = json.loads(data)
        model, fields, ids, domain, import_compat = \
            operator.itemgetter('model', 'fields', 'ids', 'domain', 'import_compat')(params)

        Model = request.env[model].with_context(**params.get('context', {}))
        if not Model._is_an_ordinary_table():
            fields = [field for field in fields if field['name'] != 'id']

        field_names = [f['name'] for f in fields]
        if import_compat:
            columns_headers = field_names
        else:
            columns_headers = [val['label'].strip() for val in fields]

        groupby = params.get('groupby')
        if not import_compat and groupby:
            groupby_type = [Model._fields[x.split(':')[0]].type for x in groupby]
            domain = [('id', 'in', ids)] if ids else domain
            groups_data = Model.read_group(domain, [x if x != '.id' else 'id' for x in field_names], groupby,
                                           lazy=False)

            # read_group(lazy=False) returns a dict only for final groups (with actual data),
            # not for intermediary groups. The full group tree must be re-constructed.
            tree = main.GroupsTreeNode(Model, field_names, groupby, groupby_type)
            for leaf in groups_data:
                tree.insert_leaf(leaf)

            response_data = self.from_group_data(fields, tree)
        else:
            Model = Model.with_context(import_compat=import_compat)
            records = Model.browse(ids) if ids else Model.search(domain, offset=0, limit=False, order=False)

            export_data = records.export_data(field_names).get('datas', [])
            response_data = self.from_data(columns_headers, export_data)

        # TODO: call `clean_filename` directly in `content_disposition`?
        return request.make_response(response_data,
                                     headers=[('Content-Disposition',
                                               content_disposition(
                                                   osutil.clean_filename(self.filename(model) + self.extension))),
                                              ('Content-Type', self.content_type)],
                                     )
