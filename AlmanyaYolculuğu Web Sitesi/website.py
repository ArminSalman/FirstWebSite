from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from flask_wtf import FlaskForm
from functools import wraps

#Kayıt Form
class RegistrationForm(Form):
    name = StringField("İsim", [validators.Length(min=3)])
    familyname= StringField("Soyisim", [validators.Length(min=3)])
    username = StringField("Kullanıcı Adı", [validators.Length(min=4, max=25) ])
    email = StringField("Email Adresi", [validators.Email(message="Geçerli bir email adresi giriniz!")])
    password = PasswordField("Şifre", [validators.DataRequired(message="Bir parola belirleyiniz!"), validators.EqualTo("confirm", message="Şifre eşleşmedi")])
    confirm = PasswordField("Şifre Tekrarı")

#Giriş Form
class LoginForm(Form):
    username = StringField("Kullanıcı Adı", [validators.Length(min=4, max=25) ])
    password = PasswordField("Şifre", [validators.DataRequired(message="Parolanızı giriniz!")])

#Deneyim Form
class ExperienceForm(Form):
    title = StringField("Başlık", [validators.Length(min=5,max=20)])
    experience = TextAreaField("Deneyiminiz", _name="textarea")

#Kullanıcı Girişi Decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if session["logined"]:
                return f(*args, **kwargs)
            else:
                flash("Gitmeye çalıştığınız sayfayı görüntülemek için giriş yapın","danger")
                return redirect(url_for("login"))
        except KeyError:
            flash("Gitmeye çalıştığınız sayfayı görüntülemek için giriş yapın","danger")
            return redirect(url_for("login"))
    return decorated_function

app = Flask(__name__)
app.secret_key = "cokmusecretbe"


#MySQL configrasyonu
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "almyolculuk"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

#Ana Sayfa
@app.route("/")
def index():
    return render_template("index.html")

#Hakkımızda
@app.route("/info")
def info():
    return render_template("info.html")

#Our Experience Page
@app.route("/our-experience",methods=["GET","POST"])
def our_experience():
    cursor = mysql.connection.cursor()
    sorgu = "Select * from experiences where username = 'GulumserKaraburun'"
    cursor.execute(sorgu)
    result = cursor.fetchall()

    if len(result) == 0:
        flash("Henüz eklenmiş bir deneyim bulunmamaktadır","warning")
        return redirect(url_for("index"))
    else:
        return render_template("our_experience.html",data = result)

#Your Experience Page
@app.route("/your-experience")
def your_experience():
    cursor = mysql.connection.cursor()
    sorgu = "Select * from experiences"
    cursor.execute(sorgu)
    result = cursor.fetchall()

    if len(result) == 0:
        flash("Henüz eklenmiş bir deneyim bulunmamaktadır","warning")
        return redirect(url_for("index"))
    else:
        return render_template("your_experience.html",data = result)

#Register Page
@app.route("/register", methods=["GET","POST"])
def register():
    form = RegistrationForm(request.form)
    #check = request.form.get("sozlesme")
    if request.method == "POST" and form.validate():
        try:
            #if check:
                name = form.name.data
                familyname = form.familyname.data
                username = form.username.data
                email = form.email.data
                password = form.password.data
                confirm = form.confirm.data
                safe_password = sha256_crypt.hash(password)

                cursor = mysql.connection.cursor()
                sorgu = "Insert into users(name,familyname,username,email,password) Values(%s,%s,%s,%s,%s)"
                cursor.execute(sorgu,(name,familyname,username,email,safe_password))
                mysql.connection.commit()
                cursor.close()
                flash("Başarıyla kaydoldunuz","success")
                return redirect(url_for("login"))
            #else:
                #flash("Kullanıcı sözleşmesini kabul ediniz","danger")
                #return redirect(url_for("register"))
        except:
            flash("Bir hata oluştu kullanıcı adınız kullanılıyor olabilir eğer düzelmezse bize mail gönderebilirsiniz","danger")
            return redirect(url_for("register"))
        
    else:
        return render_template("register.html", form = form)

#Login Page
@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        try:
            username = form.username.data
            password_entered = form.password.data
            sorgu = "Select * from users where username = %s"
            cursor = mysql.connection.cursor()
            cursor.execute(sorgu,(username,))
            data = cursor.fetchone()
            password = data["password"]
            if sha256_crypt.verify(password_entered,password):
                flash("Başarıyla giriş yaptınız","success")
                session["logined"] = True
                session["username"] = username
                admin()
                return redirect(url_for("index"))
            else:
                flash("Kullanıcı adı veya şifreniz yanlış!","danger")
                return render_template("login.html")
        except:
            flash("Kullanıcı adınız veya şifreniz yanlış eğer doğru girdiğinize eminseniz ve tekrar girdiğinizde olmuyorsa bize mail atabilirsiniz","danger")
            return redirect(url_for("login"))
        cursor.close()
    else:
        return render_template("login.html",form = form)

#Exit Page
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("index"))

