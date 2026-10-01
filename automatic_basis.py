"""Preliminary geometry-derived lengths. No claim of restraint certification."""
import service,design_basis
POLICY='GEOMETRIC_PRELIMINARY_V1'
SOURCE='Gerdau Perfis Estruturais: ASTM A572 Grau 50, fy=345 MPa, fu=450 MPa. G=77000 MPa (modelo de aço).'

def make(p,profiles,gid):
    g=next(r for r in service.grid(p) if r['id']==gid)
    cat={s['Perfil']:s for s in service.catalog()}
    if any(cat[n]['Tipo'] not in ('W','HP') for n in profiles.values()):raise ValueError('Material automático disponível apenas para W/HP deste catálogo; U/Ue exigem cadastro próprio.')
    H=p['height_mm']/1000;Lx=g['x_spacing_mm']/1000;Ly=g['y_spacing_mm']/1000
    rows=design_basis.blank_rows()
    for r in rows:
        r.update(fy_MPa=345.,fu_MPa=450.,G_MPa=77000.,Cb_positive=1.,Cb_negative=1.)
        if r['group']=='column':
            r.update(Lef_x_m=2*H,Lef_y_m=2*H,Lef_t_m=2*H,Lb_positive_m=2*H,Lb_negative_m=2*H)
        else:
            L=Lx if r['group']=='primary' else Ly
            r.update(Lef_x_m=L,Lef_y_m=L,Lef_t_m=L,Lb_positive_m=L,Lb_negative_m=L)
        r['basis']=SOURCE+' Comprimentos preliminares: colunas 2H; vigas vão integral, sem creditar contenção intermediária. Validade dos vínculos/contenções pendente.'
    result=design_basis.make(p,profiles,gid,rows)
    result.update(automatic_policy=POLICY,restraints_validated=False,length_policy='Column: 2H provisional cantilever-reference; beams: full span, no intermediate lateral-restraint credit',
                  material_specification='ASTM A572 Grade 50',material_source=SOURCE)
    return result
