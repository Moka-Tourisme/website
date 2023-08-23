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
class Channel(models.Model):
    """ A channel is a container of slides. """
    _inherit = 'slide.channel'

    def _action_remove_members(self, target_partners, **member_values):
        """ Remove the target_partner as a member of the channel (to its slide.channel.partner).
        This will make the content (slides) of the channel not available to that partner.

        Returns the removed 'slide.channel.partner's (! as sudo !)
        """
        to_leave = self._filter_remove_members(
            target_partners, **member_values)
        if to_leave:
            existing_to_remove = self.env['slide.channel.partner'].sudo().search([
                ('channel_id', 'in', self.ids),
                ('partner_id', 'not in', target_partners.ids)
            ])
            existing_to_remove_map = dict((cid, list()) for cid in self.ids)
            for item in existing_to_remove:
                existing_to_remove_map[item.channel_id.id].append(
                    item.partner_id.id)

            to_remove_values = []
            if len(list(existing_to_remove_map.values())) > 0 and list(existing_to_remove_map.values())[0] != []:
                to_remove_values = list(existing_to_remove_map.values())[0]
            if len(to_remove_values) > 0:
                slide_partners_sudo = self._remove_membership(
                    to_remove_values)
            return slide_partners_sudo
        return self.env['slide.channel.partner'].sudo()


    def _filter_remove_members(self, target_partners, **member_values):
        allowed = self.filtered(lambda channel: channel.enroll == 'public')
        on_invite = self.filtered(lambda channel: channel.enroll == 'invite')
        if on_invite:
            try:
                on_invite.check_access_rights('write')
                on_invite.check_access_rule('write')
            except:
                pass
            else:
                allowed |= on_invite
        return allowed

    def _remove_groups_members(self):
        for channel in self:
            channel._action_remove_members(
                channel.mapped('enroll_group_ids.users.partner_id'))