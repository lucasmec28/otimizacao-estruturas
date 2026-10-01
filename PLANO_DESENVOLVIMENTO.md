# Aplicação de otimização de estruturas metálicas — plano de desenvolvimento

Decisões de Lucas Rodrigues Oliveira em 29/09/2026. Implementação por etapas em Python; interface no navegador. Excel/PNG são saídas futuras, sem dependência de Excel para calcular. Este documento é um roteiro de desenvolvimento, não uma memória de cálculo.

## Ponto de partida: M23-PY-03

O app compara mezaninos uniformes, com seções W/HP constantes por grupo, por ELS parcial. Pórticos X rígidos, bases engastadas, secundárias Y biapoiadas. Limites editáveis H/400, L/350 e L/350. Não há ainda ELU, estabilidade global, análise lateral Y, cobertura integrada nem aprovação estrutural final.

Nesta versão foi acrescentada busca exaustiva entre listas de perfis candidatos para colunas, principais e secundárias, cruzadas com as geometrias e combinações selecionadas. Rigidez e peso próprio são recalculados em cada conjunto. A solução destacada é o menor subtotal dentre as alternativas que atendem ao ELS parcial, dentro da seleção; não é um ótimo estrutural final. O subtotal inclui somente esses três grupos. Limite de 200 casos completos, sem truncamento automático.

Força horizontal: soma total aplicada em X, igualmente dividida por todos os topos de coluna. A interface agora mostra a parcela por coluna e nomes T-linha-coluna. Não foi alterada a distribuição mecânica existente.

## Princípios da arquitetura

Um modelo de nós, barras, vínculos, grupos de perfis, ações e combinações deve alimentar todos os modos. Separar gerador geométrico, análise, verificações, busca e apresentação. Evitar criar motores independentes para as guias Pórtico, Mezanino e Cobertura.

Cada resultado deve conter versões do motor e do catálogo, unidades, entradas, hipóteses de vínculo/travamento, esforços, verificações aplicáveis e pendências. Falha numérica não significa reprovação resistente: deve ser classificada separadamente. Reprovação e ausência de verificação também precisam ser diferentes.

Preservar checkpoints. Não trocar equações congeladas sem teste de regressão e caso de referência. Mostrar gráficos com escalas e unidades explícitas. Não representar uma parábola arbitrária como deformada calculada.

## Etapa 1 — Busca inicial e transparência das cargas [iniciada neste checkpoint]

Entregue: candidatos por grupo; enumeração completa dentro do limite; pesos e rigidez atualizados; mínimo parcial identificado; resultado descartado da exibição quando entradas/candidatos mudam; nenhuma solução viável tratada explicitamente; distribuição horizontal uniforme documentada por nó.

Continuidade: salvar/reabrir projeto JSON versionado, distinguir interface/motor/catálogo, filtros por disponibilidade comercial, altura máxima e famílias permitidas. Identificar o espaço de busca e quantas alternativas foram efetivamente analisadas.

Aceitação: cada solução da busca deve reproduzir o cálculo da mesma geometria e dos mesmos perfis pelo modo manual. Não liberar ranking incompleto por erro ou limite de recursos.

## Etapa 2 — Modelo explícito, ações e diagnóstico

2A. Nós e barras com nomes estáveis; planta de bases; tabela de reações por combinação com esforços simultâneos e convenção de sinais. Separar reação do apoio sobre a estrutura da ação transmitida à fundação; não montar um vetor fictício misturando máximos de combinações distintas.

2B. Diagramas calculados: deformada do pórtico, deslocamento horizontal de colunas, flecha de vigas, N/V/M, marcas do máximo. Flecha absoluta e relativa à corda claramente distintas. Para cobertura, incluir terças após integrar seu modelo. Escala de deformação ampliada deve aparecer no gráfico. O limite continua sendo verificado pela rotina de extremos, não pelo número de pontos desenhados.

2C. Guia Pórtico para escolher perfis e rodar um modelo explicitamente definido. Reutilizar o mesmo modelo na otimização. Isolar um pórtico exige identificar quais cargas tributárias ele recebe; não extrair uma fatia e assumir que ela representa automaticamente o conjunto.

2D. Modos de ação horizontal: total uniforme; total proporcional a áreas tributárias; aplicada a uma fachada/alinhamento; cargas por nó. Mostrar nós carregados, coeficientes, somatório e desenho. Em malha regular, pesos relativos 1/4, 1/2 e 1 podem resultar das áreas tributárias de cantos, bordas e interiores, mas não descrevem universalmente a distribuição horizontal. Diafragma e rigidez dos sistemas resistentes podem governar a transferência. O usuário deve selecionar e conhecer a hipótese física.

Aceitação: equilíbrio de forças/momentos, comparação de curvas com casos analíticos e software independente, sinais verificados e nenhuma duplicação entre cargas automáticas e manuais.

## Etapa 3 — Mezanino dimensionado e otimização estrutural

