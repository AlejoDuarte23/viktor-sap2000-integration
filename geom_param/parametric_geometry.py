from typing import Tuple, List

class TowerColumn():
    def __init__(self, height:float, width:float, n_diagonals:int):
        self.heigh = height
        self.widht = width
        self.n_diagonals = n_diagonals
        self.nodes = dict()
        self.lines = dict()
        self.current_nodes_id = 0
        self.current_lines_id = 0
    
    def create_stringer(self, x_cord:float, y_cord:float, z_cord:float = 0) -> List:
        base_point = z_cord
        top_point = self.heigh 
        nNodes = self.n_diagonals +1
        delta =top_point /(nNodes-1)
        stringer_ids = list()

        for div in range(nNodes):
            self.nodes[self.current_nodes_id] = {"x":x_cord, "y":y_cord, "z": 0 + delta*div}
            stringer_ids.append(self.current_nodes_id)
            self.current_nodes_id += 1

        return stringer_ids

    def connect_stringers(self, stringer_1_ids:List, stringer_2_ids:List)-> None:
        if self.n_diagonals % 2 ==0:
            required_st1_ids = stringer_1_ids[:-1:2]  
            required_st2_ids = stringer_2_ids[1:-1:2]

            print(required_st1_ids)
            print(required_st2_ids)

            for i in range(self.n_diagonals):
                if i ==0:
                    self.lines[self.current_lines_id] = {"start":required_st1_ids[i], "end":required_st2_ids[i]}
                elif  i % 2 == 0:
                    self.lines[self.current_lines_id] = {"start":required_st1_ids[i-1], "end":required_st2_ids[i-1]}
                else:
                    self.lines[self.current_lines_id] = {"start":required_st1_ids[i-1], "end":required_st2_ids[i-2]}
                print("connect_stringers", i)
                print(self.lines[self.current_lines_id])
                self.current_lines_id += 1
        else:
            
            # Shortest way to get the right nodes
            required_st1_ids = stringer_1_ids[:-1:2]  
            required_st2_ids = stringer_2_ids[1::2]
            
            tags_st1 = sorted([required_st1_ids[0]] + required_st1_ids[1:] * 2)
            tags_st2 = sorted([required_st2_ids[-1]] + required_st2_ids[:-1] * 2)


            for tag_st1, tag_st2 in zip(tags_st1, tags_st2):    
                self.lines[self.current_lines_id] = {"start":tag_st1, "end": tag_st2}
                self.current_lines_id += 1

    def create_stringes_elements(self, stringer_ids:List[list]):
        for id_list in stringer_ids:
            for i in range(len(id_list)-1):
                self.lines[self.current_lines_id] = {"start":id_list[i], "end": id_list[i+1]}
                self.current_lines_id += 1
        
    def create_top_beams_elements(self, stringer_ids: List[list]):
        selected_tags = [id_list[-1] for id_list in stringer_ids]

        for i in range(len(selected_tags)):
            self.lines[self.current_lines_id] = {"start":selected_tags[i], "end": selected_tags[(i+1)%len(selected_tags)]}
            self.current_lines_id += 1
        
    def create_columns(self)->None:
        width = self.widht
        offsets = [(-width/2, -width/2), (width/2, -width/2), (width/2, width/2), (-width/2, width/2)]

        stringer_ids = [self.create_stringer(x_cord= x, y_cord = y) for x,y in offsets] 
		
        for i in range(len(stringer_ids)):
            if i % 2 == 0:
                self.connect_stringers(stringer_ids[i], stringer_ids[(i+1)%len(stringer_ids)])
            else:
                self.connect_stringers(stringer_ids[(i+1)%len(stringer_ids)],stringer_ids[i])

        self.create_stringes_elements(stringer_ids=stringer_ids)
        self.create_top_beams_elements(stringer_ids= stringer_ids)

if __name__ == "__main__":
    tower1 = TowerColumn(height=4000, width=800, n_diagonals=7)
    tower1.create_columns()