#Yönetim Paneli
@app.route("/dashboard", methods=["GET","POST"])
@login_required
def dashboard():
    if request.method == "POST":
        return redirect(url_for("add_experience"))
    else:
        cursor = mysql.connection.cursor()
        sorgu = "Select * from experiences where username = %s"
        username = session["username"]
        cursor.execute(sorgu,(username,))
        sonuc = cursor.fetchall()

        if len(sonuc) == 0:
            flash("Henüz deneyim eklememişsiniz","info")
            return render_template("dashboard.html")
        else:
            return render_template("dashboard.html",data = sonuc)
        
#Add Experience
@app.route("/dashboard/add-experience",methods=["GET","POST"])
@login_required
def add_experience():
    form = ExperienceForm(request.form)
    if request.method == "POST":
        username = session["username"]
        title = form.title.data
        content = form.experience.data

        cursor = mysql.connection.cursor()
        sorgu = "Insert into experiences(username,title,content) Values(%s,%s,%s)"
        cursor.execute(sorgu,(username,title,content))
        mysql.connection.commit()

        flash("Deneyiminiz başarıyla eklendi","success")
        cursor.close()
        return redirect(url_for("dashboard")) 
    else:
        return render_template("add_experience.html",form = form)

#Add Admin Experience
@app.route("/dashboard/add-admin-experience",methods=["GET","POST"])
@login_required
def add_admin_experience():
    if session["username"] == "GulumserKaraburun":
        form = ExperienceForm(request.form)
        if request.method == "POST":
            username = "GulumserKaraburun"
            title = form.title.data
            content = form.experience.data

            cursor = mysql.connection.cursor()
            sorgu = "Insert into experiences(username,title,content) Values(%s,%s,%s)"
            cursor.execute(sorgu,(username,title,content))
            mysql.connection.commit()

            flash("Deneyiminiz başarıyla eklendi","success")
            cursor.close()
            return redirect(url_for("dashboard")) 
        else:
            return render_template("add_experience.html",form = form)
    else:
        flash("Denediğiniz sayfaya girme izniniz bulunmamaktadır","danger")
        return redirect(url_for("index"))

#Deneyim Görüntüleme
@app.route("/experience/<string:id>")
def görüntüleme(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from experiences where id = %s"
    cursor.execute(sorgu,(id,))
    result = cursor.fetchone()

    if len(result) > 0:
        return render_template("experience.html",experience = result)
    else:
        flash("Girdiğiniz id de bir deneyim bulunmamaktadır","warning")
        return redirect(url_for("your_experience"))
    cursor.close()

#Deneyim Silme
@app.route("/delete-experience/<string:id>")
@login_required
def delete_experience(id):
    cursor = mysql.connection.cursor()
    username = session["username"]
    sorgu = "Select * from experiences where id = %s"
    cursor.execute(sorgu,(id,))
    result = cursor.fetchone()
    
    if len(result) > 0:
        ex_username = result["username"]
        if username == ex_username:
            sorgu2 = "Delete from experiences where id = %s"
            cursor.execute(sorgu2,(id,))
            mysql.connection.commit()
            flash("Deneyim başarıyla silindi","success")
            return redirect(url_for("dashboard"))
        else:
            flash("Bu deneyimi silmeye izniniz yok","danger")
            return redirect(url_for("index"))
    else:
        flash("Silmeye çalıştığınız deneyim bulunmamaktadır","danger")
        return redirect(url_for("index"))

#Deneyim Güncelleme
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * from experiences where id = %s and username = %s"
        result = cursor.execute(sorgu,(id,session["username"]))
        if result == 0:
            flash("Böyle bir deneyim bulunmamaktadır yada bu işleme izniniz yok","danger")
            return redirect(url_for("index"))
        else:
            experience = cursor.fetchone()
            form = ExperienceForm()
            form.title.data = experience["title"]
            form.experience.data = experience["content"]
            return render_template("update.html",form = form)
    else:
        form = ExperienceForm(request.form)
        newTitle = form.title.data
        newContent = form.experience.data
        username = session["username"]
        sorgu2 = "Update experiences Set title = %s,content = %s where id = %s and username = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id,username))
        mysql.connection.commit()
        flash("Deneyim başarıyla güncellendi","success")
        return redirect(url_for("dashboard"))

#Search
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method == "POST":
        keyword = request.form.get("domates")
        cursor = mysql.connection.cursor()
        sorgu = "Select * from experiences where title like '%"+keyword+"%'"
        result = cursor.execute(sorgu)
        if result == 0:
            flash("Aradığınız kelimeye uygun deneyim bulunmamıştır","info")
            return redirect(url_for("your_experience"))
        else:
            experiences = cursor.fetchall()
            return render_template("your_experience.html",data = experiences)
    else:
        return redirect(url_for("index"))

#Yönetici Session
def admin():
    if session["username"] == "ArminSalman" or session["username"] == "GulumserKaraburun":
        session["admin"] = True
    else:
        session["admin"] = False

if __name__ == "__main__":
    app.run(debug=True)