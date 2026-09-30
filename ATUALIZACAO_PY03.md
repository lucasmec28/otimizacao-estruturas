# Atualização M23-PY-03

## Instalar no aplicativo existente

Extraia o ZIP. No repositório lucasmec28/otimizacao-estruturas, use Add file > Upload files e envie juntos `app.py` e `search_profiles.py` da pasta M23_PY03. Confirme Commit changes. O primeiro arquivo substitui a interface; o segundo é um módulo novo obrigatório. Não é preciso alterar requirements.txt nem criar outro app. Aguarde a atualização do Streamlit.

## Testar a busca

Abra Buscar perfis mais leves — ELS parcial. Comece com um candidato de coluna, dois candidatos de principal e dois de secundária. Com 18 geometrias e uma combinação são 72 casos, abaixo do limite de 200. Pressione Executar busca de perfis.

Pode haver nenhuma solução que atenda: nesse caso, amplie os perfis ou reduza vãos e execute novamente. A busca varia automaticamente os perfis entre os candidatos fornecidos. Inclui peso próprio e rigidez de cada conjunto, mas apenas as verificações de ELS parcial do motor atual.

O cálculo manual de perfis fixos continua disponível abaixo, independente da busca. Alterar entradas invalida a exibição dos resultados correspondentes. A seleção do desenho apenas visualiza a hipótese.

## Melhorias

- Força horizontal explicada como total em X, igualmente dividido entre todos os topos de coluna.
- Valor por coluna e tabela de nós T-linha-coluna com coordenadas e forças antes do coeficiente HX.
- Busca exaustiva limitada, sem truncamento, e classificação de soluções por subtotal de aço.
- Melhor solução parcial destacada apenas quando atende ao ELS implementado.
- Detalhamento e registro JSON da busca com candidatos, entradas e resultados críticos.

## Limites e rastreabilidade

Motor M22 preservado byte a byte. Não foram adicionados ELU, estabilidade global ou análise lateral Y. Peso ainda é subtotal de colunas/principais/secundárias. Perfis constantes por grupo. Comparação com outra versão de BLAS pode selecionar locais críticos simétricos diferentes em caso de empate, como documentado em ATUALIZACAO_PY02.md.

Cinco testes automatizados passaram: paridade do caso M22, cálculo manual e invalidação da interface, busca comparada a cálculos individuais, inexistência de solução/limites de busca e execução/invalidação da busca na interface. Isso não substitui os benchmarks estruturais independentes previstos no plano.

PLANO_DESENVOLVIMENTO.md organiza todos os itens solicitados em 29/09/2026. Documentos PY01/PY02 são registros históricos; este arquivo descreve o incremento atual.
