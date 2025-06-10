package org.example;

import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.NodeList;
import com.github.javaparser.ast.body.BodyDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.expr.Expression;
import com.github.javaparser.ast.expr.MethodCallExpr;
import com.github.javaparser.ast.expr.ObjectCreationExpr;
import com.github.javaparser.ast.nodeTypes.NodeWithStatements;
import com.github.javaparser.ast.stmt.*;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;

public class XmlTestConversor {

    public static void main(String[] args) {
        String directoryPath = args[0];
        String outputDirectoryPath = "saida";

        File directory = new File(directoryPath);
        if (!directory.isDirectory()) {
            System.err.println("O caminho fornecido não é uma pasta válida.");
            return;
        }

        File outputDirectory = new File(outputDirectoryPath);
        if (!outputDirectory.exists()) {
            outputDirectory.mkdir();
        }

        processFilesRecursively(directory, outputDirectory);
        System.out.println("Arquivos de teste XML gerados com sucesso.");
    }

    private static void processFilesRecursively(File directory, File outputDirectory) {
        File[] files = directory.listFiles(file -> file.isFile() && file.getName().endsWith(".java"));
        if (files != null) {
            for (File file : files) {
                try {
                    CompilationUnit cu = parseJavaFile(file.getAbsolutePath());
                    processCompilationUnit(cu, outputDirectory, file.getAbsolutePath());
                } catch (FileNotFoundException e) {
                    System.err.println("Arquivo não encontrado: " + e.getMessage());
                }
            }
        }

        File[] subdirectories = directory.listFiles(File::isDirectory);
        if (subdirectories != null) {
            for (File subdirectory : subdirectories) {
                processFilesRecursively(subdirectory, outputDirectory);
            }
        }
    }

    private static CompilationUnit parseJavaFile(String filePath) throws FileNotFoundException {
        File file = new File(filePath);
        if (!file.exists()) {
            throw new FileNotFoundException("Arquivo não encontrado: " + filePath);
        }
        return StaticJavaParser.parse(file);
    }

    private static void processCompilationUnit(CompilationUnit cu, File outputDirectory, String filePath) {
        cu.findAll(MethodDeclaration.class).forEach(method -> {
            boolean hasTestAnnotation = method.getAnnotations().stream()
                    .anyMatch(annotation -> annotation.getNameAsString().equals("Test"));

            if (!hasTestAnnotation) {
                return;
            }

            String methodName = method.getNameAsString();
            StringBuilder outputBuilder = new StringBuilder();
            outputBuilder.append("<test_method name=\"").append(methodName).append("\">\n");
            outputBuilder.append("\t<file_path>").append(filePath).append("</file_path>\n");

            if (method.getBody().isPresent() && method.getBody().get().getStatements().isEmpty()) {
                outputBuilder.append("\t<empty/>\n");
            } else {
                processStatements(method.getBody().get(), outputBuilder);
            }

            outputBuilder.append("</test_method>\n");
            saveToFile(outputBuilder.toString(), new File(outputDirectory, methodName + ".xml"));
        });
    }

    private static void processStatements(NodeWithStatements<?> nodeWithStatements, StringBuilder outputBuilder) {
        List<Statement> statements = nodeWithStatements.getStatements();
        Set<String> processedStatements = new HashSet<>();

        for (Statement stmt : statements) {
            String statementContent = stmt.toString();

            if (processedStatements.contains(statementContent)) {
                continue;
            }

            processedStatements.add(statementContent);

            if (stmt instanceof ExpressionStmt) {
                ExpressionStmt exprStmt = (ExpressionStmt) stmt;
                if (exprStmt.getExpression() instanceof MethodCallExpr) {
                    processMethodCall((MethodCallExpr) exprStmt.getExpression(), outputBuilder);
                } else if (exprStmt.getExpression() instanceof ObjectCreationExpr) {
                    processObjectCreationExpr((ObjectCreationExpr) exprStmt.getExpression(), outputBuilder);
                }
            } else if (stmt instanceof ForStmt) {
                processForStatement((ForStmt) stmt, outputBuilder);
            } else if (stmt instanceof IfStmt) {
                processIfStatement((IfStmt) stmt, outputBuilder);
            } else if (stmt instanceof TryStmt) {
                processTryStatement((TryStmt) stmt, outputBuilder);
            }
        }
    }

