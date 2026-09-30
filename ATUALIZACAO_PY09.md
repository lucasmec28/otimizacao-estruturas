# M23-PY-09 — Busca conjunta ELS + verificações N–M–V

Esta entrega consolida um bloco maior: resistência axial, interação normal–momento, cisalhamento, procura do ponto crítico da interação e busca conjunta entre perfis. A versão PY08 foi executada pelo usuário; este pacote PY09 ainda não foi publicado pelo assistente.

## Conferência do arquivo enviado

Arquivo calculo_m23 (3).json: 54 resultados, 18 hipóteses, reproduzidos pelo motor local. Maior diferença absoluta de utilização: 9,11e-15; maior resíduo relativo de equilíbrio de forças: 1,08e-15. Cinco hipóteses atendem ao ELS parcial: 12, 13, 14, 17 e 18. Menor subtotal: hipótese 12, 19,943333 kg/m², utilização ELS máxima 0,761040723.

Esse arquivo contém apenas ELS e não certifica a execução dos painéis ELU. O schema M23-PY-05 identifica o formato do arquivo, não necessariamente a versão visual do app. A PY09 passa a registrar application_version separadamente.

## Resistências implementadas

- Compressão W/HP: modos elásticos x, y e torção; fator χ; redução de larguras/área efetiva; Nc,Rd. Comprimentos fornecidos são efetivos e não recebem um segundo fator K.
- Tração: apenas escoamento da área bruta. Havendo tração, registra pendência de ruptura da seção líquida efetiva. Não considera essa barra sem pendências na busca conjunta.
- Flexão forte: FLT/FLM/FLA herdadas da PY08, com capacidades por sinal e Lb informado. Cb=1 na integração por grupos; alma esbelta permanece pendente.
- Cortante na direção da alma: área Aw=d·tw, kv=5,34 para alma sem enrijecedores transversais, três ramos da expressão de resistência. Não confundir Aw com h·tw. Não dimensiona enrijecedores ou efeitos locais de cargas concentradas.
- Interação N–M: expressão de 5.5.1.2 no plano analisado. Inclui esforços simultâneos em cada seção. Cortante de um único eixo é verificado conforme 5.5.1.3/5.4.3; não foi acrescentada uma equação M–V inventada.

## Procura do ponto governante

Cada elemento possui N linear e M quadrático em t, de 0 a 1. A rotina divide os intervalos nas raízes de N, M e nos cruzamentos N/NRd=0,2. Em cada intervalo procura raízes da derivada da própria interação, além das extremidades e dos extremos de esforços. Preserva os lados das interfaces entre elementos.

Nos limites entre ramos, são consideradas as duas expressões laterais: a seleção pode representar um supremo conservador ao aproximar o limite, em vez do valor de apenas um ramo no ponto exato. O ramo e o intervalo são guardados no JSON. O índice governante também compara axial, flexão isolada e cortante, para não ocultar uma violação individual.

## Busca conjunta

Reutiliza candidatos e hipóteses da interface, combinações ELS do painel principal e combinações ELU calculadas no painel próprio. Para CADA conjunto de perfis e geometria:

1. Recalcula esforços/deslocamentos ELS e peso próprio.
2. Recalcula esforços ELU com os perfis daquele conjunto.
3. Recalcula resistências e procura pontos governantes N–M–V.
4. Classifica atendimento ao escopo condicional e registra pendências por barra.
5. Ordena pelo subtotal kg/m² e destaca o menor subtotal que atende ao escopo implementado sem pendências por barra.

Materiais, comprimentos efetivos e Lb por grupo são os mesmos entre candidatos/hipóteses: precisam ser limites aplicáveis ao conjunto escolhido, não são recalculados a partir da geometria. Essa limitação é mostrada na interface. Comprimentos menores de outra hipótese não devem ser reutilizados indevidamente.

O limite de 200 casos conta ELS + ELU, e não apenas ELS. A busca enumera integralmente o conjunto escolhido e não trunca casos. Uma falha de análise impede liberar um ranking incompleto. Dados alterados invalidam a exibição anterior. Não foram introduzidas heurísticas ou promessas de ótimo global.

## Fontes conferidas

NBR 8800:2024 disponibilizada pelo usuário, incluindo a cópia recuperada nbr-8800-24-25-projeto-de-estruturas-de-aco-e-de-estruturas-mistas-20250710-000231_compress.pdf. Conferência visual das páginas impressas 45–48 (compressão, área efetiva, tabelas 4/5 e modos elásticos), 52–53 (esbeltez), 57–58 (cortante), 61 (interação). Limites de elementos AL laminados e AA da alma: 0,56√(E/fy) e 1,49√(E/fy). Não usar a lógica de elementos soldados para W/HP laminados.

O indicador Lef/r>200 gera necessidade de revisão, não afirma que o comprimento efetivo seja necessariamente o comprimento destravado geométrico usado na recomendação de 5.3.7. Esse ponto requer conferência dos vínculos/comprimentos reais.

## Investigação adicional CBCA

A substituição literal dos valores mostrados na expressão do exemplo W410×38,8, incluindo β1=0,066 cm⁻¹, fornece λr≈129,8980, e não 130,83. Recalculando β1 sem o arredondamento impresso, λr≈129,7148 e MRd,FLT≈165,1761 kN·m. Portanto, o arredondamento visível de β1 sozinho não explica a diferença do valor publicado. A causa editorial completa permanece não confirmada. Mantidas as equações normativas e a divergência documentada; não ajustadas propriedades para coincidir.

## Fronteira estrutural

A busca é CONDICIONAL e de PRIMEIRA ORDEM. Ainda faltam segunda ordem e imperfeições, análise/estabilidade Y, validação real das contenções, efeitos locais/torção/empenamento e validação das combinações de projeto. Tração líquida permanece pendente. O subtotal não inclui contraventamentos/coletores. final_design_approved continua false em todas as saídas.

Não é legítimo chamar esta versão de dimensionamento final de mezanino. O avanço entregue é a conexão funcional entre esforços, resistências implementadas e seleção de perfis. O próximo bloco prioritário é estabilidade/segunda ordem e imperfeições, seguido da massa dos sistemas de estabilização e fechamento das pendências por barra.

## Validação

38 testes passaram em Python 3.12.14. Além da suíte anterior: referência de compressão por Euler/χ, área efetiva reduzida, ramos do cortante e área resistente correta, máximo interno da interação comparado a amostragem densa, reversões de N/M, pendência de tração, equivalência da busca com cálculos individuais, limite de casos, assinatura desatualizada e execução da interface da busca conjunta.

Um teste inicialmente exigia igualdade exata entre 1660 e 1660,0000000000002 mm²; foi corrigido para comparação numérica com tolerância. Nenhuma expressão resistente foi alterada para satisfazer esse teste.

Engine e dependências não foram modificados. service.py recebeu apenas o campo application_version. Ver LEIA_ME.md para atualização e sequência de uso. Documentos PY01...PY08 permanecem históricos.
