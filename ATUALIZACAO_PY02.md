# M23-PY-02 — Orientação das vigas

Atualização de interface de 29/09/2026. Motor e dependências preservados.

## Aplicar no aplicativo já publicado

No GitHub, abra lucasmec28/otimizacao-estruturas. Use Add file > Upload files e envie apenas app.py desta versão para a raiz do repositório. Confirme Commit changes. O Streamlit deve atualizar automaticamente. Não crie outra aplicação e não envie este ZIP diretamente.

A tela passará a identificar M23-PY-02. Escolha Visualizar geometria antes do cálculo para consultar a planta. A escolha apenas controla o desenho, não exclui hipóteses da análise. Após calcular, o detalhamento também mostra a planta da hipótese escolhida.

Principais paralelas a X, secundárias paralelas a Y. Espaçamento entre secundárias medido em X; vão das secundárias medido em Y entre principais. Colunas indicadas por quadrados nos encontros dos alinhamentos principais; não em todo cruzamento.

Exemplo da hipótese 9 enviada: 12 × 10 m, 3 vãos X de 4 m, 2 vãos Y de 5 m, secundárias espaçadas a cada 2 m em X, vencendo 5 m em Y.

## Conferência do cálculo online recebido

Registro calculo_m23.json: 18 hipóteses; 54 resultados críticos; 873 verificações individuais de deslocamento comparadas ao recálculo local. Valores de deslocamento, utilização e limites concordam com tolerância absoluta/relativa de 1e-8; diferença máxima de deslocamento 2,31e-13 mm. Pesos conferem. Atendem ao ELS parcial: 13, 14, 17 e 18.

Em geometrias simétricas há empates numéricos no ponto crítico. A execução hospedada e a local podem selecionar pontos simétricos diferentes e, para deslocamentos horizontais, sinais opostos nesses pontos. Os deslocamentos assinados de cada verificação individual conferem. Isso não altera as utilizações. O motor congelado não foi modificado nesta atualização de interface.

Esta comparação confirma consistência entre execuções do mesmo motor, não constitui benchmark independente nem aprovação estrutural final.

LEIA_ME.md e validacao.json conservam o registro da primeira versão. Este documento e validacao_py02.json registram a atualização.
