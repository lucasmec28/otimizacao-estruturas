"""Adapter of supplied PY02 generator to the four physical load channels."""
import json
import combinations_engine as ce
FAMILY_MAP={'ELSR':'ELS_RARA','ELSF':'ELS_FREQUENTE','ELSQP':'ELS_QUASE_PERMANENTE'}
SUPPORTED=['ELUN','ELSR','ELSF','ELSQP']

def generate(families=('ELUN','ELSF'),floor_type='GER',occupancy='USO3',horizontal='NONE'):
    if not families or not set(families)<=set(SUPPORTED):raise ValueError('Famílias não suportadas neste modelo de mezanino.')
    if horizontal not in ('NONE','WIND_X'):raise ValueError('Tipo horizontal não suportado.')
    p=ce.new_project();p.update(name='Mezanino — combinações automáticas',standard='NBR 8800:2024',families=list(families),g_mode='separate',q_mode='separate',prefix='AUTO_')
    definitions=[(1,'Peso próprio dos perfis','ACO',None,'G_STEEL',1),(2,'Permanente do piso',floor_type,None,'G_FLOOR',1),(3,'Sobrecarga do piso','OUT',occupancy,'Q',1)]
    if horizontal=='WIND_X':definitions += [(4,'Vento +X','VEN','VEN','HX',1),(5,'Vento −X','VEN','VEN','HX',-1)]
    bindings={}
    for case,name,kind,profile,channel,sign in definitions:
        a=ce.new_action(case);a.update(name=name,type=kind,profile=profile,origin=f'CASE_{case}')
        if channel=='HX':a.update(group=1,compatibility='exclusive')
        p['actions'].append(a);bindings[case]=(channel,sign)
    result=ce.generate(p);els=[];elu=[];audit=[]
    for c in result.combinations:
        row=dict(id=c.name,G_STEEL=0.,G_FLOOR=0.,Q=0.,HX=0.)
        for case,factor in c.cases:
            channel,sign=bindings[case];row[channel]+=float(factor)*sign
        if c.family in FAMILY_MAP:row['family']=FAMILY_MAP[c.family];els.append(row)
        else:elu.append(row)
        audit.append(dict(id=c.name,family=c.family,cases=[(i,str(v)) for i,v in c.cases],leaders=c.leaders,detail=c.detail))
    return dict(els=els,elu=elu,project=p,signature=result.signature,bank_hash=ce.BANK_HASH,audit=json.loads(json.dumps(audit,default=str)),counts=result.counts)
