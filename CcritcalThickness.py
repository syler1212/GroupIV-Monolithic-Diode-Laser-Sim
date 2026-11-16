import math
from scipy.optimize import brentq


import math
from scipy.optimize import brentq


def CalculateCriticalThickness(layer_a, layer_b):
  # 1. Template lattice constant presented at the surface (in Angstroms)
  a_template = getattr(
      layer_a,
      "final_lattice_constant_In_Plane",
      layer_a.relaxed_lattice_constant,
  )
  a_b = layer_b.relaxed_lattice_constant

  # 2. Lattice mismatch
  f = abs(a_template - a_b) / a_b
  if f < 1e-6:
    return float("inf")

  # 3. Poisson ratio and Burgers vector magnitude (b in Angstroms)
  nu = layer_b.C12 / (layer_b.C11 + layer_b.C12)
  b = a_b / math.sqrt(2.0)

  # Matthews-Blakeslee prefactor K for 60-degree dislocations on (001)
  K = (b / (2.0 * math.pi * f)) * ((2.0 - 0.5 * nu) / (1.0 + nu))

  # 4. Transcendental objective function
  def eq(hc):
    return hc - K * (math.log(hc / b) + 1.0)

  # 5. Solve in Angstroms, convert to nanometers (1 nm = 10 A)
  try:
    hc_angstroms = brentq(eq, b * 1.0001, 1e7)
    return hc_angstroms / 10.0
  except (ValueError, RuntimeError):
    return float("inf")


def calculate_relaxation(layer) -> float:
  """Calculates the relaxation factor R (from 0.0 to 1.0) based on critical thickness hc."""
  if math.isinf(layer.hc) or layer.thickness_nm <= layer.hc:
    return 0.0

  R = 1.0 - (layer.hc / layer.thickness_nm)
  return min(max(R, 0.0), 1.0)