Integrar motores normativos já desenvolvidos, após revisão dos arquivos e benchmarks; ELU, interações, cisalhamento, estabilidade, efeitos de segunda ordem aplicáveis, imperfeições, comprimentos destravados e resposta nas duas direções. Combinações rastreáveis e coerentes com as normas adotadas. Não presumir travamento eficaz pela simples presença geométrica de uma barra.

Completar massa dos componentes dentro do escopo. ELU e ELS precisam passar para uma alternativa aparecer como dimensionada. Guardar utilização governante, combinação e local. Reanalisar após cada mudança de perfil porque rigidez, esforços e peso próprio podem mudar.

Começar com grupos constantes e depois permitir grupos por pavimento, alinhamento, barra ou simetria. Dar ao usuário controle da quantidade de perfis diferentes: mínimo peso com dezenas de seções distintas pode ser pouco prático.

Para ampliar a busca: filtros físicos comprovados, reaproveitamento de análises compatíveis, busca por etapas e execução em lotes com progresso/cancelamento. Algoritmos heurísticos podem explorar grandes espaços, mas o app deve dizer quando encontrou apenas a melhor alternativa testada, sem prova de ótimo global.

Aceitação: referências independentes para análise e dimensionamento, testes de mudança da combinação governante, casos inviáveis e instáveis, e convergência das atualizações de peso próprio/modelo.

## Etapa 4 — Estrutura específica e vãos desuniformes

Entrada de listas de vãos X/Y, alturas, vínculos e contraventamentos por painel; apoios existentes e regiões onde não se pode colocar coluna. Primeiramente arranjos ortogonais; geometria livre depois. Recalcular áreas tributárias a partir dos espaçamentos reais. Não aplicar automaticamente as proporções 25/50/100 a uma malha irregular.

A guia terá dois usos: verificar perfis escolhidos e otimizar os perfis com geometria fixa. A presença do contraventamento precisa gerar a barra, suas propriedades, vínculos e participação no modelo, não somente um campo visual SIM/NÃO. Restrições arquitetônicas devem impedir a geração de alternativas incompatíveis.

Aceitação: modelo desenhado coincide com nós/barras do solver; carga total preservada; casos com painéis diferentes comparados com software independente.

## Etapa 5 — Cobertura de alma cheia

Integrar os motores W/HP e Ue e fechar as pendências de diafragma, travamentos e comparação 1X × 2X. Preservar áreas tributárias reduzidas nas bordas e na cumeeira, com afastamento da terça em relação à cumeeira como entrada. Vento em diferentes sentidos, sucção e reversão de esforços devem participar das combinações aplicáveis.

Incluir vigas de travamento no topo: posições permitidas nas colunas, cumeeira e alinhamentos intermediários por água, associadas à disposição real de contraventamentos. Verificar a transferência de esforços; não zerar automaticamente o axial das terças ao adicionar uma viga de travamento.

Beirais nas duas direções: separar prolongamento de viga/terça em balanço de um simples prolongamento da telha. Cada solução tem cargas, rigidez e massa próprias.

Apoio sobre concreto: permitir excluir colunas de aço do quantitativo e definir apoios/vínculos ou rigidezes fornecidas. Entregar reações à estrutura existente. A opção não certifica a capacidade do concreto existente e não presume engaste perfeito.

ELS definidos pelo usuário: colunas H/400; cobertura L/250, usando para duas águas o comprimento total inclinado conforme decisão já registrada e buscando o deslocamento vertical máximo, não só a cumeeira; terças L/180 para baixo e L/120 para cima. Demais componentes sem verificação ELS adicional no escopo atual.

Aceitação: análise e massa completas para cada concepção antes de comparar kg/m²; diagramas e caminhos de carga inspecionáveis.

## Etapa 6 — Mísulas e terças contínuas com luvas

Mísulas: comparar ausência/presença, comprimento e altura; extremidades no mezanino e extremidades/cumeeira nas coberturas. O valor de 10% sugerido será ponto inicial editável, não regra normativa universal nem mínimo automaticamente imposto. Registrar se a referência é vão horizontal, comprimento inclinado total ou cada água; essa definição precisa ficar inequívoca na interface antes do dimensionamento.

Modelar geometria/propriedades variáveis e a massa real do perfil cortado; incluir efeito no espaço livre e nos comprimentos destravados. Validar resistência local e transferência de esforços. Uma mísula pode reduzir o perfil principal, mas não garante reduzir massa total ou custo. A ligação rígida necessária precisa ser coerente com a ligação que será executada.

Terças com luvas: definir trechos, sobreposições, continuidade, rigidez de conexão e condições de montagem. A mera sobreposição não autoriza somar inércias como se a ação conjunta fosse perfeita. Validar o modelo contra dados de sistema/ensaios ou procedimento técnico adequado; contar massa da luva, regiões de momento negativo e reversão por sucção. Comparar sistemas simplesmente apoiado, contínuo e com luvas somente com hipóteses de conexão explícitas.

