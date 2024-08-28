
import win32com.client as win32
import pythoncom

class PySap2000():
    def __init__(self,
                 program_path:str = r"C:\Program Files\Computers and Structures\SAP2000 25\SAP2000.exe"
        ):
        self.program_path = program_path

    def create_helper(self):

        self.helper =  win32.gencache.EnsureDispatch('SAP2000v1.Helper')

    def create_object(self):
        self.SapObject = self.helper.CreateObject(self.program_path)  

    def start_application(self):
        self.SapObject.ApplicationStart()
        SapModel = self.SapObject.SapModel
        return SapModel
    
    def init_new_model(slef,Obj):
        Obj.InitializeNewModel()
        Obj.File.NewBlank()
        return Obj
    
    def create(self):
        pythoncom.CoInitialize() 
        try:
            self.create_helper()
            self.create_object()
            SapModel = self.start_application()
            SapModel = self.init_new_model(SapModel)
            return SapModel
        finally:
            pythoncom.CoUninitialize() 

def create_frame(sap_object:any, Nodes:dict, Elements:dict, material = 'R1'):
    for line_id, dict_vals in Elements.items():
        node_i = Nodes[dict_vals["start"]]
        node_j = Nodes[dict_vals["end"]]

        sap_object.FrameObj.AddByCoord(node_i["x"],
                                       node_i["y"],
                                       node_i["z"],
                                       node_j["x"],
                                       node_j["y"],
                                       node_j["z"],
                                       str(line_id),
                                       material,
                                        '1',
                                        'Global'
                                        )
        
if __name__ == "__main__":
    obj = PySap2000().create()