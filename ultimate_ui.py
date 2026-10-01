import json
RELEASE_VERSION='M23-PY-13'
import pandas as pd
import streamlit as st
import altair as alt
import ultimate,diagnostics,grid_names
import design_basis_ui
import flexure_ui
import member_strength_ui
import second_order


def show(p,profiles,gid,basis=None,generated=None):
    with st.expander('Análise preparatória ELU — perfis fixos da hipótese detalhada',expanded=False):
        st.warning('Análise X–Z e verificações condicionais. Combinações selecionadas acima; sem aprovação estrutural final. A segunda ordem exige convergência de malha; estabilidade Y permanece pendente.')
        mode=st.selectbox('Modelo de análise ELU',['Primeira ordem','Segunda ordem X com forças nocionais'],key='elu_order')
        options=None;max_seconds=180.
        if mode.startswith('Segunda'):
            options=dict(second_order.DEFAULTS)
            a,b=st.columns(2)
            options['reduction']=a.number_input('Fator de rigidez EA/EI em ELU',min_value=.1,max_value=1.,value=.8,step=.05,key='so_reduction')
            options['notional_ratio']=b.number_input('Fração nocional da carga gravitacional',min_value=0.,max_value=.01,value=.003,step=.001,format='%.4f',key='so_notional')
            max_seconds=st.number_input('Prazo máximo da análise (s)',min_value=30.,max_value=600.,value=180.,step=30.,key='elu_timeout')
            st.caption('Calcula os dois sentidos nocionais, somados às forças horizontais informadas. 0,003 corresponde a 0,3%. Distribuição pela reação gravitacional de cada coluna, incluindo peso próprio. EA/EI reduzidos somente na análise ELU. A seleção não certifica a aplicabilidade normativa ao projeto.')
            st.caption('Malha adaptativa: 4 → 8 → até 16 divisões por coluna; convergência de momentos e deslocamentos em 1%. Formulação de eixos iniciais e pequenas rotações; não é análise corrotacional.')
        st.write(f'Geometria: **{gid}** · Colunas: **{profiles["column"]}** · Principais: **{profiles["primary"]}** · Secundárias: **{profiles["secondary"]}**')
        st.caption('Confira as combinações ELU. No modo manual, preencha os coeficientes inicialmente zerados. Ações características são as informadas acima; Hx segue a distribuição uniforme por todos os topos.')
        if generated is not None:
            if not generated['elu']:
                st.info('Selecione ELU normal no painel de famílias para executar esta análise.');return
            rows=pd.DataFrame(generated['elu'])
            st.caption('Coeficientes recebidos automaticamente do gerador de combinações.')
        else:
            rows=st.data_editor(pd.DataFrame([dict(id='ELU_01',G_STEEL=0.,G_FLOOR=0.,Q=0.,HX=0.)]),num_rows='dynamic',hide_index=True,key='elu_combinations')
        confirmed=st.checkbox('Conferi as combinações ELU e compreendo o modelo selecionado e suas limitações.',key='elu_confirm')
        try:current=ultimate.signature(p,profiles,gid,rows.to_dict('records')) if options is None else second_order.signature(p,profiles,gid,rows.to_dict('records'),options)
        except (ValueError,TypeError):
            st.error('Complete a tabela de coeficientes.');return
        if st.button('Calcular esforços ELU',disabled=not confirmed,key='elu_run'):
            st.session_state.pop('elu_result',None)
            bar=st.progress(0.,text='Preparando ações ELU…')
            def update(event):
                label=f"{event['done']}/{event['total']} casos · {event['elapsed']:.1f} s · {event.get('combination','')} · {event['stage']}"
                bar.progress(event['done']/max(1,event['total']),text=label)
            try:
                with st.spinner('Calculando ações ELU e convergência…'):
                    st.session_state.elu_result=ultimate.calculate(p,profiles,gid,rows.to_dict('records')) if options is None else second_order.calculate(p,profiles,gid,rows.to_dict('records'),options,progress=update,max_seconds=max_seconds)
            except Exception as exc:st.error(f'Análise ELU interrompida: {exc}')
            finally:bar.empty()
        result=st.session_state.get('elu_result')
        if not result:return
        if not confirmed or result['signature']!=current:
            st.warning('Entradas ELU ou hipótese alteradas. Calcule novamente.');return
        result['combination_provenance']=generated
        if generated is not None:
            for case in result['full']:case['combination']['family']='ELUN'
        if result.get('performance'):
            perf=result['performance'];st.caption(f"Segunda ordem concluída: {perf['completed_cases']}/{perf['total_cases']} casos · {perf['elapsed_seconds']:.2f} s de cálculo. Tempo da hospedagem pode variar.")
        if result.get('diagnostics'):
            st.subheader('Segunda ordem X — diagnóstico de convergência')
            st.dataframe(pd.DataFrame([dict(Combinação=d['combination'],Malha=d['mesh'],Iterações=d['iterations'],Resíduo=d['relative_residual'],Erro_momentos=d['mesh_history'][-1]['moment_error'],Erro_deslocamentos=d['mesh_history'][-1]['drift_error']) for d in result['diagnostics']]),hide_index=True)
            st.dataframe(pd.DataFrame([dict(Combinação=d['combination'],Coluna=grid_names.member(x['member']),Deslocamento_1a_mm=x['first_mm'],Deslocamento_2a_mm=x['second_mm'],Amplificação=x['amplification']) for d in result['diagnostics'] for x in d['drifts']]),hide_index=True)
            st.caption('As duas ordens usam a mesma rigidez reduzida e o mesmo carregamento, incluindo nocionais. A razão de deslocamentos é diagnóstico local, não classificação normativa automática. Reações exportadas incluem forças nocionais; não são quadro final de fundações.')
        design_basis_ui.show_demands(result)
        flexure_ui.show(result,basis)
        member_strength_ui.show(result,basis,dict(midheight_loads=st.session_state.get("flexure_midheight",False),effective_restraints=st.session_state.get("flexure_restraints",False)))
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
        st.caption('N positivo em tração. Na segunda ordem, M é recuperado por equilíbrio com o termo P–δ, e V = dM/ds; não se reutiliza a parábola de primeira ordem. Nas secundárias, N = 0 por hipótese de flexão biapoiada.')
        st.download_button('Baixar análise ELU preliminar',json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),file_name='analise_elu_py13.json',mime='application/json')

        return result
