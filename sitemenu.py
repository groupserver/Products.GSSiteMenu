# coding=utf-8
import time
from urllib2 import urlparse
from zope.component import createObject
from zope.interface import implements
from zope.app.publisher.interfaces.browser import IBrowserMenuItem, IBrowserMenu
from Products.XWFCore.cache import LRUCache

userSiteMenuItems = LRUCache(cache_name='User Site Site-Menu Cache')
userSiteMenuItems.set_max_objects(5120)
# The cache will be wrong if:
#  * Permissions on pages change
#  * Roles on members change,
#  * Pages are created, and
#  * Pages are deleted.
import logging
log = logging.getLogger('GSSiteMenu')

class SimpleMenuItem(object):
    implements(IBrowserMenuItem)
    def __init__(self, action, title):
        self.action = action
        self.icon = None
        self.order = None
        self.title = title
        self.description = None
        self.filter_string = None
        
    def available(self):
        retval = True
        assert type(retval) == bool
        return retval
        
class FolderMenuItem(SimpleMenuItem):
    implements(IBrowserMenuItem)
    def __init__(self, folder):
        SimpleMenuItem.__init__(self, 
          '/%s' % folder.getId(),
          folder.title_or_id().title())

class SimpleBrowserMenuItem(object):
    def __init__(self, menuItem, context, request):
        self.action = menuItem.action
        self.icon = None
        self.order = None
        self.title = menuItem.title
        self.description = None
        self.filter_string = None        
        self.context = context
        self.request = request
        self.id = '%s-menu-link' % self.title.replace(' ', '_')

    def selected(self):
        """See zope.app.publisher.interfaces.browser.IBrowserMenuItem"""
        # --=mpj17=-- Not perfect, but it will work for now.
        normalized_action = self.action
        if self.action.startswith('@@'):
            normalized_action = self.action[2:]
        normalized_action = normalized_action.strip('/')

        rurl = self.request.getURL()
        scheme, netloc, path, query, frag = urlparse.urlsplit(rurl)
        if path.endswith('@@index.html'):
            path = path[:-12]
        path = path.strip('/')
        
        retval = (((normalized_action == '') and (path == ''))
                  or \
                  ((normalized_action != '') and \
                    path.startswith(normalized_action)))
        assert type(retval) == bool
        return retval

class SiteMenu(object):
    implements(IBrowserMenu)
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.__userInfo = None
        
        self.id = '%s_sitenav' % self.siteInfo.id
        self.description = u'Site Navigation Menu for %s' % self.siteInfo.title
        self.title = u'Site Navigation Menu'
        
    @property
    def userInfo(self):
        if self.__userInfo == None:
            self.__userInfo = createObject('groupserver.LoggedInUser', 
              self.context)
        return self.__userInfo
        
    def getMenuItems(self):
        key = '%s.%s' % (self.siteInfo.id, self.userInfo.id)
        items = userSiteMenuItems.get(key)
        if items == None:
            items = self.real_get_menu_items()
            userSiteMenuItems.add(key, items)
        assert type(items) == list
        retval = [SimpleBrowserMenuItem(i, self.context, self.request)
                  for i in items]
        return retval
        
    def real_get_menu_items(self):
        a = time.time()
        retval = []
        site = self.siteInfo.siteObj
        folderTypes = ('Folder', 'Folder (ordered)')
        folderItems = [FolderMenuItem(f) 
                        for f in site.objectValues(folderTypes)
                        if (f.getProperty('section_id') 
                          and self.can_see_folder(f))]
        retval = [SimpleMenuItem('/','Home')] \
          + folderItems  + [SimpleMenuItem('/help','Help')]
        b = time.time()
        m = 'Generated site menu for %s (%s) on %s (%s) in %.2fms' %\
          (self.userInfo.name, self.userInfo.id, 
           self.siteInfo.name, self.siteInfo.id,
           (b-a)*1000.0)
        log.info(m)
        assert type(retval) == list
        assert len(retval) >= 2
        return retval

    def can_see_folder(self, folder):
        # --=mpj17=-- The logic is here, rather than in the "allow"
        #   method of the menu item, because we only want to cache
        #   simple things, and users are not simple.
        retval = bool(self.userInfo.user.allowed(folder))
        assert type(retval) == bool
        return retval

