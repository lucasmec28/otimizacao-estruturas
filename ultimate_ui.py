import json
import pandas as pd
import streamlit as st
import altair as alt
import ultimate,diagnostics,grid_names
import design_basis_ui
import flexure_ui


def show(p,profiles,gid,basis=None):
    with st.expander('Análise preparatória ELU — perfis fixos da hipótese detalhada',expanded=False):
        st.warning('Somente esforços de primeira ordem em X–Z, com E integral e coeficientes manuais. Sem verificação resistente, imperfeições ou efeitos de segunda ordem. Este painel não aprova perfis e não altera o ranking ELS.')
        st.write(f'Geometria: **{gid}** · Colunas: **{profiles["column"]}** · Principais: **{profiles["primary"]}** · Secundárias: **{profiles["secondary"]}**')
        st.caption('Defina abaixo as combinações ELU. Os zeros iniciais são campos a preencher, não uma combinação de projeto. Ações características são as informadas acima; Hx segue a distribuição uniforme por todos os topos.')
        rows=st.data_editor(pd.DataFrame([dict(id='ELU_01',G_STEEL=0.,G_FLOOR=0.,Q=0.,HX=0.)]),num_rows='dynamic',hide_index=True,key='elu_combinations')
        confirmed=st.checkbox('Defini os coeficientes ELU para este estudo; compreendo o escopo de primeira ordem.',key='elu_confirm')
        try:current=ultimate.signature(p,profiles,gid,rows.to_dict('records'))
        except (ValueError,TypeError):
            st.error('Complete a tabela de coeficientes.');return
        if st.button('Calcular esforços ELU',disabled=not confirmed,key='elu_run'):
            st.session_state.pop('elu_result',None)
            try:
                with st.spinner('Calculando ações ELU…'):st.session_state.elu_result=ultimate.calculate(p,profiles,gid,rows.to_dict('records'))
            except Exception as exc:st.error(f'Análise ELU interrompida: {exc}')
        result=st.session_state.get('elu_result')
        if not result:return
        if not confirmed or result['signature']!=current:
            st.warning('Entradas ELU ou hipótese alteradas. Calcule novamente.');return
        design_basis_ui.show_demands(result)
        flexure_ui.show(result,basis)
        st.caption('Reações por combinação, preservando simultaneidade e sinais. Valores ainda não suficientes para dimensionamento de fundações ou bases.')
        st.dataframe(pd.DataFrame(diagnostics.reaction_table(result['full'])),hide_index=True)
        cid=st.selectbox('Combinação ELU do diagrama',[x['combination']['id'] for x in result['full']],key='elu_plot_comb')
        case=next(x['result'] for x in result['full'] if x['combination']['id']==cid)
        member=st.selectbox('Barra ELU',list(dict.fromkeys(x['member'] for x in case['force_diagrams'])),format_func=grid_names.member,key='elu_member')
        quantity=st.selectbox('Esforço ELU',['N','V','M'],key='elu_quantity')
        values=diagnostics.force_samples([x for x in case['force_diagrams'] if x['member']==member],quantity)
        unit='kN·m' if quantity=='M' else 'kN'
        chart=alt.Chart(values).mark_line().encode(x=alt.X('Posição (m):Q',axis=alt.Axis(tickCount=7)),y=alt.Y('Valor:Q',title=f'{quantity} ({unit})'),detail='Trecho:N',order='Posição (m):Q',tooltip=['Posição (m):Q','Valor:Q'])
        st.altair_chart(chart,width='stretch')
        st.caption('N positivo em tração; M = EI·v″ e V = dM/ds. Mesma convenção local dos diagramas ELS. Nas secundárias, N = 0 por hipótese do modelo de flexão biapoiada.')
        st.download_button('Baixar análise ELU preliminar',json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),file_name='analise_elu_py06.json',mime='application/json')
