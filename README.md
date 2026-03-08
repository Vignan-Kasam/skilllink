<h1 align="center">SkillLink</h1>
<p align="center">A platform that connects Clients and Skilled Workers for local service-based work opportunities.</p>

---

##  Tech Stack

### **Frontend**
| Technology | Usage |
|----------|-------|
| <img src="https://cdn.worldvectorlogo.com/logos/html-1.svg" width="24"> **HTML5** | Page structure |
| <img src="https://cdn.worldvectorlogo.com/logos/css-3.svg" width="24"> **CSS3** | UI Styling + Glassmorphism |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/javascript/javascript-original.svg" width="24"> **JavaScript** | Interactive UI |

### **Backend**
| Technology | Usage |
|----------|-------|
| <img src="https://cdn.worldvectorlogo.com/logos/flask.svg" width="28"> **Flask** | Backend Web Framework |
| <img src="https://www.python.org/static/opengraph-icon-200x200.png" width="26"> **Python 3** | Core Logic |

### **Database**
| Technology | Usage |
|----------|-------|
| <img src="https://cdn.worldvectorlogo.com/logos/sqlite.svg" width="28"> **SQLite** | Lightweight DB |
| **SQLAlchemy==2.1.0** | ORM – Models, Queries & Migrations |

---

##  Features

| Feature | Description |
|--------|-------------|
| User Login & Signup | Supports Client / Worker / Admin roles |
| Profile Dashboard | Profile image + Bio + Skills + Govt ID verification |
| Hire & Job System | Clients hire Workers; Workers find Jobs |
| Rating System | ⭐ Users rate each other after job completion |
| Private Chat | Real-time conversation feature |
| Admin Controls | Approve, Reject, Delete User Accounts |
| Modern UI | Video Background + Blur Glass UI |

---

## 📷 UI Highlights
✔ Glass UI  
✔ Smooth glowing buttons  
✔ Profile pictures centered  
✔ Clean rating UI  
✔ Background video hero styling

---

##  Folder Structure

```
SkillLink/
│
├── app.py
├── config.py
├── forms.py
├── models.py
├── utils.py
├── requirements.txt
│
├── static/
│   ├── videos/
|       └──skilllink_bg.mp4    
│   ├── profile_pics/
│   ├── govt_ids/
│   └── uploads/
│
├── instance/
│   └── database.db 
│  
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── profile_view.html
│   ├── edit_profile.html
│
│   ├── client_dashboard.html
│   ├── worker_dashboard.html
│   ├── admin_dashboard.html
│   ├── admin_users.html
│
│   ├── find_workers.html
│   ├── find_jobs.html
│   ├── job_post.html
│   ├── post_job.html
│
│   ├── applications.html
│   ├── chat.html
│   └── notifications.html
│
└── README.md
```
Note:-Pychache folder will be added after running
---

## 🛠️ Installation

```sh
git clone https://github.com/YOUR-USERNAME/SkillLink.git
```
```sh
cd SkillLink
```
```sh
python -m venv venv
```
```sh
venv\Scripts\activate
```
```sh
pip install -r requirements.txt
```
install these modules manually <b>if pip install -r requirements.txt is failed<b>
```sh
pip install Flask
pip install Werkzeug
pip install SQLAlchemy
pip install Flask-Login
pip install Flask-SQLAlchemy
pip install Flask-wtf
pip install Flask-form
pip install email_validator
```
```sh
python app.py
```
```sh
http://127.0.0.1:5000
```
## for Admin
Email
```sh
admin@skill.com
```
## admin password
```sh
admin123
```
___________________
| Team Work Pluse |
| --------------- |
| Harshith        |  
| Bindhu Reddy    |
| Harshitha       |
| Akshitha Reddy  |
| Chakradhar Reddy|
| Sai Koushik     |


 Project Status
 Completed  
 Planned Upgrades: Real-time chat (WebSockets) & Google Maps Worker Location

---

##  Show Support
If you like this project, please  the repository — it motivates us 

