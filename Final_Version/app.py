# app.py — FINAL OFFICIAL CLARKSON ROWING ATTENDANCE SYSTEM
# 100% working with your database bennetcw_IA637_rowing_DB
# Fully compliant with official Clarkson Brand Guide

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from models.user import User
from models.practice import Practice
from models.practiceAttendance import PracticeAttendance
from models.sectionalMembership import SectionalMembership
from models.section import Section
from models.athlete import Athlete
from datetime import date


from flask import make_response, send_file
import csv
from io import StringIO, BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors as rl_colors

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

app = Flask(__name__)
app.secret_key = 'clarkson-official-knight-2025'

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'boris@clarkson.edu'          # CHANGE THIS
app.config['MAIL_PASSWORD'] = 'your-app-password-here'       # CHANGE THIS
app.config['MAIL_DEFAULT_SENDER'] = 'Clarkson Rowing <boris@clarkson.edu>'

mail = Mail(app)

# Global variable to share athlete stats between routes
athlete_stats_global = []

# ——— ROUTES ———

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Redirect to correct dashboard
    return redirect('/athlete' if session.get('role') == 'Athlete' else '/admin')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User()
        if u.tryLogin(request.form['email'], request.form['password']):
            session['user_id'] = u.data[0]['UserID']
            session['name'] = u.data[0]['Name']
            session['role'] = u.data[0]['role']
            flash('Welcome back!', 'success')
            return redirect('/athlete' if session['role'] == 'Athlete' else '/admin')
        flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ——— ATHLETE DASHBOARD ———
@app.route('/athlete')
def athlete():
    if session.get('role') != 'Athlete':
        return redirect(url_for('login'))

    p = Practice()
    p.getAll(order='Practice_Date DESC')

    pa = PracticeAttendance()
    pa.cur.execute("""
        SELECT pa.*, pr.Practice_Date, pr.Practice_Type, pr.Practice_intensity_Type
        FROM Practice_Attendance pa
        JOIN Practice pr ON pa.Practice_ID = pr.Practice_ID
        WHERE pa.AthleteID = %s
        ORDER BY pr.Practice_Date DESC
    """, (session['user_id'],))
    attendance = pa.cur.fetchall()

    today = date.today()

    return render_template('athlete_dashboard.html', practices=p.data, attendance=attendance, today=today)

@app.route('/record', methods=['POST'])
def record():
    if session.get('role') != 'Athlete':
        return redirect(url_for('login'))
    
    practice_id = request.form['practice_id']
    
    # Get the practice date
    p = Practice()
    p.getById(practice_id)
    if not p.data:
        flash('Practice not found!', 'danger')
        return redirect('/athlete')
    
    practice_date = p.data[0]['Practice_Date']
    
    # BLOCK FUTURE DATES
    if practice_date > date.today():
        flash('You cannot mark attendance for future practices!', 'danger')
        return redirect('/athlete')
    
    # Check if already recorded
    pa = PracticeAttendance()
    pa.cur.execute("SELECT 1 FROM Practice_Attendance WHERE Practice_ID = %s AND AthleteID = %s", 
                   (practice_id, session['user_id']))
    if pa.cur.fetchone():
        flash('You already recorded attendance for this practice!', 'warning')
        return redirect('/athlete')
    
    # Record attendance
    pa.set({
        'Practice_ID': practice_id,
        'AthleteID': session['user_id'],
        'Duration': 0,
        'Distance': 0,
    })
    pa.insert()
    flash('Attendance recorded!', 'success')
    return redirect('/athlete')

# ——— ADMIN DASHBOARD ———
@app.route('/admin')
def admin():
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))

    # Total practices
    p = Practice()
    p.getAll(order='Practice_Date DESC')
    total_practices = len(p.data)

    # All athletes
    u = User()
    u.cur.execute("SELECT UserID, Name FROM User WHERE role = 'Athlete' ORDER BY Name")
    athletes = u.cur.fetchall()
    total_athletes = len(athletes)

    # Athlete names for dropdown
    all_athletes = [ath['Name'] for ath in athletes]

    # Attendance stats
    pa = PracticeAttendance()
    pa.cur.execute("""
        SELECT AthleteID, COUNT(*) as attended_count
        FROM Practice_Attendance 
        GROUP BY AthleteID
    """)
    attendance_counts = pa.cur.fetchall()
    attended_dict = {row['AthleteID']: row['attended_count'] for row in attendance_counts}

    athlete_stats = []
    for ath in athletes:
        attended = attended_dict.get(ath['UserID'], 0)
        percentage = round((attended / total_practices * 100), 1) if total_practices > 0 else 0
        athlete_stats.append({
            'name': ath['Name'],
            'attended': attended,
            'total': total_practices,
            'percentage': percentage
        })

    team_average = round(sum(s['percentage'] for s in athlete_stats) / total_athletes, 1) if total_athletes > 0 else 0

    # Complete attendance record
    pa.cur.execute("""
        SELECT pa.*, u.Name, pr.Practice_Date, pr.Practice_Type, pr.Practice_intensity_Type
        FROM Practice_Attendance pa
        JOIN User u ON pa.AthleteID = u.UserID
        JOIN Practice pr ON pa.Practice_ID = pr.Practice_ID
        ORDER BY pr.Practice_Date DESC, u.Name
    """)
    attendance = pa.cur.fetchall()

    # All sections for dropdown
    s = Section()
    s.getAll()
    all_sections = [row['SectionName'] for row in s.data]

    # Save stats globally for send-reminder route
    global athlete_stats_global
    athlete_stats_global = athlete_stats

    return render_template('admin_dashboard.html',
                         practices=p.data,
                         athlete_stats=athlete_stats,
                         team_average=team_average,
                         total_practices=total_practices,
                         total_athletes=total_athletes,
                         attendance=attendance,
                         all_athletes=all_athletes,
                         all_sections=all_sections)

