from DataSet import CRYSTAL_ELASTIC_STIFFNESS_CONSTANTS


def Calculate_CRYSTAL_ELASTIC_STIFFNESS_CONSTANTS(Dictionary):
  """Calculates linearly interpolated elastic stiffness constants C11 and C12

  for unary, binary, or ternary Group-IV alloys. Supports Material instances or
  plain dicts.
  """
  comp = getattr(Dictionary, "composition", Dictionary)

  # Standardize element array by padding with None if fewer than 3 elements
  elements = list(comp.keys())
  while len(elements) < 3:
    elements.append(None)

  x_element, y_element, z_element = elements[0], elements[1], elements[2]

  x = comp.get(x_element, 0.0) if x_element else 0.0
  y = comp.get(y_element, 0.0) if y_element else 0.0
  z = comp.get(z_element, 0.0) if z_element else 0.0

  def get_stiffness(el, constant_name):
    if not el or el not in CRYSTAL_ELASTIC_STIFFNESS_CONSTANTS:
      return 0.0
    return CRYSTAL_ELASTIC_STIFFNESS_CONSTANTS[el].get(constant_name, 0.0)

  # C11 Calculation
  X_C11 = get_stiffness(x_element, "C11")
  Y_C11 = get_stiffness(y_element, "C11")
  Z_C11 = get_stiffness(z_element, "C11")
  C11 = (x * X_C11) + (y * Y_C11) + (z * Z_C11)

  # C12 Calculation
  X_C12 = get_stiffness(x_element, "C12")
  Y_C12 = get_stiffness(y_element, "C12")
  Z_C12 = get_stiffness(z_element, "C12")
  C12 = (x * X_C12) + (y * Y_C12) + (z * Z_C12)

  return C11, C12