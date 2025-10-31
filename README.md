# 📊 Dashboard

Web application developed in **Flask** for uploading, storing, and visualizing data through an interactive panel.  
The system allows importing files, processing information with **pandas**, and displaying results via a **dashboard** with metrics and dynamic charts.

---

## 🚀 Main Features

- Web interface based on **Flask** with views organized using HTML templates.
- File upload and data processing with **pandas**.
- Data persistence using **SQLAlchemy**.
- Clear separation of layers:
  - **Models:** Definition of models and database connection.
  - **Services:** Business logic and data processing.
  - **Routes:** Application routes and Flask controllers.
  - **Templates / Static:** HTML views and static resources.
- Modular structure, ideal for scaling or integrating new features (reports, authentication, etc.).

---

## 🧩 Project Structure

```bash
/project
├── [app.py](http://_vscodecontentref_/0)             # Main entry point of the application
├── [config.py](http://_vscodecontentref_/1)          # General configuration (routes, database, etc.)
├── /models/                                          # Models and database connection
│   └── [models.py](http://_vscodecontentref_/2)
├── /services/                                        # Business logic and data processing
├── /routes/                                          # Flask routes and controllers
├── /templates/                                       # HTML files (views)
│   ├── [base.html](http://_vscodecontentref_/3)
│   ├── [login.html](http://_vscodecontentref_/4)
│   └── [dashboard.html](http://_vscodecontentref_/5)
├── /static/                                          # Static files (CSS, JS, images, uploads)
│   └── /uploads/
└── [requirements.txt](http://_vscodecontentref_/6)   # Project dependencies
```

## ⚙️ Installation and Execution

Follow these steps to run the project locally:

Clone the repository:

```bash
git clone https://github.com/GariboGE/Tablero.git
cd Tablero
```

Create and activate a virtual environment:

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

On macOS / Linux:

```bash
python3 -m venv .venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
flask run
```

The application will be available at:

### 👉 http://127.0.0.1:5000

## 🧠 Technologies Used

Python 3.10+
Flask
Pandas
SQLAlchemy
Jinja2

## 📁 Upcoming Improvements

Handle real-time data.
Better interactive charts.
Export reports in various formats.
Add data analitycs stats.
Add filters and summary view

## 📜 License

To be defined.

## 🧑‍💻 Author

Developed by Eric Garibo
Project in development — initial version of the Dashboard.
