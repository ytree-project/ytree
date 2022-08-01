"""
Plot the most massive halo in the dataset.
"""

import ytree

a = ytree.load("consistent_trees/tree_0_0_0.dat")

imax = a["mass"].argmax()
my_tree = a[imax]
print(f"Most massive halo is {my_tree} with M = {my_tree['mass']}.")

p = ytree.TreePlot(my_tree)
p.min_mass_ratio = 0.001
p.save("most_massive.png")
