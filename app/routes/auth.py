from flask import Blueprint, request, session, flash, redirect, url_for, render_template
import random
from app.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('auth/register.html')

@auth_bp.route('/register', methods=['POST'])
def register_action():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()
    contact_info = request.form.get('contact_info', '').strip()
    
    if not username or not email or not password:
        flash('請填寫所有必填欄位。', 'danger')
        return redirect(url_for('auth.register_page'))
        
    if not email.endswith('.edu.tw'):
        flash('註冊電子信箱必須是學校信箱（結尾需為 .edu.tw）。', 'danger')
        return redirect(url_for('auth.register_page'))
        
    if len(password) < 8:
        flash('密碼長度至少需要 8 個字元。', 'danger')
        return redirect(url_for('auth.register_page'))
        
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('此電子信箱已被註冊。', 'danger')
        return redirect(url_for('auth.register_page'))
        
    # Generate 6-digit mock verification code
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    print(f"\n========================================\n[Verification Code for {email}]: {code}\n========================================\n", flush=True)
    
    try:
        User.create(
            email=email,
            password=password,
            username=username,
            contact_info=contact_info,
            is_verified=False,
            verification_code=code
        )
        session['verify_email'] = email
        flash('註冊成功！驗證碼已生成，請在您的終端機/控制台（Terminal Console）日誌中查看 6 位數驗證碼，並於下方輸入以完成驗證。', 'success')
        return redirect(url_for('auth.verify_page', email=email))
    except Exception as e:
        flash(f'註冊失敗，資料庫發生錯誤：{str(e)}', 'danger')
        return redirect(url_for('auth.register_page'))

@auth_bp.route('/verify', methods=['GET'])
def verify_page():
    email = request.args.get('email', session.get('verify_email', ''))
    return render_template('auth/verify.html', email=email)

@auth_bp.route('/verify', methods=['POST'])
def verify_action():
    email = request.form.get('email', '').strip().lower()
    code = request.form.get('verification_code', '').strip()
    
    if not email or not code:
        flash('請填寫所有欄位。', 'danger')
        return redirect(url_for('auth.verify_page', email=email))
        
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('找不到該註冊電子信箱。', 'danger')
        return redirect(url_for('auth.verify_page', email=email))
        
    if user.verification_code == code:
        try:
            user.update(is_verified=True, verification_code=None)
            session.pop('verify_email', None)
            flash('帳號驗證成功！您現在可以登入系統了。', 'success')
            return redirect(url_for('auth.login_page'))
        except Exception as e:
            flash(f'驗證更新失敗，錯誤：{str(e)}', 'danger')
            return redirect(url_for('auth.verify_page', email=email))
    else:
        flash('驗證碼錯誤，請重新輸入。', 'danger')
        return redirect(url_for('auth.verify_page', email=email))

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('auth/login.html')

@auth_bp.route('/login', methods=['POST'])
def login_action():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()
    
    if not email or not password:
        flash('請填寫電子信箱與密碼。', 'danger')
        return redirect(url_for('auth.login_page'))
        
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        flash('電子信箱或密碼錯誤。', 'danger')
        return redirect(url_for('auth.login_page'))
        
    if not user.is_verified:
        session['verify_email'] = email
        flash('您的帳號尚未通過驗證，請先輸入驗證碼開通。', 'warning')
        return redirect(url_for('auth.verify_page', email=email))
        
    session['user_id'] = user.id
    session['username'] = user.username
    flash(f'登入成功！歡迎回來，{user.username}。', 'success')
    return redirect(url_for('index'))

@auth_bp.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('您已成功登出系統。', 'success')
    return redirect(url_for('index'))
