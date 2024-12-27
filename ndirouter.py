#
# Library for NDI Router instances
#
import NDIlib as Ndi

class NDIRoutingInstance(dict):
    """ Manipulate a single routing instance"""
    def __init__(self, name: str):
        create_desc = Ndi.RoutingCreate()
        create_desc.ndi_name = name
        dict.__init__(self, name=name, active=False, ndi=Ndi.routing_create(create_desc))

    def set_routing(self, ndi_source: Ndi.Source | None):
        if ndi_source is None:
            Ndi.routing_clear(self["ndi"])
        else:
            Ndi.routing_change(self["ndi"], ndi_source)

class NDIRouterList:
    """ Manipulate the list of NDI Router instances"""
    def __init__(self, count):
        self.router_list = []
        for x in range(count):
            self.router_list.insert(x, NDIRoutingInstance("CAM" + str(x+1)))
            self.router_list[x].set_routing(None)

    def set_routing(self, index, ndi_source: Ndi.Source | None):
        self.router_list[index].set_routing(ndi_source)
