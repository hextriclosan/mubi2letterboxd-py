import csv
import sys
from datetime import datetime

import requests
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Widget(QWidget):
    URL = "https://mubi.com/services/api/ratings"
    RECORDS_PER_PAGE = "100"

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("User data migration from MUBI.com to letterboxd.com")

        self.user_id = QLineEdit()
        self.user_id.setPlaceholderText("MUBI UserID")
        self.user_id.textChanged[str].connect(self.on_changed)

        self.go_button = QPushButton("Create CSV")
        self.go_button.clicked.connect(self.download_data)
        self.enable_button(False)

        self.controls_layout = QHBoxLayout()
        self.controls_layout.addWidget(self.user_id)
        self.controls_layout.addWidget(self.go_button)

        self.label = QLabel()
        self.set_label_text("Input MUBI UserID and chose CSV-file name and location")

        self.layout = QVBoxLayout(self)
        self.layout.addLayout(self.controls_layout)
        self.layout.addWidget(self.label)

    def on_changed(self, text: str) -> None:
        is_enabled = len(text) > 0
        self.enable_button(is_enabled)

    def enable_button(self, enabled: bool) -> None:
        self.go_button.setEnabled(enabled)

    def set_label_text(self, text: str) -> None:
        self.label.setText(text)

    def download_data(self) -> None:
        try:
            filename, _ = QFileDialog.getSaveFileName(self, caption="Save CSV file", filter="CSV Files (*.csv)")
            if not filename:
                return

            self.enable_button(False)

            params = {"user_id": self.user_id.text(), "per_page": self.RECORDS_PER_PAGE}
            csv_rows = []
            i = 0
            while True:
                QCoreApplication.processEvents()
                i += 1
                params["page"] = str(i)

                response = requests.get(self.URL, params=params)
                json_response = response.json()
                if not json_response:
                    break

                for record in json_response:
                    row = self.generate_csv_row(record)
                    csv_rows.append(row)

                self.set_label_text(f"{len(csv_rows)} records downloaded")

            self.save_csv_file(csv_rows, filename)

            self.set_label_text(f"{len(csv_rows)} records downloaded and saved as {filename}")

        except Exception as e:
            QMessageBox.warning(self, "", "Error occurred: {}".format(str(e)))

        self.enable_button(True)

    @staticmethod
    def save_csv_file(csv_rows, filename):
        with open(filename, mode="w") as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=",", quotechar='"')
            csv_writer.writerow(["tmdbID", "Title", "Year", "Directors", "Rating", "WatchedDate", "Review"])
            csv_writer.writerows(csv_rows)

    @staticmethod
    def generate_csv_row(record: list) -> list:
        record_id = str(record["id"])
        title = record["film"]["title"]
        year = str(record["film"]["year"])
        directors = ", ".join([director["name"] for director in record["film"]["directors"]])
        rating = str(record["overall"])
        time = datetime.utcfromtimestamp(record["updated_at"]).strftime("%Y-%m-%d")
        review = record["body"]

        return [record_id, title, year, directors, rating, time, review]


if __name__ == "__main__":
    app = QApplication([])

    widget = Widget()
    widget.resize(500, 80)
    widget.show()

    sys.exit(app.exec())
