def is_admin(request, db):
    email = request.session.get("email")
    if not email:
        return False

    cur = db.cursor()
    cur.execute("SELECT 1 FROM admins WHERE email=?", (email,))
    return cur.fetchone() is not None
