from flask import Flask, render_template, redirect, request, flash, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegisterForm
from utils import create_notification, add_rating, is_hired
import os
from werkzeug.utils import secure_filename
from models import db, User, Job, Application, Message, Rating, Notification, Hire


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "skilllink_secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['UPLOAD_FOLDER'] = 'static/govt_ids'
app.config['PROFILE_PIC_FOLDER'] = 'static/profile_pics'
os.makedirs(app.config['PROFILE_PIC_FOLDER'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ----------- INITIAL SETUP -----------
with app.app_context():
    db.create_all()
    if not User.query.filter_by(role="admin").first():
        admin = User(
            role="admin", name="Admin", email="admin@skill.com",
            password=generate_password_hash("admin123"),
            aadhar="000000000000",
            is_approved=True
        )
        db.session.add(admin)
        db.session.commit()


# ----------- AUTH -----------
@app.route('/')
def index():
    form = LoginForm()
    return render_template('index.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in → go to correct dashboard
    if current_user.is_authenticated:
        if current_user.role == "client":
            return redirect(url_for('client_dashboard'))
        elif current_user.role == "worker":
            return redirect(url_for('find_jobs'))
        else:
            return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            # ✅ Redirect according to role
            if user.role == "client":
                return redirect(url_for('client_dashboard'))
            elif user.role == "worker":
                return redirect(url_for('find_jobs'))
            else:
                return redirect(url_for('admin_dashboard'))

        else:
            flash("Invalid Email or Password", "danger")
            return redirect(url_for('login'))

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("⚠️ Email already exists. Try another one.", "warning")
            return redirect(url_for("register"))

        role = form.role.data
        govt_id_image_file = form.govt_id_image.data

        filename = None
        if govt_id_image_file:
            # Create safe unique filename
            filename = f"{form.name.data}_{form.aadhar.data}_{secure_filename(govt_id_image_file.filename)}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            govt_id_image_file.save(save_path)

        # Create user object
        user = User(
            name=form.name.data,
            email=form.email.data,
            aadhar=form.aadhar.data,
            role=role,
            skills=form.skills.data if role == "worker" else None,
            govt_id_image=filename,
            is_approved=False,  # Admin must approve
            profile_image="default.png"
        )

        # Hash password
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("✅ Account created successfully! Wait for admin approval.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ----------- CLIENT -----------
@app.route('/client/dashboard')
@login_required
def client_dashboard():
    if current_user.role != 'client':
        return redirect('/')

    jobs = Job.query.filter_by(client_id=current_user.id).all()
    workers = User.query.filter_by(role='worker', is_approved=True).all()
    hires = Hire.query.filter_by(client_id=current_user.id, status='hired').all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    return render_template(
        'client_dashboard.html',
        jobs=jobs,
        workers=workers,
        hires=hires,
        unread_count=unread_count
    )


@app.route('/client/post_job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != 'client': return redirect('/')

    if request.method == 'POST':
        job = Job(title=request.form['title'], description=request.form['description'], client_id=current_user.id)
        db.session.add(job)
        db.session.commit()

        workers = User.query.filter_by(role='worker', is_approved=True).all()
        for w in workers:
            create_notification(w.id, f"New Job: {job.title}")

        flash("Job Posted Successfully!")
        return redirect(url_for('client_dashboard'))

    return render_template('post_job.html')

@app.route('/find_workers', methods=['GET'])
@login_required
def find_workers():
    if current_user.role != 'client':
        return redirect('/')

    skill = request.args.get('skill', '')
    location = request.args.get('location', '')

    workers = User.query.filter(User.role == 'worker', User.is_approved == True)

    if skill:
        workers = workers.filter(User.skills.ilike(f"%{skill}%"))

    if location:
        workers = workers.filter(User.location.ilike(f"%{location}%"))

    workers = workers.all()

    return render_template("find_workers.html", workers=workers, skill=skill, location=location)

# ----------- HIRE FUNCTION (single, final) -----------
@app.route('/hire/<int:worker_id>/<int:job_id>')
@login_required
def hire_worker(worker_id, job_id):

    if current_user.role != 'client':
        flash("Only clients can hire workers.", "error")
        return redirect('/')

    worker = User.query.get_or_404(worker_id)
    job = Job.query.get_or_404(job_id)

    # Ensure job belongs to the client
    if job.client_id != current_user.id:
        flash("You cannot hire for jobs you did not post.", "error")
        return redirect('/')

    application = Application.query.filter_by(worker_id=worker.id, job_id=job.id).first()

    if not application:
        application = Application(worker_id=worker.id, job_id=job.id, status="hired")
        db.session.add(application)
    else:
        application.status = "hired"

    job.is_open = False
    db.session.commit()

    # ✅ Send notification to worker
    new_notify = Notification(user_id=worker.id, message=f"You were hired for job: {job.title}")
    db.session.add(new_notify)
    db.session.commit()

    flash("✅ Worker Hired Successfully & Notified!", "success")
    return redirect(url_for('client_dashboard'))

@app.route('/hire/<int:worker_id>')
@login_required
def hire_select_job(worker_id):
    if current_user.role != 'client':
        flash("Only clients can hire workers.", "error")
        return redirect('/')

    worker = User.query.get_or_404(worker_id)
    jobs = Job.query.filter_by(client_id=current_user.id, is_open=True).all()

    return render_template("hire_select_job.html", worker=worker, jobs=jobs)


# ----------- WORKER -----------
@app.route('/worker/dashboard')
@login_required
def worker_dashboard():
    if current_user.role != 'worker':
        return redirect('/')

    hired_clients = (
        db.session.query(User, Job)
        .join(Job, Job.client_id == User.id)
        .join(Application, Application.job_id == Job.id)
        .filter(Application.worker_id == current_user.id, Application.status == "hired")
        .all()
    )

    return render_template(
        'worker_dashboard.html',
        hired_clients=hired_clients
    )


@app.route('/workers')
@login_required
def workers():
    all_workers = User.query.filter_by(role='worker', is_approved=True).all()
    return render_template("workers.html", workers=all_workers)


@app.route('/workers')
@login_required
def worker_list():
    # render the template you have (worker_card.html)
    workers = User.query.filter_by(role="worker", is_approved=True).all()
    jobs = Job.query.filter_by(client_id=current_user.id).all() if current_user.role == "client" else []
    return render_template("worker_card.html", workers=workers, jobs=jobs)

@app.route('/find_jobs')
@login_required
def find_jobs():
    if current_user.role != 'worker':
        return redirect('/')

    search = request.args.get('search', "").strip()
    location = request.args.get('location', "").strip()

    # ✅ Base query
    jobs_query = Job.query.filter(Job.is_open == True)

    # ✅ Apply search filter (title or description)
    if search:
        jobs_query = jobs_query.filter(
            (Job.title.ilike(f"%{search}%")) |
            (Job.description.ilike(f"%{search}%"))
        )

    # ✅ Apply location filter
    if location:
        jobs_query = jobs_query.filter(Job.location.ilike(f"%{location}%"))

    jobs = jobs_query.all()

    # ✅ Get job IDs the current worker already applied to
    applied_job_ids = [
        app.job_id for app in Application.query.filter_by(worker_id=current_user.id).all()
    ]

    return render_template("find_jobs.html",
                           jobs=jobs,
                           search=search,
                           location=location,
                           applied_job_ids=applied_job_ids)

# ----------- PROFILE UPDATE -----------
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    current_user.name = request.form.get("name")
    current_user.bio = request.form.get("bio")

    if current_user.role == "worker":
        current_user.skills = request.form.get("skills")

    # Handle Profile Image Upload
    file = request.files.get("profile_image")
    if file and file.filename != "":
        filename = f"user_{current_user.id}.png"
        upload_path = os.path.join("static/uploads", filename)
        file.save(upload_path)
        current_user.profile_image = filename

    db.session.commit()
    flash("Profile Updated Successfully!")
    return redirect(url_for('profile'))

@app.route('/profile/<int:user_id>')
@login_required
def profile_view(user_id):
    user = User.query.get_or_404(user_id)
    # get reviews / ratings
    reviews = Rating.query.filter_by(recipient_id=user_id).order_by(Rating.created_at.desc()).all()

    # If current user has already rated this user for a job, you might want to prevent duplicate — optional
    existing_rating = None
    if current_user.is_authenticated:
        existing_rating = Rating.query.filter_by(recipient_id=user_id, author_id=current_user.id).first()

    return render_template('profile_view.html', user=user, reviews=reviews, existing_rating=existing_rating)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == "POST":
        current_user.name = request.form['name']
        current_user.skills = request.form.get('skills')
        current_user.bio = request.form.get('bio')

        # ✅ PROFILE IMAGE UPLOAD
        if 'profile_image' in request.files:
            pfile = request.files['profile_image']
            if pfile and pfile.filename != "":
                filename = secure_filename(pfile.filename)
                save_path = os.path.join(app.config['PROFILE_PIC_FOLDER'], filename)
                pfile.save(save_path)
                current_user.profile_image = filename   # ✅ Save filename to DB

        # ✅ GOVT ID UPLOAD
        if 'govt_id_image' in request.files:
            gfile = request.files['govt_id_image']
            if gfile and gfile.filename != "":
                filename2 = secure_filename(gfile.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename2)
                gfile.save(path)
                current_user.govt_id_image = filename2

        db.session.commit()
        return redirect(url_for('profile_view', user_id=current_user.id))

    return render_template("edit_profile.html")

# ----------- RATING SYSTEM -----------
@app.route('/rate_user/<int:user_id>', methods=['POST'])
@login_required
def rate_user(user_id):
    recipient = User.query.get_or_404(user_id)

    # who is rating
    author = current_user

    # parse form
    try:
        score = int(request.form.get('rating', 0))
    except (TypeError, ValueError):
        score = 0

    comment = request.form.get('review', '').strip()
    job_id = request.form.get('job_id') or None
    if job_id:
        try:
            job_id = int(job_id)
        except ValueError:
            job_id = None

    if score < 1 or score > 5:
        flash("Please select a rating between 1 and 5.", "warning")
        return redirect(url_for('profile_view', user_id=user_id))

    # Optional: prevent duplicate rating from same author - comment out if you allow multiple
    existing = Rating.query.filter_by(recipient_id=user_id, author_id=author.id, job_id=job_id).first()
    if existing:
        # update existing
        existing.score = score
        existing.comment = comment
        existing.created_at = datetime.utcnow()
    else:
        new_rating = Rating(recipient_id=user_id, author_id=author.id, job_id=job_id, score=score, comment=comment)
        db.session.add(new_rating)

    # create notification for recipient
    notif = Notification(user_id=user_id, message=f"You received a {score}-star rating from {author.name}")
    db.session.add(notif)

    db.session.commit()
    flash("Rating submitted. Thank you!", "success")
    return redirect(url_for('profile_view', user_id=user_id))
    # ----------- APPLY (AJAX-aware) -----------
@app.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    if current_user.role != 'worker':
        return "FORBIDDEN", 403

    job = Job.query.get_or_404(job_id)

    # ✅ Check if already applied
    existing = Application.query.filter_by(
        job_id=job_id, 
        worker_id=current_user.id
    ).first()

    if existing:
        return "ALREADY"

    # ✅ Create application
    application = Application(
        job_id=job_id,
        worker_id=current_user.id,
        client_id=job.client_id,  # client_id correctly assigned
        status="applied"
    )
    db.session.add(application)

    # ✅ Notify client
    notif = Notification(
        user_id=job.client_id,
        message=f"{current_user.name} applied for your job: {job.title}"
    )
    db.session.add(notif)

    db.session.commit()

    return "OK"

@app.route('/applications')
@login_required
def view_applications():
    if current_user.role != 'client':
        return redirect('/')

    applications = Application.query.filter_by(client_id=current_user.id).all()
    return render_template("applications.html", applications=applications)
@app.route('/approve_worker/<int:worker_id>')
@login_required
def approve_worker(worker_id):
    if current_user.role != 'admin':
        return redirect('/')

    worker = User.query.get(worker_id)
    worker.is_approved = True
    db.session.commit()

    return redirect(url_for('admin_dashboard'))


@app.route('/reject_worker/<int:worker_id>')
@login_required
def reject_worker(worker_id):
    if current_user.role != 'admin':
        return redirect('/')

    worker = User.query.get(worker_id)
    worker.is_approved = False
    db.session.commit()

    return redirect(url_for('admin_dashboard'))

# ----------- HIRE (AJAX-aware) -----------
@app.route('/hire/<int:worker_id>/<int:job_id>', methods=['POST', 'GET'])
@login_required
def hire(worker_id, job_id):
    if current_user.role != 'client':
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"ok": False, "msg": "Only clients can hire."}), 403
        flash("Only clients can hire workers.", "error")
        return redirect(url_for('index'))

    worker = User.query.get_or_404(worker_id)
    job = Job.query.get_or_404(job_id)

    if job.client_id != current_user.id:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"ok": False, "msg": "You cannot hire for jobs you didn't post."}), 403
        flash("You cannot hire for jobs you did not post.", "error")
        return redirect(url_for('client_dashboard'))

    application = Application.query.filter_by(worker_id=worker.id, job_id=job.id).first()
    if not application:
        application = Application(worker_id=worker.id, job_id=job.id, status="hired")
        db.session.add(application)
    else:
        application.status = "hired"

    job.is_open = False
    db.session.commit()

    new_notify = Notification(user_id=worker.id, message=f"You were hired for job: {job.title}")
    db.session.add(new_notify)
    db.session.commit()

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"ok": True, "msg": "Worker hired & notified."})

    flash("Worker Hired Successfully & Notified!", "success")
    return redirect(url_for('client_dashboard'))
