import os
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'targetku-secret-key-ganti-ini-saat-produksi')

_db_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'instance', 'targetku.db'))
# Neon/Render/Heroku kadang memberi URL dengan skema "postgres://", SQLAlchemy modern butuh "postgresql://"
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Folder instance/ hanya dibutuhkan untuk SQLite lokal. Di server serverless seperti
# Vercel, DATABASE_URL selalu diisi (Postgres) dan filesystem-nya read-only, jadi
# bagian ini WAJIB dilewati agar tidak error "Read-only file system".
if _db_url.startswith('sqlite:'):
    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Silakan login terlebih dahulu untuk mengakses halaman ini.'
login_manager.login_message_category = 'warning'


# ---------------------------------------------------------------------------
# MODELS
# ---------------------------------------------------------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    targets = db.relationship('Target', backref='owner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"admin-{self.id}"


class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nama = db.Column(db.String(150), nullable=False)
    nominal_target = db.Column(db.Float, nullable=False)
    tanggal_dibuat = db.Column(db.DateTime, default=datetime.utcnow)
    tanggal_target = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='berjalan')  # berjalan / tercapai
    catatan_selamat_ditampilkan = db.Column(db.Boolean, default=False)

    setoran_list = db.relationship('Setoran', backref='target', lazy=True,
                                    cascade='all, delete-orphan', order_by='Setoran.tanggal.desc()')

    @property
    def total_terkumpul(self):
        return sum(s.jumlah for s in self.setoran_list)

    @property
    def persentase(self):
        if self.nominal_target <= 0:
            return 0
        pct = (self.total_terkumpul / self.nominal_target) * 100
        return min(round(pct, 1), 100)

    @property
    def sisa(self):
        return max(self.nominal_target - self.total_terkumpul, 0)

    @property
    def sudah_tercapai(self):
        return self.total_terkumpul >= self.nominal_target


