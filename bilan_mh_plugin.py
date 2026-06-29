from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QPushButton, QCheckBox, QMessageBox, QAction, QLabel
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject, QgsFeatureRequest

class BilanMHWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bilan - Milieux humides")
        self.setMinimumWidth(400)
        self.setMinimumHeight(100)
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(10)
        self.layout().setContentsMargins(15, 15, 15, 15)

        # Case à cocher pour appliquer le calcul aux entités sélectionnées
        self.bilan_only_checkbox = QCheckBox("Appliquer seulement aux milieux humides sélectionnés")
        self.layout().addWidget(self.bilan_only_checkbox)

        # Bouton pour lancer le calcul
        self.update_bilan_button = QPushButton("Lancer le calcul du bilan")
        self.update_bilan_button.clicked.connect(self.run_bilan_update)
        self.layout().addWidget(self.update_bilan_button)


    # Fonction de calcul du bilan

    def run_bilan_update(self):
            mh_layer = QgsProject.instance().mapLayersByName("form_mh")
            if not mh_layer:
                QMessageBox.critical(self, "Erreur", "La couche des milieux humdies n'est pas dans le projet.")
                return

            mh_layer = mh_layer[0]
            
            # Vérifie si le mode édition est activé
            if not mh_layer.isEditable():
                mh_layer.startEditing()

            try:
                bilan_only_checkbox = self.bilan_only_checkbox.isChecked()
                mh_features = list(mh_layer.selectedFeatures() if bilan_only_checkbox else mh_layer.getFeatures())
                if not mh_features:
                    QMessageBox.warning(self, "Attention", "Aucune entité n'a été sélectionnée dans le formulaire milieux humides")
                    return

                mh_ids = {f["id"] for f in mh_features}

                # Étape 1 : Réinitialisation de tous les champs de la section bilan
                
                mh_field_names = [
                    "hyd_prim", "hyd_sec", "bil_hyd", "bil_drain", "bil_folisol",
                    "bil_sol_hydro", "veg_dom_h", "veg_dom_nh", "bil_veg", "bilan_mh"
                ]

                changed_hyd_prim = {}
                changed_hyd_sec = {}
                changed_bil_hyd = {}

                mh_fields = [mh_layer.fields().indexFromName(mh_name) for mh_name in mh_field_names]
                for mh_feature in mh_features:
                    mh_layer.changeAttributeValues(mh_feature.id(), {idx: 0 for idx in mh_fields})

                # Étape 2 : bilan hydrique - indicateurs primaires
                
                idx_hyd_prim = mh_layer.fields().indexFromName("hyd_prim")
                hyd_prim_field_names = [
                    "inond", "satur_surf", "lign_marqu_eau", "debris_depot", "litiere_noir", "effet_rhizo",
                    "ecorc_erod", "odeur_souf"
                ]

                hyd_prim_field = [mh_layer.fields().indexFromName(prim_name) for prim_name in hyd_prim_field_names]

                for mh_feature in mh_features:
                    hyd_prim_calcul = sum(
                        1 for idx in hyd_prim_field
                        if mh_feature.attribute(idx) == "Oui"
                    )

                    mh_layer.changeAttributeValue(mh_feature.id(), idx_hyd_prim, hyd_prim_calcul)
                    changed_hyd_prim[mh_feature.id()] = hyd_prim_calcul

                # Étape 3 : bilan hydrique - indicateurs secondaires
                idx_hyd_sec = mh_layer.fields().indexFromName("hyd_sec")
                
                hyd_sec_field_names = [
                    "racin_hors", "mousse_tronc", "souch_hyper", "lentic_hyper", "racin_adven"
                ]

                hyd_sec_field = [mh_layer.fields().indexFromName(sec_name) for sec_name in hyd_sec_field_names]

                for mh_feature in mh_features:
                    hyd_sec_calcul = sum(
                        1 for idx in hyd_sec_field
                        if mh_feature.attribute(idx) == "Oui"
                    )

                    mh_layer.changeAttributeValue(mh_feature.id(), idx_hyd_sec, hyd_sec_calcul)
                    changed_hyd_sec[mh_feature.id()] = hyd_sec_calcul

                # Étape 4 : bilan hydrique - bilan total
                idx_bil_hyd = mh_layer.fields().indexFromName("bil_hyd")
                
                for mh_feature in mh_features:
                    hyd_prim = changed_hyd_prim[mh_feature.id()]
                    hyd_sec = changed_hyd_sec[mh_feature.id()]
                    bil_hyd_calcul = 1 if hyd_prim >= 1 or hyd_sec >= 2 else 0
                    
                    mh_layer.changeAttributeValue(mh_feature.id(), idx_bil_hyd, bil_hyd_calcul)
                    changed_bil_hyd[mh_feature.id()] = bil_hyd_calcul

            
            
                # Étape 5 - bilan sol

                sol_layer = QgsProject.instance().mapLayersByName("form_section_sol")
                if not sol_layer:
                    QMessageBox.critical(self, "Erreur", "Le formulaire de section sol n'est pas présent dans le projet actif")
                
                sol_layer = sol_layer[0]

                idx_bil_drain = mh_layer.fields().indexFromName("bil_drain")
                idx_bil_folisol = mh_layer.fields().indexFromName("bil_folisol")
                idx_bil_sol_hydro = mh_layer.fields().indexFromName("bil_sol_hydro")
                idx_typ_horiz = sol_layer.fields().indexFromName("typ_horiz")
                idx_typ_sol_org = sol_layer.fields().indexFromName("typ_sol_org")
                idx_class_draing = mh_layer.fields().indexFromName("class_draing")

                # Réinitialisation des valeurs des champs

                for mh_feature in mh_features:
                    mh_layer.changeAttributeValues(mh_feature.id(), {
                        idx_bil_drain: 0,
                        idx_bil_folisol: 0,
                        idx_bil_sol_hydro: 0
                    })

                # dictionnaires de valeurs modifiées
                
                changed_bil_drain = {}
                changed_bil_folisol = {}
                changed_bil_sol_hydro = {}

                # chargement de tous les enregistrements sol selon le milieu humide

                sol_features_by_mh = {}
                expr = "\"mh_id\" IN ({})".format(",".join(f"'{mid}'" for mid in mh_ids))
                for sol_feature in sol_layer.getFeatures(QgsFeatureRequest().setFilterExpression(expr)):
                    sol_mh_id = sol_feature["mh_id"]
                    sol_features_by_mh.setdefault(sol_mh_id, []).append(sol_feature)

                # selection dans des enregistrements sol en fonction de la sélection dans milieu humide

                typ_horiz_drain = {"de1dbb7f-c822-41ac-baf0-2f6c93e190e6", "0972d149-64bc-40bf-9ae3-8dfc674f9057"}
                typ_sol_folisol = "273a2969-c15c-4c62-8b87-37ee78defc6b"

                for mh_feature in mh_features:
                    mh_id = mh_feature["id"]
                    sol_features = sol_features_by_mh.get(mh_id, [])

                    # bil_drain

                    bil_drain_calcul = sum(
                        1 for sf in sol_features
                        if sf.attribute(idx_typ_horiz) in typ_horiz_drain
                    )

                    mh_layer.changeAttributeValue(mh_feature.id(), idx_bil_drain, bil_drain_calcul)
                    changed_bil_drain[mh_feature.id()] = bil_drain_calcul

                    # bil_folisol

                    bil_folisol_calcul = sum(
                        1 for sf in sol_features
                        if sf.attribute(idx_typ_sol_org) == typ_sol_folisol
                    )

                    mh_layer.changeAttributeValue(mh_feature.id(), idx_bil_folisol, bil_folisol_calcul)
                    changed_bil_folisol[mh_feature.id()] = bil_folisol_calcul

                # bil_sol_hydro

                class_draing_valeur = {"1526dbd6-8ef6-44a3-98d3-0936d6682e56", "6d20b89b-89fc-4b29-b9df-cde0968a4d77"}

                for mh_feature in mh_features:
                    bil_drain = changed_bil_drain[mh_feature.id()]
                    bil_folisol = changed_bil_folisol[mh_feature.id()]
                    bil_sol_hydro = 1 if bil_folisol > 0 or (mh_feature.attribute(idx_class_draing) in class_draing_valeur and bil_drain > 0) else 0
                    
                    mh_layer.changeAttributeValue(mh_feature.id(), idx_bil_sol_hydro, bil_sol_hydro)
                    changed_bil_sol_hydro[mh_feature.id()] = bil_sol_hydro


                # Étape 6 : bilan de végétation

                veget_layer = QgsProject.instance().mapLayersByName("form_section_espece_vegetale")
                if not veget_layer:
                    QMessageBox.critical(self, "Erreur", "La couche espèces végétales n'est pas trouvée dans le projet.")
                    return

                veget_layer = veget_layer[0]

                if not veget_layer.isEditable():
                    veget_layer.startEditing()

                idx_recouv_rel = veget_layer.fields().indexFromName("recouv_rel_num")
                idx_dom = veget_layer.fields().indexFromName("dom")
                idx_statut = veget_layer.fields().indexFromName("statut")

                # chargement de toutes les entités végétales en une seule requête
                expr_veget = "\"mh_id\" IN ({})".format(",".join(f"'{mid}'" for mid in mh_ids))
                veget_features = list(veget_layer.getFeatures(QgsFeatureRequest().setFilterExpression(expr_veget)))

                # réinitialisation des valeurs
                for veget_feature in veget_features:
                    veget_layer.changeAttributeValues(veget_feature.id(), {
                        idx_recouv_rel: 0,
                        idx_dom: 0
                    })

                # calcul du recouvrement relatif groupé par mh_id et strate
                groups_abs = {}

                for veget_feature in veget_features:
                    veget_mh_id, strate = veget_feature["mh_id"], veget_feature["strate"]
                    recouv_abs = veget_feature["recouv_abs_num"]
                    recouv_abs = float(recouv_abs) if recouv_abs not in (None, '') else 0.0
                    groups_abs.setdefault((veget_mh_id, strate), []).append((veget_feature.id(), recouv_abs))

                changed_recouv_rel = {}
                

                for (veget_mh_id, strate), values in groups_abs.items():
                    total_recouv_abs = sum(v[1] for v in values)
                    for fid, recouv_abs in values:
                        recouv_rel = round((recouv_abs / total_recouv_abs) * 100, 2) if total_recouv_abs > 0 else 0.0
                        veget_layer.changeAttributeValue(fid, idx_recouv_rel, recouv_rel)
                        changed_recouv_rel[fid] = recouv_rel

                # calcul de la dominance

                changed_dom = {veget_feature.id(): 0 for veget_feature in veget_features}
                cumulative_sums = {}

                for veget_feature in veget_features:
                    veget_mh_id, strate = veget_feature["mh_id"], veget_feature["strate"]
                    recouv_rel = changed_recouv_rel[veget_feature.id()]
                    recouv_abs = veget_feature["recouv_abs_num"]
                    recouv_abs = float(recouv_abs) if recouv_abs not in (None, '') else 0.0
                    cumulative_sums.setdefault(veget_mh_id, {}).setdefault(strate, []).append((veget_feature.id(), recouv_rel, recouv_abs))

                for veget_mh_id, strates in cumulative_sums.items():
                    for strate, values in strates.items():
                        total_recouv_abs = sum(float(recouv_abs or 0) for _, _, recouv_abs in values)
                        if total_recouv_abs < 10:
                            for fid, _, _ in values:
                                veget_layer.changeAttributeValue(fid, idx_dom, 0)
                                changed_dom[fid] = 0
                        else:
                            values.sort(key=lambda x: x[1], reverse=True)
                            cum_sum, recouv_to_update = 0, set()
                            for fid, recouv_rel, _ in values:
                                cum_sum += float(recouv_rel or 0)
                                recouv_to_update.add(recouv_rel)
                                if cum_sum > 50 and cum_sum - recouv_rel < 50:
                                    break
                            for fid, recouv_rel, _ in values:
                                if recouv_rel in recouv_to_update:
                                    veget_layer.changeAttributeValue(fid, idx_dom, 1)
                                    changed_dom[fid] = 1

                # dom = 1 pour recouv_rel_num >= 20 si recouv_abs_num suffisant
                for veget_feature in veget_features:
                    recouv_rel = changed_recouv_rel[veget_feature.id()]
                    if recouv_rel >= 20:
                        veget_layer.changeAttributeValue(veget_feature.id(), idx_dom, 1)
                        changed_dom[veget_feature.id()] = 1

                # calcul du nombre d'espèces dominantes par milieu humide
                
                idx_veg_dom_h = mh_layer.fields().indexFromName("veg_dom_h")
                idx_veg_dom_nh = mh_layer.fields().indexFromName("veg_dom_nh")
                idx_bil_veg = mh_layer.fields().indexFromName("bil_veg")

                changed_veg_dom_h = {}
                changed_veg_dom_nh = {}
                changed_bil_veg = {}

                # regroupement des entités végétales par mh_id pour éviter une double boucle O(n*m)
                veget_features_by_mh = {}
                for veget_feature in veget_features:
                    veget_features_by_mh.setdefault(veget_feature["mh_id"], []).append(veget_feature)

                for mh_feature in mh_features:
                    mh_layer.changeAttributeValues(mh_feature.id(), {
                        idx_veg_dom_h: 0,
                        idx_veg_dom_nh: 0,
                        idx_bil_veg: 0
                    })

                for mh_feature in mh_features:
                    nb_veg_dom_h = 0
                    nb_veg_dom_nh = 0
                    mh_id = mh_feature["id"]

                    for veget_feature in veget_features_by_mh.get(mh_id, []):
                        statut = veget_feature.attribute(idx_statut)
                        dom = changed_dom[veget_feature.id()]
                        if statut in ("OBL", "FACH") and dom == 1:
                            nb_veg_dom_h += 1
                        elif statut in ("NI", "-") and dom == 1:
                            nb_veg_dom_nh += 1

                    mh_layer.changeAttributeValue(mh_feature.id(), idx_veg_dom_h, nb_veg_dom_h)
                    mh_layer.changeAttributeValue(mh_feature.id(), idx_veg_dom_nh, nb_veg_dom_nh)
                    changed_veg_dom_h[mh_feature.id()] = nb_veg_dom_h
                    changed_veg_dom_nh[mh_feature.id()] = nb_veg_dom_nh

                for mh_feature in mh_features:
                    veg_dom_h = changed_veg_dom_h[mh_feature.id()]
                    veg_dom_nh = changed_veg_dom_nh[mh_feature.id()]
                    if veg_dom_h > veg_dom_nh:
                        mh_layer.changeAttributeValue(mh_feature.id(), idx_bil_veg, 1)
                    else:
                        mh_layer.changeAttributeValue(mh_feature.id(), idx_bil_veg, 0)
                    changed_bil_veg[mh_feature.id()] = 1 if veg_dom_h > veg_dom_nh else 0

                # Étape 7 : calcul du bilan mh

                idx_bilan_mh = mh_layer.fields().indexFromName("bilan_mh")
                idx_pert_maj = mh_layer.fields().indexFromName("pert_maj")
                changed_bilan_mh = {}

                # on réinitialise les valeurs
                
                for mh_feature in mh_features:
                    mh_layer.changeAttributeValue(mh_feature.id(), idx_bilan_mh, 0)

                for mh_feature in mh_features:
                    if (changed_bil_sol_hydro[mh_feature.id()] > 0 and mh_feature.attribute(idx_pert_maj) == 0) or changed_bil_veg[mh_feature.id()] > 0:
                        mh_layer.changeAttributeValue(mh_feature.id(), idx_bilan_mh, 1)
                    else:
                        mh_layer.changeAttributeValue(mh_feature.id(), idx_bilan_mh, 0)
                    changed_bilan_mh[mh_feature.id()] = 1 if (changed_bil_sol_hydro[mh_feature.id()] > 0 and mh_feature.attribute(idx_pert_maj) == 0) or changed_bil_veg[mh_feature.id()] > 0 else 0

                # Étape 8 : résumé des valeurs calculées par le plugin

                bil_hyd_affiche = {0: "Hydrologie non typique des MH", 1: "Hydrologie de MH"}
                bil_sol_affiche = {0: "Sol non hydromorphe", 1: "Sol hydromorphe"}
                bil_veg_affiche = {0: "Dominée par essences non hygrophiles", 1: "Dominée par essences hygrophiles"}
                bilan_mh_affiche = {0: "N'est pas un milieu humide", 1: "Est un milieu humide"}
                
                lignes = []

                for mh_feature in mh_features:
                    fid = mh_feature.id()
                    mh_id = mh_feature["id"]
                    lignes.append(f"Identifiant du milieu humide : {mh_id}")
                    lignes.append("")
                    lignes.append(f"Section - Hydrologie")
                    lignes.append(f"Indicateurs primaires : {changed_hyd_prim[fid]}")
                    lignes.append(f"Indicateurs secondaires : {changed_hyd_sec[fid]}")
                    lignes.append(f"Bilan Hydrologie : {bil_hyd_affiche[changed_bil_hyd[fid]]}")
                    lignes.append("")
                    lignes.append(f"Section - Sol")
                    lignes.append(f"Nombre d'horizons minéraux : {changed_bil_drain[fid]}")
                    lignes.append(f"Nombre d'horizons organiques : {changed_bil_folisol[fid]}")
                    lignes.append(f"Bilan Sol : {bil_sol_affiche[changed_bil_sol_hydro[fid]]}")
                    lignes.append("")
                    lignes.append(f"Section - Végétation")
                    lignes.append(f"Espèces caractéristiques : {changed_veg_dom_h[fid]}")
                    lignes.append(f"Espèces non caractéristiques : {changed_veg_dom_nh[fid]}")
                    lignes.append(f"Bilan Végétation : {bil_veg_affiche[changed_bil_veg[fid]]}")
                    lignes.append("")
                    lignes.append(f"Milieu humide")
                    lignes.append(f"Bilan : {bilan_mh_affiche.get(changed_bilan_mh[fid], str(changed_bilan_mh[fid]))}")
                    lignes.append("")
                
                resume = "\n".join(lignes)

                synthese = QMessageBox(self)
                synthese.setWindowTitle("Synthèse des résultats calculés")
                synthese.setText("Les calculs ont été appliqués. Veuillez valider et enregistrer les modifications.")
                synthese.setDetailedText(resume)
                synthese.exec()

                self.close()

            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")
                mh_layer.rollBack()


class BilanMHPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.widget = None

    def initGui(self):
        self.action = QAction(QIcon(""), "Calcul du bilan milieu humide", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Calcul du bilan milieu humide", self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("&Calcul du bilan milieu humide", self.action)

    def run(self):
        if not self.widget:
            self.widget = BilanMHWidget()
        self.widget.show()