import json
import check_cache
import pandas as pd
import streamlit as st
import flexure_check,grid_names


def show(elu,basis):
    st.subheader('Flexão forte W/HP — comparação isolada e condicional')
    st.caption('FLT, FLM e FLA pela NBR 8800, Anexo D. γa1 = 1,10. Este quadro verifica apenas flexão isolada; o bloco N–M–V usa os esforços do modelo ELU selecionado. Estabilidade global permanece condicional. Não altera o ranking ELS. Nesta integração por grupo, Cb deve ser 1; não há geração automática de trechos contidos.')
    if basis is None:
        st.info('Corrija os dados do painel de materiais e travamentos.');return
    mid=st.checkbox('Para este estudo, as cargas transversais atuam na semialtura da seção, conforme a hipótese de FLT usada.',key='flexure_midheight')
    restraint=st.checkbox('Os Lb informados são limites superiores aplicáveis aos trechos de cada grupo e sinal, com contenções eficazes justificadas.',key='flexure_restraints')
    if not (mid and restraint):
        st.info('A comparação fica pendente enquanto estas condições do modelo não forem definidas. Cargas aplicadas em outra altura exigem tratamento ainda não implementado.');return
    try:result=check_cache.get_or_compute('flexure',dict(elu=elu['signature'],basis=basis,conditions=dict(midheight_loads=mid,effective_restraints=restraint)),lambda:flexure_check.evaluate(elu,basis,dict(midheight_loads=mid,effective_restraints=restraint)))
    except (ValueError,TypeError,KeyError) as exc:
        st.error(str(exc));return
    labels={'WITHIN_ISOLATED_FLEXURE':'Dentro do limite de flexão isolada','EXCEEDS_ISOLATED_FLEXURE':'Excede flexão isolada','PENDING':'Pendente'}
    records=[]
    for r in result['rows']:
        c=r.get('capacity',{});limits=c.get('limits_Nmm',{})
        records.append({'Barra':grid_names.member(r['member']),'Combinação':r['combination'],
            'Sinal de M':r['sign'],'Posição (m)':r['x_mm']/1000,'Msd (kN·m)':r['M_Nmm']/1e6,
            'N simultâneo (kN)':r['N_N']/1000,'V simultâneo (kN)':r['V_N']/1000,
            'MRd (kN·m)':c.get('MRd_Nmm',0)/1e6 if c else None,
            'FLT (kN·m)':limits.get('FLT',0)/1e6 if c else None,
            'FLM (kN·m)':limits.get('FLM',0)/1e6 if c else None,
            'FLA (kN·m)':limits.get('FLA',0)/1e6 if c else None,
            'η M isolado':r.get('eta_M'),'Governante':c.get('governing'),
            'Situação':labels[r['status']],'Pendência':r.get('reason','')})
    st.dataframe(pd.DataFrame(records),hide_index=True)
    st.warning('Mesmo quando η M ≤ 1, a barra e a estrutura ainda não estão aprovadas. N e V simultâneos são mostrados para rastreabilidade, mas suas interações não foram verificadas.')
    st.download_button('Baixar comparação de flexão isolada',json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),file_name='flexao_isolada_py13.json',mime='application/json',key='flexure_download')
