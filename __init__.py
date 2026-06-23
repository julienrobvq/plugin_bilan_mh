
def classFactory(iface):
    from .bilan_mh_plugin import BilanMHPlugin
    return BilanMHPlugin(iface)