import numpy as np
import yt

class Simplehalo(object):
    def __init__(self, halo_type, halo_id, halo_info=None):
        self.halo_type = halo_type
        self.halo_id = halo_id
        if halo_info is None:
            halo_info = {}
        for key, value in halo_info.items():
            setattr(self, key, value)
        self.descendent = None
        self.ancestors = []

class SimpleTree(object):
    def __init__(self, time_series):
        self.ts = time_series

        def find_ancestors(self, halo, ds2):
            
        
    def trace_lineage(self, halo_type, halo_id):
        ds2 = None
        current_halo = None
        for i in range(len(self.ts.outputs)-1, 1, -1):
            if ds2 is None:
                ds1 = yt.load(self.ts.outputs[i])
            else:
                ds1 = ds2                
            ds2 = yt.load(self.ts.outputs[i-1])

            if current_halo is None:
                current_halo = SimpleHalo(halo_type, halo_id,
                    halo_info={"redshift": ds1.current_redshift,
                               "ds": ds1.parameter_filename})
                hc = ds1.halo(halo_type, halo_id)
                self.find_ancestors(hc, ds2)
