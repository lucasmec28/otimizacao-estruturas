import json
import pandas as pd
import streamlit as st
import member_strength,grid_names


def display(result):
    records=[]
    labels={'WITHIN_CONDITIONAL_FIRST_ORDER_CHECKS':'Dentro dos critérios condicionais','EXCEEDS_IMPLEMENTED_CHECKS':'Excede critérios','PENDING':'Pendente'}
    for r in result['rows']:
        w=r.get('governing',{})
        records.append({'Barra':grid_names.member(r['member']),'Perfil':r['profile'],'Combinação':r['combination'],
            'η governante':r.get('eta'),'Critério':w.get('check'),'Posição (m)':w.get('x_mm',0)/1000 if w else None,
            'N simultâneo (kN)':w.get('N_N',0)/1000 if w else None,'V simultâneo (kN)':w.get('V_N',0)/1000 if w else None,
            'M simultâneo (kN·m)':w.get('M_Nmm',0)/1e6 if w else None,
            'Situação':labels[r['status']],'Pendências':'; '.join(r['pending'])})
    st.dataframe(pd.DataFrame(records),hide_index=True)
    st.caption('η governante é o maior entre axial, flexão isolada, cisalhamento e interação N–M. N/V/M da tabela são simultâneos no ponto governante. Para cortante em apenas um eixo, aplica-se 5.5.1.3/5.4.3. Mudanças de ramo da interação incluem limites laterais conservadores. A análise continua de primeira ordem.')


def show(elu,basis,conditions):
    st.subheader('Verificações conjuntas N–M e cisalhamento')
    if basis is None or not all(conditions.values()):
        st.info('Preencha materiais/comprimentos e defina as condições de carga e contenção acima.');return
    try:result=member_strength.evaluate(elu,basis,conditions)
    except (ValueError,TypeError,KeyError) as exc:st.error(str(exc));return
    display(result)
    st.warning('Resultado condicional: segunda ordem, imperfeições, estabilidade Y e efeitos locais ainda pendentes. Tração verifica apenas escoamento bruto e permanece pendente quanto à seção líquida.')
    st.download_button('Baixar verificações N–M–V',json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),file_name='verificacoes_nmv_py09.json',mime='application/json',key='nmv_download')
