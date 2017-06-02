# This library is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library. If not, see <http://www.gnu.org/licenses/>.

import os
import logging

from studioqt import QtGui

import studioqt
import studiolibrary
import studiolibrarymaya

try:
    import mutils
    import mutils.gui
    import maya.cmds
except ImportError, e:
    print e


__all__ = [
    "BaseItem",
]

logger = logging.getLogger(__name__)


class NamespaceOption:
    FromFile = "file"
    FromCustom = "custom"
    FromSelection = "selection"


class BaseItem(studiolibrary.LibraryItem):

    """Base class for anim, pose, mirror and sets transfer items."""

    def __init__(self, *args, **kwargs):
        """
        Initialise a new instance for the given path.

        :type path: str
        :type args: list
        :type kwargs: dict
        """
        studiolibrary.LibraryItem.__init__(self, *args, **kwargs)

        self._namespaces = []
        self._namespaceOption = NamespaceOption.FromSelection

        self._transferClass = None
        self._transferObject = None
        self._transferBasename = None

    def setTransferClass(self, classname):
        """
        Set the transfer class used to read and write the data.

        :type classname: mutils.TransferObject
        """
        self._transferClass = classname

    def transferClass(self):
        """
        Return the transfer class used to read and write the data.

        :rtype: mutils.TransferObject
        """
        return self._transferClass

    def transferPath(self):
        """
        Return the disc location to transfer path.

        :rtype: str
        """
        if self.transferBasename():
            return "/".join([self.path(), self.transferBasename()])
        else:
            return self.path()

    def transferBasename(self):
        """
        Return the filename of the transfer path.

        :rtype: str
        """
        return self._transferBasename

    def setTransferBasename(self, transferBasename):
        """
        Set the filename of the transfer path.

        :type: str
        """
        self._transferBasename = transferBasename

    def transferObject(self):
        """
        Return the transfer object used to read and write the data.

        :rtype: mutils.TransferObject
        """
        if not self._transferObject:
            path = self.transferPath()
            if os.path.exists(path):
                self._transferObject = self.transferClass().fromPath(path)
        return self._transferObject

    def thumbnailPath(self):
        """
        Return the thumbnail location on disc to be displayed for the item.

        :rtype: str
        """
        return self.path() + "/thumbnail.jpg"

    def settings(self):
        """
        Return a settings object for saving data to the users local disc.

        :rtype: studiolibrary.Settings
        """
        return studiolibrarymaya.settings()

    def owner(self):
        """
        Return the user who created this item.

        :rtype: str
        """
        owner = studiolibrary.LibraryItem.owner(self)
        transferObject = self.transferObject()

        if not owner and transferObject:
            owner = self.transferObject().metadata().get("user")

        return owner

    def ctime(self):
        """
        Return when the item was created.

        :rtype: str
        """
        path = self.path()
        ctime = ""

        if os.path.exists(path):
            ctime = studiolibrary.LibraryItem.ctime(self)

            if not ctime:
                ctime = int(os.path.getctime(path))

        return ctime

    def description(self):
        """
        Return the user description for this item.

        :rtype: str
        """
        description = studiolibrary.LibraryItem.description(self)
        transferObject = self.transferObject()

        if not description and transferObject:
            description = self.transferObject().metadata().get("description")

        return description

    def objectCount(self):
        """
        Return the number of controls this item contains.

        :rtype: int
        """
        if self.transferObject():
            return self.transferObject().count()
        else:
            return 0

    def contextMenu(self, menu, items=None):
        """
        This method is called when the user right clicks on this item.

        :type menu: QtWidgets.QMenu
        :type items: list[BaseItem]
        :rtype: None
        """
        import setsmenu

        action = setsmenu.selectContentAction(self, parent=menu)
        menu.addAction(action)
        menu.addSeparator()

        subMenu = self.createSelectionSetsMenu(menu, enableSelectContent=False)
        menu.addMenu(subMenu)
        menu.addSeparator()

    def showSelectionSetsMenu(self, **kwargs):
        """
        Show the selection sets menu for this item at the cursor position.

        :rtype: QtWidgets.QAction
        """
        menu = self.createSelectionSetsMenu(**kwargs)
        position = QtGui.QCursor().pos()
        action = menu.exec_(position)
        return action

    def createSelectionSetsMenu(self, parent=None, enableSelectContent=True):
        """
        Return a new instance of the selection sets menu.

        :type parent: QtWidgets.QWidget
        :type enableSelectContent: bool
        :rtype: QtWidgets.QMenu
        """
        import setsmenu

        namespaces = self.namespaces()

        menu = setsmenu.SetsMenu(
                item=self,
                parent=parent,
                namespaces=namespaces,
                enableSelectContent=enableSelectContent,
        )
        return menu

    def selectContent(self, namespaces=None, **kwargs):
        """
        Select the contents of this item in the Maya scene.

        :type namespaces: list[str]
        """
        namespaces = namespaces or self.namespaces()
        kwargs = kwargs or mutils.selectionModifiers()

        msg = "Select content: Item.selectContent(namespacea={0}, kwargs={1})"
        msg = msg.format(namespaces, kwargs)
        logger.debug(msg)

        try:
            self.transferObject().select(namespaces=namespaces, **kwargs)
        except Exception, msg:
            title = "Error while selecting content"
            studioqt.MessageBox.critical(None, title, str(msg))
            raise

    def mirrorTable(self):
        """
        Return the mirror table object for this item.

        :rtype: mutils.MirrorTable or None
        """
        mirrorTable = None
        path = self.mirrorTablePath()

        if path:
            mirrorTable = mutils.MirrorTable.fromPath(path)

        return mirrorTable

    def mirrorTablePath(self):
        """
        Return the mirror table path for this item.

        :rtype: str or None
        """
        path = None
        paths = self.mirrorTablePaths()

        if paths:
            path = paths[0]

        return path

    def mirrorTablePaths(self):
        """
        Return all mirror table paths for this item.

        :rtype: list[str]
        """
        paths = list(studiolibrary.findPaths(
                self.path(),
                match=lambda path: path.endswith(".mirror"),
                direction=studiolibrary.Direction.Up,
                depth=10,
            )
        )
        return paths

    def namespaces(self):
        """
        Return the namesapces for this item depending on the namespace option.

        :rtype: list[str]
        """
        namespaces = []
        namespaceOption = self.namespaceOption()

        # When creating a new item we can only get the namespaces from
        # selection because the file (transferObject) doesn't exist yet.
        if not self.transferObject():
            namespaces = self.namespaceFromSelection()

        # If the file (transferObject) exists then we can use the namespace
        # option to determined which namespaces to return.
        elif namespaceOption == NamespaceOption.FromFile:
            namespaces = self.namespaceFromFile()

        elif namespaceOption == NamespaceOption.FromCustom:
            namespaces = self.namespaceFromCustom()

        elif namespaceOption == NamespaceOption.FromSelection:
            namespaces = self.namespaceFromSelection()

        return namespaces

    def setNamespaceOption(self, namespaceOption):
        """
        Set the namespace option for this item.

        :type namespaceOption: NamespaceOption
        :rtype: None
        """
        self.settings().set("namespaceOption", namespaceOption)

    def namespaceOption(self):
        """
        Return the namespace option for this item.

        :rtype: NamespaceOption
        """
        namespaceOption = self.settings().get(
                "namespaceOption",
                NamespaceOption.FromSelection
        )
        return namespaceOption

    def namespaceFromCustom(self):
        """
        Return the namespace the user has set.

        :rtype: list[str]
        """
        return self.settings().get("namespaces", [])

    def setCustomNamespaces(self, namespaces):
        """
        Set the users custom namespace.

        :type namespaces: list[str]
        :rtype: None
        """
        self.settings().set("namespaces", namespaces)

    def namespaceFromFile(self):
        """
        Return the namespaces from the transfer data.

        :rtype: list[str]
        """
        return self.transferObject().namespaces()

    @staticmethod
    def namespaceFromSelection():
        """
        Return the current namespaces from the selected objects in Maya.

        :rtype: list[str]
        """
        return mutils.namespace.getFromSelection() or [""]

    def doubleClicked(self):
        """
        This method is called when the user double clicks the item.

        :rtype: None
        """
        self.load()

    def load(self, objects=None, namespaces=None, **kwargs):
        """
        Load the data from the transfer object.

        :type namespaces: list[str]
        :type objects: list[str]
        :rtype: None
        """
        logger.debug(u'Loading: {0}'.format(self.transferPath()))

        self.transferObject().load(objects=objects, namespaces=namespaces, **kwargs)

        logger.debug(u'Loading: {0}'.format(self.transferPath()))

    def save(self, objects, path=None, iconPath=None, contents=None, **kwargs):
        """
        Save the data to the transfer path on disc.

        :type path: path
        :type objects: list
        :type iconPath: str
        :raise ValidateError:
        """
        logger.info(u'Saving: {0}'.format(path))

        contents = contents or list()
        tempDir = mutils.TempDir("Transfer", clean=True)
        transferPath = tempDir.path() + "/" + self.transferBasename()

        t = self.transferClass().fromObjects(objects)
        t.save(transferPath, **kwargs)

        if iconPath:
            contents.append(iconPath)

        contents.append(transferPath)
        studiolibrary.LibraryItem.save(self, path=path, contents=contents)

        logger.info(u'Saved: {0}'.format(path))
