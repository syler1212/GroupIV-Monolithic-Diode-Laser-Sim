from DataSet import VALLEYS
from DataSet import BOWING

class BandGapResult(tuple):
    """2-tuple (BandGap, eg) for backwards compatibility with existing tests,
    while also exposing e_gamma and e_l for the UI."""
    def __new__(cls, band_gap, eg, e_gamma, e_l):
        return super().__new__(cls, (band_gap, eg))

    def __init__(self, band_gap, eg, e_gamma, e_l):
        self.e_gamma = e_gamma
        self.e_l = e_l





def CalculateBandGapTypeDict(layer_b):
  # 1. Retrieve composition dict whether layer_b.material is a Material object or dict
  comp = getattr(layer_b.material, "composition", layer_b.material)

  # Standardize elements for Group-IV ternary (Si, Ge, Sn/ASn)
  elements = list(comp.keys())
  while len(elements) < 3:
    elements.append(None)

  x_element, y_element, z_element = elements[0], elements[1], elements[2]

  x = comp.get(x_element, 0.0) if x_element else 0.0
  y = comp.get(y_element, 0.0) if y_element else 0.0
  z = comp.get(z_element, 0.0) if z_element else 0.0

  # Read pre-calculated residual strain corrections directly from layer_b
  EgammaStrainCorrection = getattr(layer_b, "EgammaStrainCorrection", 0.0)
  ELStrainCorrection = getattr(layer_b, "ELStrainCorrection", 0.0)
  EdeltaStrainCorrection = getattr(layer_b, "EdeltaStrainCorrection", 0.0)

  # ----------------------------------------------------
  # Helper to look up bowing parameters safely
  # ----------------------------------------------------
  def get_bowing(el1, el2, valley):
    if not el1 or not el2 or el1 == el2:
      return 0.0
    pair1 = el1 + el2
    pair2 = el2 + el1
    if pair1 in BOWING and valley in BOWING[pair1]:
      return BOWING[pair1][valley]
    if pair2 in BOWING and valley in BOWING[pair2]:
      return BOWING[pair2][valley]
    return 0.0

  def get_valley_energy(el, valley):
    if not el or el not in VALLEYS:
      return 0.0
    return VALLEYS[el][valley]

  # ====================================================
  # 1. Gamma Valley Calculation
  # ====================================================
  EgammaX = get_valley_energy(x_element, "Gamma")
  EgammaY = get_valley_energy(y_element, "Gamma")
  EgammaZ = get_valley_energy(z_element, "Gamma")

  xyGammaBowing = get_bowing(x_element, y_element, "Gamma")
  yzGammaBowing = get_bowing(y_element, z_element, "Gamma")
  xzGammaBowing = get_bowing(x_element, z_element, "Gamma")

  EgammaLinear = x * EgammaX + y * EgammaY + z * EgammaZ
  EgammaBowing = (
      x * y * xyGammaBowing + x * z * xzGammaBowing + y * z * yzGammaBowing
  )
  EgammaFinal = EgammaLinear - EgammaBowing + EgammaStrainCorrection

  # ====================================================
  # 2. L Valley Calculation
  # ====================================================
  ELX = get_valley_energy(x_element, "L")
  ELY = get_valley_energy(y_element, "L")
  ELZ = get_valley_energy(z_element, "L")

  xyLBowing = get_bowing(x_element, y_element, "L")
  yzLBowing = get_bowing(y_element, z_element, "L")
  xzLBowing = get_bowing(x_element, z_element, "L")

  E_L_Linear = x * ELX + y * ELY + z * ELZ
  E_L_Bowing = x * y * xyLBowing + x * z * xzLBowing + y * z * yzLBowing
  E_L_Final = E_L_Linear - E_L_Bowing + ELStrainCorrection

  # ====================================================
  # 3. Delta Valley Calculation
  # ====================================================
  EdeltaX = get_valley_energy(x_element, "Delta")
  EdeltaY = get_valley_energy(y_element, "Delta")
  EdeltaZ = get_valley_energy(z_element, "Delta")

  xydeltaBowing = get_bowing(x_element, y_element, "Delta")
  yzdeltaBowing = get_bowing(y_element, z_element, "Delta")
  xzdeltaBowing = get_bowing(x_element, z_element, "Delta")

  EdeltaLinear = x * EdeltaX + y * EdeltaY + z * EdeltaZ
  EdeltaBowing = (
      x * y * xydeltaBowing + x * z * xzdeltaBowing + y * z * yzdeltaBowing
  )
  EdeltaFinal = EdeltaLinear - EdeltaBowing + EdeltaStrainCorrection

  # ====================================================
  # 4. Bandgap Classification & Final Output
  # ====================================================
  if EgammaFinal <= E_L_Final and EgammaFinal <= EdeltaFinal:
    bandgap_type = "Direct"
  elif E_L_Final <= EdeltaFinal:
    bandgap_type = "Indirect (L)"
  else:
    bandgap_type = "Indirect (Delta)"

  return bandgap_type, EgammaFinal, E_L_Final, EdeltaFinal

# we assume the valanace band peak is E = 0 
    