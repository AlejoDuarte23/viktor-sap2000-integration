from geom_param import TowerColumn
from sap2000_engine import PySap2000, create_frame

from viktor import ViktorController
from viktor.parametrization import ViktorParametrization
from viktor.parametrization import NumberField, Text, ActionButton
from viktor.geometry import CircularExtrusion, Group, Material, Color, Point, LinearPattern, Line,RectangularExtrusion
from viktor.views import GeometryView, GeometryResult


class Parametrization(ViktorParametrization):
    text_building = Text('## Structure Geometry')
    str_width = NumberField('Structure Width', min=200, default=800)
    str_height= NumberField('Structure Height', min=1000, default=4000)
    n_diags = NumberField('Number of Diagonals', min=3, default=7)
    create_sap2000_button = ActionButton('Create SAP2000 Model', method='create_sap2000_model')


class Controller(ViktorController):
    label = 'Structure Controller'
    parametrization = Parametrization

    def create_frame(self, nodes: dict, lines: dict, sect_width: float = 100, sect_depth: float = 100) -> list:
        sections_group = []
        for line_id, dict_vals in lines.items():
            node_i = nodes[dict_vals["start"]]
            node_j = nodes[dict_vals["end"]]

            point_i = Point(node_i["x"],
                            node_i["y"],
                            node_i["z"])

            point_j = Point(node_j["x"],
                            node_j["y"],
                            node_j["z"])

            line_k = Line(point_i, point_j)
            section_k = RectangularExtrusion(sect_width, sect_depth, line_k, identifier=str(line_id))
            sections_group.append(section_k)

        return sections_group
    

    @GeometryView("3D model", duration_guess=1, x_axis_to_right=True)
    def create_render(self, params, **kwargs):
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
