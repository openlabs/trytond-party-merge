# -*- coding: utf-8 -*-
"""
    __init__.py

    :copyright: (c) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import Pool

from party import Party, PartyMergeView, PartyMerge


def register():
    Pool.register(
        Party,
        PartyMergeView,
        module='party_merge', type_='model'
    )
    Pool.register(
        PartyMerge,
        module='party_merge', type_='wizard'
    )
