import xml.etree.ElementTree as ET
import os
import re
import csv

class Detector:
    def __init__(self, dir_alvo):
        self.folder = os.path.join(dir_alvo, "saida")
        self.csv_file = 'output.csv'
        self.read_xml_files_from_folder()

    def process_xml(self, xml_file, csv_writer):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # LÓGICA UNIVERSAL DE DETECÇÃO DE MÉTODOS 
            # Se a própria raiz for um 'test_method' (Padrão Python/Java), usamos ela.
            # Se não, buscamos todos os 'test_method' dentro da árvore (Padrão Node).
            if root.tag == 'test_method':
                methods = [root]
            else:
                methods = root.findall('.//test_method')
            
            if not methods:
                print(f"⚠️ Aviso: Nenhum 'test_method' encontrado em {xml_file}")
                return

            for method in methods:
                method_name = method.attrib.get('name', 'Unknown')
                
                print_count = len(method.findall('.//print'))

                duplicates = self.detect_duplicate_asserts(method)
                duplicate_count = "Yes" if duplicates == "Yes" else "No"

                asserts_without_message = self.detect_assertion_roulette(method)

                unknown_test = self.detect_unknown_test(method)

                empty_test_count = self.detect_empty_test(method)

                literal_count = sum(
                    self.count_literals_in_expression(assert_elem.attrib.get('expected', '')) +
                    self.count_literals_in_expression(assert_elem.attrib.get('actual', ''))
                    for assert_elem in method.findall('.//assertEquals')
                )

                exception_count = len(method.findall('.//try'))
                if_count = len(method.findall('.//If'))
                else_count = len(method.findall('.//else'))
                for_loop_count = len(method.findall('.//LoopFor'))
                conditional_count = if_count + else_count + for_loop_count

                # Escreve a linha no CSV
                csv_writer.writerow([
                    method_name,
                    literal_count,
                    print_count,
                    duplicate_count,
                    "Yes" if asserts_without_message else "No",
                    "Yes" if unknown_test and empty_test_count == 0 else "No",
                    "Yes" if empty_test_count != 0 else "No",
                    exception_count,
                    conditional_count
                ])

        except ET.ParseError as e:
            print(f"Error parsing XML file: {xml_file}\nError: {e}")

    def detect_duplicate_asserts(self, method_root):
        asserts = set()
        duplicates = False
        for assert_elem in method_root.findall('.//assertEquals'):
            expected = assert_elem.attrib.get('expected', '')
            actual = assert_elem.attrib.get('actual', '')
            key = (self.normalize_assert_expression(expected), self.normalize_assert_expression(actual))
            if key in asserts:
                duplicates = True
                break
            asserts.add(key)
        return "Yes" if duplicates else "No"

    def normalize_assert_expression(self, expression):
        return re.sub(r'world.tile\(\d+, \d+\)', 'world.tile()', expression)

    def detect_assertion_roulette(self, method_root):
        asserts_without_message = 0
        assert_count = 0
        for assert_elem in method_root.findall('.//assertEquals'):
            message = assert_elem.attrib.get('message', '')
            assert_count += 1
            if not message:
                asserts_without_message += 1
        return asserts_without_message > 1 and assert_count > 1

    def detect_unknown_test(self, method_root):
        assert_types = ['assertEquals', 'assertNotEquals', 'assertTrue', 'assertFalse', 
                        'assertNull', 'assertNotNull', 'assertArrayEquals', 
                        'assertSame', 'assertNotSame', 'fail']
        has_assertions = any(len(method_root.findall(f'.//{assert_type}')) > 0 for assert_type in assert_types)
        test_expected = method_root.find('.//Test') is not None and \
                        method_root.find('.//Test').get('expected') is not None
        return not has_assertions and not test_expected

    def detect_empty_test(self, method_root):
        return sum(1 for empty_elem in method_root.findall('.//empty'))

    def count_literals_in_expression(self, expression):
        literals_count = 0
        literals_count += len(re.findall(r'<literalNumber>(\d+)</literalNumber>', expression))
        literals_count += len(re.findall(r'<literalString>(.*?)</literalString>', expression))
        return literals_count

    def read_xml_files_from_folder(self):
        if not os.path.exists(self.folder):
            print(f"The self.folder {self.folder} was not found.")
            return
        
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as output_csv:
            csv_writer = csv.writer(output_csv)
            csv_writer.writerow(["Tested Method", "Magic Literal", "Redundant Print", "Duplicated Assert", 
                                "Assertion Roulette", "Unknown Test", "Empty Test", "Number of Exceptions", 
                                "Number of Conditionals"])

            for filename in os.listdir(self.folder):
                if filename.endswith(".xml"):
                    full_path = os.path.join(self.folder, filename)
                    print(f"Reading file: {full_path}")
                    self.process_xml(full_path, csv_writer)