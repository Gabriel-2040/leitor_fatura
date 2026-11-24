# Product Requirements Document (PRD)

> **Status:** Aprovado para Arquitetura  
> **Dono:** Product Owner (PO) & Analista de Negócio  
> **Data:** 17/11/2026  
> **Versão:** 1.0 (MVP)

---

## 1. Visão Geral e Problema

### 1.1 O Problema
Atualmente, o usuário recebe faturas de cartão de crédito em arquivos PDF de diferentes instituições financeiras (Itaú, Bradesco, Nubank, Caixa Econômica). Cada banco adota um leiaute gráfico diferente, termos variados e disposições visuais distintas para os lançamentos. Isso gera três grandes dores:
1. **Falta de Visibilidade Analítica:** Faturas em PDF são documentos estáticos e de difícil análise agregada, impedindo entender a real distribuição de gastos por categoria (Alimentação, Transporte, Saúde, etc.).
2. **Cegueira de Compromissos Futuros:** Compras parceladas (ex: 02/10) pulverizam gastos ao longo dos meses, dificultando responder com precisão: *"Quanto da minha renda já está comprometida nas faturas dos próximos 3 a 12 meses?"*.
3. **Privacidade e Fragmentação:** Serviços em nuvem de agregação bancária muitas vezes exigem senhas bancárias (Open Finance) ou transferem dados confidenciais para servidores externos. O usuário deseja que seus dados financeiros permaneçam sob seu controle e armazenamento estritamente local.

### 1.2 A Solução
Um aplicativo de **Inteligência Financeira Pessoal** que funciona com processamento e armazenamento 100% locais. O sistema permite o envio de faturas em PDF de emissores selecionados, extrai com precisão todos os lançamentos, categoriza os gastos de forma automatizada com aprendizado contínuo pelas correções do usuário, e entrega um **Painel BI Interativo** com indicadores históricos e **projeção preditiva de fluxo de caixa futuro** baseado em parcelamentos ativos.

---

## 2. Público-Alvo e Personas

* **Persona Principal (Gabriel - Usuário Individual / Gestor Financeiro Pessoal):**  
  Profissional que possui múltiplos cartões de crédito em diferentes instituições e necessita de consolidação visual, relatórios categorizados e visão preditiva das parcelas futuras para planejamento orçamentário seguro, priorizando privacidade absoluta dos seus dados.
* **Persona Secundária (Futuros Usuários do Sistema):**  
  Usuários adicionais que poderão utilizar a mesma instância da aplicação no futuro, exigindo que o sistema suporte autenticação e isolamento completo de dados por usuário desde a concepção.

---

## 3. Escopo do MVP (Instituições Suportadas)

O MVP contemplará especificamente extratores especializados para os 4 seguintes emissores:
1. **Itaú** (Faturas em PDF de cartões de crédito correntistas e Itaucard)
2. **Bradesco** (Faturas em PDF de cartões Bradesco/Bradescard)
3. **Nubank** (Faturas em PDF do Roxinho / Ultravioleta)
4. **Caixa Econômica Federal** (Faturas em PDF de cartões Caixa)

---

## 4. Histórias de Usuário e Critérios de Aceite

### Épico 1: Gestão de Acesso e Identidade
- **US-01: Autenticação e Isolamento de Usuário**  
  *Como* usuário do sistema,  
  *quero* autenticar-me com login e senha,  
  *para* garantir a privacidade dos meus registros financeiros e assegurar que meus dados estejam isolados de outros potenciais usuários.
  - **Critérios de Aceite:**
    - O sistema deve validar credenciais de acesso antes de liberar qualquer visualização.
    - Todos os dados (faturas, lançamentos, regras de categorização) devem pertencer estritamente ao usuário autenticado.

### Épico 2: Importação e Extração Especializada de Faturas
- **US-02: Seleção de Emissor e Upload de Fatura**  
  *Como* usuário,  
  *quero* selecionar a instituição financeira emissora (Itaú, Bradesco, Nubank ou Caixa) e fazer o upload de uma fatura em PDF por vez,  
  *para* que o sistema execute o extrator adequado àquele leiaute.
  - **Critérios de Aceite:**
    - A interface deve permitir a escolha explícita do emissor dentre as 4 opções suportadas.
    - O sistema deve aceitar arquivos no formato `.pdf`.
    - Caso o usuário tente enviar um arquivo com extensão inválida ou corrompido, o sistema deve apresentar uma mensagem amigável de erro.

- **US-03: Extração Automatizada de Dados da Fatura**  
  *Como* usuário,  
  *quero* que o sistema processe o PDF e capture os metadados da fatura e todos os itens lançados,  
  *para* não ter que digitar lançamentos manualmente.
  - **Critérios de Aceite:**
    - Deve extrair os metadados do ciclo: **Data de Fechamento (melhor dia de compra)**, **Data de Vencimento**, **Valor Total da Fatura**.
    - Para cada lançamento, deve extrair com precisão:
      - **Data da compra/lançamento**;
      - **Descrição/Estabelecimento comercial**;
      - **Valor monetário**;
      - **Identificador de parcela** (ex: detectando formatos como `01/06`, `Parcela 3 de 10` ou ausência de parcela para compras à vista).
    - O sistema deve alertar caso haja divergência relevante entre a soma dos itens extraídos e o valor total reportado na fatura.

