import pandas as pd
import sqlite3
import os
import sys

# Paksa Python mengenali folder utama
direktori_utama = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, direktori_utama)

db_path = os.path.join(direktori_utama, 'instance', 'database.db')
csv_path = os.path.join(direktori_utama, 'data_csv', 'pimtrakol.csv')

print("Memulai proses pengambilan data pimtrakol.csv...")

if os.path.exists(csv_path):
    try:
        conn = sqlite3.connect(db_path)
        
        # 1. Baca CSV pimtrakol dengan pemisah titik koma
        df = pd.read_csv(csv_path, sep=';')
        
        # 2. Tambahkan kolom nama_obat
        df['nama_obat'] = 'pimtrakol'
        
        # 3. Ubah nama kolom agar sesuai database
        df = df.rename(columns={
            'Bulan': 'bulan',
            'Tahun': 'tahun',
            'Stok': 'jumlah_stok'
        })
        
        # 4. Ambil kolom yang diperlukan saja (mengabaikan kolom No)
        df_to_insert = df[['nama_obat', 'bulan', 'tahun', 'jumlah_stok']]
        
        # 5. Suntikkan ke database
        df_to_insert.to_sql('historis_stok', conn, if_exists='append', index=False)
        
        conn.close()
        print("✅ Berhasil! Data dari pimtrakol.csv sudah aman masuk ke database.")
    except Exception as e:
        print(f"❌ Gagal memproses file: {e}")
else:
    print(f"⚠️ File 'pimtrakol.csv' tidak ditemukan di folder 'data_csv/'.")
    print("Pastikan file tersebut ada di dalam folder 'data_csv' dan namanya sudah menggunakan huruf 'l'.")