# -*- coding: UTF-8 -*-
from subprocess import Popen, PIPE
from iniparse import ConfigParser
from dogtail.tree import root, SearchError

from common_steps import App
from common_steps import wait_until
from common_steps.app import *
from common_steps.appmenu import *
from common_steps.dialogs import *
from dogtail.utils import run
from dogtail.tree import root, SearchError
from dogtail.rawinput import keyCombo,typeText

class LOApp(App):
    """
    This class does all basic events with LO app (inherites from App class)
    """
    def __init__(self, appName, shortcut='<Control><Q>', desktopFileName=None,
                 timeout=5, a11yAppName=None, forceKill=True, parameters='',
                 recordVideo=False, processName=None):
        """
        ...
        """
        super(LOApp, self).__init__(appName, shortcut, desktopFileName, timeout,
            a11yAppName, forceKill, parameters, recordVideo)

        if processName is None:
            self.processName = self.appCommand
        else:
            self.processName = processName


    def startViaCommand(self):
        """
        Start the app via command
        """
        if self.forceKill and self.isRunning():
            self.kill()
            assert not self.isRunning(), "Application cannot be stopped"

        command = "%s %s" % (self.appCommand, self.parameters)
        self.pid = run(command, timeout=10)

        assert self.isRunning(), "Application failed to start"
        return root.application(self.a11yAppName)

    def startViaMenu(self, throughCategories=False):  # pylint: disable=W0613
        """
        Start the app via Gnome Shell menu
        """
        desktopConfig = self.parseDesktopFile()

        if self.forceKill and self.isRunning():
            self.kill()
            assert wait_until(lambda x: not x.isRunning(), self, timeout=30),\
                "Application cannot be stopped"

        # panel button Activities
        gnomeShell = root.application('gnome-shell')
        os.system("dbus-send --session --type=method_call " +
                  "--dest='org.gnome.Shell' " +
                  "'/org/gnome/Shell' " +
                  "org.gnome.Shell.FocusSearch")
        textEntry = gnomeShell.textentry('')
        assert wait_until(lambda x: x.showing, textEntry), \
            "Can't find gnome shell search textbar"

        typeText(self.desktopFileName)
        keyCombo('<Enter>')

        assert wait_until(lambda x: x.isRunning(), self, timeout=30),\
            "Application failed to start"


    def parseDesktopFile(self):
        """
        Getting all necessary data from *.dektop file of the app
        """
        cmd = 'ls -d /usr/share/applications/* | grep ".*%s.desktop"' % self.desktopFileName
        proc = Popen(cmd, shell=True, stdout=PIPE)
        # !HAVE TO check if the command and its desktop file exist
        if proc.wait() != 0:
            raise Exception("*.desktop file of the app not found")
        output = proc.communicate()[0].rstrip()
        desktopConfig = ConfigParser()
        desktopConfig.read(output)
        return desktopConfig

    def getName(self):
        desktopConfig = self.parseDesktopFile()
        return desktopConfig.get('Desktop Entry', 'name')

    def kill(self):
        """
        Kill the app via 'killall'
        """
        if self.recordVideo:
            keyCombo('<Control><Alt><Shift>R')

        try:
            # Kill by pid
            kill(self.pid, SIGTERM)
            assert wait_until(lambda x: not x.isRunning(),
                              self, timeout=10)
        except:
            # send SIGKILL if sigterm didn't work
            Popen("killall -9 " + self.processName + " > /dev/null",
                  shell=True).wait()
        self.pid = None


    def get_current_window(self, dialog=False):
        """
        Returns current window (actually last opened one)
        """
        if dialog:
            role = 'dialog'
        else:
            role = 'frame'

        soffice = root.application('soffice')
        # all_frames = [x for x in soffice.findChildren(lambda x: x.roleName == role, recursive=False)]
        all_frames = [x for x in soffice.findChildren(lambda x: True, recursive=False)]
        return all_frames[-1]
