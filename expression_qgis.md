# Bilan MH

## Bilan hydrique

### hyd_prim (indicateurs primaires)
if ("inond" = 'Oui',1,0)+
if("satur_surf" = 'Oui',1,0)+
if("lign_marqu_eau" = 'Oui',1,0)+
if("debris_depot" = 'Oui',1,0)+
if("litiere_noir" = 'Oui',1,0)+
if("effet_rhizo" = 'Oui',1,0)+
if("ecorc_erod" = 'Oui',1,0)+
if("odeur_souf" = 'Oui',1,0)

### hyd_sec (indicateurs secondaires)
if("racin_hors" = 'Oui',1,0)+
if("mousse_tronc" = 'Oui',1,0)+
if("souch_hyper" = 'Oui',1,0)+
if("lentic_hyper" = 'Oui',1,0)+
if("racin_adven" = 'Oui',1,0)

### bil_hyd (bilan hydrique)
if( "hyd_prim" >= 1,1,if( "hyd_sec" >= 2,1,0))

## Bilan du sol

### bil_drain
aggregate(
			layer:='form_section_sol',
			aggregate:='sum',
			expression:=
				 (attribute(get_feature('mh_horizon_type','id',"typ_horiz"),'type') in ('Minéral' ,'Sol perturbé (organique et minéral)'))=1,
			filter:="mh_id" = attribute(@parent,'id')
		)

Somme dans le formulaire de section sol, groupe les données selon leur mh_id, qui correspond au id dans formulaire mh. 
Quand la valeur du champ typ_horiz est de1dbb7f-c822-41ac-baf0-2f6c93e190e6 ou e284f7a9-2127-49b6-b872-e535f3dbe69a += 1

### bil_folisol
aggregate(
			layer:='form_section_sol',
			aggregate:='sum',
			expression:=
				(attribute(get_feature('mh_sol_type','id',"typ_sol_org"),
				'typ_sol_org') like ('A%'))=1,
			filter:="mh_id" = attribute(@parent,'id')
		)
Somme dans le formulaire de section sol, groupe les données selon leur mh_id, qui correspond au id dans formulaire mh. 
Quand la valeur du champ typ_sol_org = '273a2969-c15c-4c62-8b87-37ee78defc6b' += 1

### bil_sol_hydr
if(
	"bil_folisol">0 or "bil_folisol" is not NULL,1,
if(
 attribute(get_feature('mh_drainage','id',"class_draing"),'drainage') in (5,6),
 if("bil_drain" > 0,1,0),
 0))

## Bilan végétation

## veg_dom_h
aggregate(layer:='form_section_espece_vegetale',aggregate:='count',expression:='espece',
filter:= ("mh_id"  =  attribute(@parent,'id')) 
AND attribute(get_feature('table_flore_espece','id',"espece"),'statut_hydrique') in ('OBL','FACH') AND "dom" = '1')

## veg_dom_nh
aggregate(layer:='form_section_espece_vegetale',aggregate:='count',expression:='espece',filter:= ("mh_id"  =  attribute(@parent,'id')) AND attribute(get_feature('table_flore_espece','id',"espece"),'statut_hydrique') in ('NI', '-') AND "dom" = '1')

## bil_veg
if("veg_domh" >  "veg_domnh" ,1,0)


### bilan_mh
if(
	(if("bil_sol_hydro" > 0,1,0)+
	if("pert_maj" = 0,1,0)) >= 2, 1, 0
)
or
if("bil_veg" > 0, 1, 0)