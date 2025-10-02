import uuid

from flask import Flask, request, render_template, url_for, session, g, flash, redirect
from flask_session import Session
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db
from models import CityInfosMapping, PlaceTypes, UserInfos
from blueprints.trip_plan import trip_plan_bp
from blueprints.user import user_bp
from utils.jinja2_filters import init_jinja2_filters
from write_data import add_city_infos, add_place_types, add_keywords
from services.form_data_service import PreferenceFormService
from datetime import timedelta
import logging
import os
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 中間鍵，用於處理子路徑
class SubdomainMiddleware:
    """
    假設有以下請求：
    原始 URL: http://example.com/hanproj/users/profile

    environ 中的值：
    HTTP_X_SCRIPT_NAME = '/hanproj'
    SCRIPT_NAME = '' (初始為空)
    PATH_INFO = '/hanproj/users/profile'

    處理後的 environ：
    SCRIPT_NAME = '/hanproj'
    PATH_INFO = '/users/profile'
    """

    def __init__(self, app, subdomain=config.Config.APPLICATION_ROOT):
        self.app = app  # flask application instance
        self.subdomain = subdomain  # subdomain setting

    def __call__(self, environ, start_response):
        # 取得proxy server的腳本名稱
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        # 如果有
        if script_name:
            # 設置WSGI環境變數中的SCRIPT_NAME
            environ['SCRIPT_NAME'] = script_name
            # 獲取當前的請求路徑
            path_info = environ['PATH_INFO']
            # 如果路徑以SCRIPT_NAME開頭，則移除這個前綴
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        # 處理請求路徑，移除子路徑前綴
        if environ['PATH_INFO'].startswith(self.subdomain):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.subdomain):]
            environ['SCRIPT_NAME'] = self.subdomain

        return self.app(environ, start_response)


# 初始化flask應用
def create_app():
    app = Flask(__name__, static_url_path='', static_folder=config.Config.STATIC_FOLDER)
    app.config.from_object(config.Config)

    app.config.update(
        SECRET_KEY=config.Config.SECRET_KEY,
        SESSION_TYPE='filesystem',
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        SESSION_FILE_DIR=os.path.join(app.root_path, 'flask_session'),
        SESSION_COOKIE_SECURE=False,  # 開發環境設為 False，生產環境應設為 True
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_REFRESH_EACH_REQUEST=True
    )

    app.config.update(
        SECRET_KEY=config.Config.SECRET_KEY,  # 確保有設置 SECRET_KEY
        SESSION_TYPE='filesystem',
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),  # session 保存7天
        SESSION_FILE_DIR=os.path.join(app.root_path, 'flask_session'),
        SESSION_COOKIE_SECURE=False,  # 開發環境設為 False，生產環境應設為 True
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_REFRESH_EACH_REQUEST=True
    )

    # 建立 session 目錄
    if not os.path.exists(app.config['SESSION_FILE_DIR']):
        os.makedirs(app.config['SESSION_FILE_DIR'])

    # 初始化 Session
    Session(app)

    # 應用中間件
    app.wsgi_app = SubdomainMiddleware(app.wsgi_app, subdomain=config.Config.APPLICATION_ROOT)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # 初始化資料庫
    db.init_app(app)
    migrate = Migrate(app, db)

    # 註冊藍圖
    app.register_blueprint(trip_plan_bp)
    app.register_blueprint(user_bp)

    init_jinja2_filters(app)

    def custom_url_for(endpoint, **values):
        """自定義 url_for 函數"""

        # 抓取原始URL
        original_url = url_for(endpoint, **values)

        # 如果沒有加上/hanproj則自動加上
        if not original_url.startswith(config.Config.APPLICATION_ROOT):
            return f"{config.Config.APPLICATION_ROOT}{original_url}"

        return original_url

    @app.context_processor
    def utility_processor():
        """註冊自訂義url_for函數以覆蓋原本url_for函數"""
        return {'url_for': custom_url_for}

    @app.before_request
    def log_request_info():
        """request前顯示路徑，用於調適"""
        logger.debug('Headers: %s', request.headers)
        logger.debug('Path: %s', request.path)
        logger.debug('Script Root: %s', request.script_root)
        logger.debug('Base URL: %s', request.base_url)
        logger.debug('URL: %s', request.url)

    @app.after_request
    def log_response_info(response):
        """request後顯示置狀態，用於調適"""
        logger.debug('Response Status: %s', response.status)
        logger.debug('Response Headers: %s', response.headers)
        return response

    return app


app = create_app()


@app.before_request
def load_logged_in_user():
    """在每個請求前載入用戶信息"""
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        try:
            # 將字串轉換為UUID對象
            user_uuid = uuid.UUID(user_id)
            g.user = db.session.query(UserInfos).filter_by(u_id=user_uuid).first()
            if g.user is None:
                session.clear()
        except (ValueError, AttributeError) as e:
            logger.error(f"Error loading user: {str(e)}")
            g.user = None
            session.clear()


# 需要登入才能訪問的路由列表
LOGIN_REQUIRED_ROUTES = [
    'trip_plan.trip_planning',
    'trip_plan.show_result',
    'user.logout'
]

@app.before_request
def check_login_required():
    """檢查是否需要登入"""
    if request.endpoint in LOGIN_REQUIRED_ROUTES and g.user is None:
        flash({'message': '請先登入'}, 'error')
        return redirect(url_for('homepage'))


@app.route('/')
def homepage():
    form_data_service = PreferenceFormService(db.session)
    return form_data_service.render_home_page()


@app.route('/write_data')
def write_data():
    add_place_types()
    add_city_infos()
    add_keywords()
    attraction_types = db.session.query(PlaceTypes).all()
    city_infos = db.session.query(CityInfosMapping).all()
    return render_template('home.html', attraction_types=attraction_types, city_infos=city_infos)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
