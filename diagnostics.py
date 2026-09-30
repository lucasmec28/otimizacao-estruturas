"""Views of solver-derived reactions and exact first-order displacement fields."""
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import grid_names
from numpy.polynomial import Polynomial


def base_plan(bases):
    lx=max(b['x_mm'] for b in bases);ly=max(b['y_mm'] for b in bases)
    scale=min(740/max(lx,1),360/max(ly,1))
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 940 500" role="img" aria-label="Plano de bases com identificação dos nós">',
           '<rect width="940" height="500" fill="#f5f8fc" rx="12"/>',
           '<g font-family="Arial" fill="#17324d"><text x="30" y="30" font-size="20">PLANO DE BASES · FILAS A, B… (+Y) · EIXOS 1, 2… (+X)</text>']
    for y in sorted({b['y_mm'] for b in bases}):
        z=440-y*scale
        parts.append(f'<line x1="80" y1="{z}" x2="{80+lx*scale}" y2="{z}" stroke="#bed0e2"/>')
    for x in sorted({b['x_mm'] for b in bases}):
        xx=80+x*scale
        parts.append(f'<line x1="{xx}" y1="440" x2="{xx}" y2="{440-ly*scale}" stroke="#bed0e2"/>')
    for b in bases:
        x=80+b['x_mm']*scale;y=440-b['y_mm']*scale
        parts.append(f'<rect x="{x-5}" y="{y-5}" width="10" height="10" fill="#2856a6"/>')
        parts.append(f'<text x="{x+8}" y="{y-10}" font-size="13">{grid_names.base(b["frame"],b["column"])}</text>')
    for j,y in enumerate(sorted({b['y_mm'] for b in bases}),1):
        yy=440-y*scale
        parts.append(f'<circle cx="35" cy="{yy}" r="15" fill="white" stroke="#2856a6"/><text x="35" y="{yy+5}" text-anchor="middle">{grid_names.fila(j)}</text>')
    for i,x in enumerate(sorted({b['x_mm'] for b in bases}),1):
        xx=80+x*scale
        parts.append(f'<circle cx="{xx}" cy="475" r="15" fill="white" stroke="#2856a6"/><text x="{xx}" y="480" text-anchor="middle">{i}</text>')
    parts.append('</g></svg>')
    return ''.join(parts)


def reaction_table(full):
    rows=[]
    for case in full:
        co=case['combination']
        for b in case['result']['base_reactions']:
            rows.append({'Combinação':co['id'],'Família':co['family'],'Base':grid_names.base(b['frame'],b['column']),
                'X (m)':b['x_mm']/1000,'Y (m)':b['y_mm']/1000,
                'Rx apoio→estrutura (kN)':b['Rx_N']/1000,'Rz apoio→estrutura (kN)':b['Rz_N']/1000,
                'M plano apoio→estrutura (kN·m)':b['M_plane_Nmm']/1e6,
                'Fx estrutura→fundação (kN)':-b['Rx_N']/1000,'Fz estrutura→fundação (kN)':-b['Rz_N']/1000,
                'M plano estrutura→fundação (kN·m)':-b['M_plane_Nmm']/1e6})
    return rows


def samples(pieces):
    rows=[]
    for piece in pieces:
        absolute=Polynomial(piece['absolute_coefficients'])
        relative=None if piece['relative_coefficients'] is None else Polynomial(piece['relative_coefficients'])
        ts=list(np.linspace(0,1,41))
        for poly in (absolute,relative):
            if poly is not None:
                ts.extend(float(t.real) for t in poly.deriv().roots() if abs(t.imag)<1e-9 and 0<t.real<1)
        for t in sorted(set(ts)):
            row={'Posição (m)':(piece['start_mm']+t*(piece['end_mm']-piece['start_mm']))/1000,
                 'Deslocamento absoluto (mm)':float(absolute(t))}
            if relative is not None:row['Relativo à corda (mm)']=float(relative(t))
            rows.append(row)
    return pd.DataFrame(rows).drop_duplicates('Posição (m)').sort_values('Posição (m)')


