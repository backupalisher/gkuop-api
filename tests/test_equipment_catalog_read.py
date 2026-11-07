"""Чтение справочника и эвристика цифрового поиска."""
from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from services.equipment_catalog import read_catalog_xlsx


def use_inventory_digits_search(search_clean: str) -> bool:
    """Дублирует условие из web_api.main:api_get_tickets."""
    digits_only = re.sub(r'[^\d]', '', search_clean)
    search_has_letters = bool(re.search(r'[A-Za-zА-Яа-яЁё]', search_clean))
    return (not search_has_letters) and len(digits_only) >= 4


class CatalogReadTests(unittest.TestCase):
    def test_reads_address_first_format(self) -> None:
        wb = Workbook()
        ws = wb.active
        ws.append(['Адрес', 'Инвентарный номер', 'Серийный номер', 'Аппарат'])
        ws.append(['ул. Тест', '000740', '3220016942', 'Xerox WorkCentre 3325'])
        ws.append(['ул. Тест', '-', '70155PLM0YFV2', 'Lexmark MX410de'])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'to.xlsx'
            wb.save(path)
            rows = read_catalog_xlsx(path)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['serial_number'], '3220016942')
        self.assertEqual(rows[0]['inventory_number'], '000740')
        self.assertEqual(rows[1]['serial_number'], '70155PLM0YFV2')
        self.assertIsNone(rows[1]['inventory_number'])

    def test_serial_query_does_not_use_digit_fallback(self) -> None:
        self.assertFalse(use_inventory_digits_search('LM0YFV2'))
        self.assertFalse(use_inventory_digits_search('70155PLM0YFV2'))
        self.assertTrue(use_inventory_digits_search('000740'))
        self.assertTrue(use_inventory_digits_search('110134003682'))
        self.assertFalse(use_inventory_digits_search('02'))
        self.assertFalse(use_inventory_digits_search('883'))


if __name__ == '__main__':
    unittest.main()
