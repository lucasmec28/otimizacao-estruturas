# M23-PY-08 — Flexão forte isolada de W/HP

Primeira integração resistente ao painel ELU. Versão de desenvolvimento, sem publicação na hospedagem. Inclui as versões anteriores.

## Implementação

O novo w_resistance.py calcula os limites de FLT, FLM e FLA e seu mínimo, para W/HP laminados duplamente simétricos de alma não esbelta, fletidos no eixo forte. Retorna parâmetros de esbeltez, ramo da FLT, coeficientes, capacidades por estado-limite e estado governante. Unidades internas N, mm, MPa; tela em kN e kN·m. γa1 fixado em 1,10 nesta etapa.

A comparação usa os extremos positivos e negativos de M de cada barra/combinação, preservando N e V simultâneos. Usa fy do grupo, E da análise e Lb por sinal. O cadastro anterior agora alimenta esta comparação. Os comprimentos efetivos axiais, G e fu permanecem registrados para etapas futuras; não são empregados na flexão isolada.

Como ainda não há trechos de contenção explicitamente modelados, a integração aceita somente Cb=1. O núcleo matemático admite outros Cb para testes, mas o painel não libera seu uso por grupo. Lb precisa representar um limite superior aplicável aos trechos e sinais do grupo. Isso é declaração de hipótese pelo usuário, não validação automática da rigidez/resistência dos travamentos.

A formulação selecionada exige aplicação das forças transversais à semialtura. Há campo explícito para essa hipótese e para a contenção eficaz. Sem esses dados a comparação fica pendente; a opção não muda fisicamente a altura de aplicação das cargas no solver e não pode ser marcada para justificar uma condição diferente da estrutura real. Outras alturas exigem tratamento futuro.

Estados possíveis: dentro do limite de flexão isolada, excede flexão isolada, pendente. Nunca “estrutura aprovada”. O ranking permanece ELS parcial.

## Fontes e conferência

Conferidas visualmente as páginas impressas 137, 144, 145 e 146 da NBR 8800:2024 disponibilizada para o projeto: D.2.1, Tabela D.1 e D.2.8(a,e,f,h); D.2.2 também conferido no material extraído. Foram usadas as imagens previamente extraídas, incluindo check168.png, pois uma cópia local do PDF estava ilegível. As expressões coincidem com as rotinas anteriores para o escopo suportado.

Referência externa: CBCA, Manual Uso Fácil ABNT NBR 8800:2025, revisão 3, exemplo W410×38,8, páginas impressas 51–53. Com os dados numéricos impressos (Wx=640,5 cm³, Zx=736,8 cm³, Iy=404 cm⁴, J=11,69 cm⁴, Cw=150000 cm⁶, ry=2,83 cm, Lb=3000 mm, Cb=1,14, fy=345 MPa, E=200000 MPa):

- λ = 106,007, comparado a 106,01 no manual.
- λp = 42,3758, comparado a 42,38.
- FLM e FLA = 231,0873 kN·m, reproduzindo o manual.
- λr recalculado = 129,7148; o manual apresenta 130,83.
- FLT recalculada = 165,1761 kN·m; a substituição do manual corresponde a aproximadamente 166,015 kN·m.

A diferença de aproximadamente 0,51% na FLT está registrada e NÃO foi eliminada ajustando propriedades ou fórmulas para coincidir. O teste usa tolerância comparativa de 1% e também congela o resultado recalculado. Não se concluiu a causa da divergência, nem se transformou essa tolerância em margem de aceitação do projeto. O índice de utilização continua tendo referência 1,00. A reprodução exata dessa parte do benchmark permanece pendente.

## Limitações

Não verifica flexocompressão/flexotração, cisalhamento/interações, torção/empenamento, segunda ordem, imperfeições ou estabilidade global/Y. Alma esbelta gera pendência; não retorna capacidade inventada. Não valida automaticamente aço, alturas de carga, contenções ou Cb. Uma barra com N ou V significativo pode ter ηM menor que 1 e ainda falhar em outra verificação.

A relação |M|/MRd é válida apenas como comparação de flexão isolada sob as hipóteses declaradas. Não é utilização global da barra. Arquivos mantêm final_design_approved=false e não mudam a busca.

## Testes e atualização

Testes anteriores mais cinco novos: referência externa com divergência explicitada; ramos FLT e recusas; associação de Lb por sinal; condições ausentes e entradas desatualizadas; interface com hipóteses explícitas. Ver validacao_py08.json para o resultado da suíte.

Motor de análise e requirements.txt permanecem os mesmos da PY07. A nova rotina resistente é separada, sem alteração dos esforços ou deslocamentos anteriores. Ao atualizar futuramente, enviar o conteúdo de M23_PY08 para a raiz do repositório existente. Não houve publicação e não se atribui ao novo módulo a falha anterior de hospedagem.
