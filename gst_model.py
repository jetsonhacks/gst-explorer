#
#  GStreamer Inspector
#
#  Copyright (C) 2021 JetsonHacks (info@jetsonhacks.com)
#
#  MIT License
#
import subprocess
from enum import Enum


class GstListType (Enum):
    NONE = 0,
    PLUGIN = 1,
    ELEMENT = 2,
    TYPE_FINDER = 3
    ALL = 4


""" The Plugin_Element contains the name of the plugin, the feature name and a description of the element, and the type """


class Plugin_Feature():
    def __init__(self):
        self.plugin_name: str = ""
        self.feature_name: str = ""
        self.feature_description: str = ""
        self.type: GstListType = GstListType.NONE

    def __init__(self, plugin_name: str, feature_name: str, feature_description: str):
        self.plugin_name = plugin_name
        self.feature_name = feature_name
        self.feature_description = feature_description
        self.type: GstListType = GstListType.NONE


""" Gst_Inspector_Model contains information gathered through gst-inspect-1.0
  """


class Gst_Inspector_Model():

    def __init__(self):
        self.plugin_list = set()
        # Elements and Type Factories
        self.feature_dictionary = dict()

    # The "get" functions here use gst-inspect-1.0 to gather information about plugins, elements and types

    def get_plugins_and_elements(self) -> str:
        """Return the list of plugins with the elements they contain using gst-inspect-1.0 """
        try:
            to_return = subprocess.check_output(
                ["gst-inspect-1.0"], encoding='utf-8')
        except Exception as e:
            print(e)
            to_return = []
        return to_return

    def get_feature_description(self, feature_name: str) -> str:
        """ Get the element or type factory description text from gst-inspect1.0 """
        try:
            to_return = subprocess.check_output(
                ["gst-inspect-1.0", feature_name], encoding='utf-8')
        except Exception as e:
            print(e)
            to_return = []
        return to_return

    def get_plugin_description(self, plugin_name: str) -> str:
        """ Get the plugin description text from gst-inspect1.0 """
        try:
            to_return = subprocess.check_output(
                ["gst-inspect-1.0", '--plugin', plugin_name], encoding='utf-8')
        except Exception as e:
            print(e)
            to_return = []
        return to_return

    def parse_plugin_element_text(self, string_to_parse):
        """ Parse the plugins, elements and type finders from the default gst-inspect list """
        for line in string_to_parse.splitlines():
            # skip over a blank line, or the summary line at the end
            if len(line) == 0:
                continue
            if 'Total count:' in line:  # This is the summary line
                continue

            # We remove any leading spaces on the entries
            # There is a plugin name and an element/type name ; the description may be missing
            split_line = [entry.lstrip() for entry in line.split(':')]
            plugin_name, feature_name, *feature_description = split_line
            if feature_description:
                feature_description = feature_description[0]
            else:
                feature_description = ""

            plugin_feature = Plugin_Feature(
                plugin_name=plugin_name,
                feature_name=feature_name,
                feature_description=feature_description)

            self.plugin_list.add(plugin_name)

            # These aren't really elements ; Don't add them to the lists
            if 'GstDeviceProviderFactory' in feature_name \
                    or 'GstDynamicTypeFactory' in feature_name \
                    or 'GstTracerFactory' in feature_name:
                continue

            if '/' in feature_name:
                plugin_feature.type = GstListType.TYPE_FINDER
            else:
                plugin_feature.type = GstListType.ELEMENT

            self.feature_dictionary[feature_name] = plugin_feature

    def get_and_parse_elements(self):
        """ Get the plugins, elements and types using gst-inspect-1.0, then parse the results"""
        text_data = self.get_plugins_and_elements()
        self.parse_plugin_element_text(text_data)
