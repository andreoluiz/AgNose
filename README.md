# 🧪 AgNose

AgNose é uma ferramenta para detecção automatizada de *test smells* em testes unitários, baseada em uma abordagem leve e independente de framework.

A proposta implementa uma estratégia agnóstica, que transforma métodos de teste em uma **estrutura XML simplificada**, extraindo apenas as informações essenciais para a identificação de smells. Isso permite a aplicação da ferramenta em diferentes linguagens e frameworks com mínimo esforço de adaptação.

> 🔬 Esta ferramenta foi desenvolvida como parte do artigo:  
> **AgNose: A Framework-Agnostic Test Smell Detection Tool**

---

## ⚙️ Funcionalidades

- Conversão de código de teste (Java) para XML com marcações otimizadas.  
- Detecção automatizada de *test smells* diretamente nos arquivos XML.  
- Geração de relatórios estruturados em formato CSV, com informações por arquivo e por método de teste.

---

## 🧠 Estratégia

A ferramenta segue os seguintes passos:

1. **Conversão de código**: cada método de teste é convertido para um XML simplificado usando a biblioteca `JavaParser`.  
2. **Análise semântica**: o XML é processado por regras que identificam padrões de smells com base em estrutura, e não em sintaxe detalhada.  
3. **Relatório final**: os resultados são armazenados em um arquivo `.csv`, listando todos os smells detectados por método.

Essa abordagem **reduz o acoplamento com frameworks específicos** e **evita o retrabalho** na criação de ferramentas para cada linguagem.

---

## 🤝 Contribuições

Exception Handling

🙌 Contribuições

Contribuições são bem-vindas!

Modo de uso: 

Em sua pasta de teste, rode o agnose.py (ou digite o caminho para o arquivo). 
Ele irá gerar os arquivos XML para cada teste além de gerar um CSV com todos os Smeels indentificados.

