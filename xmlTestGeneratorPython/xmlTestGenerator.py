import ast
import os
import xml.etree.ElementTree as ET

class TestMethodVisitor(ast.NodeVisitor):
    def __init__(self):
        self.test_methods = []

    def visit_FunctionDef(self, node):
        if node.name.startswith("test") or any(isinstance(d, ast.Name) and d.id == "test" for d in node.decorator_list):
            self.test_methods.append(node)
        self.generic_visit(node)

def parse_python_file(path):
    with open(path, encoding="utf-8") as f:
        return ast.parse(f.read())

def xml_str(e): 
    return ET.tostring(e, encoding="unicode").strip()

def node_to_xml(node):
    if isinstance(node, ast.Constant):
        tag = "literalNumber" if isinstance(node.value, (int,float)) else "literalString" if isinstance(node.value,str) else "literal"
        e = ET.Element(tag)
        e.text = str(node.value)
        return [e]
    elif isinstance(node, ast.BinOp):
        return node_to_xml(node.left) + [ET.Element("op", value=ast.unparse(node.op))] + node_to_xml(node.right)
    elif isinstance(node, ast.Compare):
        parts = node_to_xml(node.left)
        for op, comp in zip(node.ops, node.comparators):
            parts.append(ET.Element("op", value=ast.unparse(op)))
            parts.extend(node_to_xml(comp))
        return parts
    elif isinstance(node, ast.List):
        e = ET.Element("list")
        for elt in node.elts: e.extend(node_to_xml(elt))
        return [e]
    elif isinstance(node, ast.Dict):
        e = ET.Element("dict")
        for k,v in zip(node.keys,node.values):
            pair = ET.SubElement(e,"pair")
            key = ET.SubElement(pair,"key"); key.extend(node_to_xml(k))
            val = ET.SubElement(pair,"value"); val.extend(node_to_xml(v))
        return [e]
    elif isinstance(node, ast.Set):
        e = ET.Element("set")
        for elt in node.elts: e.extend(node_to_xml(elt))
        return [e]
    elif isinstance(node, ast.Call):
        e = ET.Element("call", function=ast.unparse(node.func))
        for arg in node.args: e.extend(node_to_xml(arg))
        return [e]
    else:
        e = ET.Element("expr")
        e.text = ast.unparse(node)
        return [e]

def create_assert(parent, tag="assertEquals", **attribs):
    ET.SubElement(parent, tag, attribs)

def process_assert(node, parent):
    # Pytest assert
    if isinstance(node, ast.Assert):
        test = node.test
        if isinstance(test, ast.Compare) and len(test.ops)==1 and isinstance(test.ops[0], ast.Eq):
            expected = "".join(xml_str(p) for p in node_to_xml(test.left))
            actual = "".join(xml_str(p) for p in node_to_xml(test.comparators[0]))
            attribs = {"expected": expected, "actual": actual}
            if node.msg: attribs["message"] = xml_str(node_to_xml(node.msg)[0])
            create_assert(parent, "assertEquals", **attribs)
        else:
            attribs = {"actual": "".join(xml_str(p) for p in node_to_xml(test))}
            create_assert(parent, "assertEquals", **attribs)
    # Unittest assert*
    elif isinstance(node, ast.Call):
        func_name = getattr(node.func, 'id', getattr(node.func,'attr', None))
        if not func_name or not func_name.startswith("assert"): return
        tag_map = {"assert":"assertEquals","assertEqual":"assertEquals","assertNotEqual":"assertNotEquals",
                   "assertListEqual":"assertArrayEquals","assertDictEqual":"assertDictEquals"}
        xml_tag = tag_map.get(func_name, func_name)
        attribs = {}
        if func_name in {"assertEqual","assertNotEqual","assertListEqual","assertDictEqual"} and len(node.args)>=2:
            attribs["expected"] = xml_str(node_to_xml(node.args[0])[0])
            attribs["actual"] = xml_str(node_to_xml(node.args[1])[0])
            if len(node.args)==3: attribs["message"]=xml_str(node_to_xml(node.args[2])[0])
        elif func_name in {"assertTrue","assertFalse","assertIsNone","assertIsNotNone"} and node.args:
            attribs["actual"]="".join(xml_str(p) for p in node_to_xml(node.args[0]))
        elif func_name=="fail":
            msg_elem = node_to_xml(node.args[0])[0] if node.args else ET.Element("literalString")
            if not node.args: msg_elem.text="No message provided"
            attribs["message"]=xml_str(msg_elem)
        create_assert(parent, xml_tag, **attribs)

def process_statement(stmt, parent):
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        process_assert(stmt.value, parent)
    elif isinstance(stmt, ast.Assert):
        process_assert(stmt, parent)
    elif isinstance(stmt, (ast.If, ast.While, ast.For, ast.Try)):
        tag_map={ast.If:"If",ast.While:"loopFor",ast.For:"LoopFor",ast.Try:"try"}
        tag = tag_map[type(stmt)]
        cond = getattr(stmt,"test",getattr(stmt,"target",None))
        elem = ET.SubElement(parent, tag, condition=ast.unparse(cond) if cond else "")
        for s in getattr(stmt,"body",[]): process_statement(s, elem)
        if isinstance(stmt, ast.If) and stmt.orelse:
            else_elem = ET.SubElement(elem,"Else")
            for s in stmt.orelse: process_statement(s, else_elem)
        elif isinstance(stmt, ast.Try):
            for h in stmt.handlers:
                catch_elem = ET.SubElement(elem,"catch", type=ast.unparse(h.type) if h.type else "Exception")
                for s in h.body: process_statement(s, catch_elem)
            if stmt.finalbody:
                finally_elem = ET.SubElement(elem,"finally")
                for s in stmt.finalbody: process_statement(s, finally_elem)

def extract_test_info(node, file_path):
    method_elem = ET.Element("test_method", name=node.name)
    ET.SubElement(method_elem,"file_path").text=file_path
    if not node.body or (len(node.body)==1 and isinstance(node.body[0], ast.Pass)):
        ET.SubElement(method_elem,"empty")
    else:
        for stmt in node.body: process_statement(stmt, method_elem)
    return method_elem

def process_directory(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for root,_,files in os.walk(input_dir):
        for file in files:
            if not file.endswith(".py"): continue
            path=os.path.join(root,file)
            try:
                tree=parse_python_file(path)
                visitor=TestMethodVisitor()
                visitor.visit(tree)
                for method in visitor.test_methods:
                    method_xml=extract_test_info(method,path)
                    tree_elem=ET.ElementTree(method_xml)
                    try: ET.indent(tree_elem, space="  ")
                    except AttributeError: pass
                    tree_elem.write(os.path.join(output_dir, method.name+".xml"), encoding="utf-8", xml_declaration=True)
            except SyntaxError as e:
                print(f"Erro de sintaxe em {path}: {e}")
