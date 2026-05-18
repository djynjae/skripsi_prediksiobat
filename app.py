from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

app = Flask(__name__)

# koneksi database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# TABEL ADMIN
# =========================
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))

# =========================
# LOGIN
# =========================
@app.route('/')
def login():
    return render_template('login.html')

# =========================
# DASHBOARD
# =========================
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# =========================
# TABEL OBAT
# =========================

class Obat(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nama_obat = db.Column(
        db.String(100)
    )

    stok = db.Column(
        db.Integer
    )

    bulan = db.Column(
        db.String(20) 
    )
    tahun = db.Column(
        db.Integer
    )

# =========================
# DATA OBAT
# =========================

@app.route('/obat')
def obat():

    cari = request.args.get('cari')

    if cari:

        data_obat = Obat.query.filter(
            Obat.nama_obat.contains(cari)
        ).all()

    else:

        data_obat = Obat.query.all()

    return render_template(
        'obat.html',
        data_obat=data_obat
    ) 

# =========================
# TAMBAH OBAT
# =========================

@app.route('/tambah_obat', methods=['POST'])
def tambah_obat():

    nama_obat = request.form['nama_obat']
    stok = request.form['stok']
    bulan = request.form['bulan']
    tahun = request.form['tahun']

    obat_baru = Obat(
        nama_obat=nama_obat,
        stok=stok,
        bulan=bulan,
        tahun=tahun
    )

    db.session.add(obat_baru)
    db.session.commit()

    return redirect('/obat') 

# =========================
# HAPUS OBAT
# =========================

@app.route('/hapus_obat/<id>')
def hapus_obat(id):

    data = Obat.query.get(id)

    db.session.delete(data)

    db.session.commit()

    return redirect('/obat') 

# =========================
# PREDIKSI
# =========================
@app.route('/prediksi', methods=['GET', 'POST'])
def prediksi():

    hasil = []

    mad = 0
    mse = 0
    mape = 0

    if request.method == 'POST':

        nama_obat = request.form['obat']

        # BACA CSV

        if nama_obat == 'OBH Combi':

            data = pd.read_csv('data/obh_combi.csv')

        elif nama_obat == 'Paratusin':

            data = pd.read_csv('data/paratusin.csv')

        elif nama_obat == 'Pimtrakol':

            data = pd.read_csv('data/pimtrakol.csv')

        # AMBIL STOK

        y = data['stok'].tolist()

        n = len(y)

        # BUAT NILAI X

        x = list(range(-(n//2), (n//2)+1))

        if len(x) > n:
            x = x[:-1]

        # HITUNG X² dan XY

        xy = []
        x2 = []

        for i in range(n):

            xy.append(x[i] * y[i])

            x2.append(x[i] ** 2)

        # HITUNG a dan b

        a = sum(y) / n

        b = sum(xy) / sum(x2)

        # FORECAST

        forecast = []

        for i in range(n):

            prediksi_hasil = a + b * x[i]

            forecast.append(round(prediksi_hasil, 2))

        # MAD MSE MAPE

        error = []
        error2 = []
        ape = []

        for i in range(n):

            e = abs(y[i] - forecast[i])

            error.append(e)

            error2.append(e ** 2)

            ape.append((e / y[i]) * 100)

        mad = round(sum(error) / n, 2)

        mse = round(sum(error2) / n, 2)

        mape = round(sum(ape) / n, 2)

        # HASIL

        for i in range(n):

            hasil.append({

                'bulan': data['bulan'][i],

                'tahun': data['tahun'][i],

                'stok': y[i],

                'prediksi': forecast[i]

            })

    return render_template(

        'prediksi.html',

        hasil=hasil,

        mad=mad,

        mse=mse,

        mape=mape

    )

# =========================
# DETAIL OBAT
# =========================

@app.route('/detail_obat/<id>')
def detail_obat(id):

    data = Obat.query.get(id)

    return render_template(
    'detail_obat.html',
    data=data
)

# =========================

# UPDATE OBAT

# =========================

@app.route('/update_obat/<id>', methods=['POST'])
def update_obat(id):

    data = Obat.query.get(id)

    data.nama_obat = request.form['nama_obat']
    data.stok = request.form['stok']
    data.bulan = request.form['bulan'] 
    data.tahun = request.form['tahun']

    db.session.commit()

    return redirect('/obat')

# =========================

# TENTANG KAMI

# =========================

@app.route('/tentang')
def tentang():

    return render_template(
    'tentang.html'
)

# =========================

# HALAMAN PREDIKSI

# =========================


# =========================
# MAIN
# =========================
if __name__ == '__main__':

    with app.app_context():
        db.create_all()

    app.run(debug=True)

# =========================
