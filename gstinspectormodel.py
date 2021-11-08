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
    no_type = 0,
    plugin_type = 1,
    element_type = 2,
    type_finder_type = 3
    all_types = 4


""" The Plugin_Element contains the name of the plugin, the element name and a description of the element """


class Plugin_Element():
    def __init__(self):
        self.plugin_name: str = ""
        self.element_name: str = ""
        self.element_description: str = ""

    def __init__(self, plugin_name: str, element_name: str, element_description: str):
        self.plugin_name = plugin_name
        self.element_name = element_name
        self.element_description = element_description


""" Gst_Inspector_Model contains information gathered through gst-inspect-1.0
  """


class Gst_Inspector_Model():

    def __init__(self):
        # plugin_dictionary keys are the names of the gstreamer plugins,
        # values are elements and types which are in the plugin
        self.plugin_dictionary = dict()
        # element_dictionary keys are the name of the element,
        # the value is a Plugin_Element. The value is the containing plugin,
        # the name of the element, and the long name of the element.
        self.element_dictionary = dict()
        # types_dictionary keys are the name of the type factory,
        # the value is a Plugin_Element. The value is the containing plugin,
        # the name of the type factory, and the long name of the type factory.
        self.types_dictionary = dict()

    # The "get" functions here use gst-inspect-1.0 to gather information about plugins, elements and types

    def get_plugins_and_elements(self) -> str:
        """Return the list of plugins with the elements they contain using gst-inspect-1.0 """
        try:
            p = subprocess.Popen(
                ['gst-inspect-1.0'],
                stdout=subprocess.PIPE, universal_newlines=True)
        except:
            return []
        (stdoutdata, stderrdata) = p.communicate()
        return stdoutdata

    def get_element_description_text(self, element_or_type_name: str) -> str:
        """ Get the element or type factory description text from gst-inspect1.0 """
        try:
            p = subprocess.Popen(
                ['gst-inspect-1.0', element_or_type_name],
                stdout=subprocess.PIPE, universal_newlines=True)
        except:
            return []
        (stdoutdata, stderrdata) = p.communicate()
        return stdoutdata

    def get_plugin_description_text(self, element_name: str) -> str:
        """ Get the plugin description text from gst-inspect1.0 """
        try:
            p = subprocess.Popen(
                ['gst-inspect-1.0', '--plugin', element_name],
                stdout=subprocess.PIPE, universal_newlines=True)
        except:
            return []
        (stdoutdata, stderrdata) = p.communicate()
        return stdoutdata

    """ Parse the plugins and elements from the default gst-inspect list.
        The results will be placed into three dictionaries. Each dictionary
        is based on the type, plugin, element or type factory """

    def parse_plugin_element_text(self, string_to_parse):
        """ Parse the plugins and elements from the default gst-inspect list """
        self.plugin_dictionary.clear()
        self.element_dictionary.clear()
        self.types_dictionary.clear()
        for line in string_to_parse.splitlines():
            # skip over a blank line, or the summary line at the end
            if len(line) == 0:
                continue
            if 'Total count:' in line:  # This is the summary line
                continue
            split_line = line.split(':')
            # We remove any leading spaces on the entries
            # There is a plugin name and an element/type name ; the description may be missing
            plugin_name = split_line[0]
            element_or_type_name = split_line[1].lstrip()
            if len(split_line) < 3:
                element_description = ""
            else:
                element_description = split_line[2].lstrip()
            plugin_element = Plugin_Element(
                plugin_name=plugin_name,
                element_name=element_or_type_name,
                element_description=element_description)
            # Add the plugins to the plugin dictionary
            if plugin_element.plugin_name in self.plugin_dictionary:
                self.plugin_dictionary[plugin_element.plugin_name].append(
                    plugin_element)
            else:
                self.plugin_dictionary[plugin_element.plugin_name] = [
                    plugin_element]

            # These aren't really elements ; Don't add them to the lists
            if 'GstDeviceProviderFactory' in element_or_type_name or 'GstDynamicTypeFactory' in element_or_type_name or 'GstTracerFactory' in element_or_type_name:
                continue
            # Add the element to the elements dictionary or types dictionary
            if '/' in element_or_type_name:
                # This is a type factory name
                if element_or_type_name in self.types_dictionary:
                    # FIXME - Throw error here?
                    print("Duplicate Type!")
                else:
                    self.types_dictionary[element_or_type_name] = [
                        plugin_element]
            elif element_or_type_name in self.element_dictionary:
                # FIXME - Throw error here?
                print("Duplicate element name")
            else:
                self.element_dictionary[element_or_type_name] = [
                    plugin_element]

    def get_and_parse_elements(self):
        """ Get the plugins, elements and types using gst-inspect-1.0, then parse the results"""
        text_data = self.get_plugins_and_elements()
        self.parse_plugin_element_text(text_data)
