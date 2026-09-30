"""Browser interface, authored entirely in Python."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
import streamlit as st
import service


def plan_svg(p, g):
    """Plan from the actual solver grid, with equal X/Y scale."""
    lx, ly = p['lx_mm']/1000, p['ly_mm']/1000
    nx, ny, ns = g['nx'], g['ny'], g['secondary_intervals_per_x_bay']
    sx, sy, es = lx/nx, ly/ny, lx/(nx*ns)
    scale = min(480/lx, 330/ly)
    x0, bottom = 70, 410
    right, top = x0+lx*scale, bottom-ly*scale
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 940 510" role="img" aria-label="Planta: principais em X, secundárias em Y, espaçamento das secundárias medido em X">',
             '<rect width="940" height="510" rx="16" fill="#f5f8fc"/>']
    def line(x1,y1,x2,y2,color,width=2):
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>')
    def text(x,y,value,color='#17324d',size=16):
        parts.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,sans-serif" font-size="{size}">{value}</text>')
    text(30,32,f'PLANTA · HIPÓTESE {g["id"]}',size=20)
    for i in range(nx*ns+1):
        x=x0+i*es*scale
        line(x,top,x,bottom,'#008b8b',2)
    for j in range(ny+1):
        y=bottom-j*sy*scale
        line(x0,y,right,y,'#2856a6',5)
        for i in range(nx+1):
            x=x0+i*sx*scale
            parts.append(f'<rect x="{x-4}" y="{y-4}" width="8" height="8" fill="#17324d"/>')
    line(x0,bottom+24,x0+es*scale,bottom+24,'#9333b8',3)
    for x in (x0,x0+es*scale):line(x,bottom+17,x,bottom+31,'#9333b8')
    text(x0,bottom+54,f'e = {es:.3f} m · medido em X','#9333b8')
    line(25,410,25,345,'#17324d')
    line(25,345,20,355,'#17324d');line(25,345,30,355,'#17324d')
    text(16,334,'Y')
    line(70,488,145,488,'#17324d')
    line(145,488,135,483,'#17324d');line(145,488,135,493,'#17324d')
    text(155,494,'X')
    text(600,85,'Principais → direção X','#2856a6',20)
    text(600,116,f'Vão entre colunas: {sx:.3f} m')
    text(600,168,'Secundárias → direção Y','#008b8b',20)
    text(600,199,f'Vão entre principais: {sy:.3f} m')
    text(600,251,'Espaçamento das secundárias','#9333b8',18)
    text(600,280,f'e = vão X / {ns} = {es:.3f} m')
    text(600,330,f'Dimensões: X = {lx:g} m; Y = {ly:g} m')
    text(600,360,f'{nx} vãos X · {ny} vãos Y')
    text(600,390,f'■ {(nx+1)*(ny+1)} colunas nos nós principais')
    text(600,430,'Vista de cima; colunas na direção Z.',size=15)
    text(600,455,'Seções e ligações não estão em escala.',size=15)
    parts.append('</svg>')
    return ''.join(parts)


def show_plan(p, g):
    if g['nx']*g['secondary_intervals_per_x_bay']+g['ny']+(g['nx']+1)*(g['ny']+1)>5000:
        st.info('Malha muito densa para a prévia. Consulte os espaçamentos na tabela de modulações.')
        return
    st.image(plan_svg(p,g),width='stretch')
    st.caption('Azul: principais em X. Verde: secundárias em Y, biapoiadas em cada vão Y. Quadrados: colunas. Cruzamentos intermediários são apoios das secundárias nas principais, sem coluna adicional.')

st.set_page_config(page_title='LRO | Otimização estrutural', page_icon='🏗️', layout='wide')
st.title('Otimização de estruturas metálicas')
st.caption('M23-PY-02 · Mezanino · Planta e orientação dos espaçamentos')
st.warning('ELS parcial: análise elástica de primeira ordem dos pórticos X e vigas secundárias. Sem ELU, estabilidade global, análise lateral Y ou seleção automática de perfis. Atender aqui não significa aprovação estrutural.')

p0, s0 = service.defaults()
p = {}
with st.sidebar:
    st.header('Projeto')
    study = st.text_input('Identificação', 'DEMONSTRAÇÃO')
    st.caption('Valores iniciais demonstrativos. Defina as ações do seu projeto antes de utilizar os resultados.')
    st.subheader('Dimensões em metros')
    for k, label in [('lx_mm','Comprimento X'),('ly_mm','Comprimento Y'),('height_mm','Altura das colunas')]:
        p[k] = st.number_input(label, min_value=0.1, value=p0[k]/1000, step=0.1, key=k)*1000
    st.subheader('Faixas de espaçamento em metros')
    for axis, label in [('x','Vãos das principais — direção X'),('y','Vãos das secundárias — direção Y'),('s','Distância entre secundárias — medida em X')]:
        st.caption(label)
        a,b = st.columns(2)
        for col, suffix, title in [(a,'min','Mínimo'),(b,'max','Máximo')]:
            k=f'{axis}{suffix}_mm'
            p[k]=col.number_input(title, min_value=0.05, value=p0[k]/1000, step=0.1, key=k)*1000
    st.info('As secundárias seguem Y e se repetem ao longo de X. O espaçamento entre elas é diferente do vão que vencem.')

with st.expander('Ações, perfis e limites', expanded=True):
    a,b,c=st.columns(3)
    for col,k,label in [(a,'g_floor_kpa','Permanente do piso (kN/m²)'),(b,'q_floor_kpa','Sobrecarga (kN/m²)'),(c,'hx_total_kn','Força horizontal total X (kN)')]:
        p[k]=col.number_input(label,value=p0[k],step=0.1,key=k)
    st.caption('Peso próprio das barras calculado pelo motor. Hx é distribuído igualmente nos topos das colunas; admite sinal. Ação do piso não integra o subtotal de aço.')
    names=[s['Perfil'] for s in service.catalog()]
    profiles={}
    for col,role,label in [(a,'column','Colunas'),(b,'primary','Vigas principais X'),(c,'secondary','Vigas secundárias Y')]:
        profiles[role]=col.selectbox(label,names,index=names.index(s0[role]),key=role)
    p['E_mpa']=a.number_input('E (MPa)',min_value=1.0,value=p0['E_mpa'],key='E_mpa')
    for col,k,label in [(a,'column_limit','Colunas: H /'),(b,'primary_limit','Principais: L /'),(c,'secondary_limit','Secundárias: L /')]:
        p[k]=col.number_input(label,min_value=1.0,value=p0[k],key=k)
    st.caption('Bases engastadas; nós viga–coluna rígidos no plano X; secundárias biapoiadas. Deslocamento vertical absoluto inclui o movimento dos apoios.')
    combos=st.data_editor(pd.DataFrame([dict(id='DEMO_G_Q',family='ELS_RARA',G_STEEL=1.0,G_FLOOR=1.0,Q=1.0,HX=1.0)]),
        num_rows='dynamic',hide_index=True,key='combinations',
        column_config={'family':st.column_config.SelectboxColumn('Família ELS',options=list(service.engine.FAMILIES),required=True)})
    st.caption('Coeficientes explícitos definidos pelo usuário. DEMO_G_Q é uma combinação de teste; não há geração automática de combinações normativas.')

try:
    geometries=service.grid(p)
    if not geometries:
        st.info('Nenhuma modulação uniforme cabe nas faixas informadas. Ajuste os intervalos.')
        st.stop()
    st.subheader('Hipóteses geométricas')
    geometry_key=service.fingerprint(json.dumps({k:p[k] for k in list(p0)[:9]},sort_keys=True))
    selected=st.multiselect('Hipóteses a calcular',options=[g['id'] for g in geometries],default=[g['id'] for g in geometries],key='selection_'+geometry_key)
    st.caption(f'{len(geometries)} hipóteses geradas · {len(selected)} selecionadas · limite de 200 pares hipótese × combinação.')
    geo=pd.DataFrame([{'Hipótese':g['id'],'Vãos X':g['nx'],'Vãos Y':g['ny'],'Intervalos secundários/vão X':g['secondary_intervals_per_x_bay'],'Espaçamento X (m)':g['x_spacing_mm']/1000,'Espaçamento Y (m)':g['y_spacing_mm']/1000,'Espaçamento secundárias (m)':g['secondary_spacing_mm']/1000,'Colunas':g['column_count']} for g in geometries])
    with st.expander('Consultar modulações'):
        st.dataframe(geo,hide_index=True,width='stretch')
    st.subheader('Orientação das vigas em planta')
    st.write('As vigas principais seguem **X**. As secundárias seguem **Y**, apoiadas nas principais. A distância entre secundárias é medida em **X**.')
    preview_id=st.selectbox('Visualizar geometria antes do cálculo',[g['id'] for g in geometries],key='preview_'+geometry_key)
    show_plan(p,next(g for g in geometries if g['id']==preview_id))
    st.caption('A seleção acima apenas muda o desenho; as hipóteses calculadas são as marcadas na lista anterior. Planta baseada nas entradas atuais.')
    text=service.request(study,p,profiles,combos.to_dict('records'),selected)
except (ValueError,KeyError,TypeError,OverflowError) as exc:
    st.error(f'Entradas inválidas: {exc}')
    st.stop()

if st.button('Calcular hipóteses',type='primary',key='calculate'):
    st.session_state.pop('result',None)
    try:
        with st.spinner('Calculando esforços e deslocamentos…'):
            st.session_state.result=service.calculate(text)
    except Exception as exc:
        st.error(f'Cálculo interrompido: {exc}')

r=st.session_state.get('result')
if r is None:
    st.info('Defina os dados e clique em Calcular hipóteses.')
    st.stop()
if r['request_sha256']!=service.fingerprint(text):
    st.warning('Entradas alteradas. Calcule novamente para visualizar resultados correspondentes aos dados atuais.')
    st.stop()

df=pd.DataFrame(r['rows'])
ranking=df.groupby('id',as_index=False).agg(subtotal_kg=('subtotal_kg','first'),kg_m2=('kg_m2','first'),eta=('eta','max')).sort_values(['kg_m2','id'])
ranking['Situação ELS parcial']=ranking.eta.map(lambda x:'Atende ao escopo parcial' if x<=1 else 'Não atende')
a,b,c=st.columns(3)
a.metric('Hipóteses calculadas',len(ranking))
b.metric('Atendem ao ELS parcial',int((ranking.eta<=1).sum()))
c.metric('Resultados de componentes',len(df))
st.subheader('Comparação por subtotal de aço')
st.caption('Inclui colunas e vigas principais/secundárias. Não inclui travamentos, contraventamentos ou ligações. Perfis fixos nesta versão; esta ordenação ainda não é uma otimização estrutural completa.')
st.dataframe(ranking.rename(columns={'id':'Hipótese','subtotal_kg':'Subtotal (kg)','kg_m2':'Subtotal (kg/m²)','eta':'Maior utilização ELS'}),hide_index=True,width='stretch')
st.bar_chart(ranking.set_index('id')[['kg_m2']],x_label='Hipótese',y_label='Subtotal de aço (kg/m²)')
chosen=st.selectbox('Detalhar hipótese',ranking.id.tolist())
show_plan(p,next(g for g in geometries if g['id']==chosen))
detail=df[df.id==chosen].copy()
detail['Utilização (%)']=detail.eta*100
detail['Situação']=detail.eta.map(lambda x:'Atende ao ELS parcial' if x<=1 else 'Não atende')
st.dataframe(detail[['combination','component','signed_mm','limit_mm','Utilização (%)','Situação','location']].rename(columns={'combination':'Combinação','component':'Componente','signed_mm':'Deslocamento (mm)','limit_mm':'Limite (mm)','location':'Local crítico'}),hide_index=True,width='stretch')
st.caption('Sinal dos deslocamentos conforme eixos do motor. A utilização considera o módulo do deslocamento. Hx = 0 não verifica a resposta ao vento.')
with st.expander('Detalhamento e rastreabilidade'):
    st.json({'versão':r['schema'],'motor':r['engine_id'],'entrada':r['request_sha256'],'erro_relativo_equilibrio_maximo':float(df.balance.max()),'aprovação_estrutural_final':False})
    st.json([x for x in r['full'] if x['hypothesis_id']==chosen],expanded=False)
st.download_button('Baixar registro completo do cálculo',json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False),file_name='calculo_m23.json',mime='application/json')
st.caption('Excel e PNG serão adicionados após consolidarmos a apresentação dos resultados. O registro JSON preserva entradas e saídas; esta versão não reabre projetos pela interface.')
