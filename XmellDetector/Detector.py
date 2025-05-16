import xml.etree.ElementTree as ET
import os
import re
import csv

class Detector:
    def __init__(self,dir):
        self.folder = rf"{str(dir)+"\saida"}"
        self.csv_file = 'output.csv'
        self.read_xml_files_from_folder()

    def process_xml(self,xml_file, csv_writer):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            method_name = root.attrib.get('name', 'Unknown')
            print_count = len(root.findall('.//print'))

            duplicates = self.detect_duplicate_asserts(root)
            duplicate_count = "Yes" if duplicates == "Yes" else "No"  # Modificado para 'Yes' ou 'No'

            asserts_without_message = self.detect_assertion_roulette(root)

            unknown_test = self.detect_unknown_test(root)

            empty_test_count = self.detect_empty_test(root)

            literal_count = sum(
                self.count_literals_in_expression(assert_elem.attrib.get('expected', '')) +
                self.count_literals_in_expression(assert_elem.attrib.get('actual', ''))
                for assert_elem in root.findall('.//assertEquals')
            )

            exception_count = len(root.findall('.//try'))
            if_count = len(root.findall('.//If'))
            else_count = len(root.findall('.//else'))
            for_loop_count = len(root.findall('.//LoopFor'))
            conditional_count = if_count + else_count + for_loop_count

            csv_writer.writerow([method_name,
                                literal_count,
                                print_count,
                                duplicate_count,  # Agora vai ser 'Yes' ou 'No'
                                "Yes" if asserts_without_message else "No",
                                "Yes" if unknown_test and empty_test_count == 0 else "No",
                                "Yes" if empty_test_count != 0 else "No",
                                exception_count,
                                conditional_count])
        except ET.ParseError as e:
            print(f"Error parsing XML file: {xml_file}\nError: {e}")

    def detect_duplicate_asserts(self,root):
        asserts = set()
        duplicates = False  # Inicializamos como False, indicando que não há duplicação.

        for assert_elem in root.findall('.//assertEquals'):
            expected = assert_elem.attrib.get('expected', '')
            actual = assert_elem.attrib.get('actual', '')

            # Normalizar expressões, se necessário
            expected_normalized = self.normalize_assert_expression(expected)
            actual_normalized = self.normalize_assert_expression(actual)

            key = (expected_normalized, actual_normalized)

            if key in asserts:
                duplicates = True  # Encontrou duplicação, alteramos para True
                break  # Podemos interromper a busca, pois já encontramos duplicação
            else:
                asserts.add(key)

        return "Yes" if duplicates else "No"

    def normalize_assert_expression(self, expression):
        # Normalizar a expressão removendo detalhes como coordenadas de 'tile'
        expression = re.sub(r'world.tile\(\d+, \d+\)', 'world.tile()', expression)
        return expression

    def detect_assertion_roulette(self,root):
        asserts_without_message = 0
        assert_count = 0

        for assert_elem in root.findall('.//assertEquals'):
            message = assert_elem.attrib.get('message', '')
            assert_count += 1

            if not message:
                asserts_without_message += 1

        return asserts_without_message > 1 and assert_count > 1

    def detect_unknown_test(self,root):
        assert_types = ['assertEquals', 'assertNotEquals', 'assertTrue', 'assertFalse', 
                        'assertNull', 'assertNotNull', 'assertArrayEquals', 
                        'assertSame', 'assertNotSame', 'fail']
        
        has_assertions = any(len(root.findall(f'.//{assert_type}')) > 0 for assert_type in assert_types)

        test_expected = root.find('.//Test') is not None and \
                    root.find('.//Test').get('expected') is not None

        return not has_assertions and not test_expected

    def detect_empty_test(self,root):
        empty_test_count = sum(1 for empty_elem in root.findall('.//empty') if empty_elem.tag == 'empty')
        
        return empty_test_count



    def count_literals_in_expression(self,expression):
        literals_count = 0
        literals_count += len(re.findall(r'<literalNumber>(\d+)</literalNumber>', expression))
        literals_count += len(re.findall(r'<literalString>(.*?)</literalString>', expression))
        return literals_count

    def read_xml_files_from_folder(self):
        if not os.path.exists(self.folder):
            print(f"The self.folder {self.folder} was not found.")
            return
        
        with open(self.csv_file, 'w', newline='') as output_csv:
            csv_writer = csv.writer(output_csv)
            csv_writer.writerow(["Tested Method", "Magic Literal", "Redundant Print", "Duplicated Assert", 
                                "Assertion Roulette", "Unknown Test", "Empty Test", "Number of Exceptions", 
                                "Number of Conditionals"])

            for filename in os.listdir(self.folder):
                if filename.endswith(".xml"):
                    full_path = os.path.join(self.folder, filename)
                    print(f"Reading file: {full_path}")
                    self.process_xml(full_path, csv_writer)
if __name__ == "__main__":
    Detector()