# PY13 — cálculo de segunda ordem com menor uso de CPU

## O que foi corrigido

O print recebido contém um aviso da hospedagem sobre redução temporária de CPU, sem resultado ou erro estrutural final. A versão anterior montava uma matriz densa e, em cada iteração, fazia uma Cholesky para conferir estabilidade e três fatorações gerais para solução/refinamento. Esse trabalho se repetia para pórticos iguais. O aplicativo não limitava os threads das bibliotecas matemáticas quando executado na hospedagem, nem mostrava progresso por combinação/malha.

A nova implementação reordena os graus de liberdade por Reverse Cuthill–McKee e resolve a mesma matriz de rigidez em banda. Faz uma fatoração Cholesky por iteração e reutiliza o fator na solução e nos dois refinamentos. Mantém a verificação de positividade, os resíduos de equilíbrio, a convergência de força axial/deslocamento e a falha quando há instabilidade ou mecanismo.

O controle BLAS é fixado em um thread no processo após carregar NumPy/SciPy, evitando contextos concorrentes de alteração/restauração entre sessões. Isso reduz a multiplicação de threads; não altera o número de combinações nem a modelagem estrutural.

O cache local de pórticos na segunda ordem usa apenas classes idênticas do modelo atual: geometrias e perfis uniformes, forças horizontais iguais em todos os topos e áreas de influência de extremidade/interior. Cada pórtico físico continua exportado com seus nós, nomes, reações e diagramas. O cache não foi generalizado para ações por fachada ou vãos desuniformes, ainda não integrados.

A recuperação dos esforços expande diretamente o polinômio cúbico de deslocamento. Preserva M=-f2+f1·L·t+qy·L²·t²/2−P·(v−v0), V=dM/ds e o polinômio axial. A comparação com a expansão anterior por Polynomial e com o exemplo analítico de viga-coluna confirma a equivalência.

## Operação e rastreabilidade

Há progresso por caso/sentido, combinação, pórtico e malha. O tempo máximo inicial da análise fixa é 180 s. A busca conjunta usa 300 s por execução, compartilhando o tempo restante com a segunda ordem; a busca ELS também usa 300 s. Prazo excedido/cancelamento cooperativo nunca retorna análise completa ou ranking parcial. A resposta após cada operação numérica curta é cooperativa; não é encerramento forçado de processo pela hospedagem.

Resultados completos de extremos, flexão e N–M–V ficam em cache da sessão, com chave derivada da assinatura ELU, dados de dimensionamento e condições. Alterações dos dados invalidam o cache. É guardado apenas um resultado por tipo de verificação; falhas não substituem resultados completos. A mudança de versão limpa os resultados anteriores da sessão.

O arquivo engine/linear_algebra.py entra na assinatura do motor. Os TSV de exemplo foram reidentificados sem alterar valores numéricos. O esquema da segunda ordem passa a M23-PY13-SECOND-ORDER-X. Arquivos antigos permanecem históricos. O modo de referência densa existe apenas para testes de comparação; não é uma opção da interface.

## Evidências

No caso enviado (hipótese 1, 32 combinações × dois sentidos nocionais), todas as 64 análises terminaram. No mesmo ambiente e com um thread BLAS em ambas as versões, a PY12 levou 16,479 s e a PY13 3,995 s: aproximadamente 4,1 vezes mais rápida. Todas convergiram na malha 8, com a mesma tolerância de 1%. Diferença máxima de deslocamento 3,64×10⁻¹² mm; diferença máxima de momento 1,18×10⁻⁵ N·mm. O equilíbrio global máximo foi 6,28×10⁻¹⁴. O tempo de hospedagem pode variar e o ensaio não mede diretamente a CPU disponível no Streamlit.

A conferência dos relatórios de primeira ordem preservou massas e limites. Diferença máxima de utilização ELS ≈2,31×10⁻¹⁴. Em extremos simétricos equivalentes, pequenas diferenças de arredondamento podem trocar o nó/sinal escolhido pelo máximo; o módulo e o deslocamento no ponto originalmente indicado foram conferidos. Isso não representa mudança de capacidade ou relaxamento de critério de projeto.

N–M–V e flexão isolada foram reproduzidos exatamente a partir do relatório ELU anexado. O CSV foi conferido linha a linha, incluindo esforços simultâneos, posições e trechos. A busca de 864 casos preservou o menor subtotal ELS e sua configuração. Consulte conferencia_relatorios_usuario_py13.json e benchmark_segunda_ordem_py13.json.

Os testes incluem solução em banda versus densa com carregamentos assimétricos e barra inclinada, expansão dos polinômios, pórticos reutilizados versus solução independente, controle de threads, progresso, prazo/cancelamento, invalidação do cache, exemplo analítico e falha por instabilidade. Resultados executados em validacao_py13.json.

## Limites estruturais mantidos

Estabilidade Y, vínculos e comprimentos críticos da concepção, imperfeições locais, efeitos locais/torção e massa dos contraventamentos continuam pendentes. O exemplo detalhado de primeira ordem excede verificações; a alternativa de 19,95 kg/m² atende apenas ao ELS parcial. A conclusão da análise de segunda ordem não aprova esses perfis nem a estrutura.

## Fontes da implementação numérica

- https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.cholesky_banded.html
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.cho_solve_banded.html
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csgraph.reverse_cuthill_mckee.html
- https://github.com/joblib/threadpoolctl

Dependências declaradas: SciPy 1.17.0 e threadpoolctl 3.6.0, além das versões anteriores de Streamlit, NumPy, pandas e Altair.

Resultado da validação final: 68 testes do aplicativo e 9 do motor passaram, totalizando 77 testes. A instalação na hospedagem do usuário ainda precisa ser testada.