    private static void processObjectCreationExpr(ObjectCreationExpr objectCreationExpr, StringBuilder outputBuilder) {
        if (objectCreationExpr.getAnonymousClassBody().isPresent()) {
            NodeList<BodyDeclaration<?>> bodyDeclarations = objectCreationExpr.getAnonymousClassBody().get();

            processAnonymousClass(objectCreationExpr, outputBuilder);

            for (BodyDeclaration<?> bodyDecl : bodyDeclarations) {
                if (bodyDecl instanceof MethodDeclaration) {
                    MethodDeclaration innerMethod = (MethodDeclaration) bodyDecl;
                    outputBuilder.append("\t<inner_method name=\"").append(innerMethod.getNameAsString()).append("\">\n");
                    innerMethod.getBody().ifPresent(body -> processStatements(body, outputBuilder));
                    outputBuilder.append("\t</inner_method>\n");
                }
            }
        }
    }

    private static void processMethodCall(MethodCallExpr methodCall, StringBuilder outputBuilder) {
        String methodName = methodCall.getNameAsString();

        switch (methodName) {
            case "assertEquals" -> processAssert(methodCall, outputBuilder);
            case "assertNotEquals" -> processAssertNotEquals(methodCall, outputBuilder);
            case "assertTrue" -> processAssertTrue(methodCall, outputBuilder);
            case "assertFalse" -> processAssertFalse(methodCall, outputBuilder);
            case "assertNull" -> processAssertNull(methodCall, outputBuilder);
            case "assertNotNull" -> processAssertNotNull(methodCall, outputBuilder);
            case "assertArrayEquals" -> processAssertArrayEquals(methodCall, outputBuilder);
            case "assertSame" -> processAssertSame(methodCall, outputBuilder);
            case "assertNotSame" -> processAssertNotSame(methodCall, outputBuilder);
            case "fail" -> processFail(methodCall, outputBuilder);
            default -> {
                if (methodCall.toString().startsWith("System.out.println")) {
                    processPrintStatement(methodCall, outputBuilder);
                } else {
                    processNestedBlock(methodCall, outputBuilder);
                }
            }
        }
    }

    private static void processNestedBlock(MethodCallExpr methodCall, StringBuilder outputBuilder) {
        Optional<Node> parentNode = methodCall.getParentNode();
        while (parentNode.isPresent()) {
            Node parent = parentNode.get();

            if (parent instanceof MethodDeclaration methodDeclaration) {
                if (methodDeclaration.isAnnotationPresent("Override")) {
                    outputBuilder.append("\t<override method=\"")
                            .append(methodDeclaration.getNameAsString())
                            .append("\"/>\n");

                    methodDeclaration.getBody().ifPresent(body -> {
                        processStatements(body, outputBuilder);
                    });
                }
            }
            parentNode = parent.getParentNode();
        }
    }


        private static void processAnonymousClass(ObjectCreationExpr creationExpr, StringBuilder outputBuilder) {
        for (BodyDeclaration<?> member : creationExpr.getAnonymousClassBody().orElse(new NodeList<>())) {
            if (member instanceof MethodDeclaration methodDeclaration) {
                if (methodDeclaration.isAnnotationPresent("Override")) {
                    outputBuilder.append("\t<override method=\"")
                            .append(methodDeclaration.getNameAsString())
                            .append("\"/>\n");

                    methodDeclaration.getBody().ifPresent(body -> {
                        for (Statement statement : body.getStatements()) {
                            if (statement instanceof ExpressionStmt expressionStmt) {
                                Expression expression = expressionStmt.getExpression();
                                if (expression instanceof MethodCallExpr nestedMethodCall) {
                                    processMethodCall(nestedMethodCall, outputBuilder);
                                }
                            }
                        }
                    });
                }
            }
        }
    }

