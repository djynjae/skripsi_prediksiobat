import sqlite3
import os

DB_PATH = 'instance/database.db'

def bersihkan_tabel():
    if not os.path.exists(DB_PATH):
        print("Database belum ada. Aman!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Perintah ini akan menyapu bersih seluruh isi tabel tanpa menghapus tabelnya
        cursor.execute("DELETE FROM historis_stok")
        
        # Reset juga nomor urut id-nya kembali ke 1
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='historis_stok'")
        
        conn.commit()
        conn.close()
        print("✅ SUKSES! Seluruh data lama (bahasa Inggris) berhasil dibumihanguskan.")
        print("Tabel historis_stok sekarang 100% kosong dan siap menerima data baru.")
        
    except Exception as e:
        print("❌ Error saat membersihkan database:", e)

if __name__ == "__main__":
    bersihkan_tabel()