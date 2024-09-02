
from geom_param import TowerColumn
from sap2000_engine import PySap2000, create_frame

from viktor import ViktorController , OptionField
from viktor.parametrization import  GeometryMultiSelectField, DynamicArray
from viktor.parametrization import ViktorParametrization
from viktor.parametrization import NumberField, Text, ActionButton
from viktor.geometry import Color, Point, Sphere, Line, RectangularExtrusion
from viktor.views import GeometryView, GeometryResult


class Parametrization(ViktorParametrization):
    ''' This class wraps the parameters of the app'''
    # Structure Params
    text_building = Text('## Structure Geometry')
    str_width = NumberField('Structure Width', min=200, default=800)
    str_height = NumberField('Structure Height', min=1000, default=4000)
    n_diags = NumberField('Number of Diagonals', min=3, default=7)
    
    # Change Cross Sections
    text_select_elements = Text("## Change Cross-Section")
    select_elements = DynamicArray("Change Cross-Section")
    select_elements.select = GeometryMultiSelectField('Select Elements', min_select=1, max_select=10)
    select_elements.cross_section = OptionField("New Cross-Section", options=["EA50x6", "EA70x6"])
    
    # Change Materials
    text_change_material = Text("## Change Material")
    slc_mat_elements = DynamicArray("Change Material") # This is a Munch object with strings in it 
    slc_mat_elements.select = GeometryMultiSelectField('Select Elements', min_select=1, max_select=10)
    slc_mat_elements.material = OptionField("New Material", options=["S275", "S355"])  
    
    # Adds supports
    text_add_supports = Text("## Add Supports")  
    supports = DynamicArray("Add Supports") 
    supports.select = GeometryMultiSelectField('Select Nodes', min_select=1, max_select=10)
    supports.type = OptionField("Support Type", options=["Pinned", "Fixed"])
    
    # Run Sap2000
    text_sap2000 = Text('## Create SAP2000 Model!')
    create_sap2000_button = ActionButton('Create SAP2000 Model', method='create_sap2000_model')

