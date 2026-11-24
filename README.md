# university-extension-project-I

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![DAX](https://img.shields.io/badge/DAX-0078D4?style=for-the-badge)

Productivity analysis of Macete SENAI 4.0 machining and assembly using simulated data, Python, SQLite and Power BI. Faculdade SENAI-FIEMG.
Prova de conceito didática de análise de produtividade com **dados simulados**.
Projeto da UCE I – Fábrica 4.0, Ciência de Dados, Faculdade SENAI-FIEMG (Belo Horizonte), Grupo 2.

> **Aviso:** todos os registros são sintéticos, gerados por script. Não houve coleta na linha real nem pesquisa com usuários. Os padrões encontrados decorrem das regras de geração e não descrevem a fábrica.

## Pergunta orientadora

Quais dados ajudam a explicar por que a produção ficou abaixo do planejado?

## O que o projeto faz

1. **Python** gera uma base de eventos (ciclos, paradas e esperas) de 4 estações, de 02 a 06/11/2026.
2. **SQLite** guarda a base e calcula os indicadores de referência por SQL.
3. **Power BI Desktop** importa os CSV e recalcula os indicadores com medidas DAX, em um painel com filtros por estação e período.
4. **Testes** comparam SQL, Python e painel.

| Estação | Código |
|---|---|
| Cabeça | EST-01 |
| Pontas | EST-02 |
| Capas | EST-03 |
| Montagem | EST-04 |

Regra de negócio: um macete só é contado quando passa aprovado na montagem (EST-04). Meta: 60 macetes por dia (300 na semana). Turno de 450 min por estação e dia.

## Base simulada

- 2.075 registros: 1.726 ciclos, 256 esperas e 93 paradas.
- Semente aleatória fixa (2026), então a base é reproduzível.
- **Dois cenários inseridos de propósito:** quebra de ferramenta de 55 min nas Pontas em 04/11 e refugo elevado na Cabeça em 05/11.

Campos de `base_eventos.csv`: `evento_id`, `estacao_id`, `produto_id`, `inicio`, `fim`, `tipo_evento`, `motivo`, `quantidade_total`, `quantidade_aprovada`. Tabelas auxiliares: `estacoes.csv` e `turnos.csv` (tempo planejado e meta por dia).

## Indicadores

| Indicador | Fórmula |
|---|---|
| Tempo de ciclo médio | média de (fim − início) dos ciclos |
| Produção por hora | peças totais ÷ horas em operação (soma da duração dos ciclos) |
| Disponibilidade | (planejado − paradas) ÷ planejado; esperas não entram |
| Aprovação | peças aprovadas ÷ peças totais |
| Macetes realizados | aprovadas na montagem (EST-04) |
| Previsto × realizado | macetes realizados ÷ meta |

O OEE não foi calculado, porque o ciclo ideal de cada peça não foi definido.

## Resultados da semana (dados simulados)

| Indicador | Valor |
|---|---|
| Macetes realizados | 224 de 300 (74,7%) |
| Disponibilidade | 87,59% |
| Aprovação | 98,78% |
| Tempo de ciclo médio | 221,33 s |
| Produção por hora | 16,27 |
| Maior motivo de parada | troca de ferramenta, 319 min (28,6% dos 1.117 min parados) |
| Maior espera | Montagem, 963 min, 896 por falta de peça das Pontas |
| Menor disponibilidade | Pontas, 79,66% |

A diferença para a meta está ligada às paradas das Pontas e à espera da Montagem por peças delas. É um indício, não prova de gargalo, e vale apenas para a base simulada.

## Estrutura do repositório

```
.
├── gen.py                              # gera a base, o SQLite e os testes de validação
├── conferencia_valores_relatorio.py    # recalcula em SQL e Python os valores do relatório
├── data/
│   ├── base_eventos.csv
│   ├── estacoes.csv
│   └── turnos.csv
├── painel/
│   └── prototipo-uce-macete-senai.pbix # painel no Power BI Desktop
├── docs/
│   ├── relatorio_final                 # relatório (PDF ou DOCX)
│   └── apresentacao.pptx               # slides
└── README.md
```

## Como reproduzir

Requer Python 3 com `pandas` e `numpy`.

```bash
# 1. gerar a base (grava CSV, SQLite e resultados.json na pasta indicada)
python gen.py data

# 2. conferir os valores do relatório em SQL e Python
python conferencia_valores_relatorio.py data
```

O segundo comando imprime uma tabela com o valor do relatório, o do SQL e o do Python, e grava `conferencia_valores.csv`. Todos os 44 valores conferem.

Para ver o painel, abra o `.pbix` no Power BI Desktop (Windows). Se os caminhos dos CSV mudarem, ajuste a fonte de dados em **Transformar dados**.

## Testes

| Caso | Verificação | Situação |
|---|---|---|
| T1 | Integridade da base (0 violações) | Aprovado |
| T2 | 10 ciclos recalculados, por código independente e à mão | 10 de 10 conferem |
| T3 | SQL × Python, 30 combinações de dia e estação, 12 indicadores | Diferença 0 |
| T4 a T8 | Cartões, gráficos e filtros do painel contra os valores esperados | Aprovado |

## Limitações

- Dados simulados e dois cenários inseridos de propósito.
- Atualização manual, por importação dos CSV. Não há integração com máquinas ou sensores.
- A análise de anterioridade foi documental, sobre páginas oficiais de cinco soluções, sem teste dos produtos.
- Os valores econômicos (R$ 1.000,00 de investimento, ROI e payback) são premissas acadêmicas, não economia obtida.

## Próximos passos

Confirmar fontes reais de dados com os responsáveis, validar as premissas, rodar um piloto em uma estação e só então calcular ganho, ROI e payback.

## Equipe

Carlos e André. Orientadora: Profa. Dra. Michele 
