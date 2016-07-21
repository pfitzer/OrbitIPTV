from __init__ import _
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config, ConfigSubsection, ConfigText, ConfigPassword, ConfigInteger, getConfigListEntry
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from Tools.BoundFunction import boundFunction
from twisted.web.client import downloadPage
from enigma import eDVBDB

config.plugins.OrbitIPTV = ConfigSubsection()
config.plugins.OrbitIPTV.username = ConfigText()
config.plugins.OrbitIPTV.password = ConfigPassword()


class OrbitScreen(Screen):
    CONFIG_DIR = '/etc/enigma2/'
    BOUQUET_NAME = 'Orbit-IPTV'
    DESCS = ['DE:', 'UK:', '18', 'US:', 'USA:']
    BOUQUET = 'userbouquet.ORBIT_IPTV__tv_.tv'
    URL = "http://orbit-iptv.com:2500/get.php?username=%s&password=%s&type=dreambox&output=mpegts"
    TEMP_FILE = '/tmp/bouquet.tv'
    BOUQUET_TV = '%sbouquets.tv' % CONFIG_DIR
    BOUQUET_TV_ENTRY = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet \n' % BOUQUET
    skin = """
        <screen position="center,80" size="800,100" title="Orbit IPTV" >
            <ePixmap pixmap="skin_default/buttons/green.png" position="230,5" size="220,40" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png" position="430,5" size="220,40" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="220,40" alphatest="on" />
            <widget source="key_green" render="Label" position="230,5" size="220,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_yellow" render="Label" position="430,5" size="220,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1"  shadowColor="black" shadowOffset="-2,-2" />
            <widget source="key_red" render="Label" position="10,5" size="220,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
        </screen>"""

    def __init__(self, session, args=None):
        self.session = session

        self.username = config.plugins.OrbitIPTV.username
        self.password = config.plugins.OrbitIPTV.password
        Screen.__init__(self, session)
        self["key_red"] = StaticText(_("Close"))
        self["key_green"] = StaticText(_("Update"))
        self["key_yellow"] = StaticText(_("Settings"))
        self["myActionMap"] = ActionMap(["SetupActions", "ColorActions"],
                                        {
                                            "ok": self.go,
                                            "green": self.go,
                                            "yellow": self.settings,
                                            "red": self.cancel,
                                            "cancel": self.cancel
                                        }, -1)

        self.download_url = self.URL % (self.username.getValue(), self.password.getValue())

    def go(self):
        downloadPage(self.download_url, self.TEMP_FILE).addCallback(self.convert).addErrback(self.downloadError)

    def cancel(self):
        print "\n[MyMenu] cancel\n"

        self.close(None)

    def settings(self):
        self.session.openWithCallback(self.set_settings, OrbitSettings)

    def set_settings(self, result):
        if result is None:
            return
        print "[OrbitIPTV] settings save"
        if result['username']:
            self.username.setValue(result['username'])
            self.username.save()
        if result['password']:
            self.password.setValue(result['password'])
            self.password.save()
        self.session.open(MessageBox, text=_("User Credentials saved"), type=MessageBox.TYPE_INFO)

    def convert(self, raw):
        print "[e2Fetcher.fetchPage]: download done", raw
        new = open(self.CONFIG_DIR  + self.BOUQUET, 'w')
        new.write('#NAME %s' % self.BOUQUET_NAME + '\n')
        try:
            with open(self.TEMP_FILE) as f:
                content = f.readlines()
                lines = iter(content)
                for line in lines:
                    for desc in self.DESCS:
                        if ("#DESCRIPTION %s" % desc) in line:
                            nl = lines.next()
                            if nl != '\n':
                                new.write(line)
                                new.write(nl)
        except Exception as e:
            self.session.open(MessageBox, text=e.message, type=MessageBox.TYPE_ERROR)
        finally:
            f.close()

        new.close()
        self.check_bouquettv()
        eDVBDB.getInstance().reloadBouquets()
        eDVBDB.getInstance().reloadServicelist()
        self.session.open(MessageBox, text=_("Bouquet updated"), type=MessageBox.TYPE_INFO)
        return

    def check_bouquettv(self):
        try:
            f = open(self.BOUQUET_TV, 'a+')
            f.read()
            if not self.BOUQUET_TV_ENTRY in f:
                f.write(self.BOUQUET_TV_ENTRY)
                print "[OrbitIPTV] entry added"
        finally:
            f.close()

    def downloadError(self, raw):
        print "[e2Fetcher.fetchPage]: download Error", raw

        self.session.open(MessageBox, text=_("Error downloading: ") + self.download_url, type=MessageBox.TYPE_ERROR)

    def check_credentials(self):
        if not self.username.value or not self.password.value:
            return False
        return True


