# in here we will introduce mulitple class to describe the laser device shown the Dr. Fisher Yu's papers.
# we will need a class 'laser' that takes in a number of layers, a type for each layer, a thickness for each layer, and a postion
# of stack in the laser with 0 being the substrate. so that the program can caclulate the strain due to lattice mismatch.
# that being said we do need to add the calulations for the critical width of the layers based on the compostion and what layer compostion
# they are sitting agiast, so that we can simulate the relaxation of each layer based on width adn correctly model the next boundary of two
# layers to correctly model the entire device.

import math
from CAlloyLatticeConstant import CalculateLatticeConstantdDict
from CBiaxialStrain import CalculateBiaxialStrainDict
from CBandGapType import CalculateBandGapTypeDict
from CBgE import CalculateBandgapEnergyDict
from CValenceBand import CalculateValenceBandEnergyDict
from CBiaxialStrain import Calculate_CRYSTAL_ELASTIC_STIFFNESS_CONSTANTS
from CcritcalThickness import CalculateCriticalThickness
from CcritcalThickness import calculate_relaxation
from CAlloyLatticeConstant import Calculate_Lattice_Constant_Final
from CBiaxialStrain import  CalculateBiaxialStrainDictRelaxation

class Material:
    def __init__(self, composition: dict[str, float]):
        """
        composition: dictionary mapping element symbols to mole/atomic fractions.
        Example: {"Si": 0.7, "Ge": 0.3}
        """
        self.composition = composition
        self._validate_fractions()

    def _validate_fractions(self):
        total = sum(self.composition.values())
        # Use math.isclose to account for floating-point arithmetic imprecision
        if not math.isclose(total, 1.0, rel_tol=1e-5, abs_tol=1e-5):
            raise ValueError(f"Fractions must sum to 1.0. Current sum: {total}")

    def __repr__(self):
        formula = "".join(f"{el}_{frac:.2f}" for el, frac in self.composition.items())
        return f"Material({formula})"


class Layer:
    def __init__(self, name: str, thickness_nm: float, material: Material, doping: str = "intrinsic"):
        self.name = name
        self.thickness_nm = thickness_nm
        self.material = material
        self.doping = doping
        self.relaxed_lattice_constant = CalculateLatticeConstantdDict(material)
        self.C11, self.C12 = Calculate_CRYSTAL_ELASTIC_STIFFNESS_CONSTANTS(material)

    def __repr__(self):
        return f"Layer({self.name}, {self.thickness_nm} nm, {self.material} material, {self.doping} doping, {self.relaxed_lattice_constant}nm relaxed lattice constant)"


class SubstrateLayer(Layer):
    def __init__(self, name: str, thickness_nm: float, material: Material, doping: str = "intrinsic"):

        super().__init__(name, thickness_nm, material, doping)
        self.final_lattice_constant_In_Plane = self.relaxed_lattice_constant
        self.final_lattice_constant_Out_Plane = self.relaxed_lattice_constant

        self.EgammaStrainCorrection = 0
        self.ELStrainCorrection = 0
        self.EdeltaStrainCorrection = 0
        self.epsilon_hydrostatic = 0
        self.epsilon_shear = 0
        self.inplanestrain = 0
        self.outplanestrain = 0

        self.R = 1
        self.hc = 0




        (
        self.bandgap_type,
        self.gamma_conduction_valley, 
        self.L_conduction_valley,
        self.delta_conduction_valley
        ) = CalculateBandGapTypeDict(self)
                
        (
        self.delta_E_light_hole_valance_band,
        self.delta_E_heavy_hole_valance_band,
        self.delta_E_so_valance_band
        ) = CalculateValenceBandEnergyDict(self)
                        
        self.bandgap_energy = CalculateBandgapEnergyDict(self)


