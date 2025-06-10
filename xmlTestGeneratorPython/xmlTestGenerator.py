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
        source = f.read()
    return ast.parse(source)

def extract_test_info(node, file_path):
    method_elem = ET.Element("test_method", name=node.name)

    path_elem = ET.SubElement(method_elem, "file_path")
    path_elem.text = file_path

    if not node.body:
        ET.SubElement(method_elem, "empty")
    else:
        for stmt in node.body:
            process_statement(stmt, method_elem)

    return method_elem

def process_statement(stmt, parent_elem):
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        process_call(stmt.value, parent_elem)

    elif isinstance(stmt, ast.Assert):
        process_assert_stmt(stmt, parent_elem)

    elif isinstance(stmt, ast.If):
        if_elem = ET.SubElement(parent_elem, "If")
        for inner_stmt in stmt.body:
            process_statement(inner_stmt, if_elem)
        if stmt.orelse:
            else_elem = ET.SubElement(if_elem, "Else")
            for inner_stmt in stmt.orelse:
                process_statement(inner_stmt, else_elem)

    elif isinstance(stmt, ast.For):
        loop_elem = ET.SubElement(parent_elem, "LoopFor")
        for inner_stmt in stmt.body:
            process_statement(inner_stmt, loop_elem)

    elif isinstance(stmt, ast.While):
        loop_elem = ET.SubElement(parent_elem, "LoopFor")
        for inner_stmt in stmt.body:
            process_statement(inner_stmt, loop_elem)

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

def process_call(call_node, parent_elem):
    if isinstance(call_node.func, ast.Name):
        func_name = call_node.func.id

    elif isinstance(call_node.func, ast.Attribute):
        func_name = call_node.func.attr

    else:
        return

    if func_name.startswith("assert"):
        process_assert_function(func_name, call_node, parent_elem)

    elif func_name == "print":
        args_text = ", ".join([ast.unparse(arg) for arg in call_node.args])
        print_elem = ET.SubElement(parent_elem, "print")
        print_elem.text = args_text

def process_assert_function(name, call_node, parent_elem):
    args = call_node.args

    xml_name_map = {
        "assertEqual": "assertEquals",
        "assertNotEqual": "assertNotEquals",
        "assertListEqual": "assertArrayEquals",
        "assertDictEqual": "assertDictEquals",
    }

    xml_name = xml_name_map.get(name, name)

    assert_elem = ET.SubElement(parent_elem, xml_name)

    two_arg_asserts = (
        "assertEqual", "assertNotEqual", "assertAlmostEqual",
        "assertGreater", "assertLess", "assertListEqual", "assertDictEqual"
    )

    if name in two_arg_asserts:
        if len(args) >= 2:
            expected_elem = ET.SubElement(assert_elem, "expected")
            expected_elem.append(node_to_xml(args[0]))

            actual_elem = ET.SubElement(assert_elem, "actual")
            actual_elem.append(node_to_xml(args[1]))

        if len(args) == 3:
            message_elem = ET.SubElement(assert_elem, "message")
            message_elem.append(node_to_xml(args[2]))

    elif name in ("assertTrue", "assertFalse", "assertIsNone", "assertIsNotNone"):
        if args:
            condition_elem = ET.SubElement(assert_elem, "condition")
            condition_elem.append(node_to_xml(args[0]))

    elif name == "fail":
        message_elem = ET.SubElement(assert_elem, "message")
        if args:
            message_elem.append(node_to_xml(args[0]))
        else:
            message_elem.text = "No message provided"

def process_assert_stmt(stmt, parent_elem):
    assert_elem = ET.SubElement(parent_elem, "assert")
    condition_elem = ET.SubElement(assert_elem, "condition")
    condition_elem.append(node_to_xml(stmt.test))
    if stmt.msg:
        message_elem = ET.SubElement(assert_elem, "message")
        message_elem.append(node_to_xml(stmt.msg))

