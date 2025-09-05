import numpy as np

def read_sqm_file_positions(inpath, molecule):
    with open(inpath, "r") as _file:
        record = False
        counter = 0
        for line in _file:
            if "Final Structure" in line:
                record = True
            if record and counter > 3:
                tokens = line.strip().split()
                if len(tokens) == 0:
                    break
                node_id, atom, x, y, z = tokens[2:]
                print(tokens)
                node_id = int(node_id)
                # make sure we read the right positions
                assert molecule.nodes[node_id-1]["element"] == atom
                molecule.nodes[node_id-1]["position"] == np.array([float(x)/10.,
                                                                   float(y)/10.,
                                                                   float(z)/10.])
            elif record:
                counter += 1
    return molecule
