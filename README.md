# To-Do List App with Flask

**To-Do List App** is a web application developed with Flask that allows users to manage their daily tasks easily. It offers features like user registration, priority assignment, and attaching images to tasks.

## 🚀 Features

- **User Authentication**: Register and log in through the app or OAuth.
- **Task Management**:
  - Create, edit, and delete tasks.
  - Assign priorities: `low`, `medium`, `high`, `urgent`.
  - Attach images to tasks.
- **Integration with CheapShark**: Displays discounts on games with excellent ratings on the dashboard.

  
---

## 🛠️ Installation and Setup

### Prerequisites

- **Python** 3.8 or higher.
- **Git** installed on your system.
- A virtual environment to manage dependencies.

### Installation Steps

1. **Clone this repository**:
   ```bash
   git clone https://github.com/GariboGE/to_do_list_gariboge.git
   cd to_do_list_gariboge

2. **Create and activate a virtual environment:**:

   - On **Windows**:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```

   - On **macOS/Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

4. **Install the dependencies:**:
   ```bash
   pip install -r requirements.txt

5. **Configure the environment variables:**
   - Rename the `.env.example` file to `.env`:
   - Edit the `.env` file and provide the required values:
   - Ensure to replace placeholders like `your_secret_key_here` with your actual values.

6. **Start the app**:
   ```bash
   flask run

The application will be available at http://127.0.0.1:5000.

---

## 🧪 Test
- Make sure that the dependencies are installed and the virtual environment is active.

- Generate a `pytest.ini` file to add initial settings such as generating automatic reports 
   ```bash
      [pytest]
      addopts = --cov=app --cov=services/ --cov=routes/ --cov=forms/ --cov=models/ --cov-report=html --cov-report=term-missing

- Run the tests with:
   ```bash
   pytest
- This will generate an HTML and console report with the project coverage.

---

## Documentation
-  You can view the documentation by following the commands below:
    ```bash
    cd mkdocs
    mkdocs serve

The documentation will be available at http://127.0.0.1:8000.
