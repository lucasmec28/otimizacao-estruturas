# Otimização de estruturas metálicas — M23-PY-01

Checkpoint de 29/09/2026. Aplicação em Python com interface Streamlit no navegador.
Não depende de Excel, VBA ou exportação manual de pedidos. Não publicada online ainda.

## Escopo entregue

- Mezanino: dimensões, faixas de espaçamento, catálogo W/HP e perfis fixos por componente.
- Ações verticais, força horizontal X e combinações explícitas editáveis.
- Limites independentes H/400, L/350 e L/350 inicialmente.
- Geração e seleção de hipóteses; cálculo e ordenação por subtotal de aço.
- Resultados críticos por componente/combinação; detalhamento completo consultável.
- Bloqueio de resultados após mudanças nas entradas.
- Download JSON com entradas e saídas. Ainda sem reabertura de projetos na interface.

## Limitações estruturais

Conserva exatamente o escopo do M22: ELS parcial de primeira ordem, pórticos X com bases engastadas e nós rígidos, vigas secundárias Y biapoiadas. Deslocamentos verticais absolutos incluem movimentos dos apoios. Hx total distribuído igualmente nos topos das colunas. E integral.

Não inclui ELU, segunda ordem, estabilidade global, análise lateral Y, diafragma, cobertura, dimensionamento de travamentos ou escolha automática de perfis. O subtotal inclui somente colunas e vigas principais/secundárias; não equivale ao peso total final. Ligações permanecem fora do escopo por decisão do usuário.

Os valores iniciais e DEMO_G_Q são demonstrativos. Não são combinações normativas predefinidas. O selo 'Atende ao ELS parcial' nunca representa aprovação estrutural final.

## Arquitetura e continuidade

`app.py`: interface Python; `service.py`: validação, geração de hipóteses e chamada do motor; `engine/`: cópia congelada do motor M22; `catalogo.json`: catálogo herdado; `referencia_m22.tsv`: pedido real exportado pelo Excel do usuário.

O serviço monta temporariamente em memória a representação M22 para reaproveitar integralmente os validadores existentes. Não há trânsito de arquivos entre Excel e Python, nem subprocessos. Em etapa futura, o núcleo poderá receber diretamente objetos tipados, mantendo estes testes de equivalência.

Resultados são mantidos por sessão. Não há banco de dados, compartilhamento de projetos ou persistência automática. Baixe o registro antes de encerrar a sessão se desejar preservá-lo. Os arquivos M22 anteriores não foram alterados.

## Execução local para desenvolvimento

Python 3.11 recomendado para reproduzir este checkpoint. Em ambiente autorizado:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Isso abre uma aplicação local no navegador; não a torna acessível pela internet. O computador que hospeda precisa executar Python.

## Publicação para acesso de casa e do trabalho

Uma opção é Streamlit Community Cloud: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app

1. Usar conta GitHub do proprietário e repositório privado com o conteúdo desta pasta.
2. Conectar a conta à hospedagem Streamlit; selecionar repositório, versão Python e `app.py`.
3. Manter o acesso privado e verificar as permissões de quem poderá abrir o aplicativo.
4. Validar online o caso de referência, sessões independentes e acesso pelos dois computadores.

Não há hospedagem configurada nem URL publicada neste checkpoint. Contas e permissões da hospedagem são a pendência externa. Acesso via navegador dispensa instalar Python no computador cliente, mas não garante que a rede corporativa permitirá o endereço. Não contornar bloqueios corporativos.

## Verificação realizada

Teste de paridade exata das 54 linhas de resultados com o pedido M22 do usuário; teste da interface com Streamlit AppTest: abertura, cálculo de 18 hipóteses, alteração de carga, bloqueio de resultados antigos, recálculo e rejeição de intervalo geométrico invertido. Ambos passaram. AppTest simula a interface; não substitui inspeção visual e teste no navegador da hospedagem.

```sh
python -m unittest test_app -v
```

O motor preservado possui ainda sua suíte `engine/test_bridge_m22.py`, com a referência `demo_request.tsv` preservada. Os testes estruturais não foram substituídos pelos testes da interface.

## Próximas etapas

Publicação privada e teste online; completar a análise/verificação do mezanino; seleção automática de perfis e peso total; integrar cobertura; aprimorar desenho, mapa de calor e leitura dos resultados. Excel/PNG ficam para depois da consolidação da aplicação, conforme decisão do usuário.