class BufferLayer(Layer):
    def __init__(self, name: str, thickness_nm: float, material: Material, underlying_layer_0:SubstrateLayer , 
            doping: str = "intrinsic"):
        
        super().__init__(name, thickness_nm, material, doping)
        
        self.underlying_layer_0 = underlying_layer_0
        self.underlying_layers = [self.underlying_layer_0]
        self.hc = CalculateCriticalThickness(self.underlying_layer_0, self)
        self.R = calculate_relaxation(self)


        #this data is calculated before the consideration of relaxation of the layer
        (
        self.MaxEgammaStrainCorrection,
        self.MaxELStrainCorrection,
        self.MaxEdeltaStrainCorrection,
        self.Maxepsilon_hydrostatic,
        self.Maxepsilon_shear,
        self.Maxinplanestrain,
        self.Maxoutplanestrain
        ) = CalculateBiaxialStrainDict(self.underlying_layer_0, self)

        

        (
        self.EgammaStrainCorrection,
        self.ELStrainCorrection,
        self.EdeltaStrainCorrection,
        self.epsilon_hydrostatic,
        self.epsilon_shear,
        self.inplanestrain,
        self.outplanestrain
        ) = CalculateBiaxialStrainDictRelaxation(self.underlying_layer_0, self, self.R)




        (
        self.bandgap_type,
        self.gamma_conduction_valley, 
        self.L_conduction_valley,
        self.delta_conduction_valley
        ) = CalculateBandGapTypeDict(self)
        
        (
        self.delta_E_light_hole_valance_band,
        self.delta_E_heavy_hole_valance_band,
        self.delta_E_so_valance_band
        ) = CalculateValenceBandEnergyDict(self)
                
        self.bandgap_energy = CalculateBandgapEnergyDict(self)


        

        self.final_lattice_constant_In_Plane, self.final_lattice_constant_Out_Plane = Calculate_Lattice_Constant_Final(self.R, 
                    self.outplanestrain, self.underlying_layer_0.final_lattice_constant_In_Plane, self.relaxed_lattice_constant)



class GradedBufferLayer(Layer):
    def __init__(self, name: str, thickness_nm: float, material_bottom: Material, underlying_layer_0:SubstrateLayer ,
            underlying_layer_1: BufferLayer, material_top: Material, doping: str = "intrinsic"):
        
        super().__init__(name, thickness_nm, material_top, doping)
        
        self.underlying_layer_0 = underlying_layer_0
        self.underlying_layer_1 = underlying_layer_1
        self.underlying_layers = [self.underlying_layer_0, self.underlying_layer_1]

        self.material_bottom = material_bottom
        self.material_top = material_top
        self.relaxed_lattice_constant_bottom = CalculateLatticeConstantdDict(material_bottom)
        self.relaxed_lattice_constant_top = CalculateLatticeConstantdDict(material_top) # what we will use when we build on top of this layer.
        self.strain_top = 0
        self.relaxed_lattice_constant = self.relaxed_lattice_constant_bottom # when we begin to build this layer we have this lattice constant.

        self.Sn_increase_function = 0
        self.hc = CalculateCriticalThickness(self.underlying_layer_1, self)
        self.R = calculate_relaxation(self)

        #this data is calculated before the consideration of relaxation of the layer
        (
        self.MaxEgammaStrainCorrection,
        self.MaxELStrainCorrection,
        self.MaxEdeltaStrainCorrection,
        self.Maxepsilon_hydrostatic,
        self.Maxepsilon_shear,
        self.Maxinplanestrain,
        self.Maxoutplanestrain
        ) = CalculateBiaxialStrainDict(self.underlying_layer_1, self)
        
        

        (
        self.EgammaStrainCorrection,
        self.ELStrainCorrection,
        self.EdeltaStrainCorrection,
        self.epsilon_hydrostatic,
        self.epsilon_shear,
        self.inplanestrain,
        self.outplanestrain
        ) = CalculateBiaxialStrainDictRelaxation(self.underlying_layer_1, self, self.R)


        (
        self.bandgap_type,
        self.gamma_conduction_valley, 
        self.L_conduction_valley,
        self.delta_conduction_valley
        ) = CalculateBandGapTypeDict(self)
        
        (
        self.delta_E_light_hole_valance_band,
        self.delta_E_heavy_hole_valance_band,
        self.delta_E_so_valance_band
        ) = CalculateValenceBandEnergyDict(self)
                
        self.bandgap_energy = CalculateBandgapEnergyDict(self)



        self.final_lattice_constant_In_Plane, self.final_lattice_constant_Out_Plane = Calculate_Lattice_Constant_Final(self.R, 
            self.outplanestrain, self.underlying_layer_1.final_lattice_constant_In_Plane, self.relaxed_lattice_constant_top)




