# Valley parameters at 10 K (in eV)
# Calibrated using low-T cryogenic Varshni shifts from Vurgaftman / Sun et al.
VALLEYS = {
    'Ge':  {'Gamma': 0.898, 'L': 0.744, 'Delta': 0.930},
    'Si':  {'Gamma': 4.340, 'L': 2.060, 'Delta': 1.170},
    'ASn': {'Gamma': -0.413, 'L': 0.090, 'Delta': 1.200}
}

# Nonlinear bowing parameters (eV)
# GeASn Gamma bowing calibrated to 2.42 eV to match cryogenic 10 K direct-bandgap crossover
BOWING = {
    'SiGe':  {'Gamma': 0.21, 'L': 0.00, 'Delta': 0.10},
    'GeASn': {'Gamma': 2.42, 'L': 0.80, 'Delta': 0.00},
    'SiASn': {'Gamma': 1.30, 'L': 0.00, 'Delta': 0.00}
}

ELEMENTS_BAND_GAP_E = {
    'Ge': 0.744,    # Indirect L-valley minimum at 10 K
    'Si': 1.170,    # Indirect Delta-valley minimum at 10 K
    'A-Sn': 0.00    # Zero-gap inverted band semimetal
}

# Bandgap Pairwise bowing parameters (eV)
BOWING_COMBO_VALUES = {
    'SiGe': 0.21,
    'GeA-Sn': 2.42,
    'SiA-Sn': 1.30
}

# Γ-point (Zone Center, k = 0) in units of 2π/a
ELEMENTS_ROE_Valley_POS = {
    'Si':   (0.0, 0.0, 0.0),
    'Ge':   (0.0, 0.0, 0.0),
    'a-Sn': (0.0, 0.0, 0.0)
}

# Δ-valley (along [100] direction toward X) in units of 2π/a
ELEMENTS_Delta_Valley_POS = {
    'Si':   (0.85, 0.0, 0.0),
    'Ge':   (0.85, 0.0, 0.0),
    'a-Sn': (1.00, 0.0, 0.0)
}

# Lattice constants at 10 K (Angstroms)
# Scaled from 300 K via thermal expansion contraction: a(10 K) = a(300 K) * [1 + alpha_th * (10 - 300)]
LATTICE_A = {
    # Diamond Cubic Group IV
    "Si": 5.427,
    "Ge": 5.648,
    "ASn": 6.480,       # Gray alpha-tin
    "C": 3.566,

    # Virtual Substrates / Metamorphic Buffer Templates at 10 K
    "GeVS": 5.648,            # Fully relaxed Ge virtual substrate on Si
    "GeVS_strained": 5.660,   # Tensile strained Ge-on-Si buffer at 10 K
    "GeSnVS_04": 5.681,       # Partially relaxed Ge_0.96Sn_0.04 template
    "GeSnVS_07": 5.706,       # Partially relaxed Ge_0.93Sn_0.07 buffer

    # Common III-V Binary Substrates (Zinc Blende) at 10 K
    "GaAs": 5.642,
    "InP": 5.861,
    "GaSb": 6.085,
    "InAs": 6.049,
    "InSb": 6.469,
    "GaP": 5.444,
    "AlSb": 6.128,
    "AlAs": 5.653,
    "AlP": 5.445,

    # II-VI Substrates at 10 K
    "CdTe": 6.473,
    "ZnTe": 6.095,
    "ZnSe": 5.658,
    "ZnS": 5.402,
    "PbTe": 6.438,

    # Cubic / Oxide / Perovskite Substrates at 10 K
    "STO": 3.898,
    "LAO": 3.784,
    "MgO": 4.205,
    "GGO": 5.433,
    "DSO": 5.383,
    "LSAT": 3.863,
    "YSZ": 5.118,
    "3C-SiC": 4.356,

    # Hexagonal / Wurtzite Substrates (in-plane a) at 10 K
    "4H-SiC": 3.070,
    "6H-SiC": 3.078,
    "GaN": 3.185,
    "AlN": 3.109,
    "ZnO": 3.246,
    "Al2O3": 4.752,
}

# Real lattice constant bowing parameters in Angstroms (Å)
LATTICE_BOWING_VALUES = {
    'SiGe':  -0.026,
    'GeASn':  0.166,
    'SiASn':  0.000
}

# Hydrostatic Conduction Band Deformation Potentials (eV)
A_C_VALLEY_Values = {
    'Ge':  {'Gamma': -8.24, 'L': -1.54, 'Delta': 1.31},
    'Si':  {'Gamma': -10.50, 'L': -1.80, 'Delta': 1.72},
    'ASn': {'Gamma': -6.00, 'L': -2.14, 'Delta': 1.10}
}