class Setoran(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id'), nullable=False)
    jumlah = db.Column(db.Float, nullable=False)
    tanggal = db.Column(db.Date, default=date.today)
    catatan = db.Column(db.String(255), nullable=True)


@login_manager.user_loader
def load_user(user_id):
    if str(user_id).startswith('admin-'):
        admin_id = user_id.split('-')[1]
        return Admin.query.get(int(admin_id))
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# DECORATORS
# ---------------------------------------------------------------------------

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Admin):
            flash('Silakan login sebagai admin untuk mengakses halaman ini.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


def user_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, User):
            flash('Silakan login untuk mengakses halaman ini.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# PUBLIC ROUTES
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    if current_user.is_authenticated and isinstance(current_user, User):
        return redirect(url_for('dashboard'))
    total_user = User.query.count()
    total_target = Target.query.count()
    total_tercapai = Target.query.filter_by(status='tercapai').count()
    return render_template('index.html', total_user=total_user,
                            total_target=total_target, total_tercapai=total_tercapai)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        errors = []
        if not username or len(username) < 3:
            errors.append('Username minimal 3 karakter.')
        if not email or '@' not in email:
            errors.append('Email tidak valid.')
        if not password or len(password) < 6:
            errors.append('Password minimal 6 karakter.')
        if password != confirm:
            errors.append('Konfirmasi password tidak cocok.')
        if User.query.filter_by(username=username).first():
            errors.append('Username sudah digunakan.')
        if User.query.filter_by(email=email).first():
            errors.append('Email sudah terdaftar.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html', username=username, email=email)

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Pendaftaran berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Selamat datang kembali, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Username atau password salah.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout.', 'success')
    return redirect(url_for('index'))


# ---------------------------------------------------------------------------
# USER DASHBOARD & CRUD TARGET / SETORAN
# ---------------------------------------------------------------------------

@app.route('/dashboard')
@user_required
def dashboard():
    targets = Target.query.filter_by(user_id=current_user.id).order_by(Target.tanggal_dibuat.desc()).all()
    total_tabungan = sum(t.total_terkumpul for t in targets)
    total_target_aktif = len([t for t in targets if not t.sudah_tercapai])
    total_tercapai = len([t for t in targets if t.sudah_tercapai])

    chart_labels = [t.nama for t in targets]
    chart_data = [t.persentase for t in targets]

    return render_template('dashboard.html', targets=targets, total_tabungan=total_tabungan,
                            total_target_aktif=total_target_aktif, total_tercapai=total_tercapai,
                            chart_labels=chart_labels, chart_data=chart_data)


@app.route('/target/tambah', methods=['GET', 'POST'])
@user_required
def target_tambah():
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        nominal = request.form.get('nominal_target', '').strip()
        tanggal_target = request.form.get('tanggal_target', '').strip()

        errors = []
        if not nama or len(nama) < 3:
            errors.append('Nama target minimal 3 karakter.')
        try:
            nominal_val = float(nominal)
            if nominal_val <= 0:
                errors.append('Nominal target harus lebih dari 0.')
        except ValueError:
            errors.append('Nominal target harus berupa angka.')
            nominal_val = 0

        tgl_val = None
        if tanggal_target:
            try:
                tgl_val = datetime.strptime(tanggal_target, '%Y-%m-%d').date()
                if tgl_val < date.today():
                    errors.append('Batas waktu tidak boleh tanggal yang sudah lewat.')
            except ValueError:
                errors.append('Format tanggal tidak valid.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('target_form.html', mode='tambah', nama=nama,
                                    nominal_target=nominal, tanggal_target=tanggal_target)

        target = Target(user_id=current_user.id, nama=nama, nominal_target=nominal_val,
                         tanggal_target=tgl_val)
        db.session.add(target)
        db.session.commit()
        flash(f'Target "{nama}" berhasil dibuat!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('target_form.html', mode='tambah')


@app.route('/target/<int:target_id>/ubah', methods=['GET', 'POST'])
@user_required
def target_ubah(target_id):
    target = Target.query.get_or_404(target_id)
    if target.user_id != current_user.id:
        flash('Anda tidak memiliki akses ke target ini.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        nominal = request.form.get('nominal_target', '').strip()
        tanggal_target = request.form.get('tanggal_target', '').strip()

        errors = []
        if not nama or len(nama) < 3:
            errors.append('Nama target minimal 3 karakter.')
        try:
            nominal_val = float(nominal)
            if nominal_val <= 0:
                errors.append('Nominal target harus lebih dari 0.')
        except ValueError:
            errors.append('Nominal target harus berupa angka.')
            nominal_val = target.nominal_target

        tgl_val = None
        if tanggal_target:
            try:
                tgl_val = datetime.strptime(tanggal_target, '%Y-%m-%d').date()
            except ValueError:
                errors.append('Format tanggal tidak valid.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('target_form.html', mode='ubah', target=target, nama=nama,
                                    nominal_target=nominal, tanggal_target=tanggal_target)

        target.nama = nama
        target.nominal_target = nominal_val
        target.tanggal_target = tgl_val
        db.session.commit()
        flash(f'Target "{nama}" berhasil diperbarui.', 'success')
        return redirect(url_for('dashboard'))

    tgl_str = target.tanggal_target.strftime('%Y-%m-%d') if target.tanggal_target else ''
    return render_template('target_form.html', mode='ubah', target=target, nama=target.nama,
                            nominal_target=target.nominal_target, tanggal_target=tgl_str)


@app.route('/target/<int:target_id>/hapus', methods=['POST'])
@user_required
def target_hapus(target_id):
    target = Target.query.get_or_404(target_id)
    if target.user_id != current_user.id:
        flash('Anda tidak memiliki akses ke target ini.', 'danger')
        return redirect(url_for('dashboard'))
    nama = target.nama
    db.session.delete(target)
    db.session.commit()
    flash(f'Target "{nama}" berhasil dihapus.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/target/<int:target_id>')
@user_required
def target_detail(target_id):
    target = Target.query.get_or_404(target_id)
    if target.user_id != current_user.id:
        flash('Anda tidak memiliki akses ke target ini.', 'danger')
        return redirect(url_for('dashboard'))
    just_reached = request.args.get('reached') == '1'
    return render_template('target_detail.html', target=target, just_reached=just_reached,
                            today=date.today().strftime('%Y-%m-%d'))


@app.route('/target/<int:target_id>/setor', methods=['POST'])
@user_required
def setoran_tambah(target_id):
    target = Target.query.get_or_404(target_id)
    if target.user_id != current_user.id:
        flash('Anda tidak memiliki akses ke target ini.', 'danger')
        return redirect(url_for('dashboard'))

    jumlah = request.form.get('jumlah', '').strip()
    tanggal = request.form.get('tanggal', '').strip()
    catatan = request.form.get('catatan', '').strip()

    errors = []
    try:
        jumlah_val = float(jumlah)
        if jumlah_val <= 0:
            errors.append('Nominal setoran harus lebih dari 0.')
    except ValueError:
        errors.append('Nominal setoran harus berupa angka.')
        jumlah_val = 0

    tgl_val = date.today()
    if tanggal:
        try:
            tgl_val = datetime.strptime(tanggal, '%Y-%m-%d').date()
        except ValueError:
            errors.append('Format tanggal tidak valid.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('target_detail', target_id=target.id))

    sudah_tercapai_sebelumnya = target.sudah_tercapai

    setoran = Setoran(target_id=target.id, jumlah=jumlah_val, tanggal=tgl_val, catatan=catatan or None)
    db.session.add(setoran)
    db.session.commit()

    reached_now = False
    if not sudah_tercapai_sebelumnya and target.sudah_tercapai:
        target.status = 'tercapai'
        db.session.commit()
        reached_now = True

    flash('Setoran berhasil dicatat!', 'success')
    if reached_now:
        return redirect(url_for('target_detail', target_id=target.id, reached=1))
    return redirect(url_for('target_detail', target_id=target.id))


@app.route('/setoran/<int:setoran_id>/hapus', methods=['POST'])
@user_required
def setoran_hapus(setoran_id):
    setoran = Setoran.query.get_or_404(setoran_id)
    target = setoran.target
    if target.user_id != current_user.id:
        flash('Anda tidak memiliki akses ke data ini.', 'danger')
        return redirect(url_for('dashboard'))
    target_id = target.id
    db.session.delete(setoran)
    db.session.commit()
    if not target.sudah_tercapai and target.status == 'tercapai':
        target.status = 'berjalan'
        db.session.commit()
    flash('Setoran berhasil dihapus.', 'success')
    return redirect(url_for('target_detail', target_id=target_id))


# ---------------------------------------------------------------------------
# ADMIN ROUTES
# ---------------------------------------------------------------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            flash('Login admin berhasil.', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Username atau password admin salah.', 'danger')

    return render_template('admin_login.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Admin telah logout.', 'success')
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_user = User.query.count()
    total_target = Target.query.count()
    total_tercapai = Target.query.filter_by(status='tercapai').count()
    total_setoran = db.session.query(db.func.sum(Setoran.jumlah)).scalar() or 0
    total_transaksi = Setoran.query.count()

    users = User.query.order_by(User.created_at.desc()).all()
    user_stats = []
    for u in users:
        u_targets = Target.query.filter_by(user_id=u.id).all()
        u_total = sum(t.total_terkumpul for t in u_targets)
        user_stats.append({
            'user': u,
            'jumlah_target': len(u_targets),
            'jumlah_tercapai': len([t for t in u_targets if t.sudah_tercapai]),
            'total_tabungan': u_total,
        })

    from collections import defaultdict
    bulanan = defaultdict(float)
    for s in Setoran.query.all():
        key = s.tanggal.strftime('%Y-%m')
        bulanan[key] += s.jumlah
    bulan_sorted = sorted(bulanan.keys())[-6:]
    chart_labels = bulan_sorted
    chart_data = [round(bulanan[b], 2) for b in bulan_sorted]

    return render_template('admin_dashboard.html', total_user=total_user, total_target=total_target,
                            total_tercapai=total_tercapai, total_setoran=total_setoran,
                            total_transaksi=total_transaksi, user_stats=user_stats,
                            chart_labels=chart_labels, chart_data=chart_data)


@app.route('/admin/user/<int:user_id>/hapus', methods=['POST'])
@admin_required
def admin_user_hapus(user_id):
    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'Akun "{username}" beserta seluruh datanya berhasil dihapus.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/ganti-password', methods=['GET', 'POST'])
@admin_required
def admin_ganti_password():
    if request.method == 'POST':
        password_lama = request.form.get('password_lama', '')
        password_baru = request.form.get('password_baru', '')
        konfirmasi = request.form.get('konfirmasi_password', '')

        errors = []
        if not current_user.check_password(password_lama):
            errors.append('Password lama yang kamu masukkan salah.')
        if not password_baru or len(password_baru) < 6:
            errors.append('Password baru minimal 6 karakter.')
        if password_baru != konfirmasi:
            errors.append('Konfirmasi password baru tidak cocok.')
        if password_lama and password_baru and password_lama == password_baru:
            errors.append('Password baru tidak boleh sama dengan password lama.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('admin_ganti_password.html')

        current_user.set_password(password_baru)
        db.session.commit()
        flash('Password admin berhasil diganti. Gunakan password baru untuk login berikutnya.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_ganti_password.html')


# ---------------------------------------------------------------------------
# CLI: inisialisasi database & admin default
# ---------------------------------------------------------------------------

@app.cli.command('init-db')
def init_db():
    """Membuat tabel database dan akun admin default."""
    db.create_all()
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Admin default dibuat -> username: admin | password: admin123')
    else:
        print('Database sudah siap.')


def create_default_admin():
    db.create_all()
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()


# Dijalankan otomatis saat modul di-import oleh server mana pun (flask run, python app.py, gunicorn).
# Aman dipanggil berulang karena create_default_admin() mengecek data yang sudah ada terlebih dahulu.
with app.app_context():
    try:
        create_default_admin()
    except Exception as e:
        print(f'Peringatan: inisialisasi database tertunda ({e}). '
              f'Pastikan environment variable DATABASE_URL sudah benar.')


if __name__ == '__main__':
    app.run(debug=True)
