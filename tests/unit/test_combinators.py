import unittest

from core.src.world.systems.library.validator import LibraryJSONFileValidator


class TestCombinators(unittest.TestCase):
    def test_library_combinator(self):
        test1 = {
            "alias": "spadone",
            "components": {
                "attributes": {
                    "keyword": "spadone",
                    "name": "Uno spadone ammaccato",
                    "description": "E' certamente uno degli spadoni più malandati che tu abbia mai visto."
                },
                "weapon": "broadsword"
            }
        }
        LibraryJSONFileValidator(test1)

    def test_library_combinator2(self):
        test1 = {
            "alias": "spadone",
            "components": {
                "attributes": {
                    "keyword": "spadone",
                    "name": "Uno spadone ammaccato",
                    "description": "E' certamente uno degli spadoni più malandati che tu abbia mai visto."
                },
                "weapon": "antani"
            }
        }
        with self.assertRaises(ValueError) as e:
            LibraryJSONFileValidator(test1)
            self.assertEqual(str(e), "ValueError: 'antani' is not a valid WeaponType")
