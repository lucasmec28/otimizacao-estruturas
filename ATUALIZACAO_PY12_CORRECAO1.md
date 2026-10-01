# Correção PY12-CORRECAO1

O ZIP original contém config.toml dentro de M23_PY12/.streamlit/. A exigência desse arquivo de aparência na conferência de integridade bloqueava o aplicativo quando a subpasta não era enviada ao GitHub. A correção remove esse arquivo da lista obrigatória do manifesto. O arquivo continua incluído no pacote, como opcional.

Não houve alteração das equações, das propriedades do catálogo, dos comprimentos automáticos nem da capacidade de 1.000 casos. A correção mínima no GitHub é substituir release_manifest.json na raiz. O pacote completo pode também substituir todos os arquivos de código, mantendo o mesmo repositório, branch e caminho app.py.

A validação específica cobre abertura e cálculo ELS sem a configuração opcional, preservação do bloqueio de arquivos de cálculo faltantes ou alterados e detecção de manifesto de outra versão. A validação dos 67 testes do pacote PY12 original permanece em validacao_py12.json; não é apresentada como reexecução na revisão.
