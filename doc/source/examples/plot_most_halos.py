"""
Plot the tree with the most halos.
"""

import ytree

a = ytree.load("consistent_trees/tree_0_0_0.dat")

tree_size = a.arr([t.tree_size for t in a])
imax = tree_size.argmax()
my_tree = a[imax]
print(f"Tree with most halos is {my_tree} with {my_tree.tree_size} halos.")

p = ytree.TreePlot(my_tree)
p.min_mass_ratio = 0.001
p.save("most_halos.png")