def node_to_xml(node):
    if isinstance(node, ast.Constant):
        value = node.value
        if isinstance(value, (int, float)):
            elem = ET.Element("literalNumber")
            elem.text = str(value)
        elif isinstance(value, str):
            elem = ET.Element("literalString")
            elem.text = value
        elif value is None:
            elem = ET.Element("literalNone")
            elem.text = "None"
        elif isinstance(value, bool):
            elem = ET.Element("literalBool")
            elem.text = str(value)
        else:
            elem = ET.Element("literalValue")
            elem.text = repr(value)
        return elem

    elif isinstance(node, ast.List):
        elem = ET.Element("literalList")
        for elt in node.elts:
            elem.append(node_to_xml(elt))
        return elem

    elif isinstance(node, ast.Tuple):
        elem = ET.Element("literalTuple")
        for elt in node.elts:
            elem.append(node_to_xml(elt))
        return elem

    elif isinstance(node, ast.Set):
        elem = ET.Element("literalSet")
        for elt in node.elts:
            elem.append(node_to_xml(elt))
        return elem

    elif isinstance(node, ast.Dict):
        elem = ET.Element("literalDict")
        for key, val in zip(node.keys, node.values):
            pair = ET.SubElement(elem, "pair")
            k = node_to_xml(key)
            k.tag = "key"
            v = node_to_xml(val)
            v.tag = "value"
            pair.append(k)
            pair.append(v)
        return elem

    elif isinstance(node, ast.BinOp):
        elem = ET.Element("BinOp", op=type(node.op).__name__)
        elem.append(node_to_xml(node.left))
        elem.append(node_to_xml(node.right))
        return elem

    elif isinstance(node, ast.UnaryOp):
        elem = ET.Element("UnaryOp", op=type(node.op).__name__)
        elem.append(node_to_xml(node.operand))
        return elem

    elif isinstance(node, ast.BoolOp):
        elem = ET.Element("BoolOp", op=type(node.op).__name__)
        for val in node.values:
            elem.append(node_to_xml(val))
        return elem

    elif isinstance(node, ast.Compare):
        elem = ET.Element("Compare")
        elem.append(node_to_xml(node.left))
        for op, comparator in zip(node.ops, node.comparators):
            op_elem = ET.SubElement(elem, "op", type=type(op).__name__)
            op_elem.append(node_to_xml(comparator))
        return elem

    elif isinstance(node, ast.Call):
        elem = ET.Element("Call")
        func_elem = ET.SubElement(elem, "func")
        func_elem.text = ast.unparse(node.func)
        args_elem = ET.SubElement(elem, "args")
        for arg in node.args:
            args_elem.append(node_to_xml(arg))
        return elem

    elif isinstance(node, ast.Attribute):
        elem = ET.Element("Attribute")
        elem.text = ast.unparse(node)
        return elem

    elif isinstance(node, ast.Name):
        elem = ET.Element("Name")
        elem.text = node.id
        return elem

    else:
        elem = ET.Element("expression")
        elem.text = ast.unparse(node)
        return elem

def process_directory(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    tree = parse_python_file(file_path)
                    visitor = TestMethodVisitor()
                    visitor.visit(tree)

                    for method in visitor.test_methods:
                        method_xml = extract_test_info(method, file_path)
                        tree_elem = ET.ElementTree(method_xml)

                        try:
                            ET.indent(tree_elem, space="  ")
                        except AttributeError:
                            pass

                        output_path = os.path.join(output_dir, method.name + ".xml")
                        tree_elem.write(output_path, encoding="utf-8", xml_declaration=True)

                except SyntaxError as e:
                    print(f"Erro de sintaxe em {file_path}: {e}")

if __name__ == "__main__":
    output_dir = "saida"
    process_directory(rf"C:\Users\Denix\Documents\Agnose\teste", output_dir)
    print("Conversão concluída.")
