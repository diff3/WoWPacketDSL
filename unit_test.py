import unittest
import json
import os
from main import WoWStructParser 
from main import ModifierOperator 

class TestParser(unittest.TestCase):
    
    def setUp(self):
        """ Förberedelse för varje test. """

        with open("build/18414/json/AUTH_LOGON_CHALLENGE_C.json", "r") as f:
            self.expected_output = json.load(f)
    
    def test_parser(self):
        """ Testa parsern genom att jämföra med förväntat resultat. """
        
        # Kör parsern med data
        version = 18414
        # case = "AUTH_LOGON_CHALLENGE_C"

        # Jämför det faktiska resultatet med det förväntade resultatet
        
        for case_file in os.listdir(f"build/{version}/def"):
            if case_file.endswith(".def"):
                case = case_file.replace(".def", "")
                
                print(case)
                
                parsed_data = WoWStructParser.parse_case_unittest(version, case)

                with open(f"build/18414/json/{case}.json", "r") as f:
                    self.expected_output = json.load(f)

                self.assertEqual(parsed_data, self.expected_output)
    
    def tearDown(self):
        """ Städning efter varje test (om det behövs). """
        pass

if __name__ == '__main__':
    unittest.main()