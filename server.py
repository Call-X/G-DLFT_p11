import json
from flask import Flask,render_template,request,redirect,flash,url_for
import datetime
import environ
from pathlib import Path


project_dir = Path(__file__).parent
env = environ.Env()
environ.Env.read_env(env_file=str(project_dir / ".env"))

def loadClubs():
    with open(project_dir / 'clubs.json') as c:
        listOfClubs = json.load(c)['clubs']
        return listOfClubs

def loadCompetitions():
    with open(project_dir / 'competitions.json') as competitions:
        listOfCompetitions = json.load(competitions)['competitions']
        return listOfCompetitions
    
def serializeClub(club_to_save, filename="clubs.json"):
    with open(project_dir/filename, 'r+') as f:
        data = json.load(f)
        clubs = data['clubs']
        for club in clubs:
            if club['email'] == club_to_save['email']:
                club['points'] = str(club_to_save['points'])
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        
def serializeCompetition(comp_to_save, filename="competitions.json"):
    with open(project_dir/filename, 'r+') as f:
        data = json.load(f)
        competitions = data['competitions']
        for competition in competitions:
            if competition['name'] == comp_to_save['name']:
                competition['numberOfPlaces'] = str(comp_to_save['numberOfPlaces'])
                competition['Reservations'] = (comp_to_save['Reservations'])
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        
def has_happened(competition):
    competition_date = competition['date'].split(" ")[0]
    year, month, day = competition_date.split("-")
    if datetime.datetime(int(year), int(month), int(day)) < datetime.datetime.now():
        return True
 
all_competitions = loadCompetitions()
clubs = loadClubs()   
app = Flask(__name__)
app.config.update(
    SECRET_KEY=env("SECRET_KEY"),
    DEBUG=env("DEBUG"),
    use_reloader=True,
)

@app.errorhandler(500)
def internal_server_error(e):
    # note that we set the 500 status explicitly
    return render_template("500.html"), 500

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/showSummary",methods=['POST'])
def showSummary():
    try:
        club = [club for club in clubs if club['email'] == request.form['email']][0]
    except IndexError:
        error = True
        return render_template('500.html', error=error)
    return render_template('welcome.html', club=club, competitions=all_competitions, club_list=clubs)
    
@app.route("/book/<competition>/<club>")
def book(competition,club):
    foundClub = [c for c in clubs if c['name'] == club][0]
    foundCompetition = [c for c in all_competitions if c['name'] == competition][0]
    if foundClub and foundCompetition:
        return render_template('booking.html',club=foundClub,competition=foundCompetition)
    else:
        flash("Something went wrong-please try again")
        return render_template('welcome.html', club=club, competitions=all_competitions, club_list=clubs)
                                      
@app.route("/purchasePlaces",methods=['POST'])
def purchasePlaces():
    point_per_place = 3
    competition = [c for c in all_competitions if c['name'] == request.form['competition']][0]
    club = [c for c in clubs if c['name'] == request.form['club']][0]
    places_required = int(request.form['places'])

    if places_required < 0:
        flash("the number of the purchase should be positive")
        return render_template('welcome.html', club=club, competitions=all_competitions,club_list=clubs)
    
    # check if club as enough points
    if int(club['points']) == 0 or int(club['points']) - places_required*point_per_place < 0:
        flash("Your club doesn't have enough point !")
        return render_template('welcome.html', club=club, competitions=all_competitions)
    
    # check if there is enough place available
    if int(competition['numberOfPlaces']) < places_required:
        flash("There are not enough places in this competition which are avaible !")
        return render_template('welcome.html', club=club, competitions=all_competitions, club_list=clubs)
    
    if has_happened(competition):
        flash("This competition already happened !")
        return render_template('welcome.html', club=club, competitions=all_competitions)
    
    try:
        if competition["Reservations"][club["name"]] + places_required <= 12 and places_required <= 12:
            competition["Reservations"][club["name"]] += places_required
         
        else:
            flash("You can't book more than 12 places per competition")
            return render_template('welcome.html', club=club, competitions=all_competitions)    
        
    except KeyError:
        if places_required <= 12:
            competition['Reservations'][club['name']] = places_required  
        else:
            flash("You can't book more than 12 places per competition")
            return render_template('welcome.html', club=club, competitions=all_competitions) 
            
    club['points'] = int(club['points']) - places_required*point_per_place
    serializeClub(club)
    competition['numberOfPlaces'] = int(competition['numberOfPlaces']) - places_required
    serializeCompetition(competition)
    
    flash(f"Great Booking complete! You purchased {places_required} for the {competition['name']}!")
    return render_template('welcome.html', club=club, competitions=all_competitions) 

@app.route("/points_display_board", methods=['GET'])
def points_display_board():
    headings = ("Club Name - ", "Points")
    data = []
    for club in loadClubs():
        club_data = (club['name'], club['points'])
        data.append(club_data)
    return render_template('points_display_board.html', headings=headings, data=data)
    
@app.route("/logout")
def logout():
    return redirect(url_for('index'))
    
