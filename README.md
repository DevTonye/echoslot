# EchoSlot — Appointment Scheduling App

**EchoSlot** is a full-stack appointment scheduling application designed to help users book, view, and manage appointments with service providers. It includes user authentication, role support (clients & providers), and dynamic scheduling features.

## 🚀 Features

✔ User authentication (sign up, login)  
✔ Role-based access (clients & service providers)  
✔ Create, view, update, and delete appointments  
✔ Dynamic schedule management  
✔ Built with a robust backend and interactive frontend

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, Django |
| Frontend | HTML, CSS, HTMX |
| Database | MySQL |

## 📦 Installation

### Prerequisites
- Python 3.8+
- MySQL
- pip (Python package manager)

### 1. Clone the repository
```bash
git clone https://github.com/tobintonye/echoslot.git
cd echoslot
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure the database
Create a MySQL database and update the `DATABASES` configuration in `settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'echoslot_db',
        'USER': 'your_mysql_user',
        'PASSWORD': 'your_mysql_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 5. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a superuser (optional)
```bash
python manage.py createsuperuser
```

### 7. Start the development server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

## 📂 Project Structure
```
echoslot/
├── accounts/               # User authentication app
├── serviceapp/             # Main scheduling app
├── static/                 # Static files (CSS/JS)
├── templates/              # HTML templates
├── manage.py               # Django entry point
├── requirements.txt        # Python dependencies
└── README.md
```

## 🧪 Usage

1. **Sign up** as a client or service provider
2. **Login** to your account
3. **Clients** can view and book available time slots
4. **Providers** can manage their availability and appointments

## 🔐 Environment Variables

Create a `.env` file in the root directory:
```env
SECRET_KEY=your_secret_key_here
DEBUG=True
DATABASE_NAME=db_name
DATABASE_USER=your_mysql_user
DATABASE_PASSWORD=your_mysql_password
```

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repo
2. Create a branch (`git checkout -b feature/xyz`)
3. Commit your changes (`git commit -m 'Add feature xyz'`)
4. Push to the branch (`git push origin feature/xyz`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Tobin Tonye**  
GitHub: [@tobintonye](https://github.com/tobintonye)

## 🙏 Acknowledgments

- Django documentation
- HTMX for dynamic interactions
- MySQL for database management