    private static void processAssertArrayEquals(MethodCallExpr methodCall, StringBuilder outputBuilder) {
        if (methodCall.getArguments().size() >= 2) {
            String expected = convertToLiteral(methodCall.getArguments().get(0).toString());
            String actual = convertToLiteral(methodCall.getArguments().get(1).toString());
            outputBuilder.append("\t<assertArrayEquals expected=\"").append(expected)
                    .append("\" actual=\"").append(actual).append("\"/>\n");
        }
    }

    private static void processAssertNotEquals(MethodCallExpr methodCall, StringBuilder outputBuilder) {
        if (methodCall.getArguments().size() >= 2) {
            String expected = convertToLiteral(methodCall.getArguments().get(0).toString());
            String actual = convertToLiteral(methodCall.getArguments().get(1).toString());

            if (methodCall.getArguments().size() == 3) {
                String message = methodCall.getArguments().get(2).toString();
                outputBuilder.append("\t<assertNotEquals expected=\"").append(expected)
                        .append("\" actual=\"").append(actual)
                        .append("\" message=\"").append(message).append("\"/>\n");
            } else {
                outputBuilder.append("\t<assertNotEquals expected=\"").append(expected)
                        .append("\" actual=\"").append(actual).append("\"/>\n");
            }
        }
    }


    private static void processAssertSame(MethodCallExpr methodCall, StringBuilder outputBuilder) {
        if (methodCall.getArguments().size() >= 2) {
            String expected = convertToLiteral(methodCall.getArguments().get(0).toString());
            String actual = convertToLiteral(methodCall.getArguments().get(1).toString());
            outputBuilder.append("\t<assertSame expected=\"").append(expected)
                    .append("\" actual=\"").append(actual).append("\"/>\n");
        }
    }

    private static void processAssertNotSame(MethodCallExpr methodCall, StringBuilder outputBuilder) {
        if (methodCall.getArguments().size() >= 2) {
            String expected = convertToLiteral(methodCall.getArguments().get(0).toString());
            String actual = convertToLiteral(methodCall.getArguments().get(1).toString());
            outputBuilder.append("\t<assertNotSame expected=\"").append(expected)
                    .append("\" actual=\"").append(actual).append("\"/>\n");
        }
    }

    private static void processFail(MethodCallExpr methodCall, StringBuilder outputBuilder) {
        String message = methodCall.getArguments().isEmpty() ? "No message provided"
                : convertToLiteral(methodCall.getArguments().get(0).toString());
        outputBuilder.append("\t<fail message=\"").append(message).append("\"/>\n");
    }

    private static void processAssert(MethodCallExpr methodCall, StringBuilder outputBuilder) {
        String methodName = methodCall.getNameAsString();

        if (methodName.equals("assertEquals")) {
            String expected = convertToLiteral(methodCall.getArguments().get(0).toString());
            String actual = convertToLiteral(methodCall.getArguments().get(1).toString());

            if (methodCall.getArguments().size() == 3) {
                String message = methodCall.getArguments().get(2).toString();
                outputBuilder.append("\t<assertEquals expected=\"").append(expected)
                        .append("\" actual=\"").append(actual)
                        .append("\" message=\"").append(message).append("\"/>\n");
            } else {
                outputBuilder.append("\t<assertEquals expected=\"").append(expected)
                        .append("\" actual=\"").append(actual).append("\"/>\n");
            }
        }
    }

    private static void processAssertTrue(MethodCallExpr methodCall, StringBuilder outputBuilder) {
        if (!methodCall.getArguments().isEmpty()) {
            String condition = convertToLiteral(methodCall.getArguments().get(0).toString());
            outputBuilder.append("\t<assertTrue condition=\"").append(condition).append("\"/>\n");
        }
    }

