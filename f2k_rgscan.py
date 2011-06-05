# -*- coding: utf-8 -*-

PLUGIN_NAME = u'Foobar2000 ReplayGain'
PLUGIN_AUTHOR = u'Johannes Weißl'
PLUGIN_DESCRIPTION = '''Analyse your albums using the foobar2000 ReplayGain scanner.'''
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.10", "0.15"]

import os
import sys
import subprocess
from subprocess import Popen, PIPE

from PyQt4 import QtCore, QtGui

from picard.album import Album
from picard.track import Track
from picard.file import File
from picard.ui.options import register_options_page, OptionsPage
from picard.ui.itemviews import (BaseAction, register_file_action, register_album_action)
from picard.config import TextOption

winepath = ['winepath']
wine = ['wine']

def get_foobar2000_path():
    if os.name == 'posix':
        p = os.path.expanduser('~/.wine/drive_c/Program Files/foobar2000/foobar2000.exe')
    else:
        p = 'C:/Program Files/foobar2000/foobar2000.exe'
    return p if os.path.exists(p) else ''

class Ui_Foobar2000ReplayGainOptionsPage(object):
    def setupUi(self, Foobar2000ReplayGainOptionsPage):
        Foobar2000ReplayGainOptionsPage.setObjectName("Foobar2000ReplayGainOptionsPage")
        Foobar2000ReplayGainOptionsPage.resize(394, 300)
        self.verticalLayout = QtGui.QVBoxLayout(Foobar2000ReplayGainOptionsPage)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtGui.QGroupBox(Foobar2000ReplayGainOptionsPage)
        self.groupBox.setObjectName("groupBox")
        self.vboxlayout = QtGui.QVBoxLayout(self.groupBox)
        self.vboxlayout.setObjectName("vboxlayout")
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.vboxlayout.addWidget(self.label)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.foobar2000_path = QtGui.QLineEdit(self.groupBox)
        self.foobar2000_path.setObjectName("foobar2000_path")
        self.horizontalLayout.addWidget(self.foobar2000_path)
        self.foobar2000_browse = QtGui.QPushButton(self.groupBox)
        self.foobar2000_browse.setObjectName("foobar2000_browse")
        self.horizontalLayout.addWidget(self.foobar2000_browse)
        self.vboxlayout.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.groupBox)
        spacerItem = QtGui.QSpacerItem(368, 187, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(Foobar2000ReplayGainOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(Foobar2000ReplayGainOptionsPage)

        self.foobar2000_browse.clicked.connect(self.selectFile)

    def retranslateUi(self, Foobar2000ReplayGainOptionsPage):
        self.groupBox.setTitle(QtGui.QApplication.translate("Foobar2000ReplayGainOptionsPage", "Foobar2000 ReplayGain Scanner", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Foobar2000ReplayGainOptionsPage", _("Path to foobar2000 executable"), None, QtGui.QApplication.UnicodeUTF8))
        self.foobar2000_browse.setText(QtGui.QApplication.translate("Foobar2000ReplayGainOptionsPage", _("Browse..."), None, QtGui.QApplication.UnicodeUTF8))

    def selectFile(self):
        dir = os.path.dirname(unicode(self.foobar2000_path.text()))
        dir = dir if os.path.exists(dir) else ''
        path = QtGui.QFileDialog.getOpenFileName(directory=dir)
        if path:
            self.foobar2000_path.setText(path)

io_enc = sys.getfilesystemencoding()
def encode_cmd(cmd):
    # passing unicode to Popen doesn't work in Windows
    if not os.path.supports_unicode_filenames or os.name == 'nt':
        cmd = [x.encode(io_enc) if isinstance(x, unicode) else x for x in cmd]
    return cmd

def run_foobar2000(mode, files, tagger):
    f2k_mode = {
        'scan_track':            'Scan per-file track gain',
        'scan_single_album':     'Scan selection as single album',
        'scan_album_by_tags':    'Scan selection as albums (by tags)',
        'scan_album_by_folders': 'Scan selection as albums (by folders)',
        'remove':                'Remove ReplayGain information from files',
    }
    foobar2000_binary = tagger.config.setting['f2k_rgscan_foobar2000_path']
    foobar2000 = [foobar2000_binary, '/context_command:ReplayGain/' + f2k_mode[mode]]
    cmd = []
    if os.name == 'posix':
        c = winepath + ['-0', '-w'] + files
        files = Popen(encode_cmd(c), stdout=PIPE).communicate()[0].split('\0')[:-1]
        cmd += wine
    cmd += foobar2000 + files
    Popen(encode_cmd(cmd))

def get_files(objs):
    files = []
    for obj in objs:
        if isinstance(obj, Album) or isinstance(obj, Track):
            for f in obj.iterfiles():
                files.append(f.filename)
        elif isinstance(obj, File):
            files.append(obj.filename)
    return files

class Foobar2000ReplayGainScanAlbumByTags(BaseAction):
    NAME = _("Foobar2000: &Scan selection as albums (by tags)...")
    def callback(self, objs):
        run_foobar2000('scan_album_by_tags', get_files(objs), self.tagger)

class Foobar2000ReplayGainScanTrack(BaseAction):
    NAME = _("Foobar2000: &Scan per-file track gain...")
    def callback(self, objs):
        run_foobar2000('scan_track', get_files(objs), self.tagger)

class Foobar2000ReplayGainRemove(BaseAction):
    NAME = _("Foobar2000: &Remove ReplayGain information from files...")
    def callback(self, objs):
        run_foobar2000('remove', get_files(objs), self.tagger)

class Foobar2000ReplayGainOptionsPage(OptionsPage):
    NAME = "f2k_rgscan"
    TITLE = "Foobar2000 ReplayGain"
    PARENT = "plugins"

    options = [
        TextOption('setting', 'f2k_rgscan_foobar2000_path', get_foobar2000_path()),
    ]

    def __init__(self, parent=None):
        super(Foobar2000ReplayGainOptionsPage, self).__init__(parent)
        self.ui = Ui_Foobar2000ReplayGainOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.foobar2000_path.setText(self.config.setting['f2k_rgscan_foobar2000_path'])

    def save(self):
        self.config.setting['f2k_rgscan_foobar2000_path'] = unicode(self.ui.foobar2000_path.text())

register_file_action(Foobar2000ReplayGainScanTrack())
register_file_action(Foobar2000ReplayGainRemove())
register_album_action(Foobar2000ReplayGainScanAlbumByTags())
register_album_action(Foobar2000ReplayGainRemove())
register_options_page(Foobar2000ReplayGainOptionsPage)
