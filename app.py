# run.py
from app import create_app
from app.models.database import init_db

app = create_app()

if __name__ == '__main__':
    # LANGKAH 1: Jalankan fungsi inisialisasi database dulu
    init_db() 
    
    # LANGKAH 2: Setelah database siap, baru nyalakan server Flask
    app.run(debug=True)