from flask import Blueprint, request, flash, session, redirect, url_for, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import UserInfos
from extensions import db
from services.form_data_service import UserFormService
import logging
import uuid

user_bp = Blueprint("user", __name__, url_prefix="/user")
logger = logging.getLogger(__name__)


def login_required(f):
    """確保用戶已登入的裝飾器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash({'message': '請先登入'}, 'error')
            return redirect(url_for('homepage'))
        return f(*args, **kwargs)

    return decorated_function


@user_bp.route('/register', methods=['POST'])
def register():
    """處理用戶註冊"""
    try:
        logger.info("Received registration request")
        form_data = {
            'nickname': request.form.get('registerNickname'),
            'account': request.form.get('registerAccount'),
            'password': request.form.get('registerPassword'),
            'confirm_password': request.form.get('registerConfirmPassword')
        }

        # 驗證表單
        is_valid, error_message = UserFormService.validate_register_form(form_data)
        if not is_valid:
            logger.warning(f"Form validation failed: {error_message}")
            flash({'message': error_message}, 'error')
            return redirect(url_for('homepage'))

        # 創建新用戶
        new_user = UserInfos(
            account=form_data['account'],
            password=form_data['password'],
            real_name=form_data['nickname']
        )

        try:
            db.session.add(new_user)
            db.session.commit()

            # UUID 將自動生成，我們可以直接使用
            user_uuid = str(new_user.u_id)
            logger.info(f"Successfully created user with id: {user_uuid}")

            # 設置 session
            session.clear()
            session['user_id'] = user_uuid
            session.modified = True

            flash({
                'message': '註冊成功！',
                'uuid': user_uuid
            }, 'success')

        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}")
            db.session.rollback()
            flash({'message': '註冊失敗，該帳號可能已被使用'}, 'error')
            return redirect(url_for('homepage'))

        return redirect(url_for('homepage'))

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        flash({'message': f'註冊失敗：{str(e)}'}, 'error')
        return redirect(url_for('homepage'))


@user_bp.route('/login', methods=['POST'])
def login():
    """處理用戶登入"""
    try:
        logger.info("Received login request")
        form_data = {
            'account': request.form.get('loginAccount'),
            'password': request.form.get('loginPassword')
        }

        user = db.session.query(UserInfos).filter_by(account=form_data['account']).first()
        if not user or user.password != form_data['password']:
            flash({'message': '帳號或密碼錯誤'}, 'error')
            return redirect(url_for('homepage'))

        # 設置 session
        session.clear()
        session['user_id'] = str(user.u_id)
        session.modified = True

        flash({'message': f'登入成功！歡迎回來, {user.real_name}'}, 'success')
        return redirect(url_for('homepage'))

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        flash({'message': '登入失敗，請稍後再試'}, 'error')
        return redirect(url_for('homepage'))

@user_bp.route('/logout', methods=['POST'])
def logout():
    """處理用戶登出"""
    try:
        session.clear()
        flash({'message': '已成功登出'}, 'success')
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        flash({'message': '登出時發生錯誤'}, 'error')
    return redirect(url_for('homepage'))