# M23-PY-05 — Filas/eixos e diagramas de esforços

## Atualizar

Extraia o pacote e envie TODO o conteúdo de dentro de M23_PY05 ao repositório, incluindo engine, pela opção Add file > Upload files. Confirme Commit changes. Não envie o ZIP nem crie a subpasta M23_PY05 no GitHub. Esta versão altera app.py, diagnostics.py, grid_names.py (novo), service.py, search_profiles.py, engine/mezzanine.py, requirements.txt e os cabeçalhos dos pedidos de referência. Recomendação: atualizar o conjunto completo para manter compatibilidade.

## Identificação

Filas A, B, C... crescem em +Y. Eixos 1, 2, 3... crescem em +X. Após Z, a identificação segue AA, AB etc.

- Base A1: encontro da fila A com eixo 1.
- Topo T-A1; coluna C-A1.
- VP-A-2/3: principal da fila A entre eixos 2 e 3.
- VS-A/B-S2: secundária entre filas A e B no segundo alinhamento de secundárias em X. Esse alinhamento não necessariamente coincide com um eixo de colunas.

As plantas mostram as filas e eixos, e as tabelas/seletores usam os nomes de engenharia. O JSON conserva os identificadores internos numéricos do motor como chave de rastreabilidade. Eles não foram renumerados destrutivamente.

## Conferência dos arquivos enviados

busca_m23_py04.json: 180 casos/alternativas recalculados; pesos e utilizações conferem dentro de tolerância 1e-8. Mesma melhor solução parcial: solução 12, hipótese 12; colunas W150x13, principais W250x17,9, secundárias W150x13; subtotal 2393,2 kg / 120 m² = 19,943333 kg/m²; utilização governante aproximadamente 0,980988 na secundária. Vale somente para as entradas e ELS parcial do pedido, não como aprovação estrutural.

calculo_m23 (2).json: 54 resultados do modo de perfis fixos comparados ao recálculo; pesos/utilizações conferem. Família informada ELS_QUASE_PERMANENTE, fatores fornecidos pelo usuário; a reprodução não valida a escolha normativa dos fatores.

## VP-01-02 do print, agora VP-A-2/3

Localizada na hipótese 14, coluna W150x13, principal W250x22,3 e secundária W150x13. Vão central de 4 m da fila A; secundárias a cada 1 m. O registro screenshot_case.json preserva as entradas deste caso de teste.

Reproduzido mínimo vertical absoluto -0,495037917 mm. A curva absoluta permanece negativa em todo o vão; a curva relativa à corda tem pequena região positiva perto dos apoios. Os apoios também se deslocam verticalmente. O formato decorre do modelo com continuidade das principais e rotações dos nós rígidos, não de uma hipótese de viga isolada biapoiada.

Verificadas continuidade de deslocamento, rotação e curvatura nos limites dos elementos, relação M = EI v'' e saltos de cortante correspondentes às reações concentradas das secundárias. Não houve necessidade de alterar o cálculo da flecha para tornar a figura visualmente mais convencional.

O gráfico foi melhorado com eixo X quantitativo, linha zero tracejada, marcadores nas extremidades e legenda mais legível. A distinção entre curva absoluta e relativa é explícita.

## Diagramas N, V e M

Novo painel em Bases e deslocamentos calculados para a solução/hipótese escolhida. Selecionar combinação, barra e esforço. Campos obtidos a partir de forças de extremidade e cargas distribuídas do solver; raízes das derivadas incluídas na amostragem. As descontinuidades de V não são eliminadas.

N positivo em tração; M = EI v'' e V = dM/ds no sistema local. Coluna da base ao topo, transversal local em -X; principais em +X; secundárias em +Y. Em vigas horizontais com transversal positivo para cima, M positivo sagente. As secundárias permanecem no modelo de flexão biapoiada, com N = 0 por hipótese, não por verificação de diafragma.

Esses esforços são de primeira ordem e combinações ELS, não ELU. Não acrescentam verificações resistentes ou análise lateral Y. O limite de busca permanece 200 casos, por decisão de continuar a fase de testes.

## Validação e compatibilidade

15 testes passaram. Além dos testes da PY04, foram incluídos nomenclatura além de Z, caso exato do print/continuidade, momento versus curvatura, relação V=dM/ds, momento analítico de secundária e saltos de cortante, e operação da interface para N/V/M. A planta foi renderizada e inspecionada.

Motor identificado por fe88b10408984fc08a3e62fdfd726256bd2ef38b3b875d2f6f73dcde65a870bb. A adição dos campos de esforços mudou seu hash, mantendo os resultados anteriores de deslocamento e massa. Os cabeçalhos de referência foram atualizados; versões anteriores permanecem nos checkpoints anteriores. Altair, já utilizado pelo Streamlit, foi explicitado e fixado no requirements.txt.

## Continuidade

Etapa de diagnóstico ampliada: filas/eixos, curvas, reações e N/V/M. Próxima integração estrutural deve usar esforços de combinações ELU e os motores de resistência/estabilidade, com parâmetros de material, destravamento e vínculos explícitos; não reutilizar automaticamente esforços ELS como ELU. Guia de pórtico, geometria desuniforme e ampliações seguem PLANO_DESENVOLVIMENTO.md. ELU/estabilidade ainda não implementados nesta versão.
