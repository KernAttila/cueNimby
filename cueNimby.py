import sys
import os
from dataclasses import dataclass
import asyncio
from PySide2 import QtWidgets, QtGui

import opencue.api


@dataclass
class NimbyState:
    DEFAULT_STATE: str = "undefined"
    AVAILABLE_STATE: str = "available"
    DISABLED_STATE: str = "disabled"
    WORKING_STATE: str = "working"


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    UNDEFINED_ICON = "opencue-undefined.png"
    AVAILABLE_ICON = "opencue-available.png"
    DISABLED_ICON = "opencue-disabled.png"
    WORKING_ICON = "opencue-working.png"

    TOOLTIP = 'Cue Nimby 0.1.0 - {workstation}: {state}'

    def __init__(self, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, QtGui.QIcon(self.UNDEFINED_ICON), parent)

        self.workstation = os.getenv("HOSTNAME")
        self._host = None
        self._state = NimbyState.DEFAULT_STATE
        self.state = NimbyState.DEFAULT_STATE

        menu = QtWidgets.QMenu(parent)

        activate = menu.addAction("Set Available")
        activate.triggered.connect(self.set_available)
        activate.setIcon(QtGui.QIcon(self.AVAILABLE_ICON))

        disable = menu.addAction("Set Disabled")
        disable.triggered.connect(self.set_disabled)
        disable.setIcon(QtGui.QIcon(self.DISABLED_ICON))

        menu.addSeparator()

        close = menu.addAction("Quit Tray (rqd will still be running)")
        close.triggered.connect(lambda: sys.exit())
        close.setIcon(QtGui.QIcon("quit.png"))

        self.setContextMenu(menu)
        if self.host.isLocked():
            self.set_disabled()
        else:
            self.set_available()

        self.activated.connect(self.onTrayIconActivated)

        asyncio.run(self.listen_rqd())

    @property
    def host(self):
        self._host = opencue.api.findHost(self.workstation)
        return self._host

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

        if state == NimbyState.AVAILABLE_STATE:
            self.set_available()
        elif state == NimbyState.WORKING_STATE:
            self.set_working()
        elif state == NimbyState.DISABLED_STATE:
            self.set_disabled()
        else:
            print(f"State undefined: {state}")
            self._state = NimbyState.DEFAULT_STATE
            self.set_undefined()

        self.setToolTip(self.TOOLTIP.format(
            state=self._state.capitalize(),
            workstation=self.workstation))

    async def receive_machine_state(self, reader, writer):
        data = await reader.read(100)
        rqd_state = data.decode()
        print(f"Received state: {rqd_state=}")
        self.state = rqd_state
        confirmation = f"State received: {rqd_state=}"
        writer.write(confirmation.encode())
        await writer.drain()
        writer.close()

    async def listen_rqd(self):
        server = await asyncio.start_server(
            client_connected_cb=self.receive_machine_state,
            host='127.0.0.1',
            port=1546,
        )

        addr = server.sockets[0].getsockname()
        print(f'Listening to RQD on {addr}')

        async with server:
            await server.serve_forever()

    def onTrayIconActivated(self, reason):
        if reason == self.Trigger:
            ...
        if reason == self.DoubleClick:
            ...

    def set_available(self):
        self.host.unlock()
        self.setIcon(QtGui.QIcon(self.AVAILABLE_ICON))
        self.state = NimbyState.AVAILABLE_STATE

    def set_disabled(self):
        self.host.lock()
        self.setIcon(QtGui.QIcon(self.DISABLED_ICON))
        self.state = NimbyState.DISABLED_STATE

    def set_working(self):
        self.setIcon(QtGui.QIcon(self.WORKING_ICON))
        self.state = NimbyState.WORKING_STATE

    def set_undefined(self):
        self.setIcon(QtGui.QIcon(self.UNDEFINED_ICON))
        self.state = NimbyState.WORKING_STATE


def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = QtWidgets.QWidget()
    tray_icon = SystemTrayIcon(widget)
    tray_icon.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
