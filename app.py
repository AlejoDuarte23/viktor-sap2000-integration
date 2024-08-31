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
    select_elements.cross_section = OptionField("New Cross-Section", options= ["L2x1/4", "L3x1/4"])
    

    text_change_material = Text("## Change Material")
    slc_mat_elements =  DynamicArray("Change Material")
    slc_mat_elements.select = GeometryMultiSelectField('Select Elements', min_select=1, max_select=10)
    slc_mat_elements.material =  OptionField("New Cross-Section", options= ["A36", "A516"])


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


    def create_sap2000_model(self, params, **kwargs):

        tower3 = TowerColumn(height=params.str_height, width=params.str_width, n_diagonals=params.n_diags)
        tower3.create_columns()
        SapModel = PySap2000().create()
        MATERIAL_CONCRETE = 2

        ret = SapModel.PropMaterial.SetMaterial('CONC',MATERIAL_CONCRETE)
        ret = SapModel.PropMaterial.SetMPIsotropic('CONC',3600, 0.2, 0.0000055)
        ret = SapModel.PropFrame.SetRectangle('R1','CONC', 200, 200)

        units = 9

        ret = SapModel.SetPresentUnits(units)
        create_frame(SapModel, tower3.nodes, tower3.lines, material = 'R1')
        ret = SapModel.View.RefreshView(0, False)
