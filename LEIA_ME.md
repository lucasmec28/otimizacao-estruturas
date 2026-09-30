# Otimização de estruturas metálicas — M23-PY-11

Aplicativo Streamlit para estudo de mezaninos W/HP. Inclui o gerador de combinações enviado pelo usuário, adaptado aos canais de ações do modelo. ELU normal e ELS frequente são selecionadas inicialmente. ELS rara e quase permanente são opcionais; o modo manual continua disponível.

## Atualizar e testar

1. Extraia o ZIP e envie o CONTEÚDO de M23_PY11 à raiz do repositório, onde já existe app.py. Substitua arquivos homônimos e preserve as pastas. Não envie o ZIP nem crie outra pasta em volta do aplicativo.
2. Após a atualização do Streamlit, confira M23-PY-11 na tela.
3. Confira a geometria, as ações características, a natureza da carga permanente do piso e o uso do piso para os fatores ψ. Os valores iniciais são demonstrativos; não se deduz a categoria de uso apenas da magnitude da sobrecarga.
4. Mantenha Automática / ELU normal + ELS frequente, ou selecione as outras famílias desejadas. Se Hx for diferente de zero, indique se representa vento. Outros tipos horizontais exigem o modo manual avançado. Hx permanece a força TOTAL distribuída igualmente entre todos os topos.
5. Confira a tabela de coeficientes. Calcule hipóteses, escolha uma para detalhar e abra o painel ELU. As combinações já estão preenchidas pelo gerador. Confira o modelo de primeira/segunda ordem antes de executar.
6. Materiais W/HP já são preenchidos. Os comprimentos automáticos são PRELIMINARES e mudam com a geometria; ainda não constituem determinação dos comprimentos críticos pela estabilidade do conjunto.
7. Para buscar perfis, selecione candidatos e hipóteses. O limite conjunto continua 200 casos, contando ELS e ELU (e os dois sentidos nocionais na segunda ordem). O app não descarta combinações para caber no limite. Com vento, poderá ser necessário reduzir as hipóteses por execução.
8. Baixe os registros JSON de combinações, ELS, ELU e busca para conferência. Não há reabertura de projetos pela interface nem salvamento automático de sessões.

O pacote não foi publicado no GitHub ou Streamlit pelo assistente. Nenhuma instalação é necessária no computador usado para acessar o site.

## Limites de interpretação

A estabilidade Y, as contenções reais e a determinação dos comprimentos efetivos continuam pendentes. Por isso, o modo de comprimentos automáticos mantém as verificações resistentes como preliminares e não produz uma alternativa aprovada na busca condicional. Os valores calculados servem para inspecionar o estudo. Não basta um índice menor que 1 para remover essa pendência.

O peso ainda é subtotal de colunas e vigas; não inclui contraventamentos, coletores ou ligações. O gerador aplica fatores às ações existentes: não calcula o vento característico nem cria ações que o modelo não tem. Sobrecarga alternada por vãos, temperatura, sismo, situações especiais, construção e excepcionais não foram integrados ao modelo automático nesta etapa.

Detalhes e validação em ATUALIZACAO_PY11.md. Documentos PY01–PY10 são históricos.

## Desenvolvimento local

python -m pip install -r requirements.txt
python -m streamlit run app.py
python -m unittest discover -p 'test*.py' -v
