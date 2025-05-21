import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import sqlite3
import csv
import os

class BookManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manajemen Buku")
        self.setGeometry(100, 100, 600, 400)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        form_layout = QHBoxLayout()
        labels = ["Judul:", "Pengarang:", "Tahun:"]
        self.inputs = {}
        for label_text in labels:
            hbox = QHBoxLayout()
            label = QLabel(label_text)
            input_field = QLineEdit()
            self.inputs[label_text[:-1]] = input_field
            hbox.addWidget(label)
            hbox.addWidget(input_field)
            form_layout.addLayout(hbox)
        
        self.save_button = QPushButton("Simpan")
        self.save_button.clicked.connect(self.save_data)
        form_layout.addWidget(self.save_button)
        layout.addLayout(form_layout)

        search_layout = QHBoxLayout()
        search_label = QLabel("Cari judul...")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.search_data)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Judul", "Pengarang", "Tahun"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellDoubleClicked.connect(self.edit_data)
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        self.delete_button = QPushButton("Hapus Data")
        self.delete_button.clicked.connect(self.delete_data)
        self.export_button = QPushButton("Ekspor Data")
        self.export_button.clicked.connect(self.export_to_csv)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.export_button)
        layout.addLayout(button_layout)


        self.setup_database()
        self.load_data()

    def setup_database(self):
        self.conn = sqlite3.connect("books.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS books
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               judul TEXT,
                               pengarang TEXT,
                               tahun INTEGER)''')
        self.conn.commit()

    def load_data(self):
        self.cursor.execute("SELECT * FROM books")
        rows = self.cursor.fetchall()
        self.table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, cell in enumerate(row):
                item = QTableWidgetItem(str(cell))
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeColumnsToContents()

    def save_data(self):
        judul = self.inputs["Judul"].text()
        pengarang = self.inputs["Pengarang"].text()
        tahun = self.inputs["Tahun"].text()
        if judul and pengarang and tahun:
            self.cursor.execute("INSERT INTO books (judul, pengarang, tahun) VALUES (?, ?, ?)",
                              (judul, pengarang, int(tahun)))
            self.conn.commit()
            self.inputs["Judul"].clear()
            self.inputs["Pengarang"].clear()
            self.inputs["Tahun"].clear()
            self.load_data()

    def search_data(self):
        search_text = self.search_input.text().lower()
        self.cursor.execute("SELECT * FROM books")
        rows = self.cursor.fetchall()
        self.table.setRowCount(0)
        for row in rows:
            if search_text in row[1].lower():
                row_pos = self.table.rowCount()
                self.table.insertRow(row_pos)
                for col_idx, cell in enumerate(row):
                    item = QTableWidgetItem(str(cell))
                    self.table.setItem(row_pos, col_idx, item)
        self.table.resizeColumnsToContents()

    def edit_data(self, row, col):
        if col == 0: return  # Prevent editing ID
        item = self.table.item(row, col)
        if item:
            text, ok = QInputDialog.getText(self, "Edit", self.table.horizontalHeaderItem(col).text(),
                                          QLineEdit.Normal, item.text())
            if ok and text:
                id_val = int(self.table.item(row, 0).text())
                if col == 1:
                    self.cursor.execute("UPDATE books SET judul = ? WHERE id = ?", (text, id_val))
                elif col == 2:
                    self.cursor.execute("UPDATE books SET pengarang = ? WHERE id = ?", (text, id_val))
                elif col == 3:
                    self.cursor.execute("UPDATE books SET tahun = ? WHERE id = ?", (int(text), id_val))
                self.conn.commit()
                self.load_data()

    def delete_data(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Peringatan", "Pilih data yang ingin dihapus terlebih dahulu!")
            return
        
        judul = self.table.item(selected_row, 1).text()
        reply = QMessageBox.question(self, "Konfirmasi Hapus", 
                                   f"Apakah Anda yakin ingin menghapus data '{judul}'?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            id_val = int(self.table.item(selected_row, 0).text())
            self.cursor.execute("DELETE FROM books WHERE id = ?", (id_val,))
            self.conn.commit()
            self.load_data()

    def export_to_csv(self):
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Simpan File CSV", "books.csv", "CSV Files (*.csv)")
        
        if file_path:  
            try:
                with open(file_path, "w", newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["ID", "Judul", "Pengarang", "Tahun"])
                    self.cursor.execute("SELECT * FROM books")
                    writer.writerows(self.cursor.fetchall())
                
                QMessageBox.information(self, "Ekspor Berhasil", 
                                      f"Data berhasil diekspor ke:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Ekspor Gagal", f"Terjadi kesalahan saat mengekspor: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BookManager()
    window.show()
    sys.exit(app.exec_())