# -*- coding: utf-8 -*-
"""
    tests/test_party.py

    :copyright: (C) 2014-2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import unittest
import datetime
from dateutil.relativedelta import relativedelta

from trytond.tests.test_tryton import POOL, USER
from trytond.tests.test_tryton import DB_NAME, CONTEXT
from trytond.transaction import Transaction
import trytond.tests.test_tryton


class TestParty(unittest.TestCase):
    '''
    Test Party
    '''

    def setUp(self):
        """
        Set up data used in the tests.
        this method is called before each test function execution.
        """
        trytond.tests.test_tryton.install_module('party_merge')
        trytond.tests.test_tryton.install_module('account_invoice_history')

        self.Party = POOL.get('party.party')
        self.Address = POOL.get('party.address')
        self.Company = POOL.get('company.company')
        self.Country = POOL.get('country.country')
        self.Subdivision = POOL.get('country.subdivision')
        self.Currency = POOL.get('currency.currency')
        self.Employee = POOL.get('company.employee')
        self.Currency = POOL.get('currency.currency')
        self.Invoice = POOL.get('account.invoice')
        self.Account = POOL.get('account.account')
        self.Journal = POOL.get('account.journal')
        self.User = POOL.get('res.user')

    def setup_defaults(self):
        """Creates default data for testing
        """
        self.currency, = self.Currency.create([{
            'name': 'US Dollar',
            'code': 'USD',
            'symbol': '$',
        }])

        with Transaction().set_context(company=None):
            company_party, = self.Party.create([{
                'name': 'openlabs'
            }])
            employee_party, = self.Party.create([{
                'name': 'Jim'
            }])

        self.company, = self.Company.create([{
            'party': company_party,
            'currency': self.currency,
        }])

        self.employee, = self.Employee.create([{
            'party': employee_party.id,
            'company': self.company.id,
        }])

        self.User.write([self.User(USER)], {
            'company': self.company,
            'main_company': self.company,
            'employees': [('add', [self.employee.id])],
        })
        # Write employee separately as employees needs to be saved first
        self.User.write([self.User(USER)], {
            'employee': self.employee.id,
        })

        CONTEXT.update(self.User.get_preferences(context_only=True))

        # Create Fiscal Year
        self._create_fiscal_year(company=self.company.id)
        # Create Chart of Accounts
        self._create_coa_minimal(company=self.company.id)
        # Create a payment term
        self.payment_term, = self._create_payment_term()
        self.cash_journal, = self.Journal.search(
            [('type', '=', 'cash')], limit=1
        )

        self.country, = self.Country.create([{
            'name': 'United States of America',
            'code': 'US',
        }])

        self.subdivision, = self.Subdivision.create([{
            'country': self.country.id,
            'name': 'California',
            'code': 'CA',
            'type': 'state',
        }])

    def _create_fiscal_year(self, date=None, company=None):
        """
        Creates a fiscal year and requried sequences
        """
        FiscalYear = POOL.get('account.fiscalyear')
        Sequence = POOL.get('ir.sequence')
        SequenceStrict = POOL.get('ir.sequence.strict')
        Company = POOL.get('company.company')

        if date is None:
            date = datetime.date.today()

        if company is None:
            company, = Company.search([], limit=1)

        invoice_sequence, = SequenceStrict.create([{
            'name': '%s' % date.year,
            'code': 'account.invoice',
            'company': company,
        }])
        fiscal_year, = FiscalYear.create([{
            'name': '%s' % date.year,
            'start_date': date + relativedelta(month=1, day=1),
            'end_date': date + relativedelta(month=12, day=31),
            'company': company,
            'post_move_sequence': Sequence.create([{
                'name': '%s' % date.year,
                'code': 'account.move',
                'company': company,
            }])[0],
            'out_invoice_sequence': invoice_sequence,
            'in_invoice_sequence': invoice_sequence,
            'out_credit_note_sequence': invoice_sequence,
            'in_credit_note_sequence': invoice_sequence,
        }])
        FiscalYear.create_period([fiscal_year])
        return fiscal_year

    def _create_coa_minimal(self, company):
        """Create a minimal chart of accounts
        """
        AccountTemplate = POOL.get('account.account.template')
        Account = POOL.get('account.account')

        account_create_chart = POOL.get(
            'account.create_chart', type="wizard")

        account_template, = AccountTemplate.search(
            [('parent', '=', None)]
        )

        session_id, _, _ = account_create_chart.create()
        create_chart = account_create_chart(session_id)
        create_chart.account.account_template = account_template
        create_chart.account.company = company
        create_chart.transition_create_account()

        receivable, = Account.search([
            ('kind', '=', 'receivable'),
            ('company', '=', company),
        ])
        payable, = Account.search([
            ('kind', '=', 'payable'),
            ('company', '=', company),
        ])
        create_chart.properties.company = company
        create_chart.properties.account_receivable = receivable
        create_chart.properties.account_payable = payable
        create_chart.transition_create_properties()

    def _get_account_by_kind(self, kind, company=None, silent=True):
        """Returns an account with given spec
        :param kind: receivable/payable/expense/revenue
        :param silent: dont raise error if account is not found
        """

        if company is None:
            company, = self.Company.search([], limit=1)

        accounts = self.Account.search([
            ('kind', '=', kind),
            ('company', '=', company)
        ], limit=1)
        if not accounts and not silent:
            raise Exception("Account not found")
        return accounts[0] if accounts else False

    def _create_payment_term(self):
        """Create a simple payment term with all advance
        """
        PaymentTerm = POOL.get('account.invoice.payment_term')

        return PaymentTerm.create([{
            'name': 'Direct',
            'lines': [('create', [{'type': 'remainder'}])]
        }])

    def test0005_merge_parties(self):
        """Test party merge function.
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            party1, party2, party3 = self.Party.create([{
                'name': 'Party 1',
                'addresses': [('create', [{
                    'name': 'party1',
                    'street': 'ST2',
                    'city': 'New Delhi',
                }])]
            }, {
                'name': 'Party 2',
                'addresses': [('create', [{
                    'name': 'party2',
                    'street': 'ST2',
                    'city': 'Mumbai',
                }])]
            }, {
                'name': 'Party 3',
                'addresses': [('create', [{
                    'name': 'party3',
                    'street': 'ST2',
                    'city': 'New Delhi',
                }])]
            }])

            # Merge party2, party3 to party1
            party2.merge_into(party1)
            party3.merge_into(party1)

            self.assertEqual(len(party1.addresses), 3)

    def test0010_merge_party_historization(self):
        """
        Test that the historization feature doesn't break after party merge
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as txn:
            self.setup_defaults()

            party1, party2, party3 = self.Party.create([{
                'name': 'John Doe',
                'addresses': [('create', [{
                    'name': 'party1',
                    'street': 'ST2',
                    'city': 'New Delhi',
                    'invoice': True,
                }])]
            }, {
                'name': 'Jane Doe',
                'addresses': [('create', [{
                    'name': 'party2',
                    'street': 'ST2',
                    'city': 'Mumbai',
                    'invoice': True,
                }])],
            }, {
                'name': 'Party 3',
                'addresses': [('create', [{
                    'name': 'party3',
                    'street': 'ST2',
                    'city': 'New Delhi',
                }])],
            }])

            journal, = self.Journal.search([('name', '=', 'Revenue')])

            with Transaction().set_context({'company': self.company.id}):
                self.Invoice.create([{
                    'party': party1.id,
                    'invoice_address': party1.addresses[0],
                    'journal': journal.id,
                    'payment_term': self._create_payment_term()[0].id,
                    'currency': self.currency.id,
                    'account': self._get_account_by_kind('receivable').id,
                }, {
                    'party': party2.id,
                    'invoice_address': party2.addresses[0],
                    'journal': journal.id,
                    'payment_term': self._create_payment_term()[0].id,
                    'currency': self.currency.id,
                    'account': self._get_account_by_kind('receivable').id,
                }])

            # Merge party1, party2 into party3
            party1.merge_into(party3)
            party2.merge_into(party3)

            # Try out in Party's history table
            PartyHistory = self.Party.__table_history__()
            cursor = txn.cursor

            cursor.execute(*(PartyHistory.select(PartyHistory.id)))

            id_list = map(
                lambda x: x[0],
                cursor.fetchall()
            )

            self.assertNotIn(party1.id, id_list)
            self.assertNotIn(party2.id, id_list)
            self.assertIn(party3.id, id_list)

            # Try out in address's history table
            AddressHistory = self.Address.__table_history__()

            cursor.execute(*(AddressHistory.select(AddressHistory.party)))

            id_list = map(
                lambda x: x[0],
                cursor.fetchall()
            )

            self.assertNotIn(party1.id, id_list)
            self.assertNotIn(party2.id, id_list)
            self.assertIn(party3.id, id_list)


def suite():
    """
    Define suite
    """
    test_suite = trytond.tests.test_tryton.suite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestParty)
    )
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
