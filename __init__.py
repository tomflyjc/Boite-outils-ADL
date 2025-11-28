# -*- coding: utf-8 -*-
# Python 3

def classFactory(iface):

    from .Boite_a_outils_ADL import MainPlugin_BAO_ADL

    return MainPlugin_BAO_ADL(iface)
    
    


