def mpi_gather_list(comm, my_list):
    my_list = comm.gather(my_list, root=0)
    rlist = []
    if comm.rank == 0:
        for my_item in my_list:
            rlist.extend(my_item)
    return rlist
