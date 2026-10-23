# 📚 University Library Management System

A functional web-based University Library Management System built with Python, Flask, and SQLite3 on Termux. 

## 🚀 Features Incorporated
* **Role-Based Access Control (RBAC):** Separate interfaces for Admin, Librarian, and Student roles.
* **Barcode & QR Code Integration:** Uses phone camera streaming via `Html5-Qrcode` to scan book ISBN values on the go.
* **Fine Calculation System:** Automatic calculation of overdue returns charged at 5 Birr/day.
* **Advanced Live Search:** Dynamic filtering of books by Title, Author, Genre, or ISBN.
* **Analytics Dashboard:** Interactive charts powered by `Chart.js` tracking catalog metrics and active borrows.

## 🛠️ Technology Stack
* **Backend:** Python 3, Flask, Flask-SQLAlchemy
* **Frontend:** Offline HTML5 Custom Blueprint CSS Layouts
* **Scanning & Charts:** JavaScript (Html5-Qrcode, Chart.js)
* **Environment:** Built and run natively on Android using **Termux** & **Acode**

## 📦 How to Run Locally
1. Clone the repository or download the files.
2. Open Termux and map permissions:
   ```bash
   termux-setup-storage
   cd /sdcard/Download/university_library
   ```
3. Install dependencies:
   ```bash
   pip install flask flask_sqlalchemy werkzeug
   ```
4. Fire up the backend engine:
   ```bash
   python app.py
   ```
5. Open your web browser and visit: `http://127.0.0.1:5000`
