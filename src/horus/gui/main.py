# -*- coding: utf-8 -*-
# This file is part of the Horus Project

__author__ = 'Jesús Arroyo Torrens <jesus.arroyo@bq.com>'
__copyright__ = 'Copyright (C) 2014-2015 Mundo Reader S.L.'
__license__ = 'GNU General Public License v2 http://www.gnu.org/licenses/gpl2.html'

import gc
import os
import time
import struct
import wx._core
import webbrowser

from horus.gui.engine import driver

from horus.gui.welcome import WelcomeDialog
from horus.gui.util.preferences import PreferencesDialog
from horus.gui.util.machine_settings import MachineSettingsDialog

from horus.gui.workbench.toolbar import ToolbarConnection
from horus.gui.workbench.control.main import ControlWorkbench
from horus.gui.workbench.adjustment.main import AdjustmentWorkbench
from horus.gui.workbench.calibration.main import CalibrationWorkbench
# from horus.gui.workbench.scanning.main import ScanningWorkbench

# from horus.gui.wizard.main import *
# from horus.gui.util.versionWindow import VersionWindow

from horus.util import profile, resources, mesh_loader, version, system as sys

__version__ = version.get_version()
__build__ = version.get_build()
__github__ = version.get_github()
__name__ = "Horus " + __version__ + " BETA"


