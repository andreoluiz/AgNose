import subprocess
from XmellDetector import Detector
import os


class Domain:
    def createGenerator(path):
            path_file = rf"{path}"
            java_file = rf"{str(os.getcwd()+r"\xmlTestGenerator\src\main\java\org\example\XmlTestConversor.java")}"
            result = subprocess.run(["java","-cp",r"C:\Users\Denix\.m2\repository\com\github\javaparser\javaparser-core\3.25.10\javaparser-core-3.25.10.jar", java_file, path_file ], capture_output=True, text=True)
            print(result.stdout)
            Detector.Detector()

path = input("insira o caminho do projeto teste: ")
Domain.createGenerator(path)

# r"C:\Users\Denix\Downloads\Stirling-PDF-main\Stirling-PDF-main\src\test\java"