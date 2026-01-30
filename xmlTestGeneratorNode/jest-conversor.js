const fs = require('fs');
const path = require('path');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const generate = require('@babel/generator').default;

/**
 * Função para escapar caracteres especiais, garantindo um XML bem formado.
 */
function xmlEscape(str) {
    if (typeof str !== 'string') str = String(str);
    return str.replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&apos;');
}

/**
 * Traduz nós da AST para o formato XML do AgNose (usado dentro dos atributos).
 */
function getExpressionXml(node) {
    if (!node) return "";
    
    if (node.type === 'StringLiteral') {
        return `<literalString>${xmlEscape(node.value)}</literalString>`;
    }
    if (node.type === 'NumericLiteral') {
        return `<literalNumber>${node.value}</literalNumber>`;
    }
    if (node.type === 'Identifier') {
        return `<expr>${xmlEscape(node.name)}</expr>`;
    }
    if (node.type === 'CallExpression') {
        const funcName = xmlEscape(generate(node.callee).code);
        const argsXml = node.arguments.map(arg => getExpressionXml(arg)).join('');
        return `<call function="${funcName}">${argsXml}</call>`;
    }
    if (node.type === 'MemberExpression') {
        return `<expr>${xmlEscape(generate(node).code)}</expr>`;
    }
    return `<expr>${xmlEscape(generate(node).code)}</expr>`;
}

function parseNodeFile(filePath, outputDir) {
    const code = fs.readFileSync(filePath, 'utf-8');
    let xmlMethods = ""; 

    try {
        const ast = parser.parse(code, {
            sourceType: "module",
            plugins: ["jsx", "typescript"]
        });

        traverse(ast, {
            CallExpression(p) {
                const callee = p.node.callee;
                
                // Identifica blocos de teste: it() ou test()
                if (callee.name === 'it' || callee.name === 'test') {
                    const rawName = p.node.arguments[0].value || "unknown_test";
                    const testName = xmlEscape(rawName);
                    
                    let methodXml = `  <test_method name="${testName}">\n`;
                    methodXml += `    <file_path>${xmlEscape(filePath)}</file_path>\n`;

                    const testBody = p.get('arguments.1');
                    
                    if (!testBody || (testBody.node.body && testBody.node.body.length === 0)) {
                        methodXml += `    <empty />\n`;
                    } else {
                        testBody.traverse({
                            // Estruturas de Controle (Padrão AgNose)
                            IfStatement(ip) {
                                const cond = xmlEscape(generate(ip.node.test).code);
                                methodXml += `    <If condition="${cond}"></If>\n`;
                            },
                            TryStatement() { methodXml += `    <try />\n`; },
                            ForStatement() { methodXml += `    <LoopFor />\n`; },
                            WhileStatement() { methodXml += `    <loopFor />\n`; },
                            
                            CallExpression(ip) {
                                const fullCode = generate(ip.node).code;

                                // Identifica asserções Jest/Chai (chaining)
                                if (fullCode.startsWith('expect(')) {
                                    let actualContent = "";
                                    let expectedContent = "";

                                    let current = ip.node.callee;
                                    while (current && current.type === 'MemberExpression') {
                                        current = current.object;
                                    }
                                    
                                    if (current && current.type === 'CallExpression' && generate(current.callee).code === 'expect') {
                                        actualContent = getExpressionXml(current.arguments[0]);
                                    }

                                    if (ip.node.arguments.length > 0) {
                                        expectedContent = getExpressionXml(ip.node.arguments[0]);
                                    }

                                    // O conteúdo já sai de getExpressionXml escapado, 
                                    // mas como vai dentro de um atributo XML, escapamos novamente para garantir segurança.
                                    const actualAttr = xmlEscape(actualContent);
                                    const expectedAttr = xmlEscape(expectedContent);

                                    methodXml += `    <assertEquals actual="${actualAttr}" expected="${expectedAttr}" message="" />\n`;
                                } else if (generate(ip.node.callee).code.includes('console.log')) {
                                    methodXml += `    <print />\n`;
                                }
                            }
                        });
                    }
                    methodXml += `  </test_method>\n`;
                    xmlMethods += methodXml;
                }
            }
        });

        // Envolve tudo em uma única tag raiz <test_file>
        const xmlFinal = `<?xml version="1.0" encoding="UTF-8"?>\n<test_file>\n${xmlMethods}</test_file>`;

        const fileName = path.basename(filePath).replace(/\./g, '_') + ".xml";
        fs.writeFileSync(path.join(outputDir, fileName), xmlFinal);
        console.log(`✓ Gerado XML robusto para: ${path.basename(filePath)}`);

    } catch (e) {
        console.error(`✗ Erro ao processar ${filePath}: ${e.message}`);
    }
}

// Configuração de execução
const targetDir = process.argv[2] || './';
const outputDir = path.join(targetDir, 'saida');

if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}

function walk(dir) {
    let results = [];
    if (!fs.existsSync(dir)) return results;
    const list = fs.readdirSync(dir);
    list.forEach(file => {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);
        if (stat && stat.isDirectory() && file !== 'node_modules') {
            results = results.concat(walk(fullPath));
        } else if (file.endsWith('.test.js') || file.endsWith('.spec.js')) {
            results.push(fullPath);
        }
    });
    return results;
}

const testFiles = walk(targetDir);
testFiles.forEach(file => parseNodeFile(file, outputDir));