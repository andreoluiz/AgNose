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
            
            if len(sys.argv) > 1:
                dir_atual = os.path.abspath(sys.argv[1])
            else:
                dir_atual = os.getcwd()

            if not os.path.exists(dir_atual):
                print(f"Erro: O diretório '{dir_atual}' não existe.")
                return

            print(f"\n--- AgNose: Iniciando Análise Multi-Linguagem ---")
            print(f"Alvo: {dir_atual}")

            arquivos_encontrados = []
            for raiz, _, arquivos in os.walk(dir_atual):
                if 'node_modules' in raiz: continue
                for f in arquivos:
                    arquivos_encontrados.append(f)

            tem_python = any(f.endswith('.py') for f in arquivos_encontrados)
            tem_java = any(f.endswith('.java') for f in arquivos_encontrados)
            tem_node = any(f.endswith('.js') or f.endswith('.spec.js') or f.endswith('.test.js') for f in arquivos_encontrados)

            pasta_saida_xml = os.path.join(dir_atual, "saida")
            executou_algo = False

            if tem_python:
                print("🐍 [Python] Gerando XML via AST...")
                xmlTestGenerator.process_directory(dir_atual, pasta_saida_xml)
                executou_algo = True

            if tem_java:
                print("☕ [Java] Chamando JavaParser...")
                java_file = os.path.join(dir_arc, "xmlTestGenerator", "src", "main", "java", "org", "example", "XmlTestConversor.java")
                jar = os.path.join(dir_arc, "xmlTestGenerator", "target", "maven-status", "javaparser", "javaparser-core", "3.25.10", "javaparser-core-3.25.10.jar")
                
                cmd_java = ["java", "-cp", jar, java_file, dir_atual]
                subprocess.run(cmd_java, capture_output=True, text=True)
                executou_algo = True

            if tem_node:
                print("🟢 [Node.js] Chamando Jest-Conversor...")
                jest_parser = os.path.join(dir_arc, "xmlTestGeneratorNode", "jest-conversor.js")
                
                if os.path.exists(jest_parser):
                    res = subprocess.run(["node", jest_parser, dir_atual], capture_output=True, text=True, shell=True)
                    if res.stderr:
                        print(f"⚠️ Log/Erro do Node: {res.stderr}")
                    executou_algo = True
                else:
                    print(f"❌ Erro: Conversor Node não encontrado em: {jest_parser}")

            if executou_algo:
                print("🔍 Executando Detector de Smells...")
                Detector.Detector(dir_atual)
                
                csv_na_raiz = os.path.join(dir_arc, "output.csv")
                csv_no_alvo = os.path.join(dir_atual, "output.csv")
                
                if os.path.exists(csv_na_raiz):
                    if os.path.exists(csv_no_alvo): os.remove(csv_no_alvo)
                    os.rename(csv_na_raiz, csv_no_alvo)
                
                if os.path.exists(csv_no_alvo):
                    print(f"✅ Análise concluída. Abrindo relatório...")
                    CSVViewerApp(caminho_csv=csv_no_alvo, caminho_icon=os.path.join(dir_arc, "agnose.png"))
                else:
                    print(f"❌ Erro: O arquivo output.csv não foi gerado.")
            else:
                print("Nenhuma linguagem suportada encontrada no diretório informado.")

        except Exception as e:
            print(f"Erro crítico no AgNose: {e}")

if __name__ == "__main__":
    Domain.createGenerator()