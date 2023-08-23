# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class MembershipLineInherit(models.Model):
    _inherit = 'membership.membership_line'

    def _cron_update_membership_lines(self):
        # Update membership lines state and end date
        today = fields.Date.today()
        lines = self.search([('date_to', '<', today), ('state', 'in', ['paid', 'free', 'invoiced'])])
        for line in lines:
            #         Check if the partner have other lines that are not old that have the same membership_group_ids and not line
            other_lines = self.search([('partner', '=', line.partner.id), ('state', 'not in', ['old', 'cancel']),
                                       ('membership_id.membership_group_ids', 'in', line.membership_id.membership_group_ids.ids),
                                       ('id', '!=', line.id)])
            if not other_lines:
                line.partner.user_ids.write(
                    {'groups_id': [(3, group.id) for group in line.membership_id.membership_group_ids]})
        lines.write({'state': 'old'})

    def _compute_state(self):
        """Compute the state lines """
        today = fields.Date.today()
        if not self:
            return

        self._cr.execute('''
            SELECT reversed_entry_id, COUNT(id)
            FROM account_move
            WHERE reversed_entry_id IN %s
            GROUP BY reversed_entry_id
        ''', [tuple(self.mapped('account_invoice_id.id'))])
        reverse_map = dict(self._cr.fetchall())
        for line in self:
            move_state = line.account_invoice_id.state
            payment_state = line.account_invoice_id.payment_state

            line.state = 'none'
            if move_state == 'draft':
                line.state = 'waiting'
            elif move_state == 'posted':
                if payment_state == 'paid':
                    if reverse_map.get(line.account_invoice_id.id):
                        line.state = 'canceled'
                    else:
                        line.state = 'paid'
                elif payment_state == 'in_payment':
                    line.state = 'paid'
                elif payment_state in ('not_paid', 'partial'):
                    line.state = 'invoiced'
            elif move_state == 'cancel':
                line.state = 'canceled'
            if line.date_to < today:
                line.state = 'old'
            if line.state in ['paid', 'free']:
                line._assign_groups()

    def _assign_groups(self):
        for line in self:
            if line.membership_id.membership_group_ids:
                for group in line.membership_id.membership_group_ids:
                    if group not in line.partner.user_ids.groups_id:
                        line.partner.user_ids.write({'groups_id': [(4, group.id)]})