# ----------- ADMIN -----------
# -------------------- ADMIN DASHBOARD --------------------
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect('/')   # prevent client/worker accessing admin panel

    users = User.query.all()   # show users on dashboard if needed
    return render_template('admin_dashboard.html', users=users)


# -------------------- ADMIN MANAGE USERS PAGE --------------------
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != "admin":
        return redirect('/')

    users = User.query.all()   # show ALL users
    return render_template('admin_users.html', users=users)


# -------------------- DELETE USER --------------------
@app.route('/admin/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != "admin":
        return redirect('/')

    user = User.query.get(user_id)

    if user:
        db.session.delete(user)
        db.session.commit()

    return redirect(url_for('admin_users'))


# -------------------- APPROVE USER --------------------
@app.route('/admin/approve/<int:user_id>')
@login_required
def approve_user(user_id):
    if current_user.role != "admin":
        return redirect('/')

    user = User.query.get(user_id)

    if user:
        user.is_approved = True
        db.session.commit()

    return redirect(url_for('admin_users'))


# -------------------- REJECT USER --------------------
@app.route('/admin/reject/<int:user_id>')
@login_required
def reject_user(user_id):
    if current_user.role != "admin":
        return redirect('/')

    user = User.query.get(user_id)

    if user:
        user.is_approved = False
        db.session.commit()

    return redirect(url_for('admin_users'))

# ----------- CHAT -----------
@app.route('/chat/<int:user_id>', methods=['GET','POST'])
@login_required
def chat(user_id):
    other = User.query.get(user_id)

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()

    if request.method == "POST":
        new_msg = Message(sender_id=current_user.id, receiver_id=user_id, content=request.form['message'])
        db.session.add(new_msg)
        db.session.commit()
        return redirect(url_for('chat', user_id=user_id))  # ✅ FIXED

    return render_template("chat.html", other=other, messages=messages)

@app.route('/chats')
@login_required
def chats():
    sent = [r[0] for r in db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id).distinct().all()]
    recv = [r[0] for r in db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id).distinct().all()]
    partner_ids = set(sent + recv)
    partners = User.query.filter(User.id.in_(list(partner_ids))).all() if partner_ids else []
    return render_template('chats.html', partners=partners)

# ----------- REVEAL CONTACT (used by client JS) -----------
@app.route('/reveal-contact/<int:worker_id>/<int:job_id>')
@login_required
def reveal_contact(worker_id, job_id):
    if current_user.role != 'client':
        return jsonify({"error": "Not allowed"}), 403

    if not is_hired(worker_id, current_user.id):
        return jsonify({"error": "Hire First"}), 403

    worker = User.query.get_or_404(worker_id)
    return jsonify({
        "name": worker.name,
        "email": worker.email,
        "phone": worker.phone or "Not Provided"
    })

# ----------- NOTIFICATIONS -----------
@app.route('/notifications')
@login_required
def notifications():
    notes = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).all()
    return render_template('notifications.html', notifications=notes)

@app.route('/notification/read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    note = Notification.query.get(notification_id)
    if note and note.user_id == current_user.id:
        note.is_read = True
        db.session.commit()
    return redirect(url_for('notifications'))


if __name__ == "__main__":
    app.run(debug=True)
