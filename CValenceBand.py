import math
from DataSet import PIKUS_BIR_VALENCE_PARAMS
from DataSet import DELTA_SO
#in this file we will calculate the valanace band splitting and the overall values of LH band, HH band, SO band.
# becuase it must be so that the LH valance band sits above the HH Valance band so that the excess holes pumped in to the 
# alloy fill and lower the F_E_V value in the LH band and the electrons fill the conduction Band and raise the F_E_C value
# the F_E_V and F_E_C are the fermi energies, but for the indiviudal bands. we say that the F_E is where all states under the energy
# are filled and all state above are empty.
# the concept follows from that idea, but the two extend out from the peak of the VBM and valley of the CBM
# with F_E_V starting at VBM and going deeper into the LH band, and the electrons starting at CBM
# and filling upwards to higher enegry states.
# a very important condition for our alloy is that the F_E_C - F_E_V > E_g Bernard–Duraffourg condition
#why is this important, this is important becuase this prevents the out going light from being absorbed by a low level electron
#due to the pauli exclusion principle
# it is important that the LH band is higher in energy then the HH band becuase of the Effective mass the two electron states expierence.
#LH has a smaller effective mass and so does the conduction band so the two share a similar value in denisty of states(DOS)
# this is important becuase we want ot be able to dump holes and electrons into the alloy and maintain a charge ratio. but lower F_E_V, 
# and raise F_E_C do make the gap larger than E_g
#if HH is higher than the ratio of holes to electrons needed to dump into the alloy is ruined by the HH high denity of states requiring
#many more holes than electrons.
#once this set up is complete the applied volatge and cause emmission if above the B_g


#steps to the program

#done :calculate relaxed lattice constants of the alloy
#done :calculate the values for biaxial strain
#done :calculate bandgap type based on alloy composition and strain corrections to bandgap E
#2 calculate valance band energies for LH, HH, and SO
#3 calculate the conduction band energy
#4 calulate  F_E_c - F_E_v ensure the Bernard–Duraffourg condition is met


import math
from DataSet import DELTA_SO, PIKUS_BIR_VALENCE_PARAMS


def CalculateValenceBandEnergyDict(layer_b):
  """Calculates the valence band energy levels (delta_E_LH, delta_E_HH, delta_E_SO)

  under biaxial strain using Bir-Pikus perturbation theory. Reference E = 0 eV
  is set to the unstrained valence band maximum (VBM).
  """
  comp = getattr(layer_b.material, "composition", layer_b.material)

  # Standardize elements for unary, binary, or ternary alloys
  elements = list(comp.keys())
  while len(elements) < 3:
    elements.append(None)

  x_element, y_element, z_element = elements[0], elements[1], elements[2]

  x = comp.get(x_element, 0.0) if x_element else 0.0
  y = comp.get(y_element, 0.0) if y_element else 0.0
  z = comp.get(z_element, 0.0) if z_element else 0.0

  epsilon_hydrostatic = getattr(layer_b, "epsilon_hydrostatic", 0.0)
  epsilon_shear = getattr(layer_b, "epsilon_shear", 0.0)

  def get_pikus_param(el, param):
    if not el or el not in PIKUS_BIR_VALENCE_PARAMS:
      return 0.0
    return PIKUS_BIR_VALENCE_PARAMS[el].get(param, 0.0)

  def get_delta_so(el):
    if not el or el not in DELTA_SO:
      return 0.0
    return DELTA_SO[el]

  # Linearly interpolated deformation potentials and spin-orbit splitting
  a_v_alloy = (
      (x * get_pikus_param(x_element, "av"))
      + (y * get_pikus_param(y_element, "av"))
      + (z * get_pikus_param(z_element, "av"))
  )
  b_alloy = (
      (x * get_pikus_param(x_element, "b"))
      + (y * get_pikus_param(y_element, "b"))
      + (z * get_pikus_param(z_element, "b"))
  )
  delta_SO = (
      (x * get_delta_so(x_element))
      + (y * get_delta_so(y_element))
      + (z * get_delta_so(z_element))
  )

  # Hydrostatic shift and axial shear shift
  delta_E_Hydrostatic = a_v_alloy * epsilon_hydrostatic
  delta_E_shear = 2.0 * b_alloy * epsilon_shear

  # Bir-Pikus radical term (note the MINUS sign on the cross term)
  radical = math.sqrt(
      (delta_SO**2)
      - (delta_SO * delta_E_shear)
      + (2.25 * (delta_E_shear**2))
  )

  # Valence sub-band levels relative to unstrained VBM (Ev0 = 0)
  delta_E_HH = delta_E_Hydrostatic - 0.5 * delta_E_shear
  delta_E_LH = (
      delta_E_Hydrostatic + 0.25 * delta_E_shear - 0.5 * delta_SO + 0.5 * radical
  )
  delta_E_SO = delta_E_Hydrostatic - 0.5 * delta_SO - 0.5 * radical

  return delta_E_LH, delta_E_HH, delta_E_SO