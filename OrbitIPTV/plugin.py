from __init__ import _
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config, ConfigSubsection, ConfigText, ConfigYesNo, ConfigPassword
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from twisted.web.client import downloadPage
from settings import OrbitSettings
from enigma import eDVBDB

config.plugins.OrbitIPTV = ConfigSubsection()
config.plugins.OrbitIPTV.username = ConfigText()
config.plugins.OrbitIPTV.password = ConfigPassword()
config.plugins.OrbitIPTV.DE = ConfigYesNo(default=True)
config.plugins.OrbitIPTV.NL = ConfigYesNo(default=True)
config.plugins.OrbitIPTV.US = ConfigYesNo(default=True)
config.plugins.OrbitIPTV.UK = ConfigYesNo(default=True)
config.plugins.OrbitIPTV.NL = ConfigYesNo(default=True)
config.plugins.OrbitIPTV.XX = ConfigYesNo(default=True)
config.plugins.OrbitIPTV.IT = ConfigYesNo(default=True)


class OrbitScreen(Screen):
    CONFIG_DIR = '/etc/enigma2/'
    BOUQUET_NAME = 'Orbit-IPTV'
    DESCS = ['DE:', 'UK:', '18', 'US:', 'USA:']
    BOUQUET = 'userbouquet.ORBIT_IPTV__tv_.tv'
    URL = "http://orbit-iptv.com:2500/get.php?username=%s&password=%s&type=dreambox&output=mpegts"
    TEMP_FILE = '/tmp/bouquet.tv'
    BOUQUET_TV = '%sbouquets.tv' % CONFIG_DIR
    BOUQUET_TV_ENTRY = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet' % BOUQUET
    skin = """
        <screen position="center,80" size="700,100" title="Orbit IPTV" >
            <ePixmap pixmap="skin_default/buttons/green.png" position="10,5" size="140,40" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png" position="150,5" size="140,40" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/red.png" position="290,5" size="140,40" alphatest="on" />
            <widget source="key_green" render="Label" position="10,5" size="140,40" zPosition="1" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="150,5" size="140,40" zPosition="1" font="Regular;18" halign="center" valign="center" backgroundColor="#a08500" transparent="1"  />
            <widget source="key_red" render="Label" position="290,5" size="140,40" zPosition="1" font="Regular;18" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
        </screen>"""

    def __init__(self, session, args=None):
        self.session = session
        Screen.__init__(self, session)
        self["key_red"] = StaticText(_("Close"))
        self["key_green"] = StaticText(_("Update"))
        self["key_yellow"] = StaticText(_("Settings"))
        self["key_blue"] = StaticText(_("Countries"))
        self["actions"] = ActionMap(["ColorActions"],
                                    {
                                        "ok": self.go,
                                        "green": self.go,
                                        "yellow": self.settings,
                                        "red": self.cancel,
                                        "cancel": self.cancel
                                    }, -1)

        self.download_url = self.URL % (config.plugins.OrbitIPTV.username.getValue(), config.plugins.OrbitIPTV.password.getValue())

    def go(self):
        downloadPage(self.download_url, self.TEMP_FILE).addCallback(self.convert).addErrback(self.downloadError)

    def cancel(self):
        self.close(None)

    def settings(self):
        self.session.openWithCallback(self.set_settings, UserSettings)

    def set_settings(self, result):
        if result is None:
            return
        print "[OrbitIPTV] settings save"
        set = config.plugins.OrbitIPTV.dict()
        for k, v in result.items():
            print "[OrbitIPTV] " + k + ": " + str(v)
            set[k].value = v
            set[k].save()
        config.plugins.OrbitIPTV.save()
        config.plugins.OrbitIPTV.load()
        self.session.open(MessageBox, text=_("User Credentials saved"), type=MessageBox.TYPE_INFO)

    def convert(self, raw):
        print "[e2Fetcher.fetchPage]: download done", raw
        new = open(self.CONFIG_DIR + self.BOUQUET, 'w')
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
            exists = False
            f = open(self.BOUQUET_TV, 'a+')
            for l in f.readlines():
                if self.BOUQUET_TV_ENTRY in l:
                    exists = True
            if not exists:
                f.write(self.BOUQUET_TV_ENTRY + '\n')
                print "[OrbitIPTV] entry added"
        finally:
            f.close()

    def downloadError(self, raw):
        print "[e2Fetcher.fetchPage]: download Error", raw

        self.session.open(MessageBox, text=_("Error downloading: ") + self.download_url, type=MessageBox.TYPE_ERROR)

    def check_credentials(self):
        if not self.username.getValue() or not self.password.getValue():
            return False
        return True


class UserSettings(OrbitSettings):

    default_config = [
        {
            "key": "username",
            "value": config.plugins.OrbitIPTV.username.getValue(),
            "title": _("User"),
            "required": True,
            "type": OrbitSettings.TYPE_TEXT,
            "alternative": None
        },
        {
            "key": "password",
            "value": config.plugins.OrbitIPTV.password.getValue(),
            "title": _("Password"),
            "required": True,
            "type": OrbitSettings.TYPE_PASSWORD,
            "alternatives": None
        },
        {
            "key": "DE",
            "value": config.plugins.OrbitIPTV.DE.getValue(),
            "title": _("Germany"),
            "required": True,
            "type": OrbitSettings.TYPE_YES_NO,
            "alternative": None
        },
        {
            "key": "UK",
            "value": config.plugins.OrbitIPTV.UK.getValue(),
            "title": _("United Kingdom"),
            "required": True,
            "type": OrbitSettings.TYPE_YES_NO,
            "alternatives": None
        },
        {
            "key": "NL",
            "value": config.plugins.OrbitIPTV.NL.getValue(),
            "title": _("Netherland"),
            "required": True,
            "type": OrbitSettings.TYPE_YES_NO,
            "alternatives": None
        },
        {
            "key": "US",
            "value": config.plugins.OrbitIPTV.US.getValue(),
            "title": _("United States"),
            "required": True,
            "type": OrbitSettings.TYPE_YES_NO,
            "alternatives": None
        },
        {
            "key": "IT",
            "value": config.plugins.OrbitIPTV.IT.getValue(),
            "title": _("Italy"),
            "required": True,
            "type": OrbitSettings.TYPE_YES_NO,
            "alternatives": None
        },
    ]

    title = _("Set User Credentials")
    windowTitle = "Orbit IPTV - Settings"

    def __init__(self, session, title="", windowTitle=_("Input"), config=default_config):
        super(UserSettings, self).__init__(session, title, windowTitle, config)


def main(session, **kwargs):
    print "\n[OrbitIPTV] start\n"

    session.open(OrbitScreen)


def Plugins(**kwargs):
    return PluginDescriptor(
        name="OrbitIPTV",
        description="IPTV bouquet management",
        where=PluginDescriptor.WHERE_PLUGINMENU,
        icon="./img/logo.png",
        fnc=main)