# Elastic stiffness constants C_ij at 10 K in GPa
# Accounted for low-temperature stiffening (~+4 to +7% increase from 300 K)
CRYSTAL_ELASTIC_STIFFNESS_CONSTANTS = {
    # Group IV / Diamond Cubic Elements
    "C": {
        "structure": "cubic",
        "C11": 1085.0,
        "C12": 126.0,
        "C44": 580.0,
    },
    "Si": {
        "structure": "cubic",
        "C11": 167.7,
        "C12": 65.0,
        "C44": 80.4,
    },
    "Ge": {
        "structure": "cubic",
        "C11": 131.5,
        "C12": 49.4,
        "C44": 68.3,
    },
    "ASn": {
        "structure": "cubic",
        "C11": 71.5,
        "C12": 30.5,
        "C44": 58.0,
    },

    # Standard III-V Substrates
    "GaAs": {
        "structure": "cubic",
        "C11": 122.6,
        "C12": 57.1,
        "C44": 60.0,
    },
    "InP": {
        "structure": "cubic",
        "C11": 107.0,
        "C12": 60.5,
        "C44": 47.8,
    },
    "GaSb": {
        "structure": "cubic",
        "C11": 90.8,
        "C12": 41.3,
        "C44": 44.5,
    },
    "InAs": {
        "structure": "cubic",
        "C11": 86.5,
        "C12": 48.5,
        "C44": 39.8,
    },
    "InSb": {
        "structure": "cubic",
        "C11": 69.2,
        "C12": 37.8,
        "C44": 31.3,
    },
    "GaP": {
        "structure": "cubic",
        "C11": 143.8,
        "C12": 65.2,
        "C44": 71.4,
    },
    "AlSb": {
        "structure": "cubic",
        "C11": 91.5,
        "C12": 45.1,
        "C44": 42.4,
    },
    "AlAs": {
        "structure": "cubic",
        "C11": 122.4,
        "C12": 58.5,
        "C44": 60.1,
    },
    "AlP": {
        "structure": "cubic",
        "C11": 135.0,
        "C12": 64.5,
        "C44": 62.5,
    },

    # II-VI Substrates
    "CdTe": {
        "structure": "cubic",
        "C11": 55.0,
        "C12": 38.0,
        "C44": 20.5,
    },
    "ZnTe": {
        "structure": "cubic",
        "C11": 73.0,
        "C12": 42.0,
        "C44": 32.0,
    },
    "ZnSe": {
        "structure": "cubic",
        "C11": 89.0,
        "C12": 52.0,
        "C44": 42.0,
    },
    "ZnS": {
        "structure": "cubic",
        "C11": 109.0,
        "C12": 68.0,
        "C44": 47.5,
    },
    "PbTe": {
        "structure": "cubic",
        "C11": 110.0,
        "C12": 8.0,
        "C44": 15.0,
    },

    # Oxide / Perovskite / Carbides
    "STO": {
        "structure": "cubic",
        "C11": 325.0,
        "C12": 105.0,
        "C44": 126.0,
    },
    "LAO": {
        "structure": "cubic",
        "C11": 328.0,
        "C12": 153.0,
        "C44": 132.0,
    },
    "MgO": {
        "structure": "cubic",
        "C11": 305.0,
        "C12": 97.0,
        "C44": 159.0,
    },
    "LSAT": {
        "structure": "cubic",
        "C11": 312.0,
        "C12": 127.0,
        "C44": 122.0,
    },
    "YSZ": {
        "structure": "cubic",
        "C11": 408.0,
        "C12": 124.0,
        "C44": 61.5,
    },
    "3C-SiC": {
        "structure": "cubic",
        "C11": 395.0,
        "C12": 144.0,
        "C44": 258.0,
    },

    # Hexagonal / Wurtzite Substrates
    "4H-SiC": {
        "structure": "hexagonal",
        "C11": 508.0,
        "C12": 95.0,
        "C13": 58.0,
        "C33": 560.0,
        "C44": 166.0,
    },
    "6H-SiC": {
        "structure": "hexagonal",
        "C11": 509.0,
        "C12": 114.0,
        "C13": 54.0,
        "C33": 560.0,
        "C44": 166.0,
    },
    "GaN": {
        "structure": "hexagonal",
        "C11": 398.0,
        "C12": 147.0,
        "C13": 108.0,
        "C33": 405.0,
        "C44": 107.0,
    },
    "AlN": {
        "structure": "hexagonal",
        "C11": 402.0,
        "C12": 139.0,
        "C13": 110.0,
        "C33": 378.0,
        "C44": 120.0,
    },
    "ZnO": {
        "structure": "hexagonal",
        "C11": 215.0,
        "C12": 124.0,
        "C13": 108.0,
        "C33": 216.0,
        "C44": 44.0,
    },
    "Al2O3": {
        "structure": "hexagonal",
        "C11": 505.0,
        "C12": 166.0,
        "C13": 113.0,
        "C33": 505.0,
        "C44": 150.0,
    },
}

# Valence band deformation potentials and Pikus-Bir parameters (in eV)
PIKUS_BIR_VALENCE_PARAMS = {
    "Si": {
        "av": 2.46,
        "b": -2.10,
        "l": -1.74,
        "m": 4.56,
        "delta_so": 0.044
    },
    "Ge": {
        "av": 1.24,
        "b": -2.86,
        "l": -4.48,
        "m": 4.10,
        "delta_so": 0.290
    },
    "ASn": {
        "av": 1.58,
        "b": -2.30,
        "l": -3.02,
        "m": 3.88,
        "delta_so": 0.800
    }
}

DELTA_SO = {
    "Si": 0.044,
    "Ge": 0.290,
    "ASn": 0.800,
}