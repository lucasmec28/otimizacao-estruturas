# M23-PY-06 — Preparação da integração ELU

Checkpoint preparado enquanto a hospedagem da PY05 reinicia. Este pacote não foi publicado no GitHub ou Streamlit pelo assistente. Não é uma correção comprovada do erro de hospedagem. Manter o diagnóstico da PY05 separado da implantação desta nova funcionalidade.

## Entrega

Após calcular com perfis fixos e escolher Detalhar hipótese, existe o painel Análise preparatória ELU — perfis fixos da hipótese detalhada. Informar combinações explícitas com G_STEEL, G_FLOOR, Q e HX. Os coeficientes começam zerados, são obrigatoriamente definidos pelo usuário e uma linha toda zerada é rejeitada. A confirmação de escopo é uma declaração de entrada, não uma certificação normativa.

O painel calcula apenas a hipótese detalhada e os perfis fixos informados no topo da aplicação; não usa automaticamente os perfis de uma solução da busca. Mostra reações simultâneas por combinação e diagramas N, V e M; permite baixar JSON próprio. O ranking de busca continua ELS parcial e não incorpora esses resultados ELU ainda.

## Escopo mecânico

Primeira ordem, E integral, mesmo modelo X–Z, mesmos vínculos e cargas características do mezanino atual. Combinações manuais; força horizontal total X dividida igualmente entre todos os topos, com coeficiente de sinal livre. Não há geração ou validação normativa de combinações. Não foram incluídos segunda ordem, imperfeições, resistência das seções, cisalhamento, estabilidade lateral Y, eficácia de travamentos ou dimensionamento de bases.

O módulo usa o solver existente e descarta suas verificações ELS auxiliares na saída ELU. Nenhum deslocamento ELU é comparado a limites ELS para aprovar perfis. As saídas são identificadas ELU_FIRST_ORDER_ACTIONS_ONLY e final_design_approved=false.

## Revisão do motor W/HP anterior

Foram examinados v4_m20/engine/strength.py e w_flexure.py. Aquele motor tem rotinas de compressão, flexão forte/fraca e interação; declara pendências de cisalhamento completo, torção/empenamento e hipóteses de travamento. Flexão forte rejeita alma esbelta sem rotina específica. Tração usa plastificação bruta, sem certificação das seções líquidas/ligação. Não é suficiente conectar essas funções e chamar o resultado de dimensionamento completo.

Próxima integração: entradas de materiais e parâmetros efetivos de travamento; conferência normativa das rotinas e benchmarks; esforços ELU com tratamento de estabilidade/imperfeições; verificações aplicáveis com simultaneidade de N/V/M; estado pendente para verificações ausentes; só então incorporar aprovação resistente ao ranking. Não assumir que toda secundária trava a mesa comprimida da principal em qualquer combinação.

## Instalação posterior à recuperação da hospedagem

Enviar app.py, ultimate.py e ultimate_ui.py para a raiz do repositório (ou o conteúdo completo de M23_PY06, preservando engine). Não criar uma subpasta M23_PY06 no repositório. O motor estrutural e requirements.txt são idênticos aos da PY05; não há nova dependência. A versão visual será M23-PY-06.

Como o log da hospedagem mostrou Python 3.14.7 e o ambiente de testes atual é Python 3.12.14, a compatibilidade da hospedagem continua a ser diagnosticada separadamente. Não há evidência no log recebido que permita atribuir o erro a estas novas funções, que ainda não foram publicadas.

## Testes

20 testes automatizados passaram, incluindo todos os anteriores, escala linear das reações/forças para coeficientes sintéticos dobrados, sinal de Hx, independência dos esforços em relação aos limites ELS, rejeição de coeficientes inválidos e bloqueio de combinações sem ações. O teste de proporcionalidade usa coeficientes sintéticos, não recomendações normativas. A execução bem-sucedida do painel ELU foi exercitada com AppTest, substituindo a tabela editável por dados sintéticos no teste; isso verifica cálculo e renderização, mas não simula a edição manual de células no navegador.

Os arquivos ATUALIZACAO_PY01...PY05 e validacao anteriores são registros históricos. O plano geral continua em PLANO_DESENVOLVIMENTO.md.
