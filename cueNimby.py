import sys
import random

from PySide2 import QtWidgets, QtGui

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    DEFAULT_ICON = "opencue-default.png"
    AVAILABLE_ICON = "opencue-available.png"
    DISABLED_ICON = "opencue-disabled.png"
    WORKING_ICON = "opencue-working.png"

    DEFAULT_STATUS = "unconfigured"
    AVAILABLE_STATUS = "available"
    DISABLED_STATUS = "disabled"
    WORKING_STATUS = "working"

    TOOLTIP = 'Cue Nimby - {status} - 0.1.0'
    def __init__(self, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, QtGui.QIcon(self.DEFAULT_ICON), parent)

        self._status = self.DEFAULT_STATUS
        self.status = self.DEFAULT_STATUS

        menu = QtWidgets.QMenu(parent)

        test_a = menu.addAction("Set Available")
        test_a.triggered.connect(self.set_available)
        test_a.setIcon(QtGui.QIcon(self.AVAILABLE_ICON))

        test_b = menu.addAction("Set Disabled")
        test_b.triggered.connect(self.set_disabled)
        test_b.setIcon(QtGui.QIcon(self.DISABLED_ICON))

        test_c = menu.addAction("Set Working")
        test_c.triggered.connect(self.set_working)
        test_c.setIcon(QtGui.QIcon(self.WORKING_ICON))

        menu.addSeparator()

        quit = menu.addAction("Quit")
        quit.triggered.connect(lambda: sys.exit())
        quit.setIcon(QtGui.QIcon("quit.png"))

        self.setContextMenu(menu)

        self.activated.connect(self.onTrayIconActivated)

    @property
    def status(self):
        return self._status
    @status.setter
    def status(self, status):
        self._status = status
        self.setToolTip(self.TOOLTIP.format(status=self._status.capitalize()))
    def onTrayIconActivated(self, reason):
        if reason == self.Trigger:
            self.randomize()
    def randomize(self):
        random.choice([self.set_working, self.set_available, self.set_disabled])()
        self.showMessage("status", self.status)
    def set_available(self):
        self.setIcon(QtGui.QIcon(self.AVAILABLE_ICON))
        self.status = self.AVAILABLE_STATUS
    def set_disabled(self):
        self.setIcon(QtGui.QIcon(self.DISABLED_ICON))
        self.status = self.DISABLED_STATUS
    def set_working(self):
        self.setIcon(QtGui.QIcon(self.WORKING_ICON))
        self.status = self.WORKING_STATUS


def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = QtWidgets.QWidget()
    tray_icon = SystemTrayIcon(widget)
    tray_icon.show()
    tray_icon.showMessage('Cue Nimby', 'hello')
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
