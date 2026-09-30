import json
import pandas as pd
import streamlit as st
import design_basis
import grid_names


def show(p, profiles, gid):
    with st.expander('Materiais e travamentos — preparação do dimensionamento'):
        st.write('Registre os dados por grupo para a hipótese detalhada. fy, Lb e Cb alimentam a comparação condicional de flexão; os demais dados ficam registrados para etapas futuras. Não alteram esforços ou ranking. Zero significa dado não preenchido.')
        st.caption(f'E usado na análise: {p["E_mpa"]:g} MPa. Perfis: '+ ' · '.join(f'{design_basis.ROLES[k]}: {v}' for k,v in profiles.items()))
        st.markdown('**Comprimentos em metros:** Lef_x e Lef_y são comprimentos efetivos de flambagem nos eixos locais forte e fraco; Lef_t é o comprimento efetivo para flambagem por torção. Não são necessariamente iguais ao comprimento geométrico da barra.')
        st.markdown('**Lb_positive / Lb_negative:** comprimentos sem contenção lateral eficaz para os trechos de momento positivo e negativo, respectivamente. Nas vigas horizontais, momento positivo comprime a mesa superior. Cb deve corresponder ao trecho considerado. A presença de uma secundária não preenche automaticamente estes campos.')
        st.caption('Um valor por grupo é uma preparação simplificada. A verificação final exigirá os trechos reais, mudanças de sinal e condições de contenção. Em basis, registre aço/certificado, origem dos valores e justificativa dos travamentos.')
        labels={'group':'Grupo', 'fy_MPa':'fy (MPa)', 'fu_MPa':'fu (MPa)', 'G_MPa':'G (MPa)',
                'Lef_x_m':'Lef, eixo forte (m)', 'Lef_y_m':'Lef, eixo fraco (m)',
                'Lef_t_m':'Lef, torção (m)', 'Lb_positive_m':'Lb, M positivo (m)',
                'Lb_negative_m':'Lb, M negativo (m)', 'Cb_positive':'Cb, M positivo',
                'Cb_negative':'Cb, M negativo', 'basis':'Origem e justificativa'}
        st.caption('Grupos: column = colunas; primary = principais; secondary = secundárias. fy: escoamento; fu: ruptura; G: módulo de elasticidade transversal.')
        rows=st.data_editor(pd.DataFrame(design_basis.blank_rows()),hide_index=True,
                            column_config=labels, disabled=['group'],key='design_basis_rows',num_rows='fixed')
        try:
            result=design_basis.make(p,profiles,gid,rows.to_dict('records'))
        except (ValueError,TypeError,KeyError) as exc:
            st.error(f'Dados de dimensionamento: {exc}');return
        if result['pending_inputs']:
            st.info(f'{len(result["pending_inputs"])} campos pendentes. Você pode baixar o registro incompleto para documentar o estudo.')
        else:
            st.info('Campos preenchidos. Materiais e travamentos ainda não foram validados tecnicamente; nenhuma aprovação resistente foi emitida.')
        st.download_button('Baixar dados de dimensionamento',json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),file_name='dados_dimensionamento_py07.json',mime='application/json',key='design_basis_download')
        return result


def show_demands(result):
    with st.container():
        st.subheader('Extremos ELU por barra — esforços simultâneos')
        st.caption('Mínimo e máximo de cada esforço por barra e combinação, preservando os outros esforços no mesmo ponto. Inclui extremos internos exatos dos polinômios e os dois lados das descontinuidades. Estes pontos não substituem a busca do máximo das equações de interação.')
        records=design_basis.extrema(result['full'])
        table=pd.DataFrame([{'Combinação':r['combination'],'Barra':grid_names.member(r['member']),
            'Extremo':r['action']+' '+r['extreme'],'Posição (m)':r['x_mm']/1000,
            'Trecho':r['piece_index']+1,'t no trecho':r['t'],
            'N simultâneo (kN)':r['N_N']/1000,'V simultâneo (kN)':r['V_N']/1000,
            'M simultâneo (kN·m)':r['M_Nmm']/1e6} for r in records])
        selected=st.selectbox('Barra dos extremos ELU',list(table['Barra'].unique()),key='demand_member')
        st.dataframe(table[table['Barra']==selected],hide_index=True)
        st.download_button('Baixar extremos de todas as barras (CSV)',table.to_csv(index=False,sep=';',decimal=',').encode('utf-8-sig'),file_name='extremos_elu_py07.csv',mime='text/csv',key='demand_csv')
