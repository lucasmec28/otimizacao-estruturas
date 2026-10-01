# PY12 — capacidade e atualização consistente

## Diagnóstico do relato

A imagem mostra app.py passando cinco argumentos para ultimate_ui.show, conforme PY11. A interface de registro manual e a mensagem de nove campos pendentes correspondem à tela anterior, também presentes no JSON recebido. A assinatura de ultimate_ui.show da PY10 aceita quatro argumentos. Misturar app.py novo com ultimate_ui.py antigo reproduz um TypeError no ponto mostrado. O texto detalhado da exceção está oculto no Streamlit; portanto o diagnóstico é compatível com a evidência, sem acesso ao código efetivamente hospedado ou aos logs completos.

O JSON possui fy/fu/G e comprimentos preenchidos manualmente. Os nove campos restantes são Cb_positive, Cb_negative e a justificativa dos três grupos. Isso explica o aviso de dados incompletos, mas não explica sozinho o TypeError da chamada de função. Na política automática esses campos são preenchidos pelo aplicativo, sem exigir transcrição pelo usuário.

Geometria 9 do registro: vão das principais em X = 4 m; vão das secundárias em Y = 5 m; distância entre secundárias em X = 2 m; altura = 3 m. Na hipótese biapoiada atual, a distância entre linhas de secundárias não reduz o vão que cada secundária vence. O registro manual indicava 2 m para os comprimentos da secundária; esse valor não é adotado automaticamente como contenção. A política automática usa 5 m para essa viga e mantém a validação dos vínculos pendente.

## Mudanças

- Limite de 1.000 casos consistente em search_profiles, combined_search e no parser do motor. Aumentar apenas o texto ou o teto da busca não resolveria o bloqueio interno anterior de 200 pares geometria × combinação.
- Cálculo ELU fixo também admite até 1.000 casos. A segunda ordem conta os dois sentidos nocionais para esse limite antes de iniciar a análise.
- O parser admite mais de 20 combinações ELS, mantendo identificadores únicos, validação dos coeficientes e teto total. Capacidade geométrica e limite de 600 graus de liberdade por pórtico permanecem.
- release_manifest.json contém hashes dos arquivos executáveis, catálogos e dados-base. O app verifica essa lista antes de importar interfaces de projeto. Arquivos faltantes ou de outra versão produzem mensagem com seus nomes. Marcadores das interfaces detectam módulos anteriores ainda carregados no processo e orientam o reinício.
- A primeira abertura da PY12 seleciona o modo automático de dimensionamento e remove os resultados calculados pela versão anterior. Materiais, Cb e comprimentos preliminares vêm preenchidos; o modo manual permanece opcional. Há download de dados automáticos como dados_dimensionamento_py12.json.
- Equações de análise e resistência preservadas. A alteração da capacidade no arquivo bridge_m22.py muda sua assinatura SHA-256. Os TSV de exemplo foram reidentificados para o motor atual sem alterar seus valores numéricos. Registros históricos continuam identificados com o motor anterior.

## Verificações

Os novos testes exercitam a admissão de 1.000 casos e rejeição do excesso, execução real de 288 pares ELS, busca ELS de 216 casos com um perfil adicional e vento, busca conjunta de 228 casos, guarda da segunda ordem, detecção de arquivos antigos/faltantes e fluxo automático com as ações/perfis e geometria 9 enviados pelo usuário. A conferência das versões não valida a modelagem estrutural: essa continua sendo verificada pelos testes de equilíbrio, deslocamentos e resistência existentes.

Consulte validacao_py12.json para os resultados efetivamente executados. O TEST_RESULTS enviado para o gerador de combinações pertence ao chat de origem, cujos testes não foram fornecidos integralmente.

Resultado final: 58 testes do aplicativo e 9 do motor passaram (67 no total), em Python 3.12.14. A hospedagem do usuário não foi alterada ou acessada nesta rodada.
