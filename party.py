# -*- coding: utf-8 -*-
"""
    party.py

    :copyright: (c) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import ModelView, fields
from trytond.transaction import Transaction
from trytond.pool import PoolMeta, Pool
from trytond.wizard import Wizard, StateView, StateTransition, Button

__metaclass__ = PoolMeta
__all__ = ['Party', 'PartyMergeView', 'PartyMerge']


class Party:
    __name__ = 'party.party'

    def merge_into(self, target):
        """Merge current record to target party.
        """
        Party = Pool().get('party.party')
        ModelField = Pool().get('ir.model.field')

        party_fields = ModelField.search([
            ('relation', '=', 'party.party'),
            ('ttype', '=', 'many2one'),
        ])

        # Inactive current record first
        self.active = False
        self.save()

        cursor = Transaction().cursor

        for field in party_fields:
            Model = Pool().get(field.model.model)

            if isinstance(getattr(Model, field.name), fields.Function):
                continue

            if not hasattr(Model, '__table__'):
                continue

            sql_table = Model.__table__()

            cursor.execute(*sql_table.update(
                columns=[getattr(sql_table, field.name)], values=[target.id],
                where=(getattr(sql_table, field.name) == self.id)
            ))

        # Finally delete the party.
        Party.delete([self])


class PartyMergeView(ModelView):
    'Party Merge'
    __name__ = 'party.party.merge.view'

    target = fields.Many2One('party.party', 'Target', required=True)


class PartyMerge(Wizard):
    __name__ = 'party.party.merge'
    start_state = 'merge'

    merge = StateView(
        'party.party.merge.view',
        'party_merge.party_merge_view', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('OK', 'result', 'tryton-ok'),
        ]
    )
    result = StateTransition()

    def transition_result(self):
        Party = Pool().get('party.party')

        for party in Party.browse(Transaction().context['active_ids']):
            party.merge_into(self.merge.target)

        return 'end'
