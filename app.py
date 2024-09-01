from geom_param import TowerColumn
from sap2000_engine import PySap2000, create_frame

from viktor import ViktorController , OptionField
from viktor.parametrization import  GeometryMultiSelectField, DynamicArray
from viktor.parametrization import ViktorParametrization
from viktor.parametrization import NumberField, Text, ActionButton
from viktor.geometry import CircularExtrusion, Group, Material, Color, Point, Sphere, LinearPattern, Line,RectangularExtrusion
from viktor.views import GeometryView, GeometryResult


class Parametrization(ViktorParametrization):
    text_building = Text('## Structure Geometry')
    str_width = NumberField('Structure Width', min=200, default=800)
    str_height= NumberField('Structure Height', min=1000, default=4000)
    n_diags = NumberField('Number of Diagonals', min=3, default=7)
    
    text_select_elements = Text("## Change Cross-Section")
    select_elements =  DynamicArray("Change Cross-Section")
    select_elements.select = GeometryMultiSelectField('Select Elements', min_select=1, max_select=10)
    select_elements.cross_section = OptionField("New Cross-Section", options= ["EA50x6", "EA70x6"])
    

    text_change_material = Text("## Change Material")
    slc_mat_elements =  DynamicArray("Change Material")
    slc_mat_elements.select = GeometryMultiSelectField('Select Elements', min_select=1, max_select=10)
    slc_mat_elements.material =  OptionField("New Cross-Section", options= ["S275", "S355"])


    text_add_supports = Text("## Add Suppports")
    supports =  DynamicArray("Add Supports")
    supports.select = GeometryMultiSelectField('Select Nodes', min_select=1, max_select=10)
    supports.type =  OptionField("Support Type", options= ["Pinned", "Fixed"])


    
    text_sap2000 = Text('## Crate SAP2000 Model !')
    create_sap2000_button = ActionButton('Create SAP2000 Model', method='create_sap2000_model')




class Controller(ViktorController):
    label = 'Structure Controller'
    parametrization = Parametrization


    def create_frame(self, nodes: dict, lines: dict, sect_width: float = 100, sect_depth: float = 100) -> list:
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
            
            if not node_id_i in rendered_sphere:
                sphere_k = Sphere(point_i , radius=80,material=None, identifier= str(node_id_i))
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
        print("cross_Sectino" , params.select_elements)
        print("materials", params.slc_mat_elements )

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
        ''' convert lines into members by adding material and secction tag'''

        default_mat = {"material": material_tag}
        default_sec = {"sec_tag": sect_tag}

        members = {}
        for key, line in lines.items():
            members[key] = {**line,**default_mat,**default_sec}
        print(members)
        return members
    
    def members_factory_sap2000(self, members:dict, SapModel:any)->int:
        
        sections = {
            "EA50x6": {
                "depth":50,
                "thickness":6
            },
            "EA70x6": {
                "depth":70,
                "thickness":6,
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

        member2sap = {}
        for key, member in members.items():
            mat_name = member["material"]
            sec_name = member["sec_tag"]
            combine_name  = f"{mat_name}_{sec_name}"
            member2sap[key] = {**member, "sap_sec_id": combine_name}
        
        return member2sap


    def change_members_params(self, members:dict, params: any)->dict:
        if params.select_elements:
            for munch_dict in params.select_elements:

                print(munch_dict)
                for str_ele in munch_dict.select:
                    print(members[int(str_ele)]["sec_tag"])
                    print(munch_dict.cross_section)
                    members[int(str_ele)]["sec_tag"] = munch_dict.cross_section
        return members

    def change_members_material(self, members:dict, params: any)->None:
        if params.slc_mat_elements:
            for munch_dict in params.slc_mat_elements:
                for str_ele in munch_dict.select:
                    members[int(str_ele)]["material"] = munch_dict.material
        return members


    def create_sap2000_model(self, params, **kwargs):

        tower3 = TowerColumn(height=params.str_height, width=params.str_width, n_diagonals=params.n_diags)
        tower3.create_columns()
        SapModel = PySap2000().create()


        members = self.members_from_lines(tower3.lines, params)
        members = self.change_members_params(members=members, params=params)
        members = self.change_members_material(members=members, params=params)

        members_factory = self.members_factory(members)
        ret = self.members_factory_sap2000(members_factory, SapModel)
        
        units = 9

        ret = SapModel.SetPresentUnits(units)
        create_frame(SapModel, tower3.nodes, members_factory, material = 'S355_EA50x6')
        ret = SapModel.View.RefreshView(0, False)
