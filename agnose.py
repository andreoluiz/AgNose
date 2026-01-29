import subprocess
import os
import sys
from XmellDetector import Detector
from pathlib import Path
from view_csv import CSVViewerApp
from xmlTestGeneratorPython import xmlTestGenerator

class Domain:
    @staticmethod
    def createGenerator():
        try:
            dir_arc = Path(__file__).resolve().parent
            
            # Lógica de Argumentos ---
            # Se você digitar 'python agnose.py C:\Pasta\Teste', o sys.argv[1] será esse caminho.
            # Se não digitar nada, ele usa o os.getcwd()
            if len(sys.argv) > 1:
                dir_atual = os.path.abspath(sys.argv[1])
            else:
                dir_atual = os.getcwd()

            if not os.path.exists(dir_atual):
                print(f"Erro: O diretório '{dir_atual}' não existe.")
                return

            print(f"Diretório Alvo: {dir_atual}")
            print("Gerando XML e Verificando Smells...")

            xmlTestGenerator.process_directory(rf"{dir_atual}", "saida")

            java_file = os.path.join(
                dir_arc, "xmlTestGenerator", "src", "main", "java", "org", "example", "XmlTestConversor.java"
            )

            javaparser_jar = os.path.join(
                dir_arc, "xmlTestGenerator", "target", "maven-status", "javaparser",
                "javaparser-core", "3.25.10", "javaparser-core-3.25.10.jar"
            )

            cmd = [
                "java",
                "-cp",
                javaparser_jar,
                java_file,
                dir_atual
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            print(">>> Saída do Java:")
            print(result.stdout)

            if result.stderr:
                print(">>> Erro do Java:")
                print(result.stderr)

            Detector.Detector(dir_atual)
            
            csv_path = os.path.join(dir_atual, "output.csv")
            CSVViewerApp(caminho_csv=csv_path, caminho_icon=rf"{dir_arc}\agnose.png")

        except Exception as e:
            print(f"Erro na execução do gerador: {e}")

if __name__ == "__main__":
    Domain.createGenerator()