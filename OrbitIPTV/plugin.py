from __init__ import _
from Screens.Screen import Screen
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from twisted.web.client import downloadPage


class OrbitScreen(Screen):
    DESCS = ['DE', 'UK', '18', 'US', 'USA']
    BOUQUET = '/etc/enigma2/userbouquet.ORBIT_IPTV__tv_.tv'
    USERNAME = "[YOUR USERNAME]";
    PASSWORD = "[YOUR PASSWORD]";
    URL = "http://orbit-iptv.com:2500/get.php?username=%s&password=%s&type=dreambox&output=mpegts" % (USERNAME, PASSWORD)
    TEMP_FILE = '/tmp/bouquet.tv'
    skin = """
        <screen position="130,150" size="460,150" title="Orbit IPTV" >
        <widget name="myMenu" position="10,10" size="400,300"
        scrollbarMode="showOnDemand" />
        </screen>"""

    def __init__(self, session, args=None):
        self.session = session
        list = []
        list.append((_("Entry 1"), "load"))
        list.append((_("Exit"), "exit"))
        Screen.__init__(self, session)
        self["myMenu"] = MenuList(list)
        self["myActionMap"] = ActionMap(["SetupActions"],
                                        {
                                            "ok": self.go,
                                            "cancel": self.cancel
                                        }, -1)

    def go(self):
        returnValue = self["myMenu"].l.getCurrentSelection()[1]

        print "\n[MyMenu] returnValue: " + returnValue + "\n"
        if returnValue is not None:
            if returnValue is "load":
                downloadPage(self.URL, self.TEMP_FILE).addCallback(self.convert).addErrback(self.downloadError)
            elif returnValue is "exit":
                self.cancel()

    def myMsg(self, entry):
        self.session.open(MessageBox, _("You selected entry no. %s!") % (entry), MessageBox.TYPE_INFO)

    def cancel(self):
        print "\n[MyMenu] cancel\n"

        self.close(None)

    def convert(self, raw):
        print "[e2Fetcher.fetchPage]: download done", raw
        new = open(self.BOUQUET, 'w')

        try:
            with open(self.TEMP_FILE) as f:
                content = f.readlines()
                lines = iter(content)
                for line in lines:
                    for desc in self.DESCS:
                        if "#DESCRIPTION %s:" % desc in line:
                            new.write(line)
                            new.write(lines.next())
            f.close()
            new.close()
            self.session.open(MessageBox, text=_("Bouquet updated"))
        except Exception as e:
            self.session.open(MessageBox, text=e.msg)

    def downloadError(self, raw):
        print "[e2Fetcher.fetchPage]: download Error", raw

        self.session.open(MessageBox, text=_("Error downloading: ") + self.TEMP_FILE, type=MessageBox.TYPE_ERROR)


def main(session, **kwargs):
    print "\n[Hallo World] start\n"

    session.open(OrbitScreen)


def Plugins(**kwargs):
    return PluginDescriptor(
        name="OrbitIPTV",
        description="IPTV bouquet management",
        where=PluginDescriptor.WHERE_PLUGINMENU,
        icon="../ihad_tut.png",
        fnc=main)
