import ytree

def calc_significance(node):
   if node.descendent is None:
       dt = 0. * node["time"]
   else:
       dt = node.descendent["time"] - node["time"]

   sig = node["mass"] * dt
   if node.ancestors is not None:
       for anc in node.ancestors:
           sig += calc_significance(anc)

   node["significance"] = sig
   return sig


a = ytree.load("tiny_ctrees/locations.dat")
a.add_analysis_field("significance", "Msun*Myr")

ap = ytree.AnalysisPipeline()
ap.add_operation(calc_significance)

trees = list(a[:])
for tree in trees:
    ap.process_target(tree)

fn = a.save_arbor(filename="halo_significance", trees=trees)
a2 = ytree.load(fn)
a2.set_selector("max_field_value", "significance")
prog = list(a2[0]["prog"])
print (prog)
