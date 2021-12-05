#!/usr/bin/env python3
#
#  GStreamer Insperctor
#
#  Copyright (C) 2021 JetsonHacks (info@jetsonhacks.com)
#
#  MIT License
#

import base64
import re
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (QAbstractItemView, QAction, QApplication,
                             QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
                             QListWidget, QListWidgetItem, QMainWindow, QMenu,
                             QMenuBar, QSizePolicy, QSplitter, QTextEdit,
                             QVBoxLayout)

from gstinspectormodel import Gst_Inspector_Model, GstListType

""" We use a Model, View, Controller pattern.
 Gst_Inspector_Model contains the data. The data is gathered from running gst-inspect-1.0
 Gst_Inspector_Controller is the controller which arbitrates """


class Gst_Inspector_Controller():
    def __init__(self, model, view):
        self.model = model
        self.view = view
        # filter_dictionary is a map from the GUI combo box string values to the GstListType
        self.filter_dictionary = {"Plugins": GstListType.plugin_type,
                                  "Elements": GstListType.element_type,
                                  "Types": GstListType.type_finder_type,
                                  "All": GstListType.all_types}

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

    def populate_list_widget(self, view, model):
        # Three lists: plugins, elements, and types
        # We place them all in the list widget, and associate the type for each item
        icon = view.get_plugin_icon()
        plugin_dictionary = model.plugin_dictionary
        for key in plugin_dictionary.keys():
            self.view.add_list_item(key, GstListType.plugin_type, icon, None)

        element_dictionary = model.element_dictionary
        for key in element_dictionary.keys():
            element_value = element_dictionary[key]
            tooltip = element_value[0].element_description
            self.view.add_list_item(
                key, GstListType.element_type, None, tooltip)

        types_dictionary = model.types_dictionary
        for key in types_dictionary.keys():
            element_value = types_dictionary[key]
            tooltip = element_value[0].element_description
            self.view.add_list_item(
                key, GstListType.type_finder_type, None, tooltip)

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
            if (filter_type == GstListType.all_types) or (list_item.data(Qt.UserRole) == filter_type):
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
            if (filter_type == GstListType.all_types) or (list_item.data(Qt.UserRole) == filter_type):
                list_item.setHidden(contains_flag)
            else:
                list_item.setHidden(True)
        self.sync_list_interface()

    def on_list_clicked(self, item: QListWidgetItem):
        """Clicked on plugin/element/type list widget"""
        # item type is the key into the dictionary
        item_type = item.text()
        if item.data(Qt.UserRole) == GstListType.plugin_type:
            description_text = self.model.get_plugin_description_text(
                item_type)
        else:
            description_text = self.model.get_element_description_text(
                item_type)
        self.view.element_text_edit.setPlainText(description_text)

    def on_filter_box_changed(self, value):
        # This is the same as filtering the list by the search term
        self.on_filter_text_changed(self.view.search_widget.text())