def show(full,key):
    st.subheader('Bases e deslocamentos calculados')
    st.warning('Reações de combinações ELS do modelo parcial X–Z. Não usar este quadro para dimensionar bases/chumbadores: ELU e ações na direção Y ainda não estão integrados.')
    bases=full[0]['result']['base_reactions']
    with st.expander('Plano de bases e quadro de reações',expanded=False):
        if len(bases)<=80:st.image(base_plan(bases),width='stretch')
        else:st.info('Plano muito denso para rotular: consulte a identificação e as coordenadas na tabela.')
        st.caption('Filas A, B, C… crescem em +Y; eixos 1, 2, 3… em +X. Base A1 é o encontro da fila A com o eixo 1; topo T-A1. Os identificadores internos numéricos são preservados no JSON para rastreabilidade.')
        st.write('**Sinais:** X positivo para a direita; Z positivo para cima. M plano positivo anti-horário na vista X–Z. Na convenção tridimensional destrógira, Mᵧ = −M plano. Ações transmitidas à fundação têm sinal oposto às reações sobre a estrutura. Direção Y não calculada.')
        st.dataframe(pd.DataFrame(reaction_table(full)),hide_index=True)
        st.caption('Cada linha mantém os esforços simultâneos da mesma combinação. Não é um envelope que mistura máximos de combinações diferentes.')
        st.write('Erro relativo máximo de equilíbrio:',max(c['result']['force_balance'] for c in full),
                 '· momentos:',max(c['result']['moment_balance'] for c in full))
    with st.expander('Diagrama de deslocamento por componente',expanded=False):
        ids=[c['combination']['id'] for c in full]
        co=st.selectbox('Combinação do diagrama',ids,key=key+'_comb')
        data=next(c['result'] for c in full if c['combination']['id']==co)
        labels={'COLUNA_X':'Coluna — horizontal X','PRINCIPAL':'Viga principal — vertical Z','SECUNDARIA':'Viga secundária — vertical Z'}
        component=st.selectbox('Componente do diagrama',list(labels),format_func=labels.get,key=key+'_component')
        curves=[c for c in data['displacement_curves'] if c['component']==component]
        member=st.selectbox('Barra',list(dict.fromkeys(c['member'] for c in curves)),format_func=grid_names.member,key=key+'_member_'+component)
        pieces=[c for c in curves if c['member']==member]
        values=samples(pieces)
        melted=values.melt(id_vars='Posição (m)',var_name='Curva',value_name='Deslocamento (mm)')
        plot=alt.Chart(melted).mark_line().encode(
            x=alt.X('Posição (m):Q',title=pieces[0]['abscissa']+' (m)',axis=alt.Axis(tickCount=7)),
            y=alt.Y('Deslocamento (mm):Q',title=pieces[0]['ordinate']+' (mm)'),
            color=alt.Color('Curva:N',legend=alt.Legend(orient='bottom',labelLimit=400)),
            tooltip=['Posição (m):Q','Curva:N','Deslocamento (mm):Q'])
        zero=alt.Chart(pd.DataFrame({'zero':[0.]})).mark_rule(color='#667085',strokeDash=[4,4]).encode(y='zero:Q')
        ends=values.iloc[[0,-1]]
        points=alt.Chart(ends).mark_point(filled=True,size=65,color='#17324d').encode(x='Posição (m):Q',y='Deslocamento absoluto (mm):Q',tooltip=['Posição (m):Q','Deslocamento absoluto (mm):Q'])
        st.altair_chart(plot+zero+points,width='stretch')
        st.caption('Pontos escuros: extremidades da barra na curva absoluta. Linha tracejada: deslocamento zero. A curva relativa à corda é zero nas extremidades; a absoluta inclui o movimento dos apoios.')
        peak=values.iloc[values['Deslocamento absoluto (mm)'].abs().argmax()]
        st.write(f'Extremo da curva: **{peak["Deslocamento absoluto (mm)"]:.4f} mm** em **{peak["Posição (m)"]:.4f} m**.')
        st.caption('Curvas recuperadas dos polinômios do solver, incluindo raízes da derivada. Posições medidas a partir da base da coluna ou do início do vão. Valores negativos de Z indicam deslocamento para baixo.')
        if component=='COLUNA_X':
            top=values.iloc[-1]['Deslocamento absoluto (mm)']
            st.write(f'Critério H/{data["limits"]["column"]:g}: deslocamento do topo relativo à base = {top:.4f} mm; limite = {pieces[0]["limit_mm"]:.4f} mm. O extremo intermediário da curva não substitui o critério de topo definido para esta versão.')
        else:
            st.write(f'Limite de deslocamento absoluto adotado: {pieces[0]["limit_mm"]:.4f} mm. A curva relativa à corda mostra separadamente a flexão entre apoios; ela não substitui o critério absoluto.')
        st.caption('Exemplo: C-A1; VP-A-2/3 (fila A, entre eixos 2 e 3); VS-A/B-S2 (entre filas A e B, segundo alinhamento de secundárias em X). Terças de cobertura serão incluídas após integrar o modelo de cobertura.')
    with st.expander('Diagramas N, V e M — combinação ELS',expanded=False):
        co=st.selectbox('Combinação dos esforços',[c['combination']['id'] for c in full],key=key+'_force_comb')
        data=next(c['result'] for c in full if c['combination']['id']==co)
        pieces_all=data['force_diagrams']
        member=st.selectbox('Barra dos esforços',list(dict.fromkeys(c['member'] for c in pieces_all)),format_func=grid_names.member,key=key+'_force_member')
        quantity=st.selectbox('Esforço',['N','V','M'],key=key+'_force_quantity')
        pieces=[c for c in pieces_all if c['member']==member]
        values=force_samples(pieces,quantity)
        unit='kN·m' if quantity=='M' else 'kN'
        chart=alt.Chart(values).mark_line().encode(x=alt.X('Posição (m):Q',axis=alt.Axis(tickCount=7)),
            y=alt.Y('Valor:Q',title=f'{quantity} ({unit})'),detail='Trecho:N',order='Posição (m):Q',
            tooltip=['Posição (m):Q','Valor:Q','Trecho:N'])
        zero=alt.Chart(pd.DataFrame({'zero':[0.]})).mark_rule(color='#667085',strokeDash=[4,4]).encode(y='zero:Q')
        st.altair_chart(chart+zero,width='stretch')
        st.write(f'Mínimo: **{values.Valor.min():.4f} {unit}** · máximo: **{values.Valor.max():.4f} {unit}**')
        st.caption('Eixos locais: coluna da base ao topo; principal em +X; secundária em +Y. N positivo em tração; M = EI·v″; V = dM/ds. Para vigas horizontais com eixo transversal positivo para cima, M positivo é sagente. Na coluna, o eixo transversal local aponta para −X. Saltos de V nas cargas concentradas são preservados por trechos.')
        st.caption('Esforços do modelo ELS de primeira ordem. Nas secundárias, N = 0 decorre do modelo biapoiado de flexão, que ainda não representa diafragma ou coleta de esforços axiais. Não são verificações resistentes ELU.')


def force_samples(pieces,quantity):
    rows=[];divisor=1e6 if quantity=='M' else 1000
    for index,piece in enumerate(pieces):
        poly=Polynomial(piece[quantity+'_coefficients'])
        ts=list(np.linspace(0,1,31))+[float(t.real) for t in poly.deriv().roots() if abs(t.imag)<1e-9 and 0<t.real<1]
        for t in sorted(set(ts)):
            rows.append({'Posição (m)':(piece['start_mm']+t*(piece['end_mm']-piece['start_mm']))/1000,
                         'Valor':float(poly(t))/divisor,'Trecho':index+1})
    return pd.DataFrame(rows)
