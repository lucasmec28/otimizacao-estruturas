import json
import math
import pandas as pd
import streamlit as st
import combined_search,member_strength_ui


def show(p,candidates,els,selected,basis,elu_current):
    with st.expander('Busca conjunta de perfis — ELS + N–M–V condicional'):
        st.write('Usa as listas de candidatos da busca ELS, as hipóteses selecionadas e as combinações ELU do painel acima. Recalcula esforços, rigidez e peso próprio em cada conjunto de perfis.')
        st.caption('Os materiais e comprimentos informados por grupo serão aplicados a TODAS as hipóteses e perfis desta busca. Verifique se representam o conjunto. O ranking é condicional, ainda sem segunda ordem e estabilidade global.')
        if basis is None or elu_current is None:
            st.info('Calcule uma hipótese ELU acima para definir as combinações e preencha os dados de dimensionamento.');return
        conditions=dict(midheight_loads=st.session_state.get('flexure_midheight',False),effective_restraints=st.session_state.get('flexure_restraints',False))
        elu=elu_current['inputs']['combinations'];groups=basis['groups']
        count=math.prod(len(v) for v in candidates.values())*len(selected)*(len(els)+len(elu))
        st.write(f'Casos solicitados: **{count} / {combined_search.MAX_CASES}**, contando análises ELS e ELU.')
        valid=all(conditions.values()) and 0<count<=combined_search.MAX_CASES
        sig=combined_search.signature(p,candidates,els,elu,selected,groups,conditions)
        if st.button('Buscar por ELS e N–M–V',key='combined_run',disabled=not valid):
            st.session_state.pop('combined_result',None);bar=st.progress(0.)
            try:st.session_state.combined_result=combined_search.run(p,candidates,els,elu,selected,groups,conditions,lambda n,total:bar.progress(n/total))
            except Exception as exc:st.error(f'Busca interrompida sem liberar ranking incompleto: {exc}')
            finally:bar.empty()
        r=st.session_state.get('combined_result')
        if not r:return
        if r['signature']!=sig:
            st.warning('Entradas alteradas. Refaça a busca conjunta.');return
        rows=pd.DataFrame(r['summaries'])
        if r['best_conditional_solution'] is None:st.warning('Nenhuma alternativa atende a todos os critérios condicionais implementados sem pendências por barra.')
        else:
            best=next(x for x in r['summaries'] if x['solution']==r['best_conditional_solution'])
            st.info(f'Menor subtotal no escopo condicional: {best["kg_m2"]:.3f} kg/m² · solução {best["solution"]}. Não é aprovação estrutural final.')
        st.dataframe(rows.rename(columns={'solution':'Solução','hypothesis':'Hipótese','kg_m2':'kg/m²','within_conditional_scope':'Atende ao escopo condicional','pending_members':'Barras com pendências'}),hide_index=True)
        sid=st.selectbox('Detalhar verificações da busca conjunta',rows.solution.tolist(),key='combined_detail')
        member_strength_ui.display(next(d['nmv'] for d in r['details'] if d['solution']==sid))
        st.download_button('Baixar busca conjunta',json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False),file_name='busca_conjunta_py09.json',mime='application/json',key='combined_download')
