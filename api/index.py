from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, g
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db

# Создаем таблицы при первом запуске
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Database initialization error: {str(e)}")

# Для Vercel необходимо экспортировать приложение
app.debug = False
application = app

if __name__ == '__main__':
    app.run()
