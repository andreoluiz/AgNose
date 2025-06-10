# agnose.py
import subprocess
import os
from XmellDetector import Detector
from pathlib import Path
from view_csv import CSVViewerApp

class Domain:
    @staticmethod
    def createGenerator():
        try:
            dir_arc = Path(__file__).resolve().parent
            print("Gerando XML e Verificando Smells...")

            # Diretório atual
            dir_atual = os.getcwd()

            # Caminho para o arquivo Java
            java_file = os.path.join(
                dir_arc, "xmlTestGenerator", "src", "main", "java", "org", "example", "XmlTestConversor.java"
            )

            # Caminho para o JAR do JavaParser
            javaparser_jar = os.path.join(
                "C:", os.sep, "Users", "Denix", ".m2", "repository", "com", "github", "javaparser",
                "javaparser-core", "3.25.10", "javaparser-core-3.25.10.jar"
            )

            # Comando Java
            cmd = [
                "java",
                "-cp",
                javaparser_jar,
                java_file,
                dir_atual
            ]

            # Executar subprocesso
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Mostrar saída padrão e erro, se houver
            print(">>> Saída do Java:")
            print(result.stdout)

            if result.stderr:
                print(">>> Erro do Java:")
                print(result.stderr)

            # Chamada do Detector
            Detector.Detector(dir_atual)
            CSVViewerApp(caminho_csv=rf"{dir_atual}\output.csv", caminho_icon= rf"{dir_arc}\agnose.png")

        except Exception as e:
            print(f"Erro na execução do gerador: {e}")

if __name__ == "__main__":
    Domain.createGenerator()


