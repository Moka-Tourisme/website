# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import pdb

from odoo import api, fields, models
from datetime import date


class PartnerInherit(models.Model):
    _inherit = 'res.partner'


    @api.depends('member_lines.account_invoice_line',
             'member_lines.account_invoice_line.move_id.state',
             'member_lines.account_invoice_line.move_id.payment_state',
             'member_lines.account_invoice_line.move_id.partner_id',
             'free_member',
             'member_lines.date_to', 'member_lines.date_from',
             'associate_member')
    def _compute_membership_state(self):
        today = fields.Date.today()
        for partner in self:
            state = 'none'

            partner.membership_start = self.env['membership.membership_line'].search([
                ('partner', '=', partner.associate_member.id or partner.id), ('date_cancel', '=', False)
            ], limit=1, order='date_from').date_from
            partner.membership_stop = self.env['membership.membership_line'].search([
                ('partner', '=', partner.associate_member.id or partner.id), ('date_cancel', '=', False)
            ], limit=1, order='date_to desc').date_to
            partner.membership_cancel = self.env['membership.membership_line'].search([
                ('partner', '=', partner.id)
            ], limit=1, order='date_cancel').date_cancel

            if partner.membership_cancel and today > partner.membership_cancel:
                partner.membership_state = 'free' if partner.free_member else 'canceled'
                continue
            if partner.membership_stop and today > partner.membership_stop:
                if partner.free_member:
                    partner.membership_state = 'free'
                    continue
            if partner.associate_member:
                partner.associate_member._compute_membership_state()
                partner.membership_state = partner.associate_member.membership_state
                continue

            line_states = [mline.state for mline in partner.member_lines if \
                           (mline.date_to or date.min) >= today and \
                           (mline.date_from or date.min) <= today and \
                           mline.account_invoice_line.move_id.partner_id == partner]

            for state in line_states:
                print(state)
            if 'paid' in line_states:
                state = 'paid'
            elif 'invoiced' in line_states:
                state = 'invoiced'
            elif 'waiting' in line_states:
                state = 'waiting'
            elif 'canceled' in line_states:
                state = 'canceled'
            elif 'old' in line_states:
                state = 'old'

            if partner.free_member and state != 'paid':
                state = 'free'
            partner.membership_state = state
