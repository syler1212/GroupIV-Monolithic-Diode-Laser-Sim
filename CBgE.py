





def CalculateBandgapEnergyDict (layer_b):

    Gamma_Conduction_Band_E = layer_b.gamma_conduction_valley
    L_Conduction_Band_E = layer_b.L_conduction_valley
    Delta_Conduction_Band_E = layer_b.delta_conduction_valley
    delta_E_HH = layer_b.delta_E_heavy_hole_valance_band
    delta_E_LH = layer_b.delta_E_light_hole_valance_band
    delta_E_SO = layer_b.delta_E_so_valance_band
    
    eg = min(Gamma_Conduction_Band_E, L_Conduction_Band_E, Delta_Conduction_Band_E) - max(delta_E_LH,delta_E_HH)
    
    return eg