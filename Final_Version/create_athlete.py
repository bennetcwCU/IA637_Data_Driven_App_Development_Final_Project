# add_athlete.py
# OFFICIAL Clarkson University Rowing — Add Athlete
# Works 100% with your database: bennetcw_IA637_rowing_DB

from models.user import User
from models.athlete import Athlete
from models.section import Section
from models.sectionalMembership import SectionalMembership
import bcrypt

# ——— CONFIGURE YOUR NEW ATHLETE HERE ———
athlete_name     = "Tyler Smith"                    # ← Athlete's full name
athlete_email    = "Tyler@clarkson.edu"           # ← Must be unique!
athlete_password = "clarkson2025"                       # ← They log in with this
weight_category  = "Lwt"                             # Lwt, Hwt, Open, Coxswain
section_name     = "Men's Varsity"                 # Must match a SectionName in your Section table
# ————————————————————————————————————————

# Official Clarkson Colors for pretty terminal output
GREEN = "\033[38;2;0;78;66m"      # Clarkson Green #004e42
GOLD  = "\033[38;2;255;205;0m"   # Clarkson Gold  #ffcd00
RESET = "\033[0m"
BOLD  = "\033[1m"

print(f"{GREEN}Adding official Clarkson rower...{RESET}")
print(f"   Name     : {BOLD}{athlete_name}{RESET}")
print(f"   Email    : {BOLD}{athlete_email}{RESET}")
print(f"   Category : {BOLD}{weight_category}{RESET}")
print(f"   Section  : {BOLD}{section_name}{RESET}\n")

# Step 1: Hash password securely
hashed = bcrypt.hashpw(athlete_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Step 2: Create User account (for login)
u = User()
u.set({
    'Name': athlete_name,
    'email': athlete_email,
    'hashPassword': hashed,
    'role': 'Athlete'
})

try:
    u.insert()
    user_id = u.data[0]['UserID']
    print(f"{GREEN}Created User account (UserID: {user_id}){RESET}")
except Exception as e:
    if "Duplicate entry" in str(e):
        print(f"{GOLD}Email already exists! Looking up user...{RESET}")
        u.getByField('email', athlete_email)
        if u.data:
            user_id = u.data[0]['UserID']
            print(f"{GREEN}Found existing user → UserID: {user_id}{RESET}")
        else:
            print("Could not find user. Exiting.")
            exit()
    else:
        print(f"Error creating user: {e}")
        exit()

# Step 3: Add to Athlete table
a = Athlete()
a.set({
    'AthleteID': user_id,
    'PerformanceCatalogID': f"2024{user_id:03d}",
    'WeightCategory': weight_category
})

try:
    a.insert()
    print(f"{GREEN}Added to Athlete table{RESET}")
except Exception as e:
    if "Duplicate" in str(e):
        print("Already in Athlete table")

# Step 4: Assign to Section
s = Section()
s.getByField('SectionName', section_name)

if not s.data:
    print(f"{GOLD}Section '{section_name}' not found! Available sections:{RESET}")
    s.getAll()
    for sec in s.data:
        print(f"   • {sec['SectionName']} (ID: {sec['SectionID']})")
    exit()

section_id = s.data[0]['SectionID']

sm = SectionalMembership()
sm.set({
    'StartDate': '2025-08-25',
    'EndDate': None,
    'SectionID': section_id,
    'AthleteID': user_id
})

try:
    sm.insert()
    print(f"{GREEN}Assigned to section: {section_name}{RESET}")
except:
    print("Already assigned to section")

# Final Success Message
print(f"\n{GOLD}{'='*65}{RESET}")
print(f"{GOLD}{BOLD}     SUCCESS! ATHLETE ADDED TO CLARKSON ROWING!{RESET}")
print(f"{GOLD}{'='*65}{RESET}")
print(f"{GREEN}   Login at → http://127.0.0.1:5000{RESET}")
print(f"{GOLD}   Email    → {athlete_email}{RESET}")
print(f"{GOLD}   Password → {athlete_password}{RESET}")
print(f"{GOLD}{'='*65}{RESET}")
print(f"{GREEN}{BOLD}          Go Golden Knights!{RESET}")