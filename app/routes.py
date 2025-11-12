from flask import Blueprint, request, redirect, url_for, render_template, session
from .models import db, lifecycle, materiaal, zone, item, gebruik

main = Blueprint('main', __name__)

#Bovenstaande code niet aanpassen!!!

# Eerst User-Stories!
#----------------------HOME--------------------------
@main.route('/', methods=['GET'])
def index():
    return render_template('index.html') #hangt ervan af welke HTML we gebruiken

#----------------------LOGIN--------------------------
@main.route('/login', methods=['GET', 'POST'])
def login(): #Kan nog aangepast worden indien HTML andere benaming krijgt
    #Als gebruiker al ingelogd is, doorsturen naar homepagina
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        #Hier komt de logica om te kijken of de gebruiker bestaat en het wachtwoord klopt
        if username == 'admin' and password == '1234':  # Voorbeeldcontrole
            session['user_id'] = 1
            return redirect(url_for('main.index'))
        else:
            error = 'Ongeldige inloggegevens. Probeer het opnieuw.'
            return render_template('login.html', error=error)
    
    return render_template('login.html') #De loginpagina renderen

#----------------------IDENIFICATIE--------------------------
#Indien we geen loginpagina gebruiken en gewoon een identificatie willen dat direct doorstuurd naar de overzichtspagina:
@main.route('/', methods=['GET', 'POST'])
def start():
    '''Startpagina waar de gebruiker zijn naam invult.
    De naam wordt opgeslagen in de sessie en daarna doorgestuurd naar de homepagina.'''

    if request.method == 'POST':
        username = request.form.get('username')

        if username:
            session['username'] = username
            return redirect(url_for('main.index'))
        
    return render_template('start.html')

@main.route('/home')
def home():
    """
    Hoofdpagina met voorraadoverzicht.
    De gebruikersnaam wordt opgehaald uit de sessie.
    """
    username = session.get('username', None)

    if not username: 
        return redirect(url_for('main.start'))  # Als er geen gebruikersnaam is, terug naar startpagina

#----------------------DASHBOARD--------------------------
from sqlalchemy import func
from .models import materiaal

#Nu query opstellen voor het aantal materialen per merk
def home():
    merken_data = (
        db.session.query(
            materiaal.merk,
            func.count(materiaal.id).label('aantal')
        )
        .group_by(materiaal.merk)
        .all()
    )   #👉 Deze query haalt uit je database alle merken (uit de tabel materiaal) én telt hoeveel materialen er bij elk merk horen

    # Zet om in een lijst van dictionaries (voor HTML)
    merken_lijst = [{'merk': merk, 'aantal': aantal} for merk, aantal in merken_data]
    return render_template('home.html', merken=merken_lijst)

@main.route('/merk/<string:merknaam>')
def toon_merk(merknaam):
    "Toont alle materialen en items die horen bij een specifiek merk."
    materialen = (
        db.session.query(materiaal, item)
        .join(item, materiaal.materiaal_id == item.materiaal_id)
        .filter(materiaal.merk == merknaam)
        .all()
    )
    # Nu structuren per type voor overzicht in UI
    types = {}
    for mat, itm in materialen: 
        if mat.type not in types:
            types[mat.type] = []
        types[mat.type].append({"omschrijving": mat.omschrijving, "doel": itm.doel, "verpakking": itm.verpakking, "zone": itm.zone, "aantal": itm.aantal})

    return render_template('merk_detail.html', merknaam=merknaam, types=types)
#Wat er exact gebeurd: join combineert de tabellen materiaal en item, filter selecteert een gekozen merk, we krijgen een lijst 
#van tuples (materiaal, item). Daarna structureren we de data per type materiaal voor overzichtelijkheid.

#Tot hier ben k geraakt nu ben ik er niet zeker van hoe het verder moet. Dit heb ik zo goed mogelijk proberen doen adhv UI prototype.