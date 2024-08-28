from viktor import ViktorController
from viktor.parametrization import ViktorParametrization
from viktor.parametrization import NumberField, Text
from viktor.geometry import CircularExtrusion, Group, Material, Color, Point, LinearPattern, Line,RectangularExtrusion
from viktor.views import GeometryView, GeometryResult

import win32com.client as win32
from typing import Tuple, Dict
# import sys
# sys.path.append(r"C:\Users\aleja\Documents\sap2000_automation\app\app")


class Parametrization(ViktorParametrization):
    text_building = Text('## Frame Geometry')
    frame_height = NumberField('Frame Height', min=500, default=1000)
    frame_width = NumberField('Frame Width', min=500, default=1000)
    section_width = NumberField('Section Width', min=100, default=200)
    section_height = NumberField('Section Height', min=100, default=200)


class Controller(ViktorController):
    label = 'Frame Controller'
    parametrization = Parametrization

    def parametric_geometry(self, height: float, width: float) -> Tuple[Dict[int, dict], Dict[int, dict]]:
        nodes = {
            0: {"x": 0, "y": 0, "z": 0},
            1: {"x": 0, "y": 0, "z": height},
            2: {"x": width, "y": 0, "z": height},
            3: {"x": width, "y": 0, "z": 0},
        }

        lines = {
            1: {"start": 0, "end": 1},
            2: {"start": 1, "end": 2},
            3: {"start": 2, "end": 3},
        }

        return nodes, lines

    def create_frame(self, nodes: dict, lines: dict, sect_width: float, sect_depth: float) -> list:
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
        frame_height = params.frame_height
        frame_width = params.frame_width
        section_width = params.section_width
        section_height = params.section_height

        frame_nodes, frame_lines = self.parametric_geometry(frame_height, frame_width)

        sections_group = self.create_frame(
            nodes=frame_nodes,
            lines=frame_lines,
            sect_depth=section_height,
            sect_width=section_width
        )

        return GeometryResult(geometry=sections_group)