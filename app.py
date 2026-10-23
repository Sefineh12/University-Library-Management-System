import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'የተጠበቀ_እጅግ_ላቀ_ሚስጥራዊ_ቁልፍ'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///university_library_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- የዳታቤዝ ሞዴሎች (Database Models) ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student') # admin, librarian, student

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(50), unique=True, nullable=False) # ISBN ማጣሪያ
    quantity = db.Column(db.Integer, default=1)

class BorrowedBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(200), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    book_title = db.Column(db.String(200))
    borrow_date = db.Column(db.Date, default=datetime.utcnow().date)
    return_due_date = db.Column(db.Date, nullable=False) # የመመለሻ ቀን

# --- ረዳት ተግባር (Helper Function for Fine) ---
def calculate_fine(due_date):
    current_date = datetime.utcnow().date()
    if current_date > due_date:
        overdue_days = (current_date - due_date).days
        return overdue_days * 5 # በቀን 5 ብር የቅጣት ስሌት
    return 0

# --- ድረ-ገጽ መስመሮች (Routes) ---

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    search_query = request.args.get('search', '')
    if search_query:
        books = Book.query.filter(
            (Book.title.like(f'%{search_query}%')) | 
            (Book.author.like(f'%{search_query}%')) |
            (Book.isbn.like(f'%{search_query}%')) |
            (Book.genre.like(f'%{search_query}%'))
        ).all()
    else:
        books = Book.query.all()
        
    all_borrowed = BorrowedBook.query.all()
    
    # ለእያንዳንዱ የተበደረ መጽሐፍ ቅጣት ማስላት
    borrowed_with_fines = []
    for b in all_borrowed:
        fine = calculate_fine(b.return_due_date)
        borrowed_with_fines.append({
            'id': b.id,
            'student_name': b.student_name,
            'book_title': b.book_title,
            'borrow_date': b.borrow_date,
            'due_date': b.return_due_date,
            'fine': fine
        })
        
    blogs = Blog.query.all()
    
    # ለግራፍ ትንተና የሚሆን ዳታ ማዘጋጀት
    stats = {
        'total_books': sum([b.quantity for b in Book.query.all()]),
        'total_borrowed': len(all_borrowed),
        'total_users': User.query.count()
    }
    
    return render_template('dashboard.html', books=books, borrowed=borrowed_with_fines, blogs=blogs, search_query=search_query, stats=stats)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student') # የምዝገባ ሚና
        
        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            flash('ይህ የተጠቃሚ ስም ወይም ኢሜይል አስቀድሞ ተመዝግቧል!', 'danger')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = User(full_name=full_name, username=username, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('ምዝገባው በተሳካ ሁኔታ ተጠናቋል!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # ዋና አስተዳዳሪ (Super Admin)
        if username == 'admin' and password == 'admin123':
            session['user_id'] = 0
            session['role'] = 'admin'
            session['username'] = 'ዋና አስተዳዳሪ'
            return redirect(url_for('home'))
            
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.full_name
            return redirect(url_for('home'))
        else:
            flash('የተሳሳተ የተጠቃሚ ስም ወይም የይለፍ ቃል!', 'danger')
            
    return render_template('login.html')

@app.route('/add_book', methods=['POST'])
def add_book():
    if session.get('role') in ['admin', 'librarian']: # ለአስተዳዳሪ እና መጽሐፍ ያዥ
        title = request.form.get('title')
        author = request.form.get('author')
        genre = request.form.get('genre')
        isbn = request.form.get('isbn')
        quantity = int(request.form.get('quantity', 1))
        
        # ISBN መኖሩን ማረጋገጥ
        if Book.query.filter_by(isbn=isbn).first():
            flash('ይህ ISBN መለያ ቁጥር አስቀድሞ ተመዝግቧል!', 'danger')
            return redirect(url_for('home'))
            
        new_book = Book(title=title, author=author, genre=genre, isbn=isbn, quantity=quantity)
        db.session.add(new_book)
        db.session.commit()
        flash('መጽሐፍ በተሳካ ሁኔታ ተመዝግቧል!', 'success')
    return redirect(url_for('home'))

@app.route('/borrow_book', methods=['POST'])
def borrow_book():
    book_id = request.form.get('book_id')
    book = Book.query.get(book_id)
    if book and book.quantity > 0:
        if session.get('role') in ['admin', 'librarian']:
            student = request.form.get('student_name')
        else:
            student = session.get('username')
            
        due_date = datetime.utcnow().date() + timedelta(days=7) # የ 7 ቀናት የመመለሻ ገደብ
        new_borrow = BorrowedBook(student_name=student, book_id=book_id, book_title=book.title, return_due_date=due_date)
        book.quantity -= 1
        db.session.add(new_borrow)
        db.session.commit()
        flash('መጽሐፍ በተሳካ ሁኔታ ተበድሯል! በ 7 ቀናት ውስጥ ይመልሱ።', 'success')
    else:
        flash('ይቅርታ! ይህ መጽሐፍ ክምችት ላይ የለም።', 'danger')
    return redirect(url_for('home'))

@app.route('/return_book/<int:borrow_id>', methods=['POST'])
def return_book(borrow_id):
    if session.get('role') in ['admin', 'librarian']:
        borrowed_entry = BorrowedBook.query.get(borrow_id)
        if borrowed_entry:
            book = Book.query.get(borrowed_entry.book_id)
            if book:
                book.quantity += 1
            db.session.delete(borrowed_entry)
            db.session.commit()
            flash('መጽሐፉ በተሳካ ሁኔታ ተመልሷል!', 'success')
    return redirect(url_for('home'))

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)

@app.route('/add_blog', methods=['POST'])
def add_blog():
    if session.get('role') in ['admin', 'librarian']:
        title = request.form.get('title')
        content = request.form.get('content')
        new_blog = Blog(title=title, content=content)
        db.session.add(new_blog)
        db.session.commit()
        flash('አዲስ ዜና ተለጥፏል!', 'success')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)