#still need to implement the critcal thickness to maintain the accurracy
class ActiveLayer(Layer):
    def __init__(self, name: str, thickness_nm: float, material: Material, underlying_layer_0:SubstrateLayer ,
            underlying_layer_1: BufferLayer, underlying_layer_2: GradedBufferLayer, doping: str = "intrinsic"):
        
        super().__init__(name, thickness_nm, material, doping)
        
        self.underlying_layer_0 = underlying_layer_0
        self.underlying_layer_1 = underlying_layer_1
        self.underlying_layer_2 = underlying_layer_2

        self.underlying_layers = [self.underlying_layer_0, self.underlying_layer_1, self.underlying_layer_2]

        self.hc = CalculateCriticalThickness(self.underlying_layer_2, self)
        self.R = calculate_relaxation(self)
        #this data is calculated before the consideration of relaxation of the layer
        (
        self.MaxEgammaStrainCorrection,
        self.MaxELStrainCorrection,
        self.MaxEdeltaStrainCorrection,
        self.Maxepsilon_hydrostatic,
        self.Maxepsilon_shear,
        self.Maxinplanestrain,
        self.Maxoutplanestrain
        ) = CalculateBiaxialStrainDict(self.underlying_layer_2, self)

        (
        self.EgammaStrainCorrection,
        self.ELStrainCorrection,
        self.EdeltaStrainCorrection,
        self.epsilon_hydrostatic,
        self.epsilon_shear,
        self.inplanestrain,
        self.outplanestrain
        ) = CalculateBiaxialStrainDictRelaxation(self.underlying_layer_2, self, self.R)
        
        self.strain_top = 0
        
        (
        self.bandgap_type,
        self.gamma_conduction_valley, 
        self.L_conduction_valley,
        self.delta_conduction_valley
        ) = CalculateBandGapTypeDict(self)

        (
        self.delta_E_light_hole_valance_band,
        self.delta_E_heavy_hole_valance_band,
        self.delta_E_so_valance_band
        ) = CalculateValenceBandEnergyDict(self)
        
        self.bandgap_energy = CalculateBandgapEnergyDict(self)


        self.final_lattice_constant_In_Plane, self.final_lattice_constant_Out_Plane = Calculate_Lattice_Constant_Final(self.R, 
            self.outplanestrain, self.underlying_layer_2.final_lattice_constant_In_Plane, self.relaxed_lattice_constant)





