import sqlite3

try:
    # Buka database
    conn = sqlite3.connect('instance/database.db')
    cursor = conn.cursor()
    
    # Ambil 5 data bulan paling atas
    cursor.execute("SELECT nama_obat, bulan, tahun FROM historis_stok LIMIT 5")
    hasil = cursor.fetchall()
    
    print("\n=== HASIL RONTGEN DATABASE ===")
    for baris in hasil:
        print(baris)
    print("==============================\n")
    
except Exception as e:
    print("Error:", e)