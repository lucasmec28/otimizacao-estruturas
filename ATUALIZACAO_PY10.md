# M23-PY-10 — Segunda ordem X, nocionais e busca conjunta

Entrega: opção de análise geométrica de segunda ordem dos pórticos X, forças nocionais nos dois sentidos, redução de rigidez, refinamento automático, recuperação de esforços com P–δ e uso desses esforços nas verificações N–M–V e na busca de perfis. Não houve publicação pelo assistente.

## Conferência dos arquivos enviados pelo usuário

- busca_m23_py05.json: reproduzidos 180 casos. Maior diferença de utilização: 4,18e-14. Melhor solução ELS parcial: 35, hipótese 17, colunas W150×13,0, principais W250×17,9 e secundárias W200×15,0; 2989,2 kg e 24,91 kg/m²; utilização máxima 0,750926421.
- calculo_m23 (4).json: reproduzidas as 54 linhas; maior diferença de utilização 8,89e-15.

Ambos são registros ELS. Não contêm verificações N–M–V nem busca conjunta. Também não contêm o novo campo application_version adicionado à PY09. Isso não permite confirmar a versão efetivamente executada a partir desses anexos: podem ser registros anteriores ou gerados por uma implantação ainda não atualizada. Conferir M23-PY-10 no topo ao testar esta entrega. O botão de download ELS foi renomeado para evitar confusão.

## Modelo numérico

Reutiliza o Frame existente, com rigidez geométrica consistente e força axial média constante em cada elemento. Compressão reduz rigidez, tração aumenta. É uma formulação de eixos iniciais e pequenas rotações, não corrotacional nem análise materialmente não linear. Perda de positividade da matriz ou ausência de convergência interrompe a execução, sem liberar resultado parcial como válido.

Colunas são discretizadas inicialmente em 4 elementos, passando a 8 e, se necessário, 16. Principais são subdivididas respeitando cada apoio de secundária e garantindo refinamento compatível. As secundárias continuam Y biapoiadas, com axial nulo; não são transformadas em vigas-colunas por esta opção.

O controle compara máximos de momento por barra e deslocamentos de topo entre duas malhas consecutivas, com tolerância relativa de 1%. Há pisos numéricos de 1 N·mm para momentos e 0,001 mm para deslocamentos quase nulos. Esse critério é de convergência numérica, não tolerância de dimensionamento. O índice resistente admissível continua 1,00. Limite de 600 graus de liberdade por pórtico; falha de refinamento gera MESH_NOT_CONVERGED.

## Recuperação de esforços

Não se reutilizam os polinômios de primeira ordem. Para cada elemento, em coordenadas locais:

M(x) = −F2 + F1·x + qy·x²/2 − P·[v(x)−v(0)]

F é o vetor generalizado do elemento; P é compressão média positiva; v é o campo cúbico de deslocamento do elemento finito. V = dM/dx e N segue equilíbrio axial. O momento pode ser cúbico; a rotina de interação já procura os extremos dos polinômios resultantes. O erro da aproximação de axial médio e do campo cúbico é controlado por refinamento.

O benchmark de coluna em balanço sob força transversal H e compressão P é independente: δ = (H/P)[tan(kL)/k − L], com k²=P/(EI). Para P=0,3Pcr e 16 elementos, o deslocamento coincide com a solução analítica dentro de 1e-5 relativo. O momento de base atende a M=HL+Pδ, e os momentos recuperados coincidem com os momentos generalizados nas duas extremidades de cada elemento. Acima de Pcr, o teste exige falha por instabilidade.

## Imperfeições e rigidez

No modo de segunda ordem, o usuário pode editar o fator aplicado a EA/EI (valor inicial 0,8) e a fração nocional (inicial 0,003). Esses valores se relacionam ao procedimento de 4.10.7.1 da NBR 8800:2024 conferido nas fontes fornecidas. A escolha não classifica automaticamente a estrutura nem prova aplicabilidade normativa.

A parcela nocional em cada topo é a fração informada da reação gravitacional correspondente, obtida em uma análise linear apenas com as cargas gravitacionais da combinação. Inclui peso próprio. Reação gravitacional negativa bloqueia esta regra de distribuição e exige tratamento específico.

Executam-se +X e −X nocionais, adicionados ao Hx da combinação. Essa superposição explícita em ambos os sentidos é uma decisão do modelo desta etapa; não é um gerador normativo de combinações. Não foi implementada a direção ortogonal Y. Tampouco se afirma que todos os efeitos de imperfeições locais estejam resolvidos.

ELS permanece com E integral e sem nocionais. As resistências de seção usam o E material informado, sem aplicar novamente o fator de redução da análise.

## Diagnósticos e reações

O painel informa malha final, iterações, resíduo, diferença entre malhas e deslocamentos de primeira/segunda ordem com a MESMA rigidez e as MESMAS ações, incluindo nocionais. Razões com denominador quase nulo ficam sem valor. As razões locais não constituem classificação normativa automática de deslocabilidade.

Confere equilíbrio global de forças e equilíbrio generalizado do solver. Não usa o balanço de momentos em geometria indeformada como se fosse uma análise de primeira ordem. O benchmark inclui equilíbrio de momentos com P–Δ.

As reações apresentadas incluem nocionais. Isso é identificado na saída e na tela; não constituem o quadro final de ações para fundações. A eventual exclusão normativa de reações nocionais precisa de tratamento separado, não de subtração indiscriminada em análise não linear.

## Busca e verificações

A busca conjunta herda o modo escolhido no painel ELU. Reanalisa cada conjunto de perfis e geometria, incluindo ambos os sentidos nocionais e o refinamento. Usa os esforços recuperados nas verificações N–M–V. Dados do modo, rigidez, nocionais ou perfis alterados invalidam resultados anteriores.

O limite de 200 casos conta hipóteses × conjuntos de perfis × (combinações ELS + combinações ELU × sentidos nocionais). Refinamentos e iterações acrescentam trabalho interno. Não são truncadas alternativas. Falha numérica aborta a busca em vez de omitir silenciosamente um candidato.

Ainda faltam estabilidade/análise Y, contenções reais, seção líquida tracionada, efeitos locais de cargas concentradas, altura das cargas na FLT, torção/empenamento e massa completa de contraventamentos/coletores. Permanecem restrições de Cb=1 por grupo e Lb/comprimentos efetivos fornecidos pelo usuário. Toda aprovação permanece condicional; final_design_approved=false.

## Validação e histórico

38 testes existentes passaram; mais 7 testes novos passaram: coluna com solução analítica, instabilidade, axial nulo, forças nocionais/equilíbrio/redução de rigidez, bloqueio de malha não convergente, equivalência da busca com cálculo direto em segunda ordem e interface com invalidação dos resultados. Total: 45 testes. Ambiente Python 3.12.14.

Engine e requirements.txt preservados. A integração e recuperação novas estão em second_order.py; os esquemas de análise/verificação/busca identificam PY10. Os registros PY01...PY09 permanecem históricos. A divergência CBCA FLT documentada na PY08/PY09 permanece registrada, sem ajuste artificial da fórmula.
