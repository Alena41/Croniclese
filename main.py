import io
from flask import Flask, render_template, redirect, url_for, send_file, \
    request, abort
from app1.data import db_session
from app1.data.users import User
from app1.data.novels import Novels
from forms.user import RegisterForm
from forms.login_form import LoginForm
from forms.novel import NovelForm
from flask_login import LoginManager, login_user, current_user
from flask_login import login_required, logout_user
from werkzeug.utils import secure_filename
import os

login_manager = LoginManager()
app = Flask(__name__, static_folder='static/images')
db_session.global_init('app1/db/blogs.sqlite')
login_manager.init_app(app)
app.config['SECRET_KEY'] = '40d1649f-0493-4b70-98ba-98533de7710b'
app.config['UPLOAD_FOLDER'] = 'static/path_to_upload_folder'
app.config['UPLOAD_FOLDER1'] = 'static/images1'
app.config['UPLOAD_FOLDER2'] = 'static/doc'
packets_pull = {}


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def index():
    return render_template('ocnova.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html',
                                   title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html',
                                   title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html',
                           title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def entranc():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(
            User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('index'))
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html',
                           title='Авторизация', form=form)


@app.route('/download')
def download_file():
    path = "static/saves.docx"
    return send_file(path, as_attachment=True)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            current_user.profile_image = filename
            db_sess = db_session.create_session()
            db_sess.merge(current_user)
            db_sess.commit()
    return render_template('profile.html')


@app.route('/novels', methods=['GET', 'POST'])
@login_required
def add_news():
    global packets_pull
    form = NovelForm()
    if form.validate_on_submit():
        packets_pull[str(current_user.id)] = [form.title.data,
                                              form.content.data]
        return redirect(f'/load_files/{current_user.id}')
    return render_template('news.html',
                           title='Добавление новеллы',
                           form=form)


@app.route('/novels_delete/<int:id>', methods=['GET'])
@login_required
def delete_games(id):
    form = NovelForm()
    db_sess = db_session.create_session()
    novel = db_sess.query(Novels).filter(Novels.id == id,
                                         Novels.user == current_user).first()
    if novel:
        db_sess.delete(novel)
        db_sess.commit()
        return redirect('/')
    else:
        return abort(404)


@app.route('/load_files/<int:id>', methods=['GET', 'POST'])
@login_required
def load_file(id):
    global packets_pull
    db_sess = db_session.create_session()
    if request.method == 'POST':
        novel = Novels()
        if len(packets_pull[str(id)]) != 2:
            abort(404)
        novel.title = packets_pull[str(id)][0]
        novel.content = packets_pull[str(id)][1]

        image_file = request.files['immage']
        image_filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER1'], image_filename)
        image_file.save(image_path)

        with open(image_path, 'rb') as file:
            novel.immage = file.read()

        document_file = request.files['document']
        document_filename = secure_filename(document_file.filename)
        document_path = os.path.join(app.config['UPLOAD_FOLDER2'],
                                     document_filename)
        document_file.save(document_path)

        with open(document_path, 'rb') as file:
            novel.document = file.read()

        current_user.novel.append(novel)
        db_sess.merge(current_user)
        db_sess.commit()
        del packets_pull[str(id)]
        return redirect('/')
    return render_template('load_file.html')


@app.route('/edit_files/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_file(id):
    global packets_pull
    db_sess = db_session.create_session()
    if request.method == 'POST':
        novel = db_sess.query(Novels).filter(Novels.id == id,
                                             Novels.user == current_user
                                             ).first()
        if not novel:
            abort(404)
        novel.title = packets_pull[str(id)][0]
        novel.content = packets_pull[str(id)][1]
        novel.immage = request.files['immage'].read()
        novel.document = request.files['document'].read()
        db_sess.commit()
        del packets_pull[str(id)]
        return redirect('/')
    return render_template('load_file.html')


@app.route('/novels/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_novel(id):
    global packets_pull
    form = NovelForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        novel = db_sess.query(Novels).filter(Novels.id == id,
                                             Novels.user == current_user
                                             ).first()
        if novel:
            form.title.data = novel.title
            form.content.data = novel.content
        else:
            return abort(404)

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        novel = db_sess.query(Novels).filter(Novels.id == id,
                                             Novels.user == current_user
                                             ).first()
        if novel:
            packets_pull[str(id)] = [str(form.title.data),
                                     str(form.content.data)]
            db_sess.commit()
            return redirect(f'/edit_files/{id}')
        else:
            return abort(404)
    return render_template('news.html',
                           title='Редактирование игры',
                           form=form
                           )


@app.route('/novel/<int:id>', methods=['GET'])
def render_novel(id):
    form = NovelForm()
    db_sess = db_session.create_session()
    novel = db_sess.query(Novels).filter(Novels.id == id).first()
    if not novel:
        return abort(404)
    with open(f'static/images1/{id}.jpg', 'wb') as f:
        if novel.immage is not None:
            f.write(novel.immage)
    with open(f'static/doc/{id}.docx', 'wb') as f:
        if novel.document is not None:
            f.write(novel.document)
    if novel:
        return render_template('nov.html',
                               data=novel)
    else:
        return abort(404)


@app.route('/download_document/<int:id>')
@login_required
def download_document(id):
    db_sess = db_session.create_session()
    novel = db_sess.query(Novels).filter(Novels.id == id).first()
    if novel:
        file_data = novel.document
        return send_file(
            io.BytesIO(file_data),
            as_attachment=True,
            download_name=f"document_{id}.docx"
        )
    else:
        return abort(404)


@app.route('/all_novels', methods=['GET'])
def show_all_novels():
    db_sess = db_session.create_session()
    novels = db_sess.query(Novels).all()
    return render_template('all_novels.html', novels=novels)


def main():
    db_session.global_init('app1/db/new_blogs.sqlite')
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


@app.route('/api/help')
def api_help():
    """http://localhost:5000/api/help"""
    return 'Тяжело'


if __name__ == '__main__':
    main()
