# coding=utf-8
from AccessControl import ModuleSecurityInfo
from AccessControl import allow_class

moduleSecurity = ModuleSecurityInfo('Products.GSSiteMenu.sitemenu')
moduleSecurity.declarePublic('SiteMenuItem')
moduleSecurity.declarePublic('SiteMenu')
from sitemenu import FolderMenuItem, SimpleMenuItem, SimpleBrowserMenuItem, SiteMenu
allow_class(FolderMenuItem)
allow_class(SimpleMenuItem)
allow_class(SimpleBrowserMenuItem)
allow_class(SiteMenu)

