import unittest
import json
import os
from main import WoWStructParser 
# from modules.modifierHandler import ModifierInterPreter

class TestParser(unittest.TestCase):
    
    def setUp(self):
        """ Förberedelse för varje test. """

        with open("build/18414/json/AUTH_LOGON_CHALLENGE_C.json", "r") as f:
            self.expected_output = json.load(f)
    
    def test_parser(self):
        """ Testa parsern genom att jämföra med förväntat resultat. """
        
        version = 18414
        
        self.ant = 0
        self.succes = 0
        self.failed = 0

        for case_file in os.listdir(f"build/{version}/def"):
            if case_file.endswith(".def"):
                case = case_file.replace(".def", "")
                
                parsed_data = WoWStructParser.parse_case_unittest(version, case)

                with open(f"build/18414/json/{case}.json", "r") as f:
                    self.expected_output = json.load(f)

                self.expected_output = json.dumps(self.expected_output)
                self.ant += 1
                
                try:
                    self.assertEqual(parsed_data, self.expected_output)
                    print(case, end=" ")
                    print("PASSED")
                    self.succes += 1
                except AssertionError as e:
                    print(case, end=" ")
                    print(f"FAILED\n {e}")
                    self.failed += 1
    
    def tearDown(self):
        """ Städning efter varje test (om det behövs). """
        print("\nRESULT")
        print(f"Total : {self.ant} tests")
        print(f"Passed: {self.succes}")
        print(f"Failed: {self.failed}")

if __name__ == '__main__':
    unittest.main()