class MainWindow(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, title=__name__, size=(980, 635))

        print ">>> " + __name__ + " <<<"

        # Initialize driver
        self.initialize_driver()
        self.last_files = profile.settings['last_files']

        # Initialize GUI
        self.load_menu()
        self.load_workbenches()

        ws, hs = self.GetSize()
        x, y, w, h = wx.Display(0).GetGeometry()
        self.SetMinSize((600, 450))
        self.SetPosition((x + (w - ws) / 2., y + (h - hs) / 2.))
        self.SetIcon(wx.Icon(resources.get_path_for_image("horus.ico"), wx.BITMAP_TYPE_ICO))

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def load_workbenches(self):
        self.toolbar = ToolbarConnection(self, on_connect_callback=self.on_connect,
                                         on_disconnect_callback=self.on_disconnect)
        self.workbench = {}
        self.workbench['control'] = ControlWorkbench(self)
        self.workbench['adjustment'] = AdjustmentWorkbench(self)
        self.workbench['calibration'] = CalibrationWorkbench(self)
        # self.workbench['scanning'] = ScanningWorkbench(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.toolbar, 0, wx.ALL | wx.EXPAND)
        self.Bind(wx.EVT_COMBOBOX, self.on_combo_box_selected, self.toolbar.combo)

        for workbench in self.workbench.values():
            self.toolbar.combo.Append(workbench.name)
            sizer.Add(workbench, 1, wx.ALL | wx.EXPAND)
        name = self.workbench[profile.settings['workbench']].name
        self.toolbar.combo.SetValue(name)
        self.update_workbenches(name)
        self.SetSizer(sizer)

    def load_menu(self):
        self.menu_bar = wx.MenuBar()

        # Menu File
        self.menu_file = wx.Menu()
        self.menu_launch_wizard = self.menu_file.Append(wx.NewId(), _("Launch Wizard"))
        self.menu_file.AppendSeparator()
        self.menu_load_model = self.menu_file.Append(wx.NewId(), _("Load Model"))
        self.menu_save_model = self.menu_file.Append(wx.NewId(), _("Save Model"))
        self.menu_clear_model = self.menu_file.Append(wx.NewId(), _("Clear Model"))
        self.menu_file.AppendSeparator()
        self.menu_open_scan_profile = self.menu_file.Append(
            wx.NewId(), _("Open scan profile"), _("Opens scan profile .json"))
        self.menu_save_scan_profile = self.menu_file.Append(
            wx.NewId(), _("Save scan profile"), _("Saves scan profile .json"))
        self.menu_reset_scan_profile = self.menu_file.Append(
            wx.NewId(), _("Reset scan profile"), _("Resets scan default values"))
        self.menu_file.AppendSeparator()
        self.menu_open_calibration_profile = self.menu_file.Append(
            wx.NewId(), _("Open calibration profile"), _("Opens calibration profile .json"))
        self.menu_save_calibration_profile = self.menu_file.Append(
            wx.NewId(), _("Save calibration profile"), _("Saves calibration profile .json"))
        self.menu_reset_calibration_profile = self.menu_file.Append(
            wx.NewId(), _("Reset calibration profile"), _("Resets calibration default values"))
        self.menu_file.AppendSeparator()
        self.menu_exit = self.menu_file.Append(wx.ID_EXIT, _("Exit"))
        self.menu_bar.Append(self.menu_file, _("File"))

        # Menu Edit
        self.menu_edit = wx.Menu()
        self.menu_preferences = self.menu_edit.Append(wx.NewId(), _("Preferences"))
        self.menu_machine_settings = self.menu_edit.Append(wx.NewId(), _("Machine settings"))
        self.menu_bar.Append(self.menu_edit, _("Edit"))

        # Menu View
        self.menu_view = wx.Menu()
        self.menu_control = wx.Menu()
        self.menu_control_panel = self.menu_control.AppendCheckItem(wx.NewId(), _("Panel"))
        self.menu_control_video = self.menu_control.AppendCheckItem(wx.NewId(), _("Video"))
        self.menu_view.AppendMenu(wx.NewId(), _("Control"), self.menu_control)
        self.menu_adjustment = wx.Menu()
        self.menu_adjustment_panel = self.menu_adjustment.AppendCheckItem(wx.NewId(), _("Panel"))
        self.menu_adjustment_video = self.menu_adjustment.AppendCheckItem(wx.NewId(), _("Video"))
        self.menu_view.AppendMenu(wx.NewId(), _("Adjustment"), self.menu_adjustment)
        self.menu_calibration = wx.Menu()
        self.menu_calibration_panel = self.menu_calibration.AppendCheckItem(wx.NewId(), _("Panel"))
        self.menu_calibration_video = self.menu_calibration.AppendCheckItem(wx.NewId(), _("Video"))
        self.menu_view.AppendMenu(wx.NewId(), _("Calibration"), self.menu_calibration)
        self.menu_scanning = wx.Menu()
        self.menu_scanning_panel = self.menu_scanning.AppendCheckItem(wx.NewId(), _("Panel"))
        self.menu_scanning_video = self.menu_scanning.AppendCheckItem(wx.NewId(), _("Video"))
        self.menu_scanning_scene = self.menu_scanning.AppendCheckItem(wx.NewId(), _("Scene"))
        self.menu_view.AppendMenu(wx.NewId(), _("Scanning"), self.menu_scanning)
        self.menu_bar.Append(self.menu_view, _("View"))

        # Menu Help
        self.menu_help = wx.Menu()
        self.menu_welcome = self.menu_help.Append(wx.ID_ANY, _("Welcome"))
        if profile.settings['check_for_updates']:
            self.menu_updates = self.menu_help.Append(wx.ID_ANY, _("Updates"))
        self.menu_wiki = self.menu_help.Append(wx.ID_ANY, _("Wiki"))
        self.menu_sources = self.menu_help.Append(wx.ID_ANY, _("Sources"))
        self.menu_issues = self.menu_help.Append(wx.ID_ANY, _("Issues"))
        self.menu_forum = self.menu_help.Append(wx.ID_ANY, _("Forum"))
        self.menu_about = self.menu_help.Append(wx.ID_ABOUT, _("About"))
        self.menu_bar.Append(self.menu_help, _("Help"))

        self.SetMenuBar(self.menu_bar)

        # Events
        self.Bind(wx.EVT_MENU, self.on_launch_wizard, self.menu_launch_wizard)
        self.Bind(wx.EVT_MENU, self.on_load_model, self.menu_load_model)
        self.Bind(wx.EVT_MENU, self.on_save_model, self.menu_save_model)
        self.Bind(wx.EVT_MENU, self.on_clear_model, self.menu_clear_model)
        self.Bind(wx.EVT_MENU, lambda e: self.on_open_profile("scan_settings"),
                  self.menu_open_scan_profile)
        self.Bind(wx.EVT_MENU, lambda e: self.on_save_profile("scan_settings"),
                  self.menu_save_scan_profile)
        self.Bind(wx.EVT_MENU, lambda e: self.on_reset_profile("scan_settings"),
                  self.menu_reset_scan_profile)
        self.Bind(wx.EVT_MENU, lambda e: self.on_open_profile("calibration_settings"),
                  self.menu_open_calibration_profile)
        self.Bind(wx.EVT_MENU, lambda e: self.on_save_profile("calibration_settings"),
                  self.menu_save_calibration_profile)
        self.Bind(wx.EVT_MENU, lambda e: self.on_reset_profile("calibration_settings"),
                  self.menu_reset_calibration_profile)
        self.Bind(wx.EVT_MENU, self.on_exit, self.menu_exit)

        self.Bind(wx.EVT_MENU, self.on_preferences, self.menu_preferences)
        self.Bind(wx.EVT_MENU, self.on_machine_settings, self.menu_machine_settings)

        self.Bind(wx.EVT_MENU, self.on_control_panel_clicked, self.menu_control_panel)
        self.Bind(wx.EVT_MENU, self.on_control_video_clicked, self.menu_control_video)
        self.Bind(wx.EVT_MENU, self.on_adjustment_panel_clicked, self.menu_adjustment_panel)
        self.Bind(wx.EVT_MENU, self.on_adjustment_video_clicked, self.menu_adjustment_video)
        self.Bind(wx.EVT_MENU, self.on_calibration_panel_clicked, self.menu_calibration_panel)
        self.Bind(wx.EVT_MENU, self.on_calibration_video_clicked, self.menu_calibration_video)
        self.Bind(wx.EVT_MENU, self.on_scanning_panel_clicked, self.menu_scanning_panel)
        self.Bind(wx.EVT_MENU, self.on_scanning_video_scene_clicked, self.menu_scanning_video)
        self.Bind(wx.EVT_MENU, self.on_scanning_video_scene_clicked, self.menu_scanning_scene)

        self.Bind(wx.EVT_MENU, self.on_about, self.menu_about)
        self.Bind(wx.EVT_MENU, self.on_welcome, self.menu_welcome)
        if profile.settings['check_for_updates']:
            self.Bind(wx.EVT_MENU, self.on_updates, self.menu_updates)
        self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(
            'https://github.com/bq/horus/wiki'), self.menu_wiki)
        self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(
            'https://github.com/bq/horus'), self.menu_sources)
        self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(
            'https://github.com/bq/horus/issues'), self.menu_issues)
        self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(
            'https://groups.google.com/forum/?hl=es#!forum/ciclop-3d-scanner'), self.menu_forum)

    def on_launch_wizard(self, event):
        Wizard(self)

    def on_load_model(self, event):
        last_file = os.path.split(profile.settings['last_file'])[0]
        dlg = wx.FileDialog(
            self, _("Open 3D model"), last_file, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        wildcard_list = ';'.join(map(lambda s: '*' + s, mesh_loader.loadSupportedExtensions()))
        wildcard_filter = "All (%s)|%s;%s" % (wildcard_list, wildcard_list, wildcard_list.upper())
        wildcard_list = ';'.join(map(lambda s: '*' + s, mesh_loader.loadSupportedExtensions()))
        wildcard_filter += "|Mesh files (%s)|%s;%s" % (wildcard_list, wildcard_list,
                                                       wildcard_list.upper())
        dlg.SetWildcard(wildcard_filter)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            if filename is not None:
                self.workbench['scanning'].sceneView.loadFile(filename)
                self.append_last_file(filename)
        dlg.Destroy()

    def on_save_model(self, event):
        if self.workbench['scanning'].sceneView._object is None:
            return
        dlg = wx.FileDialog(self, _("Save 3D model"), os.path.split(
            profile.settings['last_file'])[0], style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        file_extensions = mesh_loader.saveSupportedExtensions()
        wildcard_list = ';'.join(map(lambda s: '*' + s, file_extensions))
        wildcard_filter = "Mesh files (%s)|%s;%s" % (wildcard_list, wildcard_list,
                                                     wildcard_list.upper())
        dlg.SetWildcard(wildcard_filter)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            if not filename.endswith('.ply'):
                if sys.is_linux():  # hack for linux, as for some reason the .ply is not appended.
                    filename += '.ply'
            mesh_loader.saveMesh(filename, self.workbench['scanning'].sceneView._object)
            self.append_last_file(filename)
        dlg.Destroy()

    def on_clear_model(self, event):
        if self.workbench['scanning'].sceneView._object is not None:
            dlg = wx.MessageDialog(
                self,
                _("Your current model will be erased.\nDo you really want to do it?"),
                _("Clear Point Cloud"), wx.YES_NO | wx.ICON_QUESTION)
            result = dlg.ShowModal() == wx.ID_YES
            dlg.Destroy()
            if result:
                self.workbench['scanning'].sceneView._clearScene()

    def on_open_profile(self, category):
        dlg = wx.FileDialog(self, _("Select profile file to load"), profile.get_base_path(),
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        dlg.SetWildcard("JSON files (*.json)|*.json")
        if dlg.ShowModal() == wx.ID_OK:
            profile_file = dlg.GetPath()
            profile.settings.load_settings(profile_file, categories=[category])
            self.update_profile_to_all_controls()
        dlg.Destroy()

    def on_save_profile(self, category):
        dlg = wx.FileDialog(self, _("Select profile file to save"), profile.get_base_path(),
                            style=wx.FD_SAVE)
        dlg.SetWildcard("JSON files (*.json)|*.json")
        if dlg.ShowModal() == wx.ID_OK:
            profile_file = dlg.GetPath()
            if not profile_file.endswith('.json'):
                if sys.is_linux():  # hack for linux, as for some reason the .json is not appended.
                    profile_file += '.json'
            profile.settings.save_settings(profile_file, categories=[category])
        dlg.Destroy()

    def on_reset_profile(self, category):
        dlg = wx.MessageDialog(
            self,
            _("This will reset all profile settings to defaults.\n"
              "Unless you have saved your current profile, all settings will be lost!\n"
              "Do you really want to reset?"),
            _("Profile reset"), wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal() == wx.ID_YES
        dlg.Destroy()
        if result:
            profile.settings.reset_to_default(categories=[category])
            self.update_profile_to_all_controls()

    def on_exit(self, event):
        self.Close(True)

    def on_close(self, event):
        try:
            driver.board.set_unplug_callback(None)
            driver.camera.set_unplug_callback(None)
            driver.disconnect()
            if ciclop_scan.is_scanning:
                ciclop_scan.stop()
                time.sleep(0.5)
        except:
            pass
        event.Skip()

    def append_last_file(self, last_file):
        if last_file in self.last_files:
            self.last_files.remove(last_file)
        self.last_files.append(last_file)
        if len(self.last_files) > 4:
            self.last_files = self.last_files[1:5]
        profile.settings['last_file'] = last_file
        profile.settings['last_files'] = self.last_files

    def on_preferences(self, event):
        if sys.is_windows():
            driver.disconnect()

        preferences = PreferencesDialog()
        preferences.ShowModal()

    def on_machine_settings(self, event):
        if sys.is_windows():
            driver.disconnect()

        machine_settings = MachineSettingsDialog(self)
        ret = machine_settings.ShowModal()

        if ret == wx.ID_OK:
            try:  # TODO: Fix this. If not in the Scanning workbench, _drawMachine() fails.
                self.workbench['scanning'].sceneView._drawMachine()
            except:
                pass
            profile.settings.save_settings(categories=["machine_settings"])
            self.workbench['scanning'].controls.panels["point_cloud_roi"].update_profile()

    def on_menu_view_clicked(self, key, checked, panel):
        profile.settings[key] = checked
        if checked:
            panel.Show()
        else:
            panel.Hide()
        panel.GetParent().Layout()
        panel.Layout()
        self.Layout()

    def on_control_panel_clicked(self, event):
        self.on_menu_view_clicked('view_control_panel',
                                  self.menu_control_panel.IsChecked(),
                                  self.workbench['control'].scroll_panel)

    def on_control_video_clicked(self, event):
        self.on_menu_view_clicked('view_control_video',
                                  self.menu_control_video.IsChecked(),
                                  self.workbench['control'].video_view)

    def on_adjustment_panel_clicked(self, event):
        self.on_menu_view_clicked('view_adjustment_panel',
                                  self.menu_adjustment_panel.IsChecked(),
                                  self.workbench['adjustment'].scroll_panel)

    def on_adjustment_video_clicked(self, event):
        self.on_menu_view_clicked('view_adjustment_video',
                                  self.menu_adjustment_video.IsChecked(),
                                  self.workbench['adjustment'].video_view)

    def on_calibration_panel_clicked(self, event):
        self.on_menu_view_clicked('view_calibration_panel',
                                  self.menu_calibration_panel.IsChecked(),
                                  self.workbench['calibration'].scroll_panel)

    def on_calibration_video_clicked(self, event):
        self.on_menu_view_clicked('view_calibration_video',
                                  self.menu_calibration_video.IsChecked(),
                                  self.workbench['calibration'].video_view)

    def on_scanning_panel_clicked(self, event):
        self.on_menu_view_clicked('view_scanning_panel',
                                  self.menu_scanning_panel.IsChecked(),
                                  self.workbench['scanning'].scroll_panel)

    def on_scanning_video_scene_clicked(self, event):
        checked_video = self.menu_scanning_video.IsChecked()
        checked_scene = self.menu_scanning_scene.IsChecked()
        profile.settings['view_scanning_video'] = checked_video
        profile.settings['view_scanning_scene'] = checked_scene
        self.workbench['scanning'].splitter_window.Unsplit()
        if checked_video:
            self.workbench['scanning'].video_view.Show()
            self.workbench['scanning'].splitter_window.SplitVertically(
                self.workbench['scanning'].video_view, self.workbench['scanning'].scene_panel)
            if checked_scene:
                self.workbench['scanning'].scene_panel.Show()
            else:
                self.workbench['scanning'].scene_panel.Hide()
                self.workbench['scanning'].splitter_window.Unsplit()
        else:
            self.workbench['scanning'].video_view.Hide()
            if checked_scene:
                self.workbench['scanning'].scene_panel.Show()
                self.workbench['scanning'].splitter_window.SplitVertically(
                    self.workbench['scanning'].scene_panel, self.workbench['scanning'].video_view)
                self.workbench['scanning'].splitter_window.Unsplit()
            else:
                self.workbench['scanning'].scene_panel.Hide()
                self.workbench['scanning'].splitter_window.Unsplit()

        self.workbench['scanning'].splitter_window.Layout()
        self.workbench['scanning'].Layout()
        self.Layout()

    def on_connect(self):
        for workbench in self.workbench.values():
            workbench.enable_content()
        self.workbench[profile.settings['workbench']].on_connect()

    def on_disconnect(self):
        for workbench in self.workbench.values():
            workbench.disable_content()
        self.workbench[profile.settings['workbench']].on_disconnect()

    def on_combo_box_selected(self, event):
        self.update_workbenches(event.GetEventObject().GetValue())

    def update_workbenches(self, name):
        waitCursor = wx.BusyCursor()
        for key, wb in self.workbench.iteritems():
            if wb.name == name:
                wb.Hide()
                wb.Show()
                profile.settings['workbench'] = key
            else:
                wb.Hide()

        is_scan = profile.settings['workbench'] == 'scanning'
        self.menu_file.Enable(self.menu_load_model.GetId(), is_scan)
        self.menu_file.Enable(self.menu_save_model.GetId(), is_scan)
        self.menu_file.Enable(self.menu_clear_model.GetId(), is_scan)
        self.Layout()

        del waitCursor
        gc.collect()

    def on_about(self, event):
        info = wx.AboutDialogInfo()
        icon = wx.Icon(resources.get_path_for_image("horus.ico"), wx.BITMAP_TYPE_ICO)
        info.SetIcon(icon)
        info.SetName(u'Horus')
        info.SetVersion(__version__)
        tech_description = _('Horus is an Open Source 3D Scanner manager')
        tech_description += '\nVersion: ' + __version__
        tech_description += '\nBuild: ' + __build__
        tech_description += '\nGitHub: ' + __github__
        info.SetDescription(tech_description)
        info.SetCopyright(u'(C) 2014-2015 Mundo Reader S.L.')
        info.SetWebSite(u'http://www.bq.com')
        info.SetLicence("Horus is free software; you can redistribute it and/or modify it\n"
                        "under the terms of the GNU General Public License as published by\n"
                        "the Free Software Foundation; either version 2 of the License,\n"
                        "or (at your option) any later version.\n"
                        "Horus is distributed in the hope that it will be useful,\n"
                        "but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
                        "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.\n"
                        "See the GNU General Public License for more details. You should have\n"
                        "received a copy of the GNU General Public License along with\n"
                        "File Hunter; if not, write to the Free Software Foundation,\n"
                        "Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA")
        info.AddDeveloper(u'Jesús Arroyo, Irene Sanz, Jorge Robles')
        info.AddDocWriter(u'Jesús Arroyo, Ángel Larrañaga')
        info.AddArtist(u'Jesús Arroyo, Nestor Toribio')
        info.AddTranslator(u'Jesús Arroyo, Irene Sanz, Alexandre Galode, Natasha da Silva, '
                           'Camille Montgolfier, Markus Hoedl, Andrea Fantini, Maria Albuquerque, '
                           'Meike Schirmeister')
        wx.AboutBox(info)

    def on_welcome(self, event):
        WelcomeDialog(self)

    def on_updates(self, event):
        if profile.settings['check_for_updates']:
            if version.check_for_updates():
                VersionWindow(self)
            else:
                dlg = wx.MessageDialog(self, _("You are running the latest version of Horus!"), _(
                    "Updated!"), wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()

    def on_board_unplugged(self):
        self._on_device_unplugged(
            _("Board unplugged"),
            _("Board has been unplugged. Please, plug it in and press connect"))

    def on_camera_unplugged(self):
        self._on_device_unplugged(
            _("Camera unplugged"),
            _("Camera has been unplugged. Please, plug it in and press connect"))

    def _on_device_unplugged(self, title="", description=""):
        ciclop_scan.stop()
        laser_triangulation.cancel()
        platform_extrinsics.cancel()
        self.workbench['control'].updateStatus(False)
        self.workbench['adjustment'].updateStatus(False)
        self.workbench['calibration'].updateStatus(False)
        self.workbench['scanning'].updateStatus(False)
        driver.disconnect()
        dlg = wx.MessageDialog(self, description, title, wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    def update_profile_to_all_controls(self):
        self.workbench[profile.settings['workbench']].update_controls()

        """if profile.settings['view_control_panel']:
            self.workbench['control'].scrollPanel.Show()
            self.menu_control_panel.Check(True)
        else:
            self.workbench['control'].scrollPanel.Hide()
            self.menu_control_panel.Check(False)

        if profile.settings['view_control_video']:
            self.workbench['control'].videoView.Show()
            self.menu_control_video.Check(True)
        else:
            self.workbench['control'].videoView.Hide()
            self.menu_control_video.Check(False)

        if profile.settings['view_adjustment_panel']:
            self.workbench['adjustment'].scrollPanel.Show()
            self.menu_adjustment_panel.Check(True)
        else:
            self.workbench['adjustment'].scrollPanel.Hide()
            self.menu_adjustment_panel.Check(False)

        if profile.settings['view_adjustment_video']:
            self.workbench['adjustment'].videoView.Show()
            self.menu_adjustment_video.Check(True)
        else:
            self.workbench['adjustment'].videoView.Hide()
            self.menu_adjustment_video.Check(False)

        if profile.settings['view_calibration_panel']:
            self.workbench['calibration'].scrollPanel.Show()
            self.menu_calibration_panel.Check(True)
        else:
            self.workbench['calibration'].scrollPanel.Hide()
            self.menu_calibration_panel.Check(False)

        if profile.settings['view_calibration_video']:
            self.workbench['calibration'].videoView.Show()
            self.menu_calibration_video.Check(True)
        else:
            self.workbench['calibration'].videoView.Hide()
            self.menu_calibration_video.Check(False)

        if profile.settings['view_scanning_panel']:
            self.workbench['scanning'].scrollPanel.Show()
            self.menu_scanning_panel.Check(True)
        else:
            self.workbench['scanning'].scrollPanel.Hide()
            self.menu_scanning_panel.Check(False)

        checked_video = profile.settings['view_scanning_video']
        checked_scene = profile.settings['view_scanning_scene']

        self.menu_scanning_video.Check(checked_video)
        self.menu_scanning_scene.Check(checked_scene)

        self.workbench['scanning'].splitterWindow.Unsplit()
        if checked_video:
            self.workbench['scanning'].videoView.Show()
            self.workbench['scanning'].splitterWindow.SplitVertically(
                self.workbench['scanning'].videoView, self.workbench['scanning'].scenePanel)
            if checked_scene:
                self.workbench['scanning'].scenePanel.Show()
            else:
                self.workbench['scanning'].scenePanel.Hide()
                self.workbench['scanning'].splitterWindow.Unsplit()
        else:
            self.workbench['scanning'].videoView.Hide()
            if checked_scene:
                self.workbench['scanning'].scenePanel.Show()
                self.workbench['scanning'].splitterWindow.SplitVertically(
                    self.workbench['scanning'].scenePanel, self.workbench['scanning'].videoView)
                self.workbench['scanning'].splitterWindow.Unsplit()
            else:
                self.workbench['scanning'].scenePanel.Hide()
                self.workbench['scanning'].splitterWindow.Unsplit()"""

    def initialize_driver(self):
        # Serial name
        serial_list = driver.board.get_serial_list()
        current_serial = profile.settings['serial_name']
        if len(serial_list) > 0:
            if current_serial not in serial_list:
                profile.settings['serial_name'] = serial_list[0]
        # Video id
        video_list = driver.camera.get_video_list()
        current_video_id = profile.settings['camera_id']
        if len(video_list) > 0:
            if current_video_id not in video_list:
                profile.settings['camera_id'] = unicode(video_list[0])

        self.update_driver_profile()

    def update_driver_profile(self):
        driver.camera.camera_id = int(profile.settings['camera_id'][-1:])
        driver.board.serial_name = profile.settings['serial_name']
        driver.board.baud_rate = profile.settings['baud_rate']
        driver.board.motor_invert(profile.settings['invert_motor'])

    def updateProfile(self):
        ciclop_scan.capture_texture = profile.settings['capture_texture']
        use_laser = profile.settings['use_laser']
        ciclop_scan.set_use_left_laser(use_laser == 'Left' or use_laser == 'Both')
        ciclop_scan.set_use_right_laser(use_laser == 'Right' or use_laser == 'Both')
        ciclop_scan.motor_step = profile.settings['motor_step_scanning']
        ciclop_scan.motor_speed = profile.settings['motor_speed_scanning']
        ciclop_scan.motor_acceleration = profile.settings['motor_acceleration_scanning']
        ciclop_scan.color = struct.unpack(
            'BBB', profile.settings['point_cloud_color'].decode('hex'))

        image_capture.pattern_mode.brightness = profile.settings['brightness_pattern_calibration']
        image_capture.pattern_mode.contrast = profile.settings['contrast_pattern_calibration']
        image_capture.pattern_mode.saturation = profile.settings['saturation_pattern_calibration']
        image_capture.pattern_mode.exposure = profile.settings['exposure_pattern_calibration']
        image_capture.laser_mode.brightness = profile.settings['brightness_laser_scanning']
        image_capture.laser_mode.contrast = profile.settings['contrast_laser_scanning']
        image_capture.laser_mode.saturation = profile.settings['saturation_laser_scanning']
        image_capture.laser_mode.exposure = profile.settings['exposure_laser_scanning']
        image_capture.texture_mode.brightness = profile.settings['brightness_texture_scanning']
        image_capture.texture_mode.contrast = profile.settings['contrast_texture_scanning']
        image_capture.texture_mode.saturation = profile.settings['saturation_texture_scanning']
        image_capture.texture_mode.exposure = profile.settings['exposure_texture_scanning']
        image_capture.use_distortion = profile.settings['use_distortion']

        laser_segmentation.red_channel = profile.settings['red_channel_scanning']
        laser_segmentation.open_enable = profile.settings['open_enable_scanning']
        laser_segmentation.open_value = profile.settings['open_value_scanning']
        laser_segmentation.threshold_enable = profile.settings['threshold_enable_scanning']
        laser_segmentation.threshold_value = profile.settings['threshold_value_scanning']

        current_video.set_roi_view(profile.settings['roi_view'])
        point_cloud_roi.set_diameter(profile.settings['roi_diameter'])
        point_cloud_roi.set_height(profile.settings['roi_height'])

        pattern.rows = profile.settings['pattern_rows']
        pattern.columns = profile.settings['pattern_columns']
        pattern.square_width = profile.settings['pattern_square_width']
        pattern.distance = profile.settings['pattern_origin_distance']

        self.updateCalibrationProfile()

    def updateCalibrationProfile(self):
        resolution = profile.settings['resolution'].split('x')
        driver.camera.set_frame_rate(int(profile.settings['framerate']))
        calibration_data.set_resolution(int(resolution[1]), int(resolution[0]))
        calibration_data.camera_matrix = profile.settings['camera_matrix']
        calibration_data.distortion_vector = profile.settings['distortion_vector']
        calibration_data.laser_planes[0].distance = profile.settings['distance_left']
        calibration_data.laser_planes[0].normal = profile.settings['normal_left']
        calibration_data.laser_planes[1].distance = profile.settings['distance_right']
        calibration_data.laser_planes[1].normal = profile.settings['normal_right']
        calibration_data.platform_rotation = profile.settings['rotation_matrix']
        calibration_data.platform_translation = profile.settings['translation_vector']
