# Otimização de estruturas metálicas — M23-PY-12

A PY12 aumenta a capacidade para 1.000 casos nas buscas ELS e conjunta ELS + ELU, e também no cálculo com perfis fixos. O aplicativo verifica a integridade dos arquivos antes de abrir a interface, detectando atualizações incompletas. Materiais e comprimentos geométricos preliminares são preenchidos automaticamente por padrão.

## Atualizar o aplicativo existente

1. Extraia Aplicacao_Python_M23_PY12.zip.
2. Envie TODO o conteúdo da pasta M23_PY12 à raiz do repositório lucasmec28/otimizacao-estruturas. Substitua os arquivos existentes. Preserve a subpasta engine. A subpasta .streamlit é opcional e contém apenas aparência/configuração geral. Não crie outra pasta M23_PY12 dentro do repositório.
3. Envie especialmente app.py, ultimate_ui.py, design_basis_ui.py, automatic_basis.py, service.py, search_profiles.py, combined_search.py, second_order.py, release_check.py, release_manifest.json e os arquivos dentro de engine. Atualizar apenas app.py deixa funções de versões anteriores incompatíveis.
4. Reinicie o aplicativo pelo menu de gerenciamento do Streamlit depois da atualização completa.
5. Confira M23-PY-12 na tela. Se faltarem arquivos, o app agora informa seus nomes antes de iniciar o cálculo.

## Conferir os problemas relatados

- No painel Materiais e comprimentos da concepção, o padrão é Automáticos pela concepção. A tabela é de consulta; não é necessário digitar fy, fu, G, Cb ou comprimentos. O modo Manual avançado é opcional.
- ELU normal e ELS frequente permanecem selecionadas inicialmente. Informe a natureza da carga permanente e o uso do piso. Se Hx representa vento, selecione Vento — testar +X e −X.
- A busca ELS conta: hipóteses × conjuntos de perfis × combinações ELS. Com 18 hipóteses, 2 conjuntos e 6 combinações, são 216 casos, permitidos nesta versão.
- A busca conjunta conta também as combinações ELU e os sentidos nocionais. Com 18 hipóteses, 2 conjuntos, 6 ELS e 32 ELU de primeira ordem, são 1.368 casos: reduza a seleção para caber em 1.000. Nenhuma combinação é eliminada automaticamente.

Materiais W/HP do catálogo: fy=345 MPa, fu=450 MPa e G=77.000 MPa. Os comprimentos automáticos usam uma política geométrica preliminar: colunas 2H e vigas com seu vão integral, sem crédito a contenções intermediárias. Ainda precisamos representar os vínculos e contraventamentos reais para determinar os comprimentos da concepção com rigor. Essa pendência permanece visível nos resultados; a busca não aprova alternativas com comprimentos preliminares.

O peso é subtotal de colunas e vigas. Não inclui contraventamentos, coletores ou ligações. Não há aprovação estrutural final. JSON de dados automáticos disponível para download; não há reabertura de projetos pela interface.

A versão ainda precisa de teste na hospedagem do usuário. O assistente não publicou no GitHub ou no Streamlit. Consulte ATUALIZACAO_PY12.md e validacao_py12.json. Documentos PY01–PY11 são históricos.

## Desenvolvimento local

python -m pip install -r requirements.txt
python -m streamlit run app.py
python -m unittest discover -p 'test*.py' -v

release_manifest.json identifica exatamente o código distribuído. Se alterar o código localmente, regenere o manifesto de hashes para a nova versão antes de executá-la. A interface é bloqueada quando os arquivos diferem do pacote declarado.


Correção PY12-CORRECAO1: .streamlit/config.toml deixou de ser obrigatório. Para corrigir uma instalação PY12 que informa somente sua ausência, basta substituir release_manifest.json. Equações, limite de 1.000 casos e demais arquivos do aplicativo não foram alterados.
