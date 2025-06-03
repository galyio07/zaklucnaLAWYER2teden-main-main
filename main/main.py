from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "skrivni_kljuc_123"

USERS_FILE = 'uporabniki.json'
RESERVATIONS_FILE = 'rezervacije.json'

# Funkcija za nalaganje uporabnikov iz datoteke
def load_users():
    try:
        if not os.path.exists(USERS_FILE):
            return {}
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading users: {e}")
        return {}

# Funkcija za shranjevanje uporabnikov v datoteko
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# Začetna stran preusmeri na prijavo
@app.route('/')
def zacetna():
    return redirect(url_for('prijava'))

# Prijava uporabnika
@app.route('/login', methods=['GET', 'POST'])
def prijava():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = load_users()
        
        # Preveri, če so podatki pravilni
        if username in users and users[username]['geslo'] == password:
            session['uporabnisko_ime'] = username
            return redirect(url_for('lawyer_selection'))
        else:
            return render_template('login.html', error="Napačni podatki za prijavo")
    
    return render_template('login.html')

# Registracija novega uporabnika
@app.route('/register', methods=['GET', 'POST'])
def registracija():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Preveri, če so vsa polja izpolnjena
        if not all([username, email, password, confirm_password]):
            return render_template('register.html', error="Vsa polja so obvezna")
        
        # Preveri, če se gesli ujemata
        if password != confirm_password:
            return render_template('register.html', error="Gesli se ne ujemata")
        
        users = load_users()
        
        # Preveri, če uporabniško ime že obstaja
        if username in users:
            return render_template('register.html', error="Uporabniško ime že obstaja")
        
        # Shrani novega uporabnika
        users[username] = {
            'e_posta': email,
            'geslo': password
        }
        
        save_users(users)
        return redirect(url_for('prijava'))
    
    return render_template('register.html')

# Meni za prijavljenega uporabnika
@app.route('/menu')
def meni():
    if 'uporabnisko_ime' not in session:
        return redirect(url_for('prijava'))
    return render_template('menu.html', uporabnisko_ime=session['uporabnisko_ime'])

# Odjava uporabnika
@app.route('/logout')
def logout():
    session.pop('uporabnisko_ime', None)
    return redirect(url_for('prijava'))

# Prikaz izbire odvetnika
@app.route('/lawyer_selection')
def lawyer_selection():
    if 'uporabnisko_ime' not in session:
        return redirect(url_for('prijava'))
    return render_template('lawyer_selection.html', uporabnisko_ime=session['uporabnisko_ime'])

# Prikaz pogovora z odvetnikom
@app.route('/lawyer_chat')
def lawyer_chat():
    if 'uporabnisko_ime' not in session:
        return redirect(url_for('prijava'))

    lawyer_type = request.args.get('type', 'General')

    valid_types = ['Korporativni', 'Kazenska prava', 'Družinski', 'Intelektualni']
    # Če tip ni veljaven, preusmeri nazaj na izbiro
    if lawyer_type not in valid_types:
        return redirect(url_for('lawyer_selection'))
    
    return render_template('lawyer_chat.html', lawyer_type=lawyer_type, 
                         uporabnisko_ime=session['uporabnisko_ime'])

# Preusmeritev na pogovor glede na specializacijo
@app.route('/lawyer/<specialty>')
def lawyer_chat_specialty(specialty):
    return redirect(url_for('lawyer_chat.html', type=specialty))

#API ZA REZERVACIJO
@app.route('/api/schedule', methods=['POST'])
def schedule():
    # Preberemo podatke, ki jih je uporabnik poslal
    podatki = request.get_json()

    # Preverimo, če so podatki sploh bili poslani
    if podatki is None:
        return jsonify({'success': False, 'message': 'Podatki niso bili poslani.'}), 400

    # Preverimo, če so vsi obvezni podatki prisotni
    if 'datetime' not in podatki:
        return jsonify({'success': False, 'message': 'Datum in čas manjkajo.'}), 400


    # Pripravimo prazen seznam rezervacij
    rezervacije = []

    # Če datoteka že obstaja, jo poskusimo prebrati
    if os.path.exists(RESERVATIONS_FILE):
        with open(RESERVATIONS_FILE, 'r', encoding='utf-8') as datoteka:
            try:
                rezervacije = json.load(datoteka)
            except:
                rezervacije = []

    # Ustvarimo novo rezervacijo
    nova_rezervacija = {
        'datetime': podatki['datetime'],
        'lawyer': podatki['lawyer']
    }

    # Dodamo novo rezervacijo v seznam vseh rezervacij
    rezervacije.append(nova_rezervacija)

    # Shranimo posodobljen seznam nazaj v datoteko
    with open(RESERVATIONS_FILE, 'w', encoding='utf-8') as datoteka:
        json.dump(rezervacije, datoteka, ensure_ascii=False, indent=2)

    # Uporabniku sporočimo, da je bila rezervacija uspešna
    return jsonify({'success': True, 'message': 'Termin uspešno rezerviran!'})
if __name__ == '__main__':
    app.run(debug=True)