class Controller(ViktorController):
    ''' This class renders, creates the geometry and the sap2000 model'''
    label = 'Structure Controller'
    parametrization = Parametrization

    def create_frame(self, nodes: dict, lines: dict, sect_width: float = 100, sect_depth: float = 100) -> list:
        """
        Convert topology data into VIKTOR objects: POINTS, LINES, and EXTRUSIONS.
        inputs:
            lines (dict):  {line_id: {"start": int, "end": int}}
            nodes (dict): {node_id: {"x": float, "y": float, "z": float}}
        Returns:
            list: List of VIKTOR objects representing the structure.
        """
        sections_group = []
        rendered_sphere = set()

        for line_id, dict_vals in lines.items():

            node_id_i = dict_vals["start"]
            node_id_j = dict_vals["end"]

            node_i = nodes[node_id_i]
            node_j = nodes[node_id_j]

            point_i = Point(node_i["x"],
                            node_i["y"],
                            node_i["z"])

            point_j = Point(node_j["x"],
                            node_j["y"],
                            node_j["z"])
            
            # To Do: This can be simplified 
            if not node_id_i in rendered_sphere:
                sphere_k = Sphere(point_i, radius=80,material=None, identifier= str(node_id_i))
                sections_group.append(sphere_k)
                rendered_sphere.add(node_id_i)

            if not node_id_j in rendered_sphere:
                sphere_k = Sphere(point_j , radius=80, material= None,  identifier= str(node_id_j))
                sections_group.append(sphere_k)
                rendered_sphere.add(node_id_j)

            line_k = Line(point_i, point_j)
            section_k = RectangularExtrusion(sect_width, sect_depth, line_k, identifier=str(line_id))
            sections_group.append(section_k)

        return sections_group
    
    @GeometryView("3D model", duration_guess=1, x_axis_to_right=True)
    def create_render(self, params, **kwargs):
        ''' Renders the structure tower.nodes and tower.lines returns dict compatible with the "create_frame" function'''

        tower = TowerColumn(height=params.str_height, width=params.str_width, n_diagonals=params.n_diags)
        tower.create_columns()

        sections_group = self.create_frame(
            nodes=tower.nodes,
            lines=tower.lines
        )

        return GeometryResult(geometry=sections_group)

    def members_from_lines(self,
                           lines:dict,
                           params:any,
                           material_tag:str = "S355",
                           sect_tag:str = "EA50x6",
                           )->dict:
        ''' Convert lines into members by adding material and secction tag'''

        default_mat = {"material": material_tag}
        default_sec = {"sec_tag": sect_tag}

        members = {}
        for key, line in lines.items():
            members[key] = {**line,**default_mat,**default_sec}
        print(members)
        return members
    
    def members_factory_sap2000(self, members:dict, SapModel:any)->int:
        '''
        Creates SAP2000 sections. This function implements a set to avoid creating duplicate cross sections.
        '''        
        sections = {
            "EA50x6": {
                "depth":50.0,
                "thickness":6.0
            },
            "EA70x6": {
                "depth":70.0,
                "thickness":6.0,
            }
            }
        
        materials = {
            "S355": {
                "E":210000,
                "v":0.3,
                "tc":1.2e-5
                },
            "S275": {
                "E":210000,
                "v":0.3,
                "tc":1.2e-5
                },
        }
        
        combine = set()
        mat = set()
        for key, member in members.items():
            mat_name = member["material"]
            sec_name = member["sec_tag"]
            unique_member  =  (mat_name, sec_name)
            combine_name  = f"{mat_name}_{sec_name}"
            if not unique_member in combine:

                if not mat_name in mat: 
                    MATERIAL_STEEL = 1
                    ret = SapModel.PropMaterial.SetMaterial(mat_name, MATERIAL_STEEL)
                    ret = SapModel.PropMaterial.SetMPIsotropic(mat_name,210000,0.3,1.2e-5)
                    mat.add(mat_name)
                
                print(sections[sec_name]["depth"])
                print(sections[sec_name]["thickness"])

                ret = SapModel.PropFrame.SetAngle(
                    Name = combine_name,
                    MatProp= mat_name,
                    T3=sections[sec_name]["depth"],
                    T2=sections[sec_name]["depth"],
                    Tf=sections[sec_name]["thickness"],
                    Tw=sections[sec_name]["thickness"]
                )

                combine.add(unique_member)
        return ret

    def members_factory(self, members:dict)-> dict:
        '''Create section id '''
        member2sap = {}
        for key, member in members.items():
            mat_name = member["material"]
            sec_name = member["sec_tag"]
            combine_name  = f"{mat_name}_{sec_name}"
            member2sap[key] = {**member, "sap_sec_id": combine_name}
        
        return member2sap


    def change_members_params(self, members:dict, params: any)->dict:
        '''Changes members cross section'''
        if params.select_elements:
            for munch_dict in params.select_elements:

                print(munch_dict)
                for str_ele in munch_dict.select:
                    print(members[int(str_ele)]["sec_tag"])
                    print(munch_dict.cross_section)
                    members[int(str_ele)]["sec_tag"] = munch_dict.cross_section
        return members

    def change_members_material(self, members:dict, params: any)->None:
        '''Changes members material'''

        if params.slc_mat_elements:
            for munch_dict in params.slc_mat_elements:
                for str_ele in munch_dict.select:
                    members[int(str_ele)]["material"] = munch_dict.material
        return members

    def assing_supports(self,params:any, SapModel:any)->None | int:
        '''Assign support to nodes'''
        if params.supports:
            for munch_dict in params.supports:
                for node_id in munch_dict.select:
                    if munch_dict.type == "Pinned":
                        ret= SapModel.PointObj.SetRestraint(node_id, [1, 1, 1, 0, 0, 1])
                    else:
                        ret = SapModel.PointObj.SetRestraint(node_id, [1, 1, 1, 1, 1, 1])
                
                return ret 
        return None 


    def create_sap2000_model(self, params, **kwargs):
        '''Creates the sap2000 model'''
        tower3 = TowerColumn(height=params.str_height, width=params.str_width, n_diagonals=params.n_diags)
        tower3.create_columns()
        SapModel = PySap2000().create()


        members = self.members_from_lines(tower3.lines, params)
        members = self.change_members_params(members=members, params=params)
        members = self.change_members_material(members=members, params=params)

        members_factory = self.members_factory(members)
        
        units = 9
        ret = SapModel.SetPresentUnits(units)

        ret = self.members_factory_sap2000(members_factory, SapModel)
        create_frame(SapModel, tower3.nodes, members_factory, material = 'S355_EA50x6')
        ret = self.assing_supports(params= params, SapModel=SapModel)
        ret = SapModel.View.RefreshView(0, False)
