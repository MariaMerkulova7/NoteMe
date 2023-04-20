import datetime
from dateutil.relativedelta import relativedelta
from flask import Flask, render_template, request, redirect, abort
from data import db_session
from data.users import User
from data.notes import Notes
from forms.registration_form import RegisterForm
from forms.entrance_form import EntranceForm
from forms.new_note import NewNotesForm
from flask_login import login_required, LoginManager, login_user, current_user, logout_user

import calendar

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

app.config['SECRET_KEY'] = 'my_secret_key'

colors = []


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def start(title='Главная страница - NoteMe'):
    return render_template('logo.html', title=title)


@app.route('/registration/', methods=['GET', 'POST'])
def register(title='Регистрация - NoteMe'):
    form = RegisterForm()
    if form.validate_on_submit():
        if len(form.password.data) < 8:
            return render_template('register.html', title=title,
                                   form=form,
                                   message="Пароль должен быть не меньше 8 символов")
        if form.password.data != form.password_again.data:
            return render_template('register.html', title=title,
                                   form=form,
                                   message="Пароли не совпадают")

        db_sess = db_session.create_session()

        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title=title,
                                   form=form,
                                   message="Такой пользователь уже есть")

        user = User(
            name=form.name.data,
            email=form.email.data,
        )

        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        return render_template('wait.html', title=title, text=form.name.data)
    return render_template('registration.html', title=title, form=form)


@app.route('/entrance/', methods=['POST', 'GET'])
def entrance(title='Вход - NoteMe'):
    form = EntranceForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        person = db_sess.query(User).filter(User.email == form.email.data).first()
        if not person:
            return render_template('entrance.html', title=title,
                                   form=form,
                                   message="Такого пользователя нет")

        if not person.check_password(form.password.data):
            return render_template('entrance.html', title=title,
                                   form=form,
                                   message="Неверный пароль")

        login_user(person, remember=form.remember_me.data)
        return redirect("/main_page/")

    return render_template('entrance.html', title=title, form=form)


@app.route('/quit/')
@login_required
def quit():
    logout_user()
    return redirect("/")


@app.route('/add_notes/', methods=['GET', 'POST'])
@login_required
def add_note(title='Добавление заметки - NoteMe'):
    form = NewNotesForm()

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        new_note = Notes()
        new_note.title = form.title.data
        new_note.text = form.text.data
        new_note.date_of_event = form.date_of_event.data
        new_note.time_of_event = form.time_of_event.data
        current_user.notes.append(new_note)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/main_page/')

    return render_template('note_adder.html', title=title,
                           form=form)


@app.route('/edit_notes/<int:current_note_id>', methods=['GET', 'POST'])
@login_required
def edit_note(current_note_id, title='Изменение заметки - NoteMe'):
    form = NewNotesForm()

    if request.method == "GET":
        db_sess = db_session.create_session()
        current_note = db_sess.query(Notes).filter(Notes.id == current_note_id, Notes.user == current_user).first()

        if current_note:
            form.title.data = current_note.title
            form.text.data = current_note.text
            form.date_of_event.data = current_note.date_of_event
            form.time_of_event.data = current_note.time_of_event

        else:
            abort(404)

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        current_note = db_sess.query(Notes).filter(Notes.id == current_note_id, Notes.user == current_user).first()

        if current_note:
            current_note.title = form.title.data
            current_note.text = form.text.data
            current_note.date_of_event = form.date_of_event.data
            current_note.time_of_event = form.time_of_event.data
            db_sess.commit()
            return redirect('/main_page/')

        else:
            abort(404)

    return render_template('note_adder.html', title=title, form=form)


@app.route('/delete_notes/<int:current_note_id>', methods=['GET', 'POST'])
@login_required
def delete_note(current_note_id):
    db_sess = db_session.create_session()
    current_note = db_sess.query(Notes).filter(Notes.id == current_note_id, Notes.user == current_user).first()

    if current_note:
        db_sess.delete(current_note)
        db_sess.commit()

    else:
        abort(404)

    return redirect('/main_page/')


NAME_OF_MONTH = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь",
                 "Ноябрь", "Декабрь"]
NAME_OF_DAY = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def create_calendar(screen_month):
    obj = datetime.datetime.strptime(screen_month, "%Y-%m-%d")
    list_of_days = calendar.monthcalendar(obj.year, obj.month)

    if len(list_of_days) != 6:
        list_of_days.append([0 for _ in range(7)])

    return list_of_days


def previous_month(screen_month):
    obj = datetime.datetime.strptime(screen_month, "%Y-%m-%d")
    previous = obj + relativedelta(months=-1)

    return previous


def next_month(screen_month):
    obj = datetime.datetime.strptime(screen_month, "%Y-%m-%d")
    next_screen_month = obj + relativedelta(months=1)

    return next_screen_month


@app.route("/main_page/")
@app.route("/main_page/<date_to_see>/", methods=['GET', 'POST'])
@login_required
def main_for_authorized(date_to_see=datetime.datetime.now().strftime("%Y-%m-%d"), title='Главная страница - NoteMe'):
    db_sess = db_session.create_session()
    screen_date = datetime.datetime.strptime(date_to_see, "%Y-%m-%d")
    screen_year = screen_date.year
    screen_month = screen_date.month
    screen_day = screen_date.day
    next_month_after_screen = next_month(date_to_see).strftime("%Y-%m-%d")
    previous_month_before_screen = previous_month(date_to_see).strftime("%Y-%m-%d")
    cur_month = datetime.datetime.now().month
    cur_day = datetime.datetime.now().day
    cur_year = datetime.datetime.now().year
    notes = db_sess.query(Notes).filter(Notes.user == current_user,
                                        Notes.date_of_event == f"{screen_year}-{str(screen_month).rjust(2, '0')}-{str(screen_day).rjust(2, '0')}")

    return render_template("main.html", title=title, notes=notes, content=create_calendar(date_to_see),
                           cur_month=cur_month, cur_day=cur_day, cur_year=cur_year, screen_day=screen_day,
                           screen_year=screen_year, screen_month=screen_month,
                           next_month_after_screen=next_month_after_screen,
                           previous_month_before_screen=previous_month_before_screen)


if __name__ == '__main__':
    db_session.global_init("db/info.db")
    app.run(port=8080, host='127.0.0.1')
