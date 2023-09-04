import sys
import os
import platform
import threading
import json
from dataclasses import dataclass
import asyncio
from PySide2 import QtWidgets, QtGui

import opencue.api
import opencue.exception


RQD_HOST = '127.0.0.1'
RQD_TRAY_PORT = 1546

@dataclass
class NimbyState:
    DEFAULT_STATE: str = "undefined"
    ERROR_STATE: str = "error"
    AVAILABLE_STATE: str = "available"
    DISABLED_STATE: str = "disabled"
    WORKING_STATE: str = "working"


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    _pwd = os.path.dirname(__file__)
    UNDEFINED_ICON = os.path.join(_pwd, "opencue-undefined.png")
    ERROR_ICON = os.path.join(_pwd, "opencue-error.png")
    AVAILABLE_ICON = os.path.join(_pwd, "opencue-available.png")
    DISABLED_ICON = os.path.join(_pwd, "opencue-disabled.png")
    WORKING_ICON = os.path.join(_pwd, "opencue-working.png")

    TOOLTIP = 'OpenCueTray-0.1.0 - {workstation}: {state}\n{extra}'

    def __init__(self, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, QtGui.QIcon(self.UNDEFINED_ICON), parent)

        self.workstation = os.getenv("HOSTNAME") or platform.node()
        self._host = None
        self._state = NimbyState.DEFAULT_STATE
        self.message = ""
        self.current_frames = {}

        menu = QtWidgets.QMenu(parent)

        activate = menu.addAction("Set Available")
        activate.triggered.connect(self.unlock_host)
        activate.setIcon(QtGui.QIcon(self.AVAILABLE_ICON))

        disable = menu.addAction("Set Disabled")
        disable.triggered.connect(self.lock_host)
        disable.setIcon(QtGui.QIcon(self.DISABLED_ICON))

        menu.addSeparator()

        close = menu.addAction("Quit Tray (rqd will still be running)")
        close.triggered.connect(self.close_tray)
        close.setIcon(QtGui.QIcon("quit.png"))

        self.setContextMenu(menu)
        host = self.host
        if host is None:
            print("Could not reach server")
            self.state = NimbyState.DISABLED_STATE
        elif host.isLocked():
            print("host locked")
            self.state = NimbyState.DISABLED_STATE
        elif host.coresReserved() > 0.0:
            print("host working")
            self.state = NimbyState.WORKING_STATE
        else:
            print("host free")
            self.state = NimbyState.AVAILABLE_STATE

        self.activated.connect(self.onTrayIconActivated)

        self.server_thread = threading.Thread(target=lambda: asyncio.run(self.listen_rqd()))
        self.server_thread.start()

    def close_tray(self):
        os.system('kill %d' % os.getpid())

    @property
    def host(self):
        try:
            self._host = opencue.api.findHost(self.workstation)
        except opencue.exception.ConnectionException as error:
            self.message = "Could not reach server"
            self.state = NimbyState.ERROR_STATE
        else:
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
        elif state == NimbyState.ERROR_STATE:
            self.set_failed()
        else:
            print(f"State undefined: {state}")
            self._state = NimbyState.DEFAULT_STATE
            self.set_undefined()

        message = self.TOOLTIP.format(
            state=self._state.capitalize(),
            workstation=self.workstation,
            extra=self.message)
        self.setToolTip(message)
        self.showMessage("OpenCue", message)

    async def receive_machine_state(self, reader, writer):
        data = await reader.read(300)
        rqd_state, message = json.loads(data.decode())
        print(f"Received state: {rqd_state=}, {message=}")
        self.message = message
        self.state = rqd_state
        confirmation = f"State received: {rqd_state=}"
        writer.write(confirmation.encode())
        await writer.drain()
        writer.close()

    async def listen_rqd(self):
        try:
            self.server = await asyncio.start_server(
                client_connected_cb=self.receive_machine_state,
                host=RQD_HOST,
                port=RQD_TRAY_PORT,
            )
        except OSError:
            print("CueTray already running")
            self.close_tray()

        addr = self.server.sockets[0].getsockname()
        print(f'Listening to RQD on {addr}')

        async with self.server:
            await self.server.serve_forever()

    def onTrayIconActivated(self, reason):
        if reason == self.Trigger:
            ...
        if reason == self.DoubleClick:
            ...

    def unlock_host(self):
        self.host.unlock()

    def lock_host(self):
        self.host.lock()

    def set_available(self):
        self.setIcon(QtGui.QIcon(self.AVAILABLE_ICON))

    def set_disabled(self):
        self.setIcon(QtGui.QIcon(self.DISABLED_ICON))

    def set_working(self):
        self.setIcon(QtGui.QIcon(self.WORKING_ICON))

    def set_failed(self):
        self.setIcon(QtGui.QIcon(self.ERROR_ICON))

    def set_undefined(self):
        self.setIcon(QtGui.QIcon(self.UNDEFINED_ICON))


def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = QtWidgets.QWidget()
    tray_icon = SystemTrayIcon(widget)
    tray_icon.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
