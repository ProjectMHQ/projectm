import unittest

from core.src.world.systems.library.validator import LibraryJSONFileValidator


class TestLibraryCombinators(unittest.TestCase):
    def test_library_combinator(self):
        test1 = {
            "libname": "spadone",
            "components": {
                "attributes": {
                    "keyword": "spadone",
                    "name": "Uno spadone ammaccato",
                    "description": "E' certamente uno degli spadoni più malandati che tu abbia mai visto.",
                    "collectible": True
                }
            }
        }
        LibraryJSONFileValidator(test1)