### Épico 3: Categorização Inteligente e Aprendizado Contínuo
- **US-04: Categorização Automática de Gastos**  
  *Como* usuário,  
  *quero* que os lançamentos sejam categorizados automaticamente em macrocategorias pré-definidas,  
  *para* entender meus hábitos de consumo sem esforço de classificação inicial.
  - **Critérios de Aceite:**
    - O sistema deve aplicar macrocategorias padrão de mercado: *Alimentação/Supermercado*, *Saúde/Farmácia*, *Transporte/Combustível*, *Moradia/Serviços*, *Lazer/Entretenimento*, *Educação*, *Compras/Vestuário*, *Assinaturas/Serviços*, *Tarifas/Juros*, *Outros*.
    - Ao final do processamento da fatura, nenhum lançamento deve ficar sem categoria (itens não reconhecidos caem em *Outros*).

- **US-05: Reclassificação Manual com Aprendizado por Reforço**  
  *Como* usuário,  
  *quero* alterar manualmente a categoria de qualquer lançamento na tela,  
  *para* que o sistema memorize minha correção e classifique lançamentos idênticos ou similares automaticamente nas próximas faturas.
  - **Critérios de Aceite:**
    - A interface deve permitir alterar a categoria de um lançamento com poucos cliques.
    - O sistema deve persistir a associação entre o padrão do estabelecimento e a categoria definida pelo usuário.
    - Em uploads subsequentes, o padrão corrigido pelo usuário deve ter prioridade máxima sobre a inferência automática padrão.

### Épico 4: Painel BI e Projeções Financeiras
- **US-06: Dashboard BI de Análise Histórica e Indicadores Consolidados**  
  *Como* usuário,  
  *quero* visualizar um painel com indicadores agregados e gráficos dinâmicos da fatura e do histórico,  
  *para* analisar a evolução dos meus gastos no tempo e a distribuição por categoria.
  - **Critérios de Aceite:**
    - Cards de KPI: Total da fatura atual, Variação percentual em relação à fatura anterior, Categoria de maior impacto no mês.
    - Gráfico de Composição: Distribuição percentual e em valor por categoria (gráfico de rosca/pizza ou barras horizontais).
    - Histórico Cronológico: Evolução do valor total das faturas ao longo dos meses já importados.
    - Filtros dinâmicos: Permitir filtrar por emissor/cartão, período e categoria.

- **US-07: Projeção de Gastos Futuros (Compromissos e Parcelamentos)**  
  *Como* usuário,  
  *quero* consultar um relatório preditivo que projete os totais de faturas dos próximos meses com base nas parcelas ativas,  
  *para* antecipar meu comprometimento financeiro e planejar meu orçamento.
  - **Critérios de Aceite:**
    - O sistema deve calcular para cada compra parcelada quantas parcelas restam até a quitação e alocá-las cronologicamente nos meses futuros subsequentes.
    - Deve exibir um gráfico e tabela com a projeção mensal de gastos já contratados para os próximos meses (ex: M+1, M+2, ..., M+N).
    - O usuário deve conseguir ver detalhadamente quais compras compõem o valor projetado de cada mês futuro.

---

## 5. Regras de Negócio (RN)

- **RN-01 (Privacidade e Armazenamento Local):** Todo o processamento de arquivos PDF, extração de texto, armazenamento em banco e inferências analíticas devem ser executados localmente no ambiente do usuário. Nenhuma informação de compra ou identificação pessoal de fatura pode ser transmitida para serviços públicos de nuvem de terceiros sem autorização prévia.
- **RN-02 (Anti-Duplicidade de Faturas):** O sistema não deve permitir o processamento duplicado da mesma fatura para o mesmo emissor e mês/ano de competência, a menos que o usuário solicite explicitamente a sobrescrita/reprocessamento.
- **RN-03 (Consistência de Parcelas nas Projeções):** Se em uma fatura do mês `03/2026` consta um item com parcela `02/05` no valor de R\$ 100,00, o sistema deve automaticamente projetar:
  - Mês `04/2026` (Parcela 03/05): R\$ 100,00
  - Mês `05/2026` (Parcela 04/05): R\$ 100,00
  - Mês `06/2026` (Parcela 05/05): R\$ 100,00
  - A partir de `07/2026`: Parcela encerrada (R\$ 0,00 deste compromisso).
- **RN-04 (Tratamento de Estornos e Créditos):** Valores lançados como crédito/estorno (geralmente com sinal negativo ou marcados com estorno) devem abater o valor da respectiva categoria e do total da fatura.
- **RN-05 (Prevalência de Regras Personalizadas):** O histórico de reclassificação do usuário tem prevalência absoluta sobre o dicionário léxico/modelo padrão de categorização.

---

## 6. Fora de Escopo (O que NÃO será feito no MVP)

Para garantir foco e entrega rápida de valor, os seguintes itens estão explicitamente **fora do escopo do MVP**:
1. Integração com APIs abertas de bancos (Open Finance / Open Banking) para busca automática sem PDF.
2. Leitura de faturas de outros bancos além dos 4 especificados (ex: Santander, Inter, C6, BTG serão incluídos em versões futuras).
3. Processamento de faturas enviadas em lote (múltiplos PDFs simultâneos em um único upload).
4. Envio de notificações push ou alertas de vencimento por e-mail/WhatsApp.
5. Exportação automática para planilhas Google Sheets ou Notion via API externa.
6. Aplicativo nativo mobile (iOS / Android).

---

## 7. Critérios de Sucesso do MVP

1. **Acurácia de Extração:** Taxa de sucesso superior a 95% na extração de lançamentos e valores das faturas dos 4 emissores alvo.
2. **Tempo de Processamento:** Tempo de processamento e renderização do BI inferior a 5 segundos após o upload do PDF.
3. **Assertividade da Projeção:** 100% de precisão matemática na distribuição temporal das parcelas futuras restantes identificadas.
4. **Usabilidade de Reclassificação:** O usuário consegue corrigir a categoria de um lançamento com no máximo 2 cliques.