Aceitação: estudos de convergência da discretização e comparação com casos de referência. Não atribuir ganho estrutural a detalhes de conexão que não foram justificados.

## Etapa 7 — Pórticos treliçados

Começar por geometrias paramétricas limitadas: banzos paralelos e cobertura triangular, com tipologias de diagonais predefinidas; variar altura, quantidade de painéis, perfis dos banzos/diagonais/montantes e posição dos apoios de terças.

Separar treliça ideal articulada de modelo com excentricidades, banzos contínuos e cargas fora dos nós. Considerar reversão de esforços, flambagem no plano/fora do plano e travamentos. Contar número de barras, ligações e complexidade de fabricação, além de kg/m². Manter restrições de transporte e montagem como parâmetros de concepção.

Aceitação: tipologia por tipologia validada. Somente depois liberar combinações amplas de geometrias. Comparar soluções completas com vigas de alma cheia usando o mesmo escopo de massa e ações.

## Etapa 8 — Bases e chumbadores [novo escopo autorizado]

O usuário agora solicitou dimensionamento de placas de base e chumbadores, além de quadro de cargas e plano de bases. O quadro/planta vem na etapa 2; o dimensionamento das bases vem após estabilizar esforços ELU e condições de apoio.

Entradas previstas: geometria da base, materiais, concreto, bordas, espessuras, embutimento, armaduras/condições relevantes e sistema de ancoragem. Verificações devem contemplar os modos aplicáveis de aço e concreto e as aprovações/dados do produto escolhido. Tipologias simples primeiro; bases rígidas complexas, enrijecedores e interação com fundação depois.

Compatibilizar rigidez assumida no modelo com a base projetada. Demais ligações viga–coluna, gussets etc. não passam automaticamente a ser dimensionadas pelo app; continuam fora do escopo detalhado salvo nova solicitação. Quando indispensáveis para justificar continuidade/mísulas, seus requisitos devem ser tratados explicitamente.

## Etapa 9 — Biblioteca de concepções e objetivos econômicos

Pesquisa de catálogos em paralelo às etapas estruturais. Registrar fabricante, edição, fonte e condições de validade. Sistemas comerciais dão ideias de arranjo e podem fornecer benchmarks específicos; suas tabelas não são intercambiáveis com qualquer perfil, conexão ou norma.

Além de peso: custo estimado de fabricação, comprimento de solda, número de peças/ligações, transporte, pintura e disponibilidade comercial podem ser objetivos futuros. Mostrar fronteira entre peso, custo e complexidade em vez de esconder tudo em um único índice arbitrário.

## Etapa 10 — Importação de arquitetura e IA assistida

Sequência recomendada: projeto JSON próprio → DXF com camadas/escala → IFC com unidades e objetos → PDF vetorial → imagens raster com OCR. IFC é um formato aberto de intercâmbio BIM; não garante, por si, que o arquivo contenha modelo analítico, cargas ou vínculos corretos.

A IA pode identificar eixos, cotas, obstáculos, regiões livres, apoios aparentes e propor arranjos. A interface deve exibir a origem e a confiança da informação e pedir confirmação de escala, cargas, materiais, vínculos, continuidade e restrições ausentes/ambíguas. Em seguida, o solver determinístico analisa e verifica as alternativas confirmadas.

Meta possível: importar um arranjo, delimitar áreas sem coluna, propor concepções, otimizar perfis/alturas/vãos e emitir resultados rastreáveis. Não prometer que qualquer desenho permite um projeto executivo correto sem decisões e revisão de engenharia. Chamadas à IA exigirão configuração própria, tratamento de dados e custos; nunca colocar chaves no repositório.

## Ordem prática de continuidade

M23-PY-03 entrega o primeiro mecanismo de busca. O próximo incremento deve priorizar modelo identificável, reações e diagramas, junto à integração progressiva de ELU/estabilidade. A busca completa de mezanino vem antes de mísulas, treliças e interpretação automática de desenhos. Essas etapas reutilizam o mesmo núcleo, evitando reescrever uma aplicação para cada tipologia.

## Fontes iniciais consultadas (referências de concepção, não substituem normas brasileiras)

- Steel Construction Info, portal frames: https://steelconstruction.info/topics/design/portal-frames
- Metsec, sistemas de terças: https://www.metsec.com/products/purlins-side-rails/purlins/
- Metsec, sistema com luvas: https://www.metsec.com/products/purlins-side-rails/purlins/sleeved-purlin-system/
- buildingSMART, IFC: https://technical.buildingsmart.org/standards/ifc/

As rotinas normativas de cada nova etapa devem ser conferidas diretamente nas fontes vigentes disponibilizadas para o projeto antes da implementação.


PY12: limite de 1.000 casos integrado ao motor e às buscas; proteção contra atualização incompleta e modo automático de dados como padrão. Prioridade técnica permanece representar vínculos/contraventamentos reais nas duas direções, determinar comprimentos da concepção e incluir seus pesos.