class Gst_Inspector_View(QMainWindow):

    LIST_WIDTH = 280
    WINDOW_WIDTH = 960
    WINDOW_HEIGHT = 540

    def setup(self, controller):
        """ Initialize the main parts of the UI. These are two frames placed in a horizontal splitter."""

        # The Left frame is the list of plugins, elements and types.
        left_frame = self.setup_left_frame(controller)
        # The right frame is a text frame which displays the detailed info of the above.
        right_frame = self.setup_right_frame(controller)

        # Make up the horizontal splitter, then add the left and right frames
        horizontal_splitter = QSplitter(Qt.Horizontal)
        horizontal_splitter.addWidget(left_frame)
        horizontal_splitter.addWidget(right_frame)
        horizontal_splitter.setChildrenCollapsible(False)
        # With point size 12, the list widget should be large enough to
        # avoid a horizontal scroller.
        horizontal_splitter.setSizes(
            [Gst_Inspector_View.LIST_WIDTH, Gst_Inspector_View.WINDOW_WIDTH-Gst_Inspector_View.LIST_WIDTH])
        # Add the splitter to the main window
        self.setCentralWidget(horizontal_splitter)

        # Set the font of the window a little larger; 12 point
        qfont = self.font()
        qfont.setPointSize(12)
        self.setFont(qfont)
        # Initial layout window size
        self.setGeometry(100, 100, Gst_Inspector_View.WINDOW_WIDTH, Gst_Inspector_View.WINDOW_HEIGHT)
        self.setWindowTitle('GStreamer Inspector')
        self.setup_menu_bar()

    def setup_left_frame(self, controller: Gst_Inspector_Controller):
        """ The Left frame contains the list of plugins, elements and types.
            There is a list, a search box and a combo box which select the type of element """
        left_frame = QFrame()
        left_vbox = QVBoxLayout()
        left_frame.setLayout(left_vbox)

        # Create the text filter box
        # Note: We should be able to add a Completer here also
        self.search_widget = QLineEdit()
        self.search_widget.setClearButtonEnabled(True)
        self.search_widget.setPlaceholderText("Search")
        self.search_widget.textChanged.connect(
            controller.on_filter_text_changed)
        left_vbox.addWidget(self.search_widget)

        # Gst type of element filter
        # Combo box that selects the type of Gst element to be examined
        filter_box = QHBoxLayout()
        filter_label = QLabel("Filter")
        filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        filter_box.addWidget(filter_label)
        self.filter_combo_box = QComboBox(self)
        self.filter_combo_box.addItems(["All", "Plugins", "Elements", "Types"])
        self.filter_combo_box.currentTextChanged.connect(
            controller.on_filter_box_changed)
        filter_box.addWidget(self.filter_combo_box)
        left_vbox.addLayout(filter_box)

        # The list of plugins, elements and types
        self.list_widget = QListWidget()
        self.list_widget.setSortingEnabled(True)
        self.list_widget.setMinimumWidth(280)
        self.list_widget.itemClicked.connect(controller.on_list_clicked)
        left_vbox.addWidget(self.list_widget)

        # A label that displays the number of items being displayed
        self.info_label = QLabel("")
        left_vbox.addWidget(self.info_label)
        return left_frame

    def setup_right_frame(self, controller):
        """ The right frame is a text display which displays
            detailed info about the plugin, element or type """
        right_frame = QFrame()
        right_vbox = QVBoxLayout()
        right_frame.setLayout(right_vbox)

        self.element_text_edit = QTextEdit()
        # Use the default Terminal font
        # This is a monospaced font, also called fixed-pitch or fixed-width
        # Fixed width characters are used so that the columns 'line up' in the text
        self.element_text_edit.setFontFamily('Monospace')
        self.element_text_edit.setFontPointSize(11)
        self.element_text_edit.setReadOnly(True)
        right_vbox.addWidget(self.element_text_edit)
        return right_frame

    # For demonstration purposes, we introduce the Google "baseline_list_alt_black_24dp.png" directly
    # into the Python script as a binary string. This is so we don't have to depend on the file being present.

    def get_plugin_icon(self):
        """ Return an icon with the Google 'baseline_list_alt_black_24dp.png' as its image """
        encoded_list_png = b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAQAAABKfvVzAAAANElEQVQ4y2NgGLTgEMN/AnAfqob/REAMDfgA9TQg08hOoZ6GUT+MBD+QlLz3E1S+e9BmfgD6da5PGPX1WQAAAABJRU5ErkJggg=='
        decoded_list_png = base64.b64decode(encoded_list_png)
        pix_map = QPixmap()
        pix_map.loadFromData(decoded_list_png)
        icon = QIcon(pix_map)
        return icon

    def add_list_item(self, key: str, type: GstListType, icon: QIcon, tooltip: str):
        if icon == None:
            list_widget = QListWidgetItem(key)
        else:
            list_widget = QListWidgetItem(icon, key)
        list_widget.setData(Qt.UserRole, type)
        if tooltip is not None:
            list_widget.setToolTip(tooltip)
        self.list_widget.addItem(list_widget)

    def setup_menu_bar(self):
        """ Mostly here as a placeholder """
        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)
        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)
        fileMenu.addSeparator()
        self.exitAction = QAction("&Exit", self)
        fileMenu.addAction(self.exitAction)
        # This closes the window, then exits the program
        self.exitAction.triggered.connect(self.close)


def main():
    app = QApplication(sys.argv)
    controller = Gst_Inspector_Controller(
        Gst_Inspector_Model(), Gst_Inspector_View())
    controller.setup()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
