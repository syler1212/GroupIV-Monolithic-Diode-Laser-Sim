from DataSet import LATTICE_A
from DataSet import LATTICE_BOWING_VALUES
from DataSet import A_C_VALLEY_Values


def CalculateLatticeConstantdDict(Dictionary):
  # 1. Handle both Material class instances and raw dictionaries
  comp = getattr(Dictionary, "composition", Dictionary)

  # 2. Extract present elements and pad with None for unary/binary alloys
  elements = list(comp.keys())
  while len(elements) < 3:
    elements.append(None)

  x_element, y_element, z_element = elements[0], elements[1], elements[2]

  x = comp.get(x_element, 0.0) if x_element else 0.0
  y = comp.get(y_element, 0.0) if y_element else 0.0
  z = comp.get(z_element, 0.0) if z_element else 0.0

  # ----------------------------------------------------
  # Helper to look up bowing parameters bidirectionally
  # ----------------------------------------------------
  def get_lattice_bowing(el1, el2):
    if not el1 or not el2 or el1 == el2:
      return 0.0
    pair1 = el1 + el2
    pair2 = el2 + el1
    if pair1 in LATTICE_BOWING_VALUES:
      return LATTICE_BOWING_VALUES[pair1]
    if pair2 in LATTICE_BOWING_VALUES:
      return LATTICE_BOWING_VALUES[pair2]
    return 0.0

  def get_lattice_constant(el):
    if not el or el not in LATTICE_A:
      return 0.0
    return LATTICE_A[el]

  # 3. Linear Vegard combination
  xLatticeConstant = get_lattice_constant(x_element)
  yLatticeConstant = get_lattice_constant(y_element)
  zLatticeConstant = get_lattice_constant(z_element)

  LinearLatticeConstant = (
      (x * xLatticeConstant) + (y * yLatticeConstant) + (z * zLatticeConstant)
  )

  # 4. Bowing correction
  xyLatticeBowing = get_lattice_bowing(x_element, y_element)
  yzLatticeBowing = get_lattice_bowing(y_element, z_element)
  xzLatticeBowing = get_lattice_bowing(x_element, z_element)

  BowingLatticeConstant = (
      (x * y * xyLatticeBowing)
      + (y * z * yzLatticeBowing)
      + (x * z * xzLatticeBowing)
  )

  AlloyLatticeConstant = LinearLatticeConstant - BowingLatticeConstant
  return AlloyLatticeConstant


def Calculate_Lattice_Constant_Final(R, epsilon_out, a_template, a_0):
  final_lattice_constant_In_Plane = a_template + (R * (a_0 - a_template))
  final_lattice_constant_Out_Plane = a_0 * (1.0 + epsilon_out)

  return final_lattice_constant_In_Plane, final_lattice_constant_Out_Plane


