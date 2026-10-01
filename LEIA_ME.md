# Otimização de estruturas metálicas — M23-PY-13

A PY13 trata o consumo de CPU observado na segunda ordem: solver de matriz em banda, controle de threads BLAS, reaproveitamento de pórticos iguais e de resultados completos das verificações durante a navegação. Mantém as equações da análise, rigidez reduzida, forças nocionais e tolerância de convergência de malha em 1%.

## Atualização

1. Extraia o ZIP e envie TODO o conteúdo de M23_PY13 à raiz do repositório lucasmec28/otimizacao-estruturas, substituindo os arquivos existentes e preservando a subpasta engine. app.py fica na raiz. A configuração .streamlit/config.toml continua opcional.
2. Envie também os arquivos novos engine/linear_algebra.py, execution_control.py e check_cache.py, além do requirements.txt e do release_manifest.json atualizados.
3. O Streamlit instalará SciPy e threadpoolctl conforme requirements.txt. Aguarde a atualização das dependências e reinicie o app se necessário.
4. Confira M23-PY-13 na tela. Não é necessário instalar Python no computador usado para acessar o site.

A implantação no GitHub/Streamlit permanece a cargo do usuário; não foi publicada pelo assistente.

## Segunda ordem

Selecione uma hipótese, mantenha as combinações desejadas e escolha Segunda ordem X com forças nocionais. O app mostra quantidade de casos concluídos, combinação, malha e tempo decorrido. Com 32 combinações e dois sentidos nocionais, serão 64 casos. O prazo inicial é 180 segundos e pode ser ajustado no próprio painel.

Prazo excedido interrompe o cálculo sem liberar resultados incompletos. Esse aviso é diferente de instabilidade, mecanismo ou falta de convergência. A tolerância da malha não foi relaxada para obter velocidade. A análise continua de eixos iniciais, pequenas rotações e rigidez geométrica com força axial média por elemento, restrita ao plano X–Z. Não equivale a análise global 3D ou liberação final da concepção.

A busca conjunta conta ELS + ELU e os dois sentidos nocionais, mantendo o teto de 1.000 casos. Seu prazo inicial é 300 segundos. A busca ELS também tem prazo de 300 segundos. Todas bloqueiam excesso ou interrupção sem liberar ranking parcial.

O aviso Your app has been throttled é da hospedagem e indica redução temporária de CPU. A atualização não remove uma restrição já aplicada. Se o aviso continuar, respeite o prazo mostrado pela plataforma antes de avaliar o desempenho novamente. O tempo medido localmente não é garantia do tempo na hospedagem.

## Conferência dos arquivos recebidos

Os 108 casos ELS e 32 ELU de primeira ordem foram reproduzidos. O CSV de 5.568 extremos corresponde ao relatório ELU. N–M–V (928 linhas) e flexão isolada (1.404 linhas) foram reproduzidos a partir dos esforços enviados. A busca ELS de 864 casos/144 alternativas reproduziu o menor subtotal de 19,95 kg/m², hipótese 12, com colunas W150×13 e vigas principais/secundárias W200×15.

Essa alternativa atende apenas ao ELS parcial. A hipótese detalhada nos relatórios resistentes é a 1, com principais W250×17,9 e secundárias W150×13: é outra configuração e apresentou critérios excedidos. Nenhuma das duas conclusões constitui aprovação estrutural final. Comprimentos automáticos, estabilidade Y e contenções reais continuam pendentes; o peso ainda exclui contraventamentos e coletores.

Registros históricos PY01–PY12 preservados. Consulte ATUALIZACAO_PY13.md e validacao_py13.json para evidências desta versão.

## Desenvolvimento local

python -m pip install -r requirements.txt
python -m streamlit run app.py
python -m unittest discover -p 'test*.py' -v
python -m unittest discover -s engine -p 'test*.py' -v

Python mínimo 3.11 para as dependências atuais. Ambiente de validação: Python 3.12.14. O manifesto verifica os arquivos do pacote antes da análise; alterações locais exigem manifesto correspondente à versão editada.