class CapLayer(Layer):
    def __init__(self, name: str, thickness_nm: float, material: Material, 
            underlying_layer_0:SubstrateLayer , underlying_layer_1: BufferLayer, 
            underlying_layer_2: GradedBufferLayer, underlying_layer_3 : ActiveLayer,
            doping: str = "intrinsic"):
        
        super().__init__(name, thickness_nm, material, doping)
        self.underlying_layer_0 = underlying_layer_0
        self.underlying_layer_1 = underlying_layer_1
        self.underlying_layer_2 = underlying_layer_2
        self.underlying_layer_3 = underlying_layer_3

        self.underlying_layers = [self.underlying_layer_0, self.underlying_layer_1, self.underlying_layer_2, self.underlying_layer_3]
        self.hc = CalculateCriticalThickness(self.underlying_layer_3, self)
        self.R = calculate_relaxation(self)

        #this data is calculated before the consideration of relaxation of the layer
        (
        self.MaxEgammaStrainCorrection,
        self.MaxELStrainCorrection,
        self.MaxEdeltaStrainCorrection,
        self.Maxepsilon_hydrostatic,
        self.Maxepsilon_shear,
        self.Maxinplanestrain,
        self.Maxoutplanestrain
        ) = CalculateBiaxialStrainDict(self.underlying_layer_3, self)
        
        

        (
        self.EgammaStrainCorrection,
        self.ELStrainCorrection,
        self.EdeltaStrainCorrection,
        self.epsilon_hydrostatic,
        self.epsilon_shear,
        self.inplanestrain,
        self.outplanestrain
                ) = CalculateBiaxialStrainDictRelaxation(self.underlying_layer_3, self, self.R)



        (
        self.bandgap_type,
        self.gamma_conduction_valley, 
        self.L_conduction_valley,
        self.delta_conduction_valley
        ) = CalculateBandGapTypeDict(self)
        
        (
        self.delta_E_light_hole_valance_band,
        self.delta_E_heavy_hole_valance_band,
        self.delta_E_so_valance_band
        ) = CalculateValenceBandEnergyDict(self)
                
        self.bandgap_energy = CalculateBandgapEnergyDict(self)

        self.final_lattice_constant_In_Plane, self.final_lattice_constant_Out_Plane = Calculate_Lattice_Constant_Final(self.R, 
            self.outplanestrain, self.underlying_layer_3.final_lattice_constant_In_Plane, self.relaxed_lattice_constant)


class TopContactLayer(Layer):
    def __init__(self, name: str, thickness_nm: float, material: Material, 
            underlying_layer_0:SubstrateLayer , underlying_layer_1: BufferLayer, 
            underlying_layer_2: GradedBufferLayer, underlying_layer_3 : ActiveLayer,
            underlying_layer_4 : CapLayer,
            doping: str = "intrinsic"):
        
        super().__init__(name, thickness_nm, material, doping)
        self.underlying_layer_0 = underlying_layer_0
        self.underlying_layer_1 = underlying_layer_1
        self.underlying_layer_2 = underlying_layer_2
        self.underlying_layer_3 = underlying_layer_3
        self.underlying_layer_4 = underlying_layer_4


        self.underlying_layers = [self.underlying_layer_0, self.underlying_layer_1, self.underlying_layer_2, 
        self.underlying_layer_3, self.underlying_layer_4]
        
        self.hc = CalculateCriticalThickness(self.underlying_layer_4, self)

        self.R = calculate_relaxation(self)

        #this data is calculated before the consideration of relaxation of the layer
        (
        self.MaxEgammaStrainCorrection,
        self.MaxELStrainCorrection,
        self.MaxEdeltaStrainCorrection,
        self.Maxepsilon_hydrostatic,
        self.Maxepsilon_shear,
        self.Maxinplanestrain,
        self.Maxoutplanestrain
        ) = CalculateBiaxialStrainDict(self.underlying_layer_4, self)
                


     

        (
        self.EgammaStrainCorrection,
        self.ELStrainCorrection,
        self.EdeltaStrainCorrection,
        self.epsilon_hydrostatic,
        self.epsilon_shear,
        self.inplanestrain,
        self.outplanestrain
                ) = CalculateBiaxialStrainDictRelaxation(self.underlying_layer_4, self, self.R)


        (
        self.bandgap_type,
        self.gamma_conduction_valley, 
        self.L_conduction_valley,
        self.delta_conduction_valley
        ) = CalculateBandGapTypeDict(self)
        
        (
        self.delta_E_light_hole_valance_band,
        self.delta_E_heavy_hole_valance_band,
        self.delta_E_so_valance_band
        ) = CalculateValenceBandEnergyDict(self)
                
        self.bandgap_energy = CalculateBandgapEnergyDict(self)

        

        self.final_lattice_constant_In_Plane, self.final_lattice_constant_Out_Plane = Calculate_Lattice_Constant_Final(self.R, 
            self.outplanestrain, self.underlying_layer_4.final_lattice_constant_In_Plane, self.relaxed_lattice_constant)


