import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 生成密码"password123"的哈希值
print(hash_password("123456"))
