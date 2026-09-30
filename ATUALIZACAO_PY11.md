# PY11 — combinações automáticas e dados da concepção

## Integração

O engine.py enviado foi preservado como combinations_engine.py, alterando somente o nome do arquivo de catálogo para combinations_catalog.json. O catálogo é cópia integral do recebido. Isso evita colisão com a pasta engine do motor estrutural. O banco informa fontes normativas; a presente integração não constitui auditoria integral de todos os fatores e famílias que o gerador independente suporta.

A interface automática oferece ELUN, ELSR, ELSF e ELSQP. O padrão solicitado é ELUN + ELSF. Não são expostas ELUE/ELUC/ELUX porque o modelo estrutural atual não representa suas ações e situações particulares. Pelo fluxo atual, pelo menos uma família ELS precisa ser selecionada.

Mapeamento: caso 1 = peso próprio dos perfis, aço; caso 2 = permanente do piso, natureza escolhida; caso 3 = sobrecarga do piso, categoria de uso escolhida; casos 4/5 = vento +X/−X, quando Hx é informado como vento. Os ventos pertencem a grupo mutuamente exclusivo. Coeficientes permanentes favoráveis/desfavoráveis são enumerados e variáveis podem estar ausentes. As ações são globais: a enumeração não implementa sobrecarga alternada por vãos.

No exemplo inicial sem vento: 8 ELUN e 2 ELSF. Com vento: 32 ELUN e 6 ELSF. Todas são preservadas, inclusive casos com variável ausente. O teto do cálculo ELU fixo foi ampliado de 20 para 200 combinações para comportar a geração. A busca conjunta permanece limitada a 200 casos totais e bloqueia excesso sem truncar.

Os registros exportados pela interface incluem combination_provenance, com projeto, categorias, assinatura, hash do banco e trilha de fatores. A rastreabilidade é acrescentada apenas a resultados correspondentes às entradas atuais. Modo manual fica identificado por provenance nula. O download exclusivo de combinações permite conferência antes de calcular.

## Materiais e comprimentos

W/HP do catálogo: ASTM A572 Grau 50, fy=345 MPa e fu=450 MPa; G=77000 MPa como parâmetro do modelo. Fonte do aço: Gerdau, Folder Perfis Estruturais — Informações Técnicas:
https://www2.gerdau.com/sites/gln_gerdau/files/downloadable_files/Folder%20Perfis%20Estruturais%20Gerdau%20-%20Informa%C3%A7%C3%B5es%20T%C3%A9cnicas.pdf

Não há aplicação desses valores a U laminados/Ue: estes não fazem parte do catálogo executável atual e exigem cadastro específico de material e procedimento resistente.

A política GEOMETRIC_PRELIMINARY_V1 preenche colunas com 2H e vigas com seu vão integral, Cb=1, sem creditar travamentos intermediários. É uma referência geométrica simplificada, não uma solução de flambagem nem garantia de conservadorismo para qualquer pórtico. A busca recalcula esses valores para cada hipótese e os preserva em nmv.basis. A validação de vínculos permanece pendente por barra, impedindo classificar a alternativa automática como atendida no escopo condicional. O modo manual avançado permanece disponível.

## Validação

Os testes adicionados conferem coeficientes do cenário padrão, exclusão dos ventos opostos, simetria dos sinais, seleção de famílias, assinatura por categoria de uso, execução de todos os 32 casos ELU com vento e 6 ELS, comprimentos por geometria e bloqueio de aprovação com comprimentos preliminares. A busca de duas geometrias confirma o recálculo dos dados por hipótese.

O arquivo TEST_RESULTS recebido refere-se aos testes do gerador no chat de origem. Seus testes não foram anexados; não se afirma que foram reexecutados aqui. Os testes locais e seu resultado estão registrados em validacao_py11.json.

## Próximos passos

Prioridade: representar contraventamentos e vínculos reais nas duas direções, derivar comprimentos/trechos a partir da concepção e incluir o peso dos travamentos. Em seguida ampliar a busca com controle de execução e avançar nos vãos desuniformes e coberturas. Não é adequado considerar concluída a otimização estrutural apenas pela geração das combinações.
