
from CCrystalStiffnessConstant import (
    Calculate_CRYSTAL_ELASTIC_STIFFNESS_CONSTANTS,
)
from DataSet import (
    A_C_VALLEY_Values,
    CRYSTAL_ELASTIC_STIFFNESS_CONSTANTS,
    LATTICE_A,
)

# If you have XI_U_DELTA in DataSet, import it; otherwise default fallback is provided
try:
  from DataSet import XI_U_DELTA
except ImportError:
  XI_U_DELTA = {"Si": 8.6, "Ge": 9.42, "ASn": 7.0, "Sn": 7.0}


def Calculate_A_C(Dictionary):
  """Calculates linear Vegard conduction band deformation potentials (a_c).

  Supports Material class instances as well as unary, binary, and ternary dicts.
  """
  comp = getattr(Dictionary, "composition", Dictionary)

  elements = list(comp.keys())
  while len(elements) < 3:
    elements.append(None)

  x_element, y_element, z_element = elements[0], elements[1], elements[2]

  x = comp.get(x_element, 0.0) if x_element else 0.0
  y = comp.get(y_element, 0.0) if y_element else 0.0
  z = comp.get(z_element, 0.0) if z_element else 0.0

  def get_ac(el, valley):
    if not el or el not in A_C_VALLEY_Values:
      return 0.0
    return A_C_VALLEY_Values[el].get(valley, 0.0)

  ACgammaX, ACgammaY, ACgammaZ = (
      get_ac(x_element, "Gamma"),
      get_ac(y_element, "Gamma"),
      get_ac(z_element, "Gamma"),
  )
  AC_L_X, AC_L_Y, AC_L_Z = (
      get_ac(x_element, "L"),
      get_ac(y_element, "L"),
      get_ac(z_element, "L"),
  )
  AC_delta_X, AC_delta_Y, AC_delta_Z = (
      get_ac(x_element, "Delta"),
      get_ac(y_element, "Delta"),
      get_ac(z_element, "Delta"),
  )

  AC_gamma_alloy = (x * ACgammaX) + (y * ACgammaY) + (z * ACgammaZ)
  AC_L_alloy = (x * AC_L_X) + (y * AC_L_Y) + (z * AC_L_Z)
  AC_delta_alloy = (x * AC_delta_X) + (y * AC_delta_Y) + (z * AC_delta_Z)

  return AC_gamma_alloy, AC_L_alloy, AC_delta_alloy


def Calculate_Xi_u_Delta(Dictionary):
  """Linearly averages the Delta-valley uniaxial deformation potential Xi_u."""
  comp = getattr(Dictionary, "composition", Dictionary)
  return sum(
      comp.get(el, 0.0) * XI_U_DELTA.get(el, 0.0) for el in comp if el is not None
  )


def CalculateBiaxialStrainDict(layer_a, layer_b):
  """Computes max/initial coherent strain (R = 0) against the template surface."""
  return CalculateBiaxialStrainDictRelaxation(layer_a, layer_b, R=0.0)


def CalculateBiaxialStrainDictRelaxation(layer_a, layer_b, R):
  """Computes residual strain components and bandgap energy shifts for relaxation degree R."""
  # In-plane template footprint of the underlying layer
  a_template = layer_a.final_lattice_constant_In_Plane
  a_0 = layer_b.relaxed_lattice_constant

  # Elastic stiffness constants (use cached layer attributes if present)
  C11 = getattr(
      layer_b,
      "C11",
      Calculate_CRYSTAL_ELASTIC_STIFFNESS_CONSTANTS(layer_b.material)[0],
  )
  C12 = getattr(
      layer_b,
      "C12",
      Calculate_CRYSTAL_ELASTIC_STIFFNESS_CONSTANTS(layer_b.material)[1],
  )

  # Residual in-plane strain scaled by (1 - R)
  InPlaneStrain = (1.0 - R) * ((a_template - a_0) / a_0)

  # Vertical strain along growth axis [001]
  OutOfPlaneStrain = -2.0 * (C12 / C11) * InPlaneStrain

  # Hydrostatic (volume) and Shear (shape) components
  epsilon_hydrostatic = (2.0 * InPlaneStrain) + OutOfPlaneStrain
  epsilon_shear = OutOfPlaneStrain - InPlaneStrain

  # Conduction band deformation potentials
  AC_gamma_alloy, AC_L_alloy, AC_delta_alloy = Calculate_A_C(layer_b.material)

  # Hydrostatic energy shifts
  HydrostaticGammaEnergyChange = epsilon_hydrostatic * AC_gamma_alloy
  HydrostaticLEnergyChange = epsilon_hydrostatic * AC_L_alloy
  HydrostaticDeltaEnergyChange = epsilon_hydrostatic * AC_delta_alloy

  # Shear energy shifts (Gamma and L valleys experience zero first-order shear along [001])
  ShearGammaEnergyChange = 0.0
  ShearLEnergyChange = 0.0
  SheardeltaEnergyChange = 0.0

  # Longitudinal Delta valley [001] splitting
  #Xi_u_delta = Calculate_Xi_u_Delta(layer_b.material)
  #SheardeltaEnergyChange = (2.0 / 3.0) * Xi_u_delta * epsilon_shear

  # Total energy corrections
  EgammaStrainCorrection = HydrostaticGammaEnergyChange + ShearGammaEnergyChange
  ELStrainCorrection = HydrostaticLEnergyChange + ShearLEnergyChange
  EdeltaStrainCorrection = HydrostaticDeltaEnergyChange + SheardeltaEnergyChange

  return (
      EgammaStrainCorrection,
      ELStrainCorrection,
      EdeltaStrainCorrection,
      epsilon_hydrostatic,
      epsilon_shear,
      InPlaneStrain,
      OutOfPlaneStrain,
  )