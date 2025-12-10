# create_admin.py
# OFFICIAL Clarkson University Rowing — Add Admin User
# Works 100% with your database: bennetcw_IA637_rowing_DB

from models.user import User
import bcrypt

# ——— CONFIGURE YOUR ADMIN HERE ———
admin_name     = "Boris Smith"                    #
admin_email    = "boris@clarkson.edu"           
admin_password = "knight2025"                    
# ——————————————————————————————————


GREEN = "\033[38;2;0;78;66m"      
GOLD  = "\033[38;2;255;205;0m"   
RESET = "\033[0m"
BOLD  = "\033[1m"

print(f"{GREEN}Creating official Clarkson Rowing Admin...{RESET}")
print(f"   Name     : {BOLD}{admin_name}{RESET}")
print(f"   Email    : {BOLD}{admin_email}{RESET}")
print(f"   Role     : {BOLD}Admin{RESET}")
print(f"   Password : {BOLD}{admin_password}{RESET}\n")

# Hash password securely (exactly like the app does)
hashed = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Create the admin
u = User()
u.set({
    'Name': admin_name,
    'email': admin_email,
    'hashPassword': hashed,
    'role': 'Admin'
})

try:
    u.insert()
    print(f"{GOLD}{'='*60}{RESET}")
    print(f"{GOLD}          SUCCESS! ADMIN CREATED!{RESET}")
    print(f"{GOLD}{'='*60}{RESET}")
    print(f"{GREEN}   Login at → http://127.0.0.1:5000{RESET}")
    print(f"{GOLD}   Email    → {admin_email}{RESET}")
    print(f"{GOLD}   Password → {admin_password}{RESET}")
    print(f"{GOLD}{'='*60}{RESET}")
    print(f"{GREEN}{BOLD}          Go Golden Knights!{RESET}")
except Exception as e:
    if "Duplicate entry" in str(e):
        print(f"{GOLD}That email already exists. Try a different one!{RESET}")
    else:
        print(f"Error: {e}")