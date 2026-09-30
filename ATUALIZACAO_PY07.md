# M23-PY-07 — Dados de dimensionamento e extremos simultâneos

Checkpoint de desenvolvimento preparado enquanto a hospedagem da versão anterior reinicia. Não foi publicado e não resolve por si só o incidente do Streamlit. Inclui a PY06 integralmente.

## Novidades

1. Painel de materiais e travamentos por grupo: colunas, principais e secundárias. fy, fu e G em MPa; comprimentos efetivos forte/fraco/torção e comprimentos destravados associados aos sinais de momento em metros; Cb e justificativa. E é o mesmo informado para a análise. Valores começam zerados e são identificados como pendentes, sem pressupor material ou contenção.
2. Registro JSON próprio com geometria, perfis, propriedades de catálogo, hash do catálogo selecionado, entradas e pendências. Dados incompletos podem ser documentados. Campos preenchidos recebem FILLED_UNVERIFIED, jamais aprovação estrutural. Não há ainda reimportação desse registro.
3. Tabela de extremos individuais ELU por barra e combinação: mínimos e máximos de N, V e M, com os três esforços simultâneos, posição e identificação do trecho. Exportação CSV com ponto e vírgula, vírgula decimal e UTF-8 com BOM para facilitar abertura no Excel.

## Cálculo dos extremos

Os diagramas existentes são polinômios em t, de zero a um em cada elemento. A rotina inclui extremidades e raízes reais internas das derivadas de cada esforço; avalia N/V/M no mesmo ponto. As duas faces das interfaces entre elementos permanecem candidatas distintas, preservando saltos de cortante. Cada mínimo/máximo seleciona um ponto governante, sem enumerar todos os empates.

O teste sintético tem M = 10t − 10t², cujo máximo interno ocorre em t=0,5; confere também axial simultâneo e salto de cortante. Uma comparação adicional verifica que os extremos do modelo real envolvem uma amostragem densa dos diagramas. A amostragem é teste, não algoritmo de cálculo.

ATENÇÃO: extremos individuais de esforços não garantem encontrar o máximo de uma equação de interação. A futura rotina resistente deverá procurar extremos da própria interação, por trechos, com esforços simultâneos e capacidades adequadas a cada trecho. Não combinar máximos independentes para criar uma solicitação fictícia.

## Fronteira técnica

Esta versão NÃO calcula resistências novas. O registro de materiais/travamentos não modifica solver, diagramas, peso ou ranking. Um comprimento/Cb por grupo é preparação simplificada, não substitui discretização de trechos contidos e justificativa da contenção eficaz. Lb de momento positivo/negativo não é deduzido automaticamente da distância entre secundárias. Colunas continuam exigindo interpretação dos eixos locais e dos lados comprimidos.

O motor anterior W/HP contém rotinas aproveitáveis, mas ainda tem pendências de cisalhamento completo, torção/empenamento e hipóteses de contenção, além de restrições para almas esbeltas. Não foram copiadas equações normativas sem revalidar sua aplicabilidade ao novo modelo. Próxima etapa: conferência normativa e benchmarks de resistência, seguida da integração por trecho com estabilidade e imperfeições.

A análise ELU continua de primeira ordem e coeficientes manuais. O ranking continua ELS parcial, sem aprovação final de perfis.

## Testes e execução

25 testes automatizados passaram no Python 3.12.14, incluindo os 20 anteriores e cinco testes novos: estados incompleto/preenchido e isolamento dos dados; entradas inválidas; extremos internos e descontinuidade; conferência de extremos do modelo; renderização dos novos painéis. Testes de interface são locais com AppTest, não validação do serviço hospedado.

Motor e dependências preservados. Os esquemas anteriores de resultados mantêm suas versões; a interface mostra M23-PY-07 e o novo registro tem esquema próprio M23-PY07-DESIGN-BASIS.

## Atualização posterior

Depois de diagnosticar a hospedagem, enviar o conteúdo da pasta M23_PY07 para a raiz do repositório existente, mantendo app.py na raiz. Não colocar M23_PY07 como subpasta. Em relação à PY06, os arquivos de execução alterados são app.py e ultimate_ui.py; os novos são design_basis.py e design_basis_ui.py. O pacote completo já inclui tudo.

A compatibilidade da hospedagem Python 3.14.7 continua não verificada. Esta versão foi testada localmente em Python 3.12.14; não há evidência nova sobre a causa do incidente anterior.
