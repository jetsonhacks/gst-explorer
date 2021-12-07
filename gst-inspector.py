#!/usr/bin/env python3
#
#  GStreamer Inspector
#
#  Copyright (C) 2021 JetsonHacks (info@jetsonhacks.com)
#
#  MIT License
#

import base64
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (QAction, QApplication,
                             QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
                             QListWidget, QMainWindow, QMenu,
                             QMenuBar, QSizePolicy, QSplitter, QTextEdit,
                             QVBoxLayout)
from gst_controller import Gst_Inspector_Controller

from gst_model import Gst_Inspector_Model


""" We use a Model, View, Controller pattern.
 Gst_Inspector_Model contains the data. The data is gathered from running gst-inspect-1.0
 Gst_Inspector_Controller is the controller which arbitrates between the model and the view """


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
        self.setGeometry(100, 100, Gst_Inspector_View.WINDOW_WIDTH,
                         Gst_Inspector_View.WINDOW_HEIGHT)
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
