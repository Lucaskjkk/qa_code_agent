# 🧪 QA Agents System

Sistema de agentes inteligentes para **testes automatizados de código**, utilizando **LangChain** e **Python**.  
Projetado para analisar, validar e gerar testes de forma autônoma, aumentando a qualidade e confiabilidade do software.

---

## 🚀 Visão Geral

O **QA Agents System** é uma arquitetura baseada em múltiplos agentes de IA que trabalham em conjunto para:

- Analisar código fonte
- Identificar possíveis bugs e falhas
- Gerar testes automatizados (unitários e integração)
- Validar regras de negócio
- Sugerir melhorias no código

---

## 🧠 Arquitetura

O sistema utiliza uma abordagem multi-agente orquestrada:

### 🔹 Agentes principais

- **Code Analyzer Agent**
  - Analisa estrutura e lógica do código
  - Identifica padrões e possíveis problemas

- **Test Generator Agent**
  - Gera testes automatizados (ex: `pytest`)
  - Cria cenários baseados no código analisado

- **Bug Finder Agent**
  - Detecta falhas potenciais
  - Sugere correções

- **Validation Agent**
  - Garante que os testes cobrem regras de negócio
  - Valida consistência

- **Orchestrator**
  - Coordena o fluxo entre os agentes
  - Gerencia contexto com LangChain

---

## ⚙️ Tecnologias

- **Python 3.10+**
- **LangChain**
- **LLMs (OpenAI, OpenRouter, etc)**
- **Pytest**
- **AST (Abstract Syntax Tree)**
- **Docker (opcional)**

---

---

## 🔄 Fluxo de Execução

1. Input do código
2. Análise pelo **Code Analyzer**
3. Geração de testes pelo **Test Generator**
4. Detecção de falhas pelo **Bug Finder**
5. Validação final pelo **Validation Agent**
6. Output:
   - Testes gerados
   - Relatório de qualidade
   - Sugestões de melhoria

---

## ▶️ Como Executar
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

pip install -r requirements.txt
