from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

app = Flask(__name__)
CORS(app)

# 配置
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# JWT配置
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'  # 生产环境中应使用更复杂的密钥
app.config['JWT_EXPIRATION_DELTA'] = timedelta(days=1)  # JWT过期时间

# 确保必要的目录存在
os.makedirs('data', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

# JWT工具函数
def generate_token(user_id, username):
    """生成JWT token"""
    payload = {
        'exp': datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA'],
        'iat': datetime.utcnow(),
        'user_id': user_id,
        'username': username
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def decode_token(token):
    """解码JWT token"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token已过期'}
    except jwt.InvalidTokenError:
        return {'error': 'Token无效'}

# JWT认证中间件
from functools import wraps
def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': '缺少认证token'}), 401
        
        # 验证token
        payload = decode_token(token)
        if 'error' in payload:
            return jsonify({'error': payload['error']}), 401
        
        # 将用户信息添加到请求上下文
        request.user_id = payload['user_id']
        request.username = payload['username']
        
        return f(*args, **kwargs)
    return decorated

# 可选的JWT验证中间件（不强制要求认证，但提供的token必须有效）
def jwt_optional(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # 如果有token，则必须验证其有效性
        if token:
            payload = decode_token(token)
            if payload and 'error' in payload:
                # 如果提供了token但无效，则返回错误而不是继续执行
                return jsonify({'error': payload['error']}), 401
            elif payload and 'error' not in payload:
                # 如果token有效，则提取用户信息
                request.user_id = payload['user_id']
                request.username = payload['username']
        else:
            # 如果没有提供token, 直接阻断请求
            return jsonify({'error': '缺少认证token'}), 401



        
        # 没有提供token时继续执行
        return f(*args, **kwargs)
    return decorated

# 数据文件路径
USERS_FILE = 'data/users.json'
CORNERS_FILE = 'data/corners.json'

# 初始化数据文件
def init_data_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    
    if not os.path.exists(CORNERS_FILE):
        with open(CORNERS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    else:
        # 为现有角落添加share_id（如果不存在）
        corners = load_corners()
        updated = False
        for corner in corners:
            if 'share_id' not in corner:
                corner['share_id'] = str(uuid.uuid4())
                updated = True
        if updated:
            save_corners(corners)

# 读取数据
def load_users():
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def load_corners():
    try:
        with open(CORNERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

# 保存数据
def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def save_corners(corners):
    with open(CORNERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(corners, f, ensure_ascii=False, indent=2)

# 工具函数
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def find_user_by_username(username):
    users = load_users()
    return next((user for user in users if user['username'] == username), None)

def find_user_by_id(user_id):
    users = load_users()
    return next((user for user in users if user['id'] == user_id), None)
    
# 好友系统工具函数
def get_user_friends(user_id):
    """获取用户的好友列表"""
    user = find_user_by_id(user_id)
    if user:
        return user.get('friends', [])
    return []

def add_friend_request(sender_id, receiver_id):
    """发送好友请求"""
    users = load_users()
    
    # 检查用户是否存在
    sender = find_user_by_id(sender_id)
    receiver = find_user_by_id(receiver_id)
    
    if not sender or not receiver:
        return False, '用户不存在'
    
    # 检查是否已经是好友
    if receiver_id in sender.get('friends', []):
        return False, '已经是好友'
    
    # 检查是否已经发送过请求
    for user in users:
        if user['id'] == receiver_id:
            friend_requests = user.get('friend_requests', [])
            if sender_id in friend_requests:
                return False, '好友请求已发送'

    # 添加好友请求
    for user in users:
        if user['id'] == receiver_id:
            if 'friend_requests' not in user:
                user['friend_requests'] = []
            if sender_id not in user['friend_requests']:
                user['friend_requests'].append(sender_id)

    save_users(users)
    return True, '好友请求已发送'

def accept_friend_request(receiver_id, sender_id):
    """接受好友请求"""
    users = load_users()
    
    # 检查用户是否存在
    receiver = find_user_by_id(receiver_id)
    sender = find_user_by_id(sender_id)
    
    if not receiver or not sender:
        return False, '用户不存在'
    
    # 检查好友请求是否存在
    friend_requests = receiver.get('friend_requests', [])
    if sender_id not in friend_requests:
        return False, '好友请求不存在'

    # 双向添加好友
    for user in users:
        if user['id'] == receiver_id:
            # 移除好友请求
            user['friend_requests'].remove(sender_id)
            # 添加好友
            if 'friends' not in user:
                user['friends'] = []
            if sender_id not in user['friends']:
                user['friends'].append(sender_id)
        elif user['id'] == sender_id:
            # 添加好友
            if 'friends' not in user:
                user['friends'] = []
            if receiver_id not in user['friends']:
                user['friends'].append(receiver_id)

    save_users(users)
    return True, '好友请求已接受'

def reject_friend_request(receiver_id, sender_id):
    """拒绝好友请求"""
    users = load_users()
    
    # 检查用户是否存在
    receiver = find_user_by_id(receiver_id)
    if not receiver:
        return False, '用户不存在'
    
    # 检查好友请求是否存在
    friend_requests = receiver.get('friend_requests', [])
    if sender_id not in friend_requests:
        return False, '好友请求不存在'

    # 移除好友请求
    for user in users:
        if user['id'] == receiver_id:
            user['friend_requests'].remove(sender_id)

    save_users(users)
    return True, '好友请求已拒绝'

def remove_friend(user_id, friend_id):
    """删除好友"""
    users = load_users()
    
    # 检查用户是否存在
    user = find_user_by_id(user_id)
    friend = find_user_by_id(friend_id)
    
    if not user or not friend:
        return False, '用户不存在'
    
    # 检查是否是好友
    if friend_id not in user.get('friends', []):
        return False, '不是好友'

    # 双向删除好友
    for user in users:
        if user['id'] == user_id:
            user['friends'].remove(friend_id)
        elif user['id'] == friend_id:
            user['friends'].remove(user_id)

    save_users(users)
    return True, '好友已删除'
    

def get_friend_requests(user_id):
    """获取用户的好友请求列表"""
    user = find_user_by_id(user_id)
    if user:
        return user.get('friend_requests', [])
    return []

# API 路由

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Urban Canvas API is running'})

# 用户注册
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    username = data['username'].strip()
    password = data['password']
    
    if len(username) < 3:
        return jsonify({'error': '用户名至少3个字符'}), 400
    
    if len(password) < 6:
        return jsonify({'error': '密码至少6个字符'}), 400
    
    # 检查用户名是否已存在
    if find_user_by_username(username):
        return jsonify({'error': '用户名已存在'}), 409
    
    # 创建新用户
    users = load_users()
    new_user = {
        'id': str(uuid.uuid4()),
        'username': username,
        'password_hash': generate_password_hash(password),
        'created_at': datetime.now().isoformat()
    }
    
    users.append(new_user)
    save_users(users)
    
    # 返回用户信息（不包含密码）
    user_info = {k: v for k, v in new_user.items() if k != 'password_hash'}
    return jsonify({'message': '注册成功', 'user': user_info}), 201

# 用户登录
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    username = data['username'].strip()
    password = data['password']
    
    user = find_user_by_username(username)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    # 生成JWT token
    token = generate_token(user['id'], user['username'])
    
    # 返回用户信息和token（不包含密码）
    user_info = {k: v for k, v in user.items() if k != 'password_hash'}
    return jsonify({
        'message': '登录成功', 
        'user': user_info,
        'token': token
    })

# 获取角落列表
@app.route('/api/corners', methods=['GET'])
@jwt_optional
def get_corners():
    corners = load_corners()
    
    # 获取当前用户ID（从JWT或查询参数）
    current_user_id = None
    if hasattr(request, 'user_id'):
        # 优先从JWT获取用户ID
        current_user_id = request.user_id
    else:
        # 兼容旧方式，从查询参数获取
        current_user_id = request.args.get('user_id')
    
    # 隐私角落过滤：根据可见性策略过滤
    filtered_corners = []
    for corner in corners:
        # 检查用户是否有权访问
        if can_access_corner(current_user_id, corner):
            filtered_corners.append(corner)
    corners = filtered_corners
    
    # 获取查询参数
    tags = request.args.get('tags')  # 多个标签，逗号分隔
    search = request.args.get('search')
    
    # 标签筛选
    if tags:
        # 多标签搜索：支持逗号分隔的多个标签
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        if tag_list:
            corners = [c for c in corners if 
                      any(tag in c.get('tags', []) for tag in tag_list)]
    
    # 文本搜索
    if search:
        search_lower = search.lower()
        corners = [c for c in corners if 
                  search_lower in c.get('title', '').lower() or 
                  search_lower in c.get('description', '').lower() or
                  search_lower in c.get('address', '').lower()]
    
    # 按创建时间倒序排列
    corners.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # 处理每个角落，确保返回的点赞数为liked_users的长度
    for corner in corners:
        corner['likes'] = len(corner.get('liked_users', []))
    
    return jsonify({'corners': corners})


# 创建新角落
@app.route('/api/corners', methods=['POST'])
@jwt_required
def create_corner():
    # 检查是否有文件上传
    if 'image' not in request.files:
        return jsonify({'error': '请上传图片'}), 400
    
    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': '请上传有效的图片文件'}), 400
    
    # 获取表单数据
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    address = request.form.get('address', '').strip()
    tags = request.form.get('tags', '').strip()
    
    # 从JWT中获取用户信息
    user_id = request.user_id
    
    # 验证必填字段
    if not all([title, description, latitude, longitude]):
        return jsonify({'error': '请填写所有必填字段'}), 400
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        return jsonify({'error': '经纬度格式错误'}), 400
    
    # 保存图片
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower()
    new_filename = f"{uuid.uuid4().hex}.{file_ext}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
    file.save(file_path)
    
    # 创建新角落
    corners = load_corners()
    # 获取隐私设置，默认为公开
    visibility = request.form.get('visibility', 'public')
    specific_friends = request.form.get('specific_friends', '').split(',') if request.form.get('specific_friends') else []
    exclude_friends = request.form.get('exclude_friends', '').split(',') if request.form.get('exclude_friends') else []
    
    # 清理空值
    specific_friends = [friend.strip() for friend in specific_friends if friend.strip()]
    exclude_friends = [friend.strip() for friend in exclude_friends if friend.strip()]
    
    new_corner = {
        'id': str(uuid.uuid4()),
        'share_id': str(uuid.uuid4()),  # 生成分享ID
        'title': title,
        'description': description,
        'latitude': latitude,
        'longitude': longitude,
        'address': address,
        'tags': [tag.strip() for tag in tags.split(',') if tag.strip()],
        'image_url': f'/uploads/{new_filename}',
        'user_id': user_id,
        'created_at': datetime.now().isoformat(),
        'visibility': visibility,  # 隐私策略类型
        'specific_friends': specific_friends,  # 指定可见的好友ID列表
        'exclude_friends': exclude_friends,  # 指定不可见的好友ID列表
        'liked_users': [],
        'favorited_users': [],
        'comments': []
    }
    
    corners.append(new_corner)
    save_corners(corners)
    
    return jsonify({'message': '角落创建成功', 'corner': new_corner}), 201

# 获取所有标签（预设标签）
@app.route('/api/tags', methods=['GET'])
def get_tags():
    # 预设标签列表
    preset_tags = [
        '美食', '旅行', '运动', '艺术', '摄影',
        '阅读', '音乐', '电影', '宠物', '自然'
    ]
    
    # 获取搜索参数
    search_query = request.args.get('q', '').strip()
    
    # 如果有搜索参数，进行模糊过滤
    if search_query:
        filtered_tags = [tag for tag in preset_tags if search_query.lower() in tag.lower()]
        return jsonify({'tags': sorted(filtered_tags)})
    
    return jsonify({'tags': sorted(preset_tags)})

# 点赞功能
@app.route('/api/corners/<corner_id>/like', methods=['POST'])
@jwt_required
def like_corner(corner_id):
    # 从JWT中获取用户信息
    user_id = request.user_id
    
    corners = load_corners()
    corner = next((c for c in corners if c['id'] == corner_id), None)
    
    if not corner:
        return jsonify({'error': '角落不存在'}), 404
    
    # 初始化liked_users数组（如果不存在）
    if 'liked_users' not in corner:
        corner['liked_users'] = []
    
    # 检查用户是否已点赞
    if user_id in corner['liked_users']:
        # 取消点赞
        corner['liked_users'].remove(user_id)
        message = '取消点赞成功'
        is_liked = False
    else:
        # 添加点赞
        corner['liked_users'].append(user_id)
        message = '点赞成功'
        is_liked = True
    
    save_corners(corners)
    
    return jsonify({
        'message': message, 
        'likes': len(corner['liked_users']),
        'is_liked': is_liked
    })

# 获取角落详情（包含用户点赞和收藏状态）
@app.route('/api/corners/<corner_id>', methods=['GET'])
def get_corner_detail(corner_id):
    corners = load_corners()
    corner = next((c for c in corners if c['id'] == corner_id), None)
    
    if not corner:
        return jsonify({'error': '角落不存在'}), 404
    
    # 获取用户ID（用于隐私检查和显示点赞收藏状态）
    user_id = request.args.get('user_id')
    
    # 隐私检查：根据可见性策略检查访问权限
    visibility = corner.get('visibility', 'public')
    corner_owner_id = corner.get('user_id')
    
    # 检查用户是否有权访问
    if not can_access_corner(user_id, corner):
        return jsonify({'error': '无权访问此角落'}), 403
    
    is_liked = False
    is_favorited = False
    
    if user_id:
        if 'liked_users' in corner:
            is_liked = user_id in corner['liked_users']
        if 'favorited_users' in corner:
            is_favorited = user_id in corner['favorited_users']
    
    # 复制corner对象，避免修改原始数据
    corner_data = corner.copy()
    # 确保返回点赞数为liked_users的长度
    corner_data['likes'] = len(corner.get('liked_users', []))
    
    # 返回角落详情和状态
    return jsonify({
        'corner': corner_data,
        'is_liked': is_liked,
        'is_favorited': is_favorited
    })

# 收藏功能
@app.route('/api/corners/<corner_id>/favorite', methods=['POST'])
@jwt_required
def favorite_corner(corner_id):
    # 从JWT中获取用户信息
    user_id = request.user_id
    
    corners = load_corners()
    corner = next((c for c in corners if c['id'] == corner_id), None)
    
    if not corner:
        return jsonify({'error': '角落不存在'}), 404
    
    # 初始化favorited_users数组（如果不存在）
    if 'favorited_users' not in corner:
        corner['favorited_users'] = []
    
    # 检查用户是否已收藏
    if user_id in corner['favorited_users']:
        # 取消收藏
        corner['favorited_users'].remove(user_id)
        message = '取消收藏成功'
        is_favorited = False
    else:
        # 添加收藏
        corner['favorited_users'].append(user_id)
        message = '收藏成功'
        is_favorited = True
    
    save_corners(corners)
    
    return jsonify({
        'message': message, 
        'favorites_count': len(corner['favorited_users']),
        'is_favorited': is_favorited
    })

# 获取用户收藏的角落列表
@app.route('/api/users/<user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    # 验证用户是否存在
    if not find_user_by_id(user_id):
        return jsonify({'error': '用户不存在'}), 404
    
    corners = load_corners()
    # 筛选出用户收藏的角落，并考虑隐私设置
    favorited_corners = []
    for corner in corners:
        # 检查是否收藏
        is_favorited = 'favorited_users' in corner and user_id in corner['favorited_users']
        # 检查隐私权限：使用新的访问控制逻辑
        can_see = can_access_corner(user_id, corner)
        
        if is_favorited and can_see:
            favorited_corners.append(corner)
    
    return jsonify({
        'corners': favorited_corners,
        'count': len(favorited_corners)
    })

# 添加评论功能
@app.route('/api/corners/<corner_id>/comment', methods=['POST'])
@jwt_required
def add_comment(corner_id):
    data = request.get_json()
    
    # 从JWT中获取用户信息
    user_id = request.user_id
    
    if not data or not data.get('content'):
        return jsonify({'error': '评论内容不能为空'}), 400
    
    content = data['content'].strip()
    
    if len(content) == 0:
        return jsonify({'error': '评论内容不能为空'}), 400
    
    # 获取用户信息
    user = find_user_by_id(user_id)
    
    corners = load_corners()
    corner = next((c for c in corners if c['id'] == corner_id), None)
    
    if not corner:
        return jsonify({'error': '角落不存在'}), 404
    
    # 确保comments字段存在
    if 'comments' not in corner:
        corner['comments'] = []
    
    # 创建新评论
    new_comment = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'username': user['username'],
        'content': content,
        'created_at': datetime.now().isoformat()
    }
    
    corner['comments'].append(new_comment)
    save_corners(corners)
    
    return jsonify({'message': '评论成功', 'comment': new_comment}), 201

# 删除评论功能
@app.route('/api/corners/<corner_id>/comments/<comment_id>', methods=['DELETE'])
@jwt_required
def delete_comment(corner_id, comment_id):
    # 从JWT中获取用户信息
    user_id = request.user_id
    
    corners = load_corners()
    corner = next((c for c in corners if c['id'] == corner_id), None)
    
    if not corner:
        return jsonify({'error': '角落不存在'}), 404
    
    # 查找评论
    comments = corner.get('comments', [])
    comment_index = next((i for i, c in enumerate(comments) if c['id'] == comment_id), -1)
    
    if comment_index == -1:
        return jsonify({'error': '评论不存在'}), 404
    
    # 校验是否是自己的评论
    if comments[comment_index]['user_id'] != user_id:
        return jsonify({'error': '无权删除此评论'}), 403
    
    # 删除评论
    comments.pop(comment_index)
    save_corners(corners)
    
    return jsonify({'message': '评论删除成功'}), 200

# 删除角落功能
@app.route('/api/corners/<corner_id>', methods=['DELETE'])
@jwt_required
def delete_corner(corner_id):
    # 从JWT中获取用户信息
    user_id = request.user_id
    
    corners = load_corners()
    corner_index = next((i for i, c in enumerate(corners) if c['id'] == corner_id), -1)
    
    if corner_index == -1:
        return jsonify({'error': '角落不存在'}), 404
    
    # 校验是否是自己的角落
    if corners[corner_index]['user_id'] != user_id:
        return jsonify({'error': '无权删除此角落'}), 403
    
    # 删除角落
    deleted_corner = corners.pop(corner_index)
    save_corners(corners)
    
    return jsonify({'message': '角落删除成功'}), 200

# 更新角落功能
@app.route('/api/corners/<corner_id>', methods=['PUT'])
@jwt_required
def update_corner(corner_id):
    # 从JWT中获取用户信息
    user_id = request.user_id
    
    corners = load_corners()
    corner_index = next((i for i, c in enumerate(corners) if c['id'] == corner_id), -1)
    
    if corner_index == -1:
        return jsonify({'error': '角落不存在'}), 404
    
    # 校验是否是自己的角落
    if corners[corner_index]['user_id'] != user_id:
        return jsonify({'error': '无权更新此角落'}), 403
    
    # 获取表单数据
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    address = request.form.get('address', '').strip()
    tags = request.form.get('tags', '').strip()
    visibility = request.form.get('visibility', 'public')
    specific_friends = request.form.get('specific_friends', '').split(',') if request.form.get('specific_friends') else []
    exclude_friends = request.form.get('exclude_friends', '').split(',') if request.form.get('exclude_friends') else []
    
    # 清理空值
    specific_friends = [friend.strip() for friend in specific_friends if friend.strip()]
    exclude_friends = [friend.strip() for friend in exclude_friends if friend.strip()]
    
    # 验证必填字段
    if not all([title, description, latitude, longitude]):
        return jsonify({'error': '请填写所有必填字段'}), 400
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        return jsonify({'error': '经纬度格式错误'}), 400
    
    # 更新角落信息
    corner = corners[corner_index]
    corner['title'] = title
    corner['description'] = description
    corner['latitude'] = latitude
    corner['longitude'] = longitude
    corner['address'] = address
    corner['tags'] = [tag.strip() for tag in tags.split(',') if tag.strip()]
    corner['visibility'] = visibility
    corner['specific_friends'] = specific_friends
    corner['exclude_friends'] = exclude_friends
    
    # 处理图片更新
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            # 保存新图片
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            new_filename = f"{uuid.uuid4().hex}.{file_ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            file.save(file_path)
            corner['image_url'] = f'/uploads/{new_filename}'
    
    save_corners(corners)
    
    return jsonify({'message': '角落更新成功', 'corner': corner}), 200

# 静态文件服务
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 公开访问的分享端点
@app.route('/api/share/<share_id>', methods=['GET'])
def get_shared_corner(share_id):
    """通过分享ID获取角落信息，无需认证"""
    corners = load_corners()
    corner = next((c for c in corners if c.get('share_id') == share_id), None)
    
    if not corner:
        return jsonify({'error': '分享链接无效或已过期'}), 404
    
    # 检查分享权限：只有公开角落或显式允许分享的角落才能被访问
    is_private = corner.get('privacy', False)
    # 对于通过分享ID访问的角落，即使是私有的也允许访问，因为分享ID本身就是访问凭证

    # 复制corner对象，避免修改原始数据
    corner_data = corner.copy()
    # 确保返回点赞数为liked_users的长度
    corner_data['likes'] = len(corner.get('liked_users', []))
    # 移除可能的敏感信息
    if 'share_id' in corner_data:
        del corner_data['share_id']
    
    return jsonify({'corner': corner_data})

# 生成/更新分享链接
@app.route('/api/corners/<corner_id>/share-link', methods=['POST'])
@jwt_required
def generate_share_link(corner_id):
    """为角落生成或重置分享链接"""
    # 从JWT中获取用户信息
    user_id = request.user_id
    
    corners = load_corners()
    corner = next((c for c in corners if c['id'] == corner_id), None)
    
    if not corner:
        return jsonify({'error': '角落不存在'}), 404
    
    # 生成新的分享ID
    corner['share_id'] = str(uuid.uuid4())
    save_corners(corners)
    
    # 返回分享信息
    share_link = f"/share/{corner['share_id']}"  # 前端路由
    return jsonify({
        'message': '分享链接生成成功',
        'share_link': share_link,
        'share_id': corner['share_id']
    })

# 好友系统API
# 搜索用户
@app.route('/api/users/search', methods=['GET'])
@jwt_required
def search_users():
    """搜索用户"""
    query = request.args.get('q', '').strip()
    current_user_id = request.user_id
    
    if not query:
        return jsonify({'error': '搜索关键词不能为空'}), 400
    
    users = load_users()
    results = []
    
    for user in users:
        # 排除当前用户
        if user['id'] == current_user_id:
            continue
        
        # 按用户名搜索
        if query.lower() in user['username'].lower():
            # 检查是否已经是好友
            is_friend = current_user_id in user.get('friends', [])
            
            # 检查是否有未处理的好友请求
            has_pending_request = False
            friend_requests = user.get('friend_requests', [])
            if current_user_id in friend_requests:
                has_pending_request = True
            
            results.append({
                'id': user['id'],
                'username': user['username'],
                'is_friend': is_friend,
                'has_pending_request': has_pending_request
            })
    
    return jsonify({'users': results})

# 发送好友请求
@app.route('/api/friends/request', methods=['POST'])
@jwt_required
def send_friend_request():
    """发送好友请求"""
    data = request.get_json()
    sender_id = request.user_id
    receiver_id = data.get('receiver_id')
    
    if not receiver_id:
        return jsonify({'error': '接收者ID不能为空'}), 400
    
    # 不能向自己发送好友请求
    if sender_id == receiver_id:
        return jsonify({'error': '不能向自己发送好友请求'}), 400
    
    success, message = add_friend_request(sender_id, receiver_id)
    if not success:
        return jsonify({'error': message}), 400
    
    return jsonify({'message': message})

# 处理好友请求
@app.route('/api/friends/request/<sender_id>', methods=['PUT'])
@jwt_required
def handle_friend_request(sender_id):
    """处理好友请求（接受/拒绝）"""
    data = request.get_json()
    receiver_id = request.user_id
    action = data.get('action')  # 'accept' 或 'reject'
    
    if action not in ['accept', 'reject']:
        return jsonify({'error': '无效的操作'}), 400
    
    if action == 'accept':
        success, message = accept_friend_request(receiver_id, sender_id)
    else:
        success, message = reject_friend_request(receiver_id, sender_id)
    
    if not success:
        return jsonify({'error': message}), 400
    
    return jsonify({'message': message})

# 获取好友列表
@app.route('/api/friends', methods=['GET'])
@jwt_required
def get_friends():
    """获取好友列表"""
    user_id = request.user_id
    
    users = load_users()
    friends = []
    
    # 找到当前用户
    current_user = find_user_by_id(user_id)
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 获取好友ID列表
    friend_ids = current_user.get('friends', [])
    
    # 构建好友信息列表
    for user in users:
        if user['id'] in friend_ids:
            friends.append({
                'id': user['id'],
                'username': user['username']
            })
    
    return jsonify({'friends': friends})

# 获取好友请求列表
@app.route('/api/friends/requests', methods=['GET'])
@jwt_required
def get_friend_requests_list():
    """获取好友请求列表"""
    user_id = request.user_id
    
    users = load_users()
    requests = []
    
    # 找到当前用户
    current_user = find_user_by_id(user_id)
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 获取好友请求ID列表
    request_ids = current_user.get('friend_requests', [])
    
    # 构建好友请求信息列表
    for user in users:
        if user['id'] in request_ids:
            requests.append({
                'id': user['id'],
                'username': user['username']
            })
    
    return jsonify({'requests': requests})

# 删除好友
@app.route('/api/friends/<friend_id>', methods=['DELETE'])
@jwt_required
def delete_friend(friend_id):
    """删除好友"""
    user_id = request.user_id
    
    success, message = remove_friend(user_id, friend_id)
    if not success:
        return jsonify({'error': message}), 400
    
    return jsonify({'message': message})

# 获取好友的角落列表
@app.route('/api/friends/<friend_id>/corners', methods=['GET'])
@jwt_required
def get_friend_corners(friend_id):
    """获取好友的角落列表，只返回对当前用户可见的角落"""
    current_user_id = request.user_id
    
    # 检查目标用户是否存在
    friend = find_user_by_id(friend_id)
    if not friend:
        return jsonify({'error': '用户不存在'}), 404
    
    # 检查是否是好友
    if not is_friend(current_user_id, friend_id):
        return jsonify({'error': '只有好友才能查看对方的角落'}), 403
    
    # 获取所有角落
    corners = load_corners()
    
    # 筛选出好友创建的且对当前用户可见的角落
    friend_corners = []
    for corner in corners:
        # 检查是否是好友创建的
        if corner.get('user_id') == friend_id:
            # 检查当前用户是否有权访问
            if can_access_corner(current_user_id, corner):
                friend_corners.append(corner)
    
    # 按创建时间倒序排列
    friend_corners.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # 处理每个角落，确保返回的点赞数为liked_users的长度
    for corner in friend_corners:
        corner['likes'] = len(corner.get('liked_users', []))
    
    return jsonify({'corners': friend_corners, 'count': len(friend_corners)})

# 检查用户是否有权访问角落
def can_access_corner(user_id, corner):
    """检查用户是否有权访问角落
    
    Args:
        user_id: 用户ID
        corner: 角落对象
    
    Returns:
        bool: 是否有权访问
    """
    # 角落创建者始终可以访问
    if user_id == corner.get('user_id'):
        return True
    
    # 获取可见性策略
    visibility = corner.get('visibility', 'public')
    
    if visibility == 'public':
        # 公开：所有人可见
        return True
    elif visibility == 'private':
        # 仅自己可见：只有创建者可见
        return False
    elif visibility == 'friends':
        # 仅好友可见：检查是否是好友
        return is_friend(user_id, corner.get('user_id'))
    elif visibility == 'specific_friends':
        # 指定好友可见：检查是否在指定列表中
        specific_friends = corner.get('specific_friends', [])
        return user_id in specific_friends
    elif visibility == 'exclude_friends':
        # 指定好友不可见：检查是否不在排除列表中
        exclude_friends = corner.get('exclude_friends', [])
        return user_id not in exclude_friends
    else:
        # 默认：公开
        return True

# 检查两个用户是否是好友
def is_friend(user_id1, user_id2):
    """检查两个用户是否是好友
    
    Args:
        user_id1: 用户1 ID
        user_id2: 用户2 ID
    
    Returns:
        bool: 是否是好友
    """
    users = load_users()
    user1 = find_user_by_id(user_id1)
    user2 = find_user_by_id(user_id2)
    
    if not user1 or not user2:
        return False
    
    # 检查用户1是否在用户2的好友列表中
    friends1 = user1.get('friends', [])
    friends2 = user2.get('friends', [])
    
    return user_id2 in friends1 and user_id1 in friends2

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    init_data_files()
    print("🎨 城事绘图后端服务启动中...")
    print("📁 数据存储：JSON 文件")
    print("🌐 服务地址：http://localhost:8000")
    app.run(debug=True, host='0.0.0.0', port=8000)