class OrbitSettings(Screen, ConfigListScreen):
    TYPE_TEXT = 0
    TYPE_PASSWORD = 1
    TYPE_PIN = 2

    skin = """
		<screen position="center,center" size="700,120"  title="Input">
			<widget source="title" render="Label" position="5,0" zPosition="1" size="690,25" font="Regular;22" halign="left" valign="bottom" backgroundColor="background" transparent="1" />
			<widget name="config" position="15,30" size="690,80" scrollbarMode="showOnDemand" zPosition="1"/>
		</screen>"""

    default_config = [
        {
            "key": "username",
            "value": config.plugins.OrbitIPTV.username.getValue(),
            "title": _("User"),
            "required": True,
            "type": TYPE_TEXT,
            "alternative": None
        },
        {
            "key": "password",
            "value": config.plugins.OrbitIPTV.password.getValue(),
            "title": _("Password"),
            "required": True,
            "type": TYPE_PASSWORD,
            "alternatives": None
        },
    ]


    title = _("Set User Credentials")
    windowTitle = "Orbit IPTV - Settings"

    def __init__(self, session, title="", windowTitle=_("Input"), config=default_config):
        Screen.__init__(self, session)
        ConfigListScreen.__init__(self, [], session)

        self._config = config
        self._title = title

        self["title"] = StaticText(self._title)
        self["setupActions"] = ActionMap(["SetupActions"],
                                         {
                                             "save": self._ok,
                                             "cancel": self._cancel,
                                             "ok": self._ok,
                                         }, -2)

        self._configElements = []
        self._createConfigElements()

        self.onExecBegin.append(self.__onExcecBegin)
        self.onShow.append(self._createSetup)
        self.onShown.append(boundFunction(self.setTitle, windowTitle))
        self.onClose.append(self.__onClose)


    def __onExcecBegin(self):
        self.saveKeyboardMode()
        self.setKeyboardModeAscii()


    def __onClose(self):
        self.restoreKeyboardMode()


    def _createConfigElements(self):
        append = self._configElements.append
        for item in self._config:
            if item["type"] == self.TYPE_TEXT:
                append((ConfigText(default=item["value"], fixed_size=False), item))
            elif item["type"] == self.TYPE_PASSWORD:
                append((ConfigPassword(default=item["value"], fixed_size=False), item))
            elif item["type"] == self.TYPE_PIN:
                val = item["value"] or 0
                append((ConfigInteger(default=int(val)), item))


    def _createSetup(self):
        lst = []
        for config, item in self._configElements:
            lst.append(getConfigListEntry(item["title"], config))
        self["config"].setList(lst)


    def _ok(self):
        if self._checkInput():
            ret = {}
            for config, item in self._configElements:
                ret[item["key"]] = str(config.value)
            self.close(ret)
        else:
            self.close(None)


    def _checkInput(self):
        return True


    def _checkSingleInput(self, value, config):
        return value != None and value != ""


    def _cancel(self):
        self.close(None)


def main(session, **kwargs):
    print "\n[OrbitIPTV] start\n"

    session.open(OrbitScreen)


def Plugins(**kwargs):
    return PluginDescriptor(
        name="OrbitIPTV",
        description="IPTV bouquet management",
        where=PluginDescriptor.WHERE_PLUGINMENU,
        icon="../ihad_tut.png",
        fnc=main)
