# AgNose

AgNose é uma ferramenta para análise automatizada de testes que converte código-fonte de testes em arquivos XML otimizados e realiza a detecção de test smells em cima dessa representação estruturada.

🧠 Funcionalidades:

Conversão de código de teste para XML com marcações otimizadas.

Detecção automatizada de test smells diretamente nos arquivos XML.

Relatórios estruturados que facilitam a visualização dos problemas detectados.

🧪 Test Smells Detectáveis

Redundant Print

Unknown Test

Empty Test

Duplicated Assert

Assertion Roulette

Conditional Test

Magic Number

Exception Handling

🙌 Contribuições

Contribuições são bem-vindas!

Modo de uso: 

Substitua a CLASSPATH do java parse no arquivo "agnose.py" para o diretório atual em sua máquina.
Em sua pasta de teste, rode o agnose.py (ou digite o caminho para o arquivo). 
Ele irá gerar os arquivos XML para cada teste além de gerar um CSV com todos os Smeels indentificados.

