# -*- coding: utf-8 -*-
"""
    party.py

    :copyright: (c) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import ModelView, fields
from trytond.transaction import Transaction
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval
from trytond.wizard import Wizard, StateView, StateTransition, Button

__metaclass__ = PoolMeta
__all__ = ['Party', 'PartyMergeView', 'PartyMerge']


class Party:
    __name__ = 'party.party'

    def merge_into(self, target):
        """Merge current record to target party.
        """
        ModelField = Pool().get('ir.model.field')

        # Inactive party first
        self.active = False
        self.save()

        cursor = Transaction().cursor

        if self._history:
            # Update the party history first.
            #
            # The approach is to make the history of all merged records
            # also the history of the target record.
            party_history_table = self.__table_history__()
            cursor.execute(
                *party_history_table.update(
                    columns=[party_history_table.id],
                    values=[target.id],
                    where=(party_history_table.id == self.id)
                )
            )

        party_fields = ModelField.search([
            ('relation', '=', 'party.party'),
            ('ttype', '=', 'many2one'),
        ])
        for field in party_fields:
            Model = Pool().get(field.model.model)

            if isinstance(getattr(Model, field.name), fields.Function):
                continue

            if not hasattr(Model, '__table__'):
                continue

            sql_table = Model.__table__()

            # Update direct foreign key references
            cursor.execute(*sql_table.update(
                columns=[getattr(sql_table, field.name)], values=[target.id],
                where=(getattr(sql_table, field.name) == self.id)
            ))
            if Model._history:
                # If historization is enabled on the model
                # then the party value in the history should
                # now point to the target party id since the
                # history of the current party is already the history of
                # target party.
                history_table = Model.__table_history__()
                cursor.execute(*history_table.update(
                    columns=[getattr(history_table, field.name)],
                    values=[target.id],
                    where=(getattr(history_table, field.name) == self.id)
                ))


class PartyMergeView(ModelView):
    'Party Merge'
    __name__ = 'party.party.merge.view'

    duplicates = fields.One2Many(
        'party.party', None, "Duplicates", readonly=True,
    )
    target = fields.Many2One(
        'party.party', 'Target', required=True,
        domain=[('id', 'not in', Eval('duplicates'))],
        depends=['duplicates'],
    )


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

    def default_merge(self, fields):
        return {
            'duplicates': Transaction().context['active_ids'],
        }

    def transition_result(self):
        for party in self.merge.duplicates:
            party.merge_into(self.merge.target)

        return 'end'
