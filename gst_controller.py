#
#  GStreamer Inspector
#
#  Copyright (C) 2021 JetsonHacks (info@jetsonhacks.com)
#
#  MIT License
#
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QAbstractItemView, QListWidgetItem)

import re
from gst_model import GstListType


class Gst_Inspector_Controller():
    def __init__(self, model, view):
        self.model = model
        self.view = view
        # filter_dictionary is a map from the GUI combo box string values to the GstListType
        self.filter_dictionary = {"Plugins": GstListType.PLUGIN,
                                  "Elements": GstListType.ELEMENT,
                                  "Types": GstListType.TYPE_FINDER,
                                  "All": GstListType.ALL}

    def setup(self):
        """ Get the plugins, elements and types and setup the window elements"""
        self.model.get_and_parse_elements()
        self.view.setup(self)
        # Populate the list widget with the plugins, elements and types
        self.populate_list_widget(self.view, self.model)
        # Select 'Elements' in the combo box filter
        # Most people want to examine elements first
        self.view.filter_combo_box.setCurrentText("Elements")
        # Good to go, show the window
        self.view.show()

    # Add a list widget to the Views feature list widget
    def add_list_item(self, key: str, type: GstListType, icon: QIcon, tooltip: str):
        if icon == None:
            list_widget = QListWidgetItem(key)
        else:
            list_widget = QListWidgetItem(icon, key)
        list_widget.setData(Qt.UserRole, type)
        if tooltip is not None:
            list_widget.setToolTip(tooltip)
        self.view.list_widget.addItem(list_widget)

    def populate_list_widget(self, view, model):
        # Three lists: plugins, elements, and types
        # We place them all in the list widget, and associate the type for each item
        icon = view.get_plugin_icon()

        for plugin_name in model.plugin_list:
            self.add_list_item(
                plugin_name, GstListType.PLUGIN, icon, None)

        for key, feature_value in model.feature_dictionary.items():
            tooltip = feature_value.feature_description
            self.add_list_item(key, feature_value.type, None, tooltip)

        view.list_widget.sortItems()

    def sync_list_interface(self):
        """ Synch the list_widget and element_text_edit """
        scroll_bar = self.view.list_widget.verticalScrollBar()
        if scroll_bar is not None:
            scroll_bar.setValue(0)
        # Check for selected item
        selected_indexes = self.view.list_widget.selectedIndexes()
        if len(selected_indexes) == 0:
            # No selected items in list
            self.view.element_text_edit.setPlainText("")
        else:
            selected_items = self.view.list_widget.selectedItems()
            # This is a list, the selected item will be first
            list_widget_item = selected_items[0]
            # This will update the element_text_edit appropriately
            self.on_list_clicked(list_widget_item)
            # Then make sure that the selected item is visible
            self.view.list_widget.scrollToItem(
                list_widget_item, QAbstractItemView.PositionAtCenter)
        self.update_status_label()

    def update_status_label(self):
        """ Update the status label to reflect currently selected items"""
        # Get the current number of items that are being shown
        visible_count = 0
        total_count = 0
        combo_selection = self.view.filter_combo_box.currentText()
        filter_type = self.filter_dictionary[combo_selection]
        for i in range(self.view.list_widget.count()):
            list_item = self.view.list_widget.item(i)
            if not list_item.isHidden():
                visible_count += 1
            if (filter_type == GstListType.ALL) or (list_item.data(Qt.UserRole) == filter_type):
                total_count += 1

        if self.view.search_widget.text() == '':
            self.view.info_label.setText(f"{total_count} items")
        else:
            self.view.info_label.setText(
                f"{visible_count} of {total_count} items shown")

    def on_filter_text_changed(self, filter_text: str):
        """ The search box filters the list items by the given filter_text
        Obeys combo box setting:  plugins, elements, types, or all """
        combo_selection = self.view.filter_combo_box.currentText()
        filter_type = self.filter_dictionary[combo_selection]
        for i in range(self.view.list_widget.count()):
            list_item = self.view.list_widget.item(i)
            contains_flag = re.search(
                filter_text, list_item.text(), re.IGNORECASE)
            contains_flag = contains_flag is None
            # Obey the filter setting in the combo box too
            if (filter_type == GstListType.ALL) or (list_item.data(Qt.UserRole) == filter_type):
                list_item.setHidden(contains_flag)
            else:
                list_item.setHidden(True)
        self.sync_list_interface()

    def on_list_clicked(self, item: QListWidgetItem):
        """Clicked on plugin/element/type list widget"""
        # item type is the key into the dictionary
        item_type = item.text()
        if item.data(Qt.UserRole) == GstListType.PLUGIN:
            description_text = self.model.get_plugin_description(
                item_type)
        else:
            description_text = self.model.get_feature_description(
                item_type)
        self.view.element_text_edit.setPlainText(description_text)

    def on_filter_box_changed(self, value):
        # This is the same as filtering the list by the search term
        self.on_filter_text_changed(self.view.search_widget.text())
