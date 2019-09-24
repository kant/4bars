# uncompyle6 version 3.3.3
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.16 (default, Apr 12 2019, 15:32:40) 
# [GCC 4.2.1 Compatible Apple LLVM 10.0.1 (clang-1001.0.46.3)]
# Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/Push/actions.py
# Compiled at: 2018-11-20 19:30:59
from __future__ import absolute_import, print_function, unicode_literals
import Live
from ableton.v2.base import depends, listens, task
from ableton.v2.control_surface import Component
from ableton.v2.control_surface.mode import SetAttributeMode, ModesComponent
from pushbase.consts import MessageBoxText
from pushbase.device_chain_utils import is_empty_drum_pad
from pushbase.browser_modes import BrowserAddEffectMode
from pushbase.action_with_options_component import OptionsComponent
from pushbase.message_box_component import Messenger

class CreateDefaultTrackComponent(Component, Messenger):

    @depends(selection=None)
    def __init__(self, selection=None, *a, **k):
        super(CreateDefaultTrackComponent, self).__init__(*a, **k)
        self.options = OptionsComponent(parent=self)
        self.options.selected_option = None
        self.options.option_names = (u'Audio', u'Midi', u'Return')
        self.options.labels = (u'Create track:', u'', u'', u'')
        self.options.selected_color = 'Browser.Load'
        self.options.unselected_color = 'Browser.Load'
        self._on_option_selected.subject = self.options
        self._selection = selection
        return

    @listens('selected_option')
    def _on_option_selected(self, option):
        if option is not None:
            self.create_track()
            self.options.selected_option = None
        return

    def create_track(self):
        try:
            song = self.song
            selected_option = self.options.selected_option
            if selected_option == 0:
                song.create_audio_track()
            else:
                if selected_option == 1:
                    song.create_midi_track()
                else:
                    if selected_option == 2:
                        song.create_return_track()
        except Live.Base.LimitationError:
            self.expect_dialog(MessageBoxText.TRACK_LIMIT_REACHED)
        except RuntimeError:
            self.expect_dialog(MessageBoxText.MAX_RETURN_TRACKS_REACHED)

    def on_enabled_changed(self):
        self.options.selected_option = None
        return


class CreateInstrumentTrackComponent(Component, Messenger):

    @depends(selection=None)
    def __init__(self, selection=None, browser_mode=None, browser_component=None, browser_hotswap_mode=None, *a, **k):
        super(CreateInstrumentTrackComponent, self).__init__(*a, **k)
        self._selection = selection
        self._with_browser_modes = ModesComponent(parent=self)
        self._with_browser_modes.add_mode('create', [
         self._prepare_browser,
         SetAttributeMode(self.application.browser, 'filter_type', Live.Browser.FilterType.instrument_hotswap),
         SetAttributeMode(browser_component, 'do_load_item', self._do_browser_load_item),
         browser_mode,
         browser_component.reset_load_memory])
        self._with_browser_modes.add_mode('hotswap', [
         browser_hotswap_mode,
         browser_mode])
        self._go_to_hotswap_task = self._tasks.add(task.sequence(task.delay(1), task.run(self._go_to_hotswap)))
        self._go_to_hotswap_task.kill()

    def on_enabled_changed(self):
        self._with_browser_modes.selected_mode = 'create' if self.is_enabled() else None
        self._go_to_hotswap_task.kill()
        return

    def _prepare_browser(self):
        self.application.browser.hotswap_target = None
        return

    def _do_browser_load_item(self, item):
        song = self.song
        try:
            song.create_midi_track()
        except Live.Base.LimitationError:
            self.expect_dialog(MessageBoxText.TRACK_LIMIT_REACHED)

        item.action()
        self._go_to_hotswap_task.restart()

    def _go_to_hotswap(self):
        self._with_browser_modes.selected_mode = 'hotswap'


class CreateDeviceComponent(Component):

    @depends(selection=None)
    def __init__(self, selection=None, browser_component=None, browser_mode=None, browser_hotswap_mode=None, insert_left=False, *a, **k):
        super(CreateDeviceComponent, self).__init__(*a, **k)
        self._selection = selection
        self._add_effect_mode = BrowserAddEffectMode(selection=selection, browser=self.application.browser, application_view=self.application.view, insert_left=insert_left)
        self._create_device_modes = ModesComponent(parent=self)
        self._create_device_modes.add_mode('create', [
         SetAttributeMode(browser_component, 'do_load_item', self._do_browser_load_item),
         self._add_effect_mode,
         browser_mode,
         browser_component.reset_load_memory])
        self._create_device_modes.add_mode('hotswap', [
         browser_hotswap_mode,
         browser_mode])
        self._go_to_hotswap_task = self._tasks.add(task.sequence(task.delay(1), task.run(self._go_to_hotswap)))
        self._go_to_hotswap_task.kill()

    def on_enabled_changed(self):
        self._go_to_hotswap_task.kill()
        if self.is_enabled():
            if is_empty_drum_pad(self._selection.selected_object):
                self._create_device_modes.selected_mode = 'hotswap'
            else:
                self._create_device_modes.selected_mode = 'create'

    def _go_to_hotswap(self):
        self._create_device_modes.selected_mode = 'hotswap'

    def _do_browser_load_item(self, item):
        selection = self._add_effect_mode.get_selection_for_insert()
        if selection:
            self._selection.selected_object = selection
        item.action()
        self._go_to_hotswap_task.restart()