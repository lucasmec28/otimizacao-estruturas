# M23-PY-04 — Bases, reações e curvas de deslocamento

Checkpoint de 29/09/2026. Continuidade da etapa 2 do plano de desenvolvimento.

## Atualizar o aplicativo publicado

Extraia o ZIP. Abra M23_PY04 e envie seu conteúdo ao repositório lucasmec28/otimizacao-estruturas pela opção Add file > Upload files. Arraste os arquivos e a pasta engine preservando a estrutura; não envie a pasta M23_PY04 como uma subpasta do repositório e não envie o ZIP. Confirme Commit changes. Nesta atualização houve mudanças no motor e nos arquivos de referência: substituir somente app.py não é suficiente.

Arquivos necessários alterados/novos: app.py, service.py, search_profiles.py, diagnostics.py, referencia_m22.tsv, demo_request.tsv e engine/mezzanine.py. As dependências permanecem as mesmas. O pacote inclui o restante para permitir uma atualização completa consistente.

## Novidades

No cálculo com perfis fixos, selecione Detalhar hipótese. Aparecerá Bases e deslocamentos calculados, com dois painéis: Plano de bases e quadro de reações; Diagrama de deslocamento por componente.

Na busca de perfis, escolha uma solução e pressione Calcular bases e diagramas desta solução. O diagnóstico recalcula apenas a geometria escolhida com os perfis dessa solução e todas as combinações atuais. Alterar a solução ou as entradas invalida esse diagnóstico.

O plano identifica B-linha-coluna; a linha cresce em +Y e a coluna cresce em +X. O nó de topo correspondente é T-linha-coluna. Coordenadas aparecem na tabela. Modelos com mais de 80 bases usam a tabela para evitar um plano de rótulos ilegíveis.

A tabela conserva as componentes simultâneas por combinação. Reação apoio→estrutura e ação estrutura→fundação aparecem com sinais opostos. X positivo à direita, Z para cima. M plano positivo anti-horário na vista X–Z; em eixos 3D destrógiros, My = −M plano. Não há componente Y calculada nem quadro ELU nesta versão. Não utilizar o quadro parcial ELS para dimensionar bases ou chumbadores.

As curvas utilizam os polinômios de deslocamento do solver. Os pontos de visualização incluem extremos obtidos das raízes da derivada. Colunas: deslocamento horizontal X por altura Z; principais: deslocamento vertical absoluto e relativo à corda, por posição no vão X; secundárias: deslocamento vertical absoluto e relativo à corda, por posição no vão Y. Colunas continuam verificadas pelo deslocamento do topo relativo à base, conforme critério atual, não pelo máximo intermediário da curva.

C-linha-coluna; VP-linha-vão X; VS-vão Y-alinhamento em X. Terças serão incluídas após integrar cobertura. Esta versão apresenta curvas de deslocamento, não diagramas N/V/M nem deformada tridimensional.

## Motor e compatibilidade

Os cálculos de rigidez, esforços, peso e verificações anteriores foram preservados. O motor passou a devolver reações individuais e coeficientes dos campos de deslocamento e a verificar equilíbrio global de momentos. Isso alterou sua identificação SHA-256. referencia_m22.tsv e demo_request.tsv conservam as mesmas entradas físicas, com cabeçalho adaptado ao novo motor; não são cópias byte a byte dos antigos arquivos congelados. Os pacotes anteriores permanecem preservados.

Arquivos de pedido de motores anteriores não devem ser forçados a passar pela checagem de versão. O resultado antigo regression_m22.tsv é mantido como referência numérica de regressão, não como saída deste novo motor.

## Verificações

Dez testes passaram: paridade da interface; invalidação de resultados; busca versus cálculos individuais; limites e ausência de solução; invalidação da busca; regressão dos resultados M22; equilíbrio das bases para Hx = 0, +10 e −10 kN; sinais das ações na fundação; extremos das curvas versus verificações; solução analítica de flecha no meio do vão biapoiado; navegação dos três tipos de curva na interface. Alguns destes cenários são agrupados nos dez métodos de teste.

O limite de 200 casos continua provisório. 107 perfis em cada um dos três grupos resultam em 1.225.043 conjuntos; para 18 geometrias e uma combinação são 22.050.774 casos. Evoluir para lotes retomáveis, seleção de famílias/grupos, poda justificada e distinção entre busca completa e melhor solução encontrada. Não suprimir candidatos silenciosamente nem prometer ótimo global quando a busca não for exaustiva.

O arquivo enviado pelo usuário nesta etapa, calculo_m23 (1).json, corresponde ao cálculo manual com 54 resultados. Pesos, limites e utilizações foram comparados ao recálculo com tolerância 1e-8 e conferem. O print mostra bloqueio de 324 casos, não execução de uma busca com esse tamanho.

## Próximo incremento

Consolidar a interface de pórtico/modelo explícito e integrar progressivamente verificações ELU/estabilidade com os motores normativos e referências já existentes. Completar esses critérios antes de apresentar uma solução como estrutura dimensionada. O plano completo permanece em PLANO_DESENVOLVIMENTO.md.
