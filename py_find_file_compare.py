import sys
# from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QPushButton, QGridLayout, QLineEdit, QFileDialog,
                             QPlainTextEdit, QTreeWidget)  # QErrorMessage)
from file_find_compare import FileFindCompare

DEBUG = False


class PyFindFileCompare(QWidget):
    # widgets
    base_dir = None
    inp_file = None
    out_text = None
    btn_base_dir = None
    btn_inp_file = None
    btn_start = None
    tv_out = None
    _out_file = None

    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        layout.addWidget(QLabel(text='Basisordner: '), 0, 0)
        self.base_dir = QLineEdit()
        self.base_dir.setReadOnly(True)
        self.base_dir.setText('//fs1/Daten/Zeichnungen-Projekte')
        layout.addWidget(self.base_dir, 0, 1)
        self.btn_base_dir = QPushButton('Basisordner auswählen: ')
        layout.addWidget(self.btn_base_dir, 0, 2)
        self.btn_base_dir.clicked.connect(self.get_basedir)

        layout.addWidget(QLabel(text='Eingabedatei: '), 1, 0)
        self.inp_file = QLineEdit()
        self.inp_file.setReadOnly(True)
        self.inp_file.setText('//fs1/Daten/Zeichnungen-Projekte')
        layout.addWidget(self.inp_file, 1, 1)
        self.btn_inp_file = QPushButton('Eingabedatei auswählen')
        self.btn_inp_file.setDisabled(True)
        layout.addWidget(self.btn_inp_file, 1, 2)
        self.btn_inp_file.clicked.connect(self.get_inp_file)

        self.btn_start = QPushButton('Start')
        self.btn_start.setDisabled(True)
        layout.addWidget(self.btn_start, 2, 2)
        self.btn_start.clicked.connect(self.start_search)

        self.out_text = QPlainTextEdit()
        self.out_text.setReadOnly(True)
        layout.addWidget(self.out_text, 3, 0, 1, 3)

        self.tv_out = QTreeWidget()
        self.tv_out.hide()
        layout.addWidget(self.tv_out, 4, 0, 1, 3)

        self.setLayout(layout)
        self.setFixedWidth(900)
        self.setMinimumHeight(500)
        self.show()

    def get_basedir(self):
        bdir = str(QFileDialog.getExistingDirectory(self,
                                                    "Basisordner auswählen",
                                                    self.base_dir.text()
                                                    ))
        if bdir:
            self.base_dir.setText(bdir)
            # we got a valid input path so enable the input file button
            self.btn_inp_file.setDisabled(False)
            if DEBUG:
                self.out_text.appendPlainText('got base dir: %s' % self.base_dir.text())
            if self.inp_file.text() != '':
                self.inp_file.setText(self.base_dir.text())

    def get_inp_file(self):
        # stop the user from changing the base dir to avoid weird issues
        # TODO: make it more user friendly later
        self.btn_base_dir.setDisabled(True)
        infile = str(QFileDialog.getOpenFileName(self,
                                                "Eingabedatei auswählen",
                                                self.inp_file.text(),
                                                '*.txt'
                                                )[0]
                     )
        if infile:
            if infile.find(self.base_dir.text()) != 0:
                self.out_text.appendPlainText('Fehler: Die Eingabedatei muß im Basisverzeichnis oder unterordner liegen!')
                return
            else:
                self.btn_start.setDisabled(False)
            self.inp_file.setText(infile)
            self._out_file = self.inp_file.text().replace('.txt', '_output.txt')
            if DEBUG:
                self.out_text.appendPlainText('got input file: %s' % self.inp_file.text())
                self.out_text.appendPlainText('output filename: %s' % self._out_file)

    def start_search(self):
        # just to be save disable both other buttons
        self.btn_inp_file.setDisabled(True)
        self.btn_inp_file.setDisabled(True)

        ffc = FileFindCompare(self.inp_file.text(), self._out_file, self.base_dir.text())
        self.out_text.appendPlainText('Liste der Dateien: %s' % self.inp_file.text())
        self.out_text.appendPlainText('Basisordner: %s' % self.base_dir.text())
        ffc.find_compare()
        self.out_text.appendPlainText('Ausgabe wird gespeichert als %s' % self._out_file)

        self.out_text.appendPlainText('Ausgabe als text:')
        self.out_text.appendPlainText(ffc.generate_output())

        ffc.save_output()

    def populate_tv(self):
        # TODO: populate the treeview
        self.tv_out.show()


if __name__ == '__main__':
    app = QApplication([])
    win = PyFindFileCompare()
    sys.exit(app.exec_())

