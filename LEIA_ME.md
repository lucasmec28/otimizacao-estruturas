# Otimização de estruturas metálicas — M23-PY-09

Aplicação Python/Streamlit para mezaninos com perfis W/HP. Esta versão inclui todas as entregas anteriores. Consulte ATUALIZACAO_PY09.md para escopo técnico e validação. Os documentos PY01...PY08 são históricos.

## Atualização do app existente

Extraia o ZIP. Envie o CONTEÚDO de M23_PY09 para a raiz do repositório, onde app.py já está. Mantenha a pasta engine e substitua os arquivos homônimos. Não crie uma pasta M23_PY09 dentro do repositório. Nenhuma instalação é necessária no computador que acessa o site.

Esta versão foi testada em Python 3.12.14. O assistente não publicou o pacote no GitHub/Streamlit. O usuário confirmou a execução da PY08; a PY09 ainda precisa de teste na hospedagem.

## Como testar a nova busca

1. Informe geometria, ações e combinações ELS. Na busca ELS, escolha os candidatos de colunas, principais e secundárias.
2. Calcule com perfis fixos e escolha uma hipótese para detalhar.
3. Em Materiais e travamentos, informe fy, G, comprimentos efetivos forte/fraco/torção, Lb por sinal, Cb=1 e justificativa por grupo. Os campos começam zerados; não são valores recomendados. fu está reservado para futura seção líquida.
4. Informe combinações ELU no painel próprio e calcule os esforços ELU.
5. Defina as condições de altura da carga e contenções apenas se forem coerentes com o modelo real. Consulte as verificações conjuntas N–M e cisalhamento.
6. Abra Busca conjunta de perfis — ELS + N–M–V condicional. Confirme que os comprimentos e materiais por grupo se aplicam a todas as hipóteses selecionadas. Execute a busca. O total considera ELS e ELU, com limite de 200 casos, sem truncamento.
7. Baixe busca_conjunta_py09.json para conferência. Para um cálculo fixo, baixe verificacoes_nmv_py09.json. calculo_m23.json continua sendo o registro ELS; não contém as verificações resistentes.

## Interpretação

Dentro dos critérios condicionais significa atendimento apenas às verificações implementadas e às hipóteses declaradas. Segunda ordem, imperfeições, estabilidade Y, contenções reais e efeitos locais ainda precisam ser tratados. Tração tem escoamento bruto calculado, mas ruptura da seção líquida fica pendente. Nenhum resultado é aprovação estrutural final.

Os kg/m² ainda incluem apenas colunas e vigas principais/secundárias. Contraventamentos e coletores não estão incluídos. A busca retorna o menor subtotal no conjunto testado e no escopo condicional, não o menor peso final da estrutura.

Não há salvamento automático de projetos nem reimportação de sessões. Baixe os registros antes de encerrar ou reiniciar a sessão.

## Desenvolvimento local

python -m pip install -r requirements.txt
python -m streamlit run app.py
python -m unittest discover -p 'test*.py' -v