# ——— CREATE PRACTICE ———
@app.route('/create-practice')
def create_practice_page():
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))
    return render_template('create_practice.html')

@app.route('/create_practice', methods=['POST'])
def create_practice():
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))

    p = Practice()
    p.set({
        'Practice_Date': request.form['date'],
        'Practice_Type': request.form['type'],
        'Practice_intensity_Type': request.form['intensity']
    })
    p.insert()
    flash('Practice created successfully!', 'success')
    return redirect('/admin')

# ——— ANALYTICS ———
@app.route('/analytics')
def analytics():
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))

    pa = PracticeAttendance()
    pa.cur.execute("""
        SELECT 
            u.Name,
            COALESCE(SUM(pa.Distance), 0) as total_meters,
            COALESCE(SUM(pa.Duration), 0) as total_minutes,
            COUNT(pa.Practice_ID) as practices_attended
        FROM User u
        LEFT JOIN Practice_Attendance pa ON u.UserID = pa.AthleteID
        WHERE u.role = 'Athlete'
        GROUP BY u.UserID, u.Name
        ORDER BY total_meters DESC
    """)
    performance_data = pa.cur.fetchall()

    return render_template('analytics.html', performance=performance_data)

# ——— MANAGE PRACTICES ———
@app.route('/manage-practices')
def manage_practices():
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))
    p = Practice()
    p.getAll(order='Practice_Date DESC')
    return render_template('manage_practices.html', practices=p.data)

@app.route('/delete-practice/<int:id>')
def delete_practice(id):
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))
    p = Practice()
    p.delete(id)
    flash('Practice deleted!', 'success')
    return redirect('/manage-practices')

# ——— MANAGE USERS ———
@app.route('/manage-users')
def manage_users():
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))
    u = User()
    u.getAll(order='Name')
    return render_template('manage_users.html', users=u.data)

@app.route('/change-role/<int:user_id>/<string:new_role>')
def change_role(user_id, new_role):
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))
    if new_role not in ['Athlete', 'Admin']:
        flash('Invalid role!', 'danger')
        return redirect('/manage-users')
    
    u = User()
    u.getById(user_id)
    if u.data:
        u.data[0]['role'] = new_role
        u.update()
        flash(f"Role changed to {new_role}!", 'success')
    else:
        flash('User not found!', 'danger')
    return redirect('/manage-users')

@app.route('/delete-user/<int:user_id>')
def delete_user(user_id):
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))

    # Delete in correct order
    PracticeAttendance().cur.execute("DELETE FROM Practice_Attendance WHERE AthleteID = %s", (user_id,))
    PracticeAttendance().conn.commit()

    SectionalMembership().cur.execute("DELETE FROM Sectional_Membership WHERE AthleteID = %s", (user_id,))
    SectionalMembership().conn.commit()

    Athlete().cur.execute("DELETE FROM Athlete WHERE AthleteID = %s", (user_id,))
    Athlete().conn.commit()

    User().cur.execute("DELETE FROM User WHERE UserID = %s", (user_id,))
    User().conn.commit()

    flash('User deleted successfully!', 'success')
    return redirect('/manage-users')

# ——— SEND EMAIL REMINDER ———
@app.route('/send-reminder/<string:athlete_name>')
def send_reminder(athlete_name):
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))

    global athlete_stats_global
    athlete = None
    for stat in athlete_stats_global:
        if stat['name'] == athlete_name:
            athlete = stat
            break
    
    if not athlete:
        flash('Athlete not found!', 'danger')
        return redirect('/admin')

    # Get athlete's email
    u = User()
    u.cur.execute("SELECT email FROM User WHERE Name = %s AND role = 'Athlete'", (athlete_name,))
    result = u.cur.fetchone()
    
    if not result or not result['email']:
        flash('No email found for this athlete.', 'danger')
        return redirect('/admin')

    athlete_email = result['email']

    msg = Message(
        subject="Clarkson Rowing — Attendance Reminder",
        recipients=[athlete_email],
        body=f"""Dear {athlete_name},

This is a friendly reminder from the Clarkson Rowing coaching staff.

Your current practice attendance is {athlete['percentage']}% ({athlete['attended']} out of {athlete['total']} practices).

Regular attendance is critical for team success and your development as a rower.

Please make every effort to attend all practices.

Go Golden Knights!

— Clarkson Rowing Coaching Staff
"""
    )
    
    try:
        mail.send(msg)
        flash(f'Reminder sent to {athlete_name}!', 'success')
    except Exception as e:
        flash(f'Failed to send email: {str(e)}', 'danger')

    return redirect('/admin')


