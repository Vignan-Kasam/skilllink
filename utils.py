from models import Notification, db, Rating, User

def create_notification(user_id, message):
    """
    Create and save a notification for a user.
    """
    note = Notification(user_id=user_id, message=message)
    db.session.add(note)
    db.session.commit()
    return note

def mark_notification_read(notification):
    notification.is_read = True
    db.session.commit()

def add_rating(worker_id, client_id, job_id, score, comment=None):
    """
    Create a rating record and return it.
    Also returns the worker's new average (consumer code can fetch).
    """
    r = Rating(worker_id=worker_id, client_id=client_id, job_id=job_id, score=int(score), comment=comment)
    db.session.add(r)
    db.session.commit()
    # Optionally: compute avg
    worker = User.query.get(worker_id)
    avg = worker.average_rating()
    return r, avg
def is_hired(worker_id, client_id):
    application = Application.query.filter_by(worker_id=worker_id).join(Job).filter(Job.client_id==client_id, Application.status=='hired').first()
    return application is not None
