import ast
import os
import xml.etree.ElementTree as ET

class TestMethodVisitor(ast.NodeVisitor):
    def __init__(self):
        self.test_methods = []

    def visit_FunctionDef(self, node):
        if any(isinstance(d, ast.Name) and d.id == 'test' for d in node.decorator_list) or node.name.startswith("test"):
            self.test_methods.append(node)
        self.generic_visit(node)

def parse_python_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return ast.parse(f.read())

def extract_test_info(node, file_path):
    method_elem = ET.Element("test_method", name=node.name)
    ET.SubElement(method_elem, "file_path").text = file_path

    # Verifica se o método é vazio ou contém apenas 'pass'
    if not node.body or (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
        ET.SubElement(method_elem, "empty")
    else:
        for stmt in node.body:
            process_statement(stmt, method_elem)

    return method_elem

def xml_fragment_to_string(elem):
    return ET.tostring(elem, encoding="unicode").strip()

def node_to_xml(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            literal = ET.Element("literalNumber")
            literal.text = str(node.value)
            return [literal]
        elif isinstance(node.value, str):
            literal = ET.Element("literalString")
            literal.text = node.value
            return [literal]
        else:
            generic = ET.Element("literal")
            generic.text = str(node.value)
            return [generic]

    elif isinstance(node, ast.BinOp):
        parts = []
        parts.extend(node_to_xml(node.left))
        op = ast.unparse(node.op)
        parts.append(ET.Element("op", value=op))
        parts.extend(node_to_xml(node.right))
        return parts

    elif isinstance(node, ast.List):
        list_elem = ET.Element("list")
        for elt in node.elts:
            list_elem.extend(node_to_xml(elt))
        return [list_elem]

    elif isinstance(node, ast.Dict):
        dict_elem = ET.Element("dict")
        for k, v in zip(node.keys, node.values):
            pair = ET.SubElement(dict_elem, "pair")
            key_elem = ET.SubElement(pair, "key")
            key_elem.extend(node_to_xml(k))
            value_elem = ET.SubElement(pair, "value")
            value_elem.extend(node_to_xml(v))
        return [dict_elem]

    elif isinstance(node, ast.Call):
        call_elem = ET.Element("call")
        call_elem.set("function", ast.unparse(node.func))
        for arg in node.args:
            call_elem.extend(node_to_xml(arg))
        return [call_elem]

    else:
        raw = ET.Element("expr")
        raw.text = ast.unparse(node)
        return [raw]

def process_call(call_node, parent_elem):
    func_name = call_node.func.id if isinstance(call_node.func, ast.Name) else (
        call_node.func.attr if isinstance(call_node.func, ast.Attribute) else None
    )
    if func_name is None:
        return

    if func_name.startswith("assert"):
        process_assert_function(func_name, call_node, parent_elem)
    elif func_name == "print":
        print_elem = ET.SubElement(parent_elem, "print")
        for arg in call_node.args:
            print_elem.extend(node_to_xml(arg))

def process_assert_function(name, call_node, parent_elem):
    args = call_node.args
    xml_name_map = {
        "assert": "assertEquals",
        "assertEqual": "assertEquals",
        "assertNotEqual": "assertNotEquals",
        "assertListEqual": "assertArrayEquals",
        "assertDictEqual": "assertDictEquals",
    }
    xml_name = xml_name_map.get(name, name)
    attribs = {}

    if name in {
        "assertEqual", "assertNotEqual", "assertListEqual", "assertDictEqual",
        "assertAlmostEqual", "assertGreater", "assertLess"
    } and len(args) >= 2:
        expected_xml = node_to_xml(args[0])[0]
        actual_xml = node_to_xml(args[1])[0]
        attribs["expected"] = xml_fragment_to_string(expected_xml)
        attribs["actual"] = xml_fragment_to_string(actual_xml)

        if len(args) == 3:
            message_xml = node_to_xml(args[2])[0]
            attribs["message"] = xml_fragment_to_string(message_xml)

    elif name in {"assertTrue", "assertFalse", "assertIsNone", "assertIsNotNone"} and args:
        cond_xml = node_to_xml(args[0])[0]
        attribs["condition"] = xml_fragment_to_string(cond_xml)

    elif name == "fail":
        msg_elem = node_to_xml(args[0])[0] if args else ET.Element("literalString")
        if not args:
            msg_elem.text = "No message provided"
        attribs["message"] = xml_fragment_to_string(msg_elem)

    ET.SubElement(parent_elem, xml_name, attribs)

def process_assert_stmt(stmt, parent_elem):
    cond_str = ast.unparse(stmt.test)
    attribs = {"condition": cond_str}
    if stmt.msg:
        msg_xml = node_to_xml(stmt.msg)[0]
        attribs["message"] = xml_fragment_to_string(msg_xml)
    ET.SubElement(parent_elem, "assertEquals", attribs)

def process_statement(stmt, parent_elem):
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        process_call(stmt.value, parent_elem)

    elif isinstance(stmt, ast.Assert):
        process_assert_stmt(stmt, parent_elem)

    elif isinstance(stmt, ast.If):
        condition_str = ast.unparse(stmt.test)
        if_elem = ET.SubElement(parent_elem, "If", condition=condition_str)
        for s in stmt.body:
            process_statement(s, if_elem)
        if stmt.orelse:
            else_elem = ET.SubElement(if_elem, "Else")
            for s in stmt.orelse:
                process_statement(s, else_elem)

    elif isinstance(stmt, ast.While):
        condition_str = ast.unparse(stmt.test)
        while_elem = ET.SubElement(parent_elem, "loopFor", condition=condition_str)
        for s in stmt.body:
            process_statement(s, while_elem)

    elif isinstance(stmt, ast.For):
        loop_elem = ET.SubElement(parent_elem, "For", condition=ast.unparse(stmt.target))
        for s in stmt.body:
            process_statement(s, loop_elem)

    elif isinstance(stmt, ast.Try):
        try_elem = ET.SubElement(parent_elem, "try")
        for s in stmt.body:
            process_statement(s, try_elem)
        for handler in stmt.handlers:
            catch_elem = ET.SubElement(try_elem, "catch", type=ast.unparse(handler.type) if handler.type else "Exception")
            for s in handler.body:
                process_statement(s, catch_elem)
        if stmt.finalbody:
            finally_elem = ET.SubElement(try_elem, "finally")
            for s in stmt.finalbody:
                process_statement(s, finally_elem)

def process_directory(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    tree = parse_python_file(path)
                    visitor = TestMethodVisitor()
                    visitor.visit(tree)

                    for method in visitor.test_methods:
                        method_xml = extract_test_info(method, path)
                        tree_elem = ET.ElementTree(method_xml)
                        try:
                            ET.indent(tree_elem, space="  ")
                        except AttributeError:
                            pass
                        out_path = os.path.join(output_dir, method.name + ".xml")
                        tree_elem.write(out_path, encoding="utf-8", xml_declaration=True)

                        

                except SyntaxError as e:
                    print(f"Erro de sintaxe em {path}: {e}")

# if __name__ == "__main__":
#     output_dir = "saida"
#     input_dir = r"C:\Users\Denix\Documents\Agnose\teste"
#     process_directory(input_dir, output_dir)
#     print("Conversão concluída.")