class Device:
    def __init__(self, name: str):
        self.name = name
        self.layers: list[Layer] = []

    def add_Substratelayer(self, layer: SubstrateLayer):
        self.layers.append(layer)

    def add_Bufferlayer(self, layer: BufferLayer):
        self.layers.append(layer)

    def add_GradedBufferlayer(self, layer: GradedBufferLayer):
        self.layers.append(layer)

    def add_Activelayer(self, layer: ActiveLayer):
        self.layers.append(layer)

    def add_Caplayer(self, layer: CapLayer):
        self.layers.append(layer)

    def add_TopContactlayer(self, layer: TopContactLayer):
        self.layers.append(layer)

    def total_thickness(self) -> float:
        return sum(layer.thickness_nm for layer in self.layers)

    def __repr__(self):
        return f"Device('{self.name}', {len(self.layers)} layers)"


# Create individual layers
substrate_layer = SubstrateLayer(name="Layer 0", thickness_nm=140000.0, material= Material({'Si':1}), doping="intrinsic")

buffer_layer = BufferLayer(name="Layer 1", thickness_nm=500.0, underlying_layer_0=substrate_layer, material= Material({'Ge': 1}), doping="n+")

# for the graded layer the rate of increse in Sn(usally) is dependant on the layer below, for now we will approximate it as linear from
# boundary to boundary
graded_buffer_layer = GradedBufferLayer(name="Layer 2", thickness_nm=700.0, 
    material_bottom= Material({'Ge': 0.92, 'ASn':0.08}), 
    underlying_layer_0=substrate_layer,
    underlying_layer_1=buffer_layer,
    material_top= Material({'Ge': 0.89, 'ASn':0.11}), doping="n+")

active_layer = ActiveLayer(name='Layer 3', thickness_nm=1000.0, material = Material({'Ge': 0.89, 'ASn':0.11}),
    underlying_layer_0=substrate_layer,
    underlying_layer_1=buffer_layer,
    underlying_layer_2=graded_buffer_layer, 
    doping='intrinsic')
cap_layer = CapLayer(name='Layer 4', thickness_nm=170.0, material= Material({'Si':0.03,'Ge': 0.89, 'ASn':0.08}),
    underlying_layer_0=substrate_layer,
    underlying_layer_1=buffer_layer,
    underlying_layer_2=graded_buffer_layer,
    underlying_layer_3=active_layer,
    doping='p')
topContact_layer = TopContactLayer(name='Layer 5', thickness_nm=70.0, material= Material({'Si':0.03,'Ge': 0.89, 'ASn':0.08}), 
    underlying_layer_0=substrate_layer,
    underlying_layer_1=buffer_layer,
    underlying_layer_2=graded_buffer_layer,
    underlying_layer_3=active_layer,
    underlying_layer_4=cap_layer,
    doping='p+')

# Create the device and assemble the stack
laser_diode = Device("GeSn Diode Laser")
laser_diode.add_Substratelayer(substrate_layer)
laser_diode.add_Bufferlayer(buffer_layer)
laser_diode.add_GradedBufferlayer(graded_buffer_layer)
laser_diode.add_Activelayer(active_layer)
laser_diode.add_Caplayer(cap_layer)
laser_diode.add_TopContactlayer(topContact_layer)

print(laser_diode)
# Output: Device

print(f"Total thickness: {laser_diode.total_thickness()} nm")
# Output: Total thickness



#the Ui sliders will be able to change the material compostion of the selected layer
# the selected layers bandgap nature will be displayed along with strain and types of strain
