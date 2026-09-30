import json
import pandas as pd
import streamlit as st
import combinations_adapter as adapter
import combinations_engine as ce


def show(p):
    mode=st.radio('Definição das combinações',['Automática','Manual avançada'],horizontal=True,key='combo_mode')
    if mode=='Manual avançada':return None
    families=st.multiselect('Famílias de combinações',adapter.SUPPORTED,default=['ELUN','ELSF'],format_func=lambda k:ce.FAMILIES[k],key='combo_families')
    a,b=st.columns(2)
    types=[r['code'] for r in ce.BANK['types'] if r['nature']=='G direta']
    floor=a.selectbox('Natureza da carga permanente do piso',types,index=types.index('GER'),format_func=lambda k:ce.TYPES[k]['label'],key='combo_floor_type')
    occupancy=b.selectbox('Uso do piso para fatores ψ',['USO1','USO2','USO3'],index=2,format_func=lambda k:ce.PROFILES[k]['label'],key='combo_occupancy')
    horizontal='NONE'
    if p['hx_total_kn']!=0:
        choice=st.selectbox('Natureza da força horizontal X',['Selecionar','Vento — testar +X e −X'],key='combo_horizontal')
        if choice=='Selecionar':
            st.info('Informe a natureza de Hx. Para ações horizontais de outra origem, use o modo manual avançado.');return {'error':True}
        horizontal='WIND_X'
    try:r=adapter.generate(families,floor,occupancy,horizontal)
    except ValueError as exc:st.error(str(exc));return {'error':True}
    if not r['els']:
        st.info('Este fluxo do mezanino exige ao menos uma família ELS para calcular e comparar geometrias.');return {'error':True}
    st.caption('NBR 8800:2024 · banco enviado do gerador PY02. ELU normal e ELS frequente selecionadas inicialmente. Permanentes favoráveis/desfavoráveis e presença/ausência de variáveis são enumeradas; ventos opostos são incompatíveis. A natureza do piso e seu uso definem os fatores, não o peso informado.')
    st.write(f'**{len(r["elu"])} combinações ELU · {len(r["els"])} combinações ELS**')
    with st.expander('Conferir coeficientes e fontes'):
        st.dataframe(pd.DataFrame(r['elu']+r['els']),hide_index=True)
        st.download_button('Baixar combinações e rastreabilidade',json.dumps(r,ensure_ascii=False,indent=2,default=str),file_name='combinacoes_mezanino_py11.json',mime='application/json',key='combos_audit')
    return r