@app.route('/export-attendance/csv')
def export_attendance_csv():
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))

    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(['Athlete', 'Attended', 'Total', 'Attendance %'])

    # Data
    for stat in athlete_stats_global:
        writer.writerow([
            stat['name'],
            stat['attended'],
            stat['total'],
            f"{stat['percentage']}%"
        ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=clarkson_rowing_attendance.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/export-attendance/pdf')
def export_attendance_pdf():
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    styles['Title'].fontName = 'DejaVuSans'
    styles['Normal'].fontName = 'DejaVuSans'
    styles['Heading1'].fontName = 'DejaVuSans'

    # Title
    title = Paragraph("Clarkson Rowing — Practice Attendance Report", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Table data
    data = [['Athlete', 'Attended', 'Total', 'Attendance %']]
    for stat in athlete_stats_global:
        data.append([
            stat['name'],  # Now safely rendered with DejaVuSans
            str(stat['attended']),
            str(stat['total']),
            f"{stat['percentage']}%"
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#004e42'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#ffcd00'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), '#f8f9fa'),
        ('GRID', (0, 0), (-1, -1), 1, '#004e42'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="clarkson_rowing_attendance.pdf", mimetype='application/pdf')

@app.route('/my-account')
def my_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    u = User()
    u.getById(session['user_id'])
    user_data = u.data[0] if u.data else {}
    
    return render_template('my_account.html', user=user_data)

@app.route('/update-account', methods=['POST'])
def update_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    u = User()
    u.getById(session['user_id'])
    
    if not u.data:
        flash('User not found!', 'danger')
        return redirect('/my-account')
    
    # Update fields
    new_name = request.form['name'].strip()
    new_email = request.form['email'].strip()
    new_password = request.form['password']
    
    if new_name:
        u.data[0]['Name'] = new_name
    if new_email:
        u.data[0]['email'] = new_email
    if new_password:
        import bcrypt
        u.data[0]['hashPassword'] = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    
    u.update()
    
    # Update session
    session['name'] = new_name or session['name']
    
    flash('Account updated successfully!', 'success')
    return redirect('/my-account')

@app.route('/my-history')
def my_history():
    if session.get('role') != 'Athlete':
        return redirect(url_for('login'))

    pa = PracticeAttendance()
    pa.cur.execute("""
        SELECT pa.*, pr.Practice_Date, pr.Practice_Type, pr.Practice_intensity_Type
        FROM Practice_Attendance pa
        JOIN Practice pr ON pa.Practice_ID = pr.Practice_ID
        WHERE pa.AthleteID = %s
        ORDER BY pr.Practice_Date DESC
    """, (session['user_id'],))
    history = pa.cur.fetchall()

    return render_template('my_history.html', history=history)

@app.route('/update-practice-record', methods=['POST'])
def update_practice_record():
    if session.get('role') != 'Athlete':
        return redirect(url_for('login'))

    record_id = request.form['record_id']
    duration = request.form['duration'] or 0
    distance = request.form['distance'] or 0

    pa = PracticeAttendance()
    pa.cur.execute("""
        UPDATE Practice_Attendance 
        SET Duration = %s, Distance = %s 
        WHERE Practice_SessionID = %s AND AthleteID = %s
    """, (duration, distance, record_id, session['user_id']))
    pa.conn.commit()

    flash('Practice record updated!', 'success')
    return redirect('/my-history')

@app.route('/edit-practice/<int:practice_id>')
def edit_practice(practice_id):
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))
    
    p = Practice()
    p.getById(practice_id)
    if not p.data:
        flash('Practice not found!', 'danger')
        return redirect('/manage-practices')
    
    return render_template('edit_practice.html', practice=p.data[0])

@app.route('/update-practice/<int:practice_id>', methods=['POST'])
def update_practice(practice_id):
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))
    
    p = Practice()
    p.cur.execute("""
        UPDATE Practice 
        SET Practice_Date = %s, Practice_Type = %s, Practice_intensity_Type = %s 
        WHERE Practice_ID = %s
    """, (
        request.form['date'],
        request.form['type'],
        request.form['intensity'],
        practice_id
    ))
    p.conn.commit()
    
    flash('Practice updated successfully!', 'success')
    return redirect('/manage-practices')

if __name__ == '__main__':
    app.run(debug=True, port=5000)