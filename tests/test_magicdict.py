from django.test import TestCase
from collections import OrderedDict
from billserve.networking.models.MagicDict import MagicDict


class MagicDictTestCase(TestCase):
    def setUp(self):
        self.data = OrderedDict({'name': 'Brian',
                                 'car': OrderedDict({'manufacturer': 'Volkswagon',
                                                     'model': 'Jetta',
                                                     'year': 2009}),
                                 'phones': OrderedDict({'item': [
                                     OrderedDict({'name': 'iPhone 6'}),
                                     OrderedDict({'name': 'iPhone 7'}),
                                     OrderedDict({'name': 'iPhone 8'})
                                 ]})
                                 })
        self.magic_dict = MagicDict(self.data, ['name', 'car', 'phones'], ['sid'])

    def test_cleaned(self):
        cleaned = self.magic_dict.cleaned()

        self.assertEqual(cleaned['name'], 'Brian')
        self.assertEqual(cleaned['car'], {'manufacturer': 'Volkswagon', 'model': 'Jetta', 'year': 2009})
        self.assertEqual(cleaned['phones'], [{'name': 'iPhone 6'}, {'name': 'iPhone 7'}, {'name': 'iPhone 8'}])
        self.assertEqual(cleaned['sid'], None)
