# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError, UserError


class MembershipLineInherit(models.Model):
    _inherit = 'membership.membership_line'

    # Set default value from membership_id.membership_group_ids if exists else nothing
    group_ids = fields.Many2many('res.groups', string='Groups', store=True)
    user_id = fields.Many2one('res.users', string='Users', store=True)

    def _cron_set_default_membership_groups(self):
        print("Cron set default membership groups")
        # For each membership lines that have no group_ids, set the default groups from the membership_id.membership_group_ids
        lines = self.search([('group_ids', '=', False), ('partner.user_ids', '!=', False)])
        print("lines: ", lines)
        for line in lines:
            line.write({'group_ids': [(6, 0, line.membership_id.membership_group_ids.ids)]})

    def _cron_update_membership_lines(self):
        # Update membership lines state and end date
        today = fields.Date.today()
        lines = self.search([('date_to', '<', today), ('state', 'in', ['paid', 'free', 'invoiced'])])
        for line in lines:
            # Check if the partner have other lines that are not old that have the same membership_group_ids and not line
            other_lines = self.search([('partner', '=', line.partner.id), ('state', 'not in', ['old', 'cancel']),
                                       ('group_ids', 'in',
                                        line.group_ids.ids),
                                       ('id', '!=', line.id)])
            if not other_lines:
                line.partner.user_id.write(
                    {'groups_id': [(3, group.id) for group in line.membership_id.membership_group_ids]})
            if line.user_id:
                # Check if the user have other lines that are not old that have the same membership_group_ids and not line
                other_lines = self.search(
                    ['|', ('partner', '=', line.user_id.partner_id.id), ('user_id', '=', line.user_id.id),
                     ('state', 'not in', ['old', 'cancel']),
                     ('group_ids', 'in',
                      line.group_ids.ids),
                     ('id', '!=', line.id)])
                if not other_lines:
                    line.user_id.write(
                        {'groups_id': [(3, group.id) for group in line.group_ids]},
                        {'associate_member': False}
                    )
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
                        user = self.env['res.users'].search([('partner_id', '=', line.partner.id)])
                        if user:
                            for group in line.group_ids:
                                group.write({'users': [(4, user.id)]})
                elif payment_state == 'in_payment':
                    line.state = 'paid'
                    user = self.env['res.users'].search([('partner_id', '=', line.partner.id)])
                    if user:
                        for group in line.group_ids:
                            group.write({'users': [(4, user.id)]})
                elif payment_state in ('not_paid', 'partial'):
                    line.state = 'invoiced'
            elif move_state == 'cancel':
                line.state = 'canceled'
            if line.date_to < today:
                line.state = 'old'

    @api.onchange('user_id')
    def _check_associated_member(self):
        for user in self.user_id:
            if user.partner_id:
                if user.partner_id.associate_member and str(user.partner_id.associate_member.id != self.partner.id)[6:]:
                    raise ValidationError(_('The partner %s is already an associated member') % user.partner_id.name)

    def write(self, vals):
        old_user_id = self.user_id
        old_group_ids = self.group_ids
        super(MembershipLineInherit, self).write(vals)
        # Get the user from the membership partner from the partner and add the groups
        user = self.env['res.users'].search([('partner_id', '=', self.partner.id)])
        if self.state in ['paid', 'free']:
            if self.user_id and old_user_id:
                if self.user_id != old_user_id:
                    if old_user_id:
                        # Check if the user is not the partner of another membership line
                        other_lines = self.search(
                            [('user_id', '=', old_user_id.id),
                             ('state', 'not in', ['old', 'cancel']),
                             ('id', '!=', self.id)])
                        if not other_lines:
                            old_user_id.write({'associate_member': False})
                        if old_group_ids:
                            for group in old_group_ids:
                                if self.user_id in group.users:
                                    # Remove only if there is no other membership line with the same group
                                    other_lines = self.search(
                                        ['|', ('partner', '=', old_user_id.partner_id.id),
                                         ('user_id', '=', old_user_id.id),
                                         ('state', 'not in', ['old', 'cancel']),
                                         ('group_ids', 'in',
                                          group.ids),
                                         ('id', '!=', self.id)])
                                    if not other_lines:
                                        group.write({'users': [(3, self.user_id.id)]})
                    if not self.user_id.associate_member or self.user_id.associate_member == self.partner:
                        self.user_id.write({'associate_member': self.partner.id})
                        if self.group_ids:
                            for group in self.group_ids:
                                if self.user_id not in group.users:
                                    group.write({'users': [(4, self.user_id.id)]})

            elif not self.user_id and old_user_id:
                # Check if the user is not the partner of another membership line
                other_lines = self.search(
                    [('user_id', '=', old_user_id.id),
                     ('state', 'not in', ['old', 'cancel']),
                     ('id', '!=', self.id)])
                if not other_lines:
                    old_user_id.write({'associate_member': False})
                # Remove all groups from the user from the group_ids of the membership line except if there is another membership line with the same group_ids
                if old_group_ids:
                    for group in old_group_ids:
                        if old_user_id in group.users:
                            # Remove only if there is no other membership line with the same group
                            other_lines = self.search(
                                ['|', ('partner', '=', old_user_id.partner_id.id), ('user_id', '=', old_user_id.id),
                                 ('state', 'not in', ['old', 'cancel']),
                                 ('group_ids', 'in',
                                  group.ids),
                                 ('id', '!=', self.id)])
                            if not other_lines:
                                group.write({'users': [(3, old_user_id.id)]})

            elif self.user_id and not old_user_id:
                # If user_id has no associate_member, set the partner as associate_member of the partner of the membership line else raise an error
                if not self.user_id.associate_member or self.user_id.associate_member == self.partner:
                    self.user_id.write({'associate_member': self.partner.id})
                else:
                    raise ValidationError(_('The user %s is already an associated member') % self.user_id.name)
                if self.group_ids:
                    for group in self.group_ids:
                        if self.user_id not in group.users:
                            group.write({'users': [(4, self.user_id.id)]})

            if self.group_ids and old_group_ids:
                for removed_group in old_group_ids - self.group_ids:
                    if user in removed_group.users:
                        # Remove only if there is no other membership line with the same group
                        other_lines = self.search(
                            ['|', ('partner', '=', user.id), ('user_id', '=', user.id),
                             ('state', 'not in', ['old', 'cancel']),
                             ('group_ids', 'in',
                              removed_group.ids),
                             ('id', '!=', self.id)])
                        if not other_lines:
                            removed_group.write({'users': [(3, user.id)]})
                    if self.user_id:
                        if self.user_id in removed_group.users:
                            # Search other membership line with the same group where the user is the partner
                            other_lines = self.search(
                                ['|', ('partner', '=', self.user_id.partner_id.id), ('user_id', '=', self.user_id.id),
                                 ('state', 'not in', ['old', 'cancel']),
                                 ('group_ids', 'in',
                                  removed_group.ids),
                                 ('id', '!=', self.id)])
                            if not other_lines:
                                removed_group.write({'users': [(3, self.user_id.id)]})

                for added_group in self.group_ids - old_group_ids:
                    if user not in added_group.users:
                        added_group.write({'users': [(4, user.id)]})
                    if self.user_id:
                        if self.user_id not in added_group.users:
                            added_group.write({'users': [(4, self.user_id.id)]})
            elif self.group_ids and not old_group_ids:
                for added_group in self.group_ids:
                    if not user:
                        raise ValidationError(_('No user is linked to the partner %s') % self.partner.name)
                    if user not in added_group.users:
                        added_group.write({'users': [(4, user.id)]})
                    if self.user_id:
                        if self.user_id not in added_group.users:
                            added_group.write({'users': [(4, self.user_id.id)]})
            elif not self.group_ids and old_group_ids:
                for removed_group in old_group_ids:
                    if user in removed_group.users:
                        # Remove only if there is no other membership line with the same group for the current partner
                        other_lines = self.search(
                            ['|', ('partner', '=', user.id), ('user_id', '=', user.id),
                             ('state', 'not in', ['old', 'cancel']),
                             ('group_ids', 'in',
                              removed_group.ids),
                             ('id', '!=', self.id)])
                        if not other_lines:
                            removed_group.write({'users': [(3, user.id)]})
                    if self.user_id:
                        if self.user_id in removed_group.users:
                            # Search other membership line with the same group where the user is the partner
                            other_lines = self.search(
                                ['|', ('partner', '=', self.user_id.partner_id.id), ('user_id', '=', self.user_id.id),
                                 ('state', 'not in', ['old', 'cancel']),
                                 ('group_ids', 'in',
                                  removed_group.ids),
                                 ('id', '!=', self.id)])
                            if not other_lines:
                                removed_group.write({'users': [(3, self.user_id.id)]})

    def create(self, vals):
        for cell in vals:
            if cell['membership_id']:
                membership_group_ids = self.env['product.template'].search(
                    [('id', '=', cell['membership_id'])]).membership_group_ids
                cell['group_ids'] = [(6, 0, membership_group_ids.ids)]
        return super(MembershipLineInherit, self).create(vals)
