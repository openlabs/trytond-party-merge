# -*- coding: utf-8 -*-
"""
    tests/test_party.py

    :copyright: (C) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
DIR = os.path.abspath(os.path.normpath(os.path.join(
    __file__, '..', '..', '..', '..', '..', 'trytond'
)))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))
import unittest

if 'DB_NAME' not in os.environ:
    from trytond.config import CONFIG
    CONFIG['db_type'] = 'sqlite'
    os.environ['DB_NAME'] = ':memory:'

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

        self.Party = POOL.get('party.party')

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