    private static void processAssertFalse(MethodCallExpr methodCall, StringBuilder outputBuilder) {
        if (!methodCall.getArguments().isEmpty()) {
            String condition = convertToLiteral(methodCall.getArguments().get(0).toString());
            outputBuilder.append("\t<assertFalse condition=\"").append(condition).append("\"/>\n");
        }
    }

    private static void processAssertNull(MethodCallExpr methodCall, StringBuilder outputBuilder) {
        if (!methodCall.getArguments().isEmpty()) {
            String variable = convertToLiteral(methodCall.getArguments().get(0).toString());
            outputBuilder.append("\t<assertNull variable=\"").append(variable).append("\"/>\n");
        }
    }

    private static void processAssertNotNull(MethodCallExpr methodCall, StringBuilder outputBuilder) {
        if (!methodCall.getArguments().isEmpty()) {
            String variable = convertToLiteral(methodCall.getArguments().get(0).toString());
            outputBuilder.append("\t<assertNotNull variable=\"").append(variable).append("\"/>\n");
        }
    }

    private static void processPrintStatement(MethodCallExpr methodCall, StringBuilder outputBuilder) {
        if (methodCall.getNameAsString().equals("log") && methodCall.getScope().isPresent() &&
                methodCall.getScope().get().toString().equals("console")) {

            String content = methodCall.getArguments().toString().replaceAll("[\\[\\]]", "").trim();
            outputBuilder.append("\t<print>").append(content).append("</print>\n");
        }
    }


    private static String convertToLiteral(String value) {
        if (value.matches("\\d+")) {
            return "&lt;literalNumber&gt;" + value + "&lt;/literalNumber&gt;";
        } else if (value.matches("\".*\"")) {
            return "&lt;literalString&gt;" + value.replace("\"", "") + "&lt;/literalString&gt;";
        }
        return value.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;");
    }

    private static void processForStatement(ForStmt forStmt, StringBuilder outputBuilder) {
        outputBuilder.append("\t<LoopFor>\n");
        processStatements((NodeWithStatements<?>) forStmt.getBody(), outputBuilder);
        outputBuilder.append("\t</LoopFor>\n");
    }

    private static void processIfStatement(IfStmt ifStmt, StringBuilder outputBuilder) {
        outputBuilder.append("\t<If>\n");
        processStatements((NodeWithStatements<?>) ifStmt.getThenStmt(), outputBuilder);
        if (ifStmt.getElseStmt().isPresent()) {
            outputBuilder.append("\t<Else>\n");
            processStatements((NodeWithStatements<?>) ifStmt.getElseStmt().get(), outputBuilder);
            outputBuilder.append("\t</Else>\n");
        }
        outputBuilder.append("\t</If>\n");
    }

    private static void processTryStatement(TryStmt tryStmt, StringBuilder outputBuilder) {
        outputBuilder.append("\t<try>\n");
        processStatements(tryStmt.getTryBlock(), outputBuilder);
        tryStmt.getCatchClauses().forEach(catchClause -> {
            outputBuilder.append("\t\t<catch>\n");
            processStatements(catchClause.getBody(), outputBuilder);
            outputBuilder.append("\t\t</catch>\n");
        });
        if (tryStmt.getFinallyBlock().isPresent()) {
            outputBuilder.append("\t\t<finally>\n");
            processStatements(tryStmt.getFinallyBlock().get(), outputBuilder);
            outputBuilder.append("\t\t</finally>\n");
        }
        outputBuilder.append("\t</try>\n");
    }

    private static void saveToFile(String content, File outputFile) {
        try (FileWriter writer = new FileWriter(outputFile)) {
            writer.write(content);
        } catch (IOException e) {
            System.err.println("Erro ao salvar o arquivo: " + e.getMessage());
        }
    }
}