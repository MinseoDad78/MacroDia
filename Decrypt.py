import hashlib
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# --- 설정 ---
PASSWORD = "6130"
FILE_IN = '게임방용.dat'
FILE_OUT = '게임방용_decrypted.dat'

def remove_pkcs7_padding(data):
    """PKCS#7 패딩 제거"""
    if len(data) == 0:
        return data
    try:
        pad_len = data[-1]
        if pad_len > len(data) or pad_len == 0 or pad_len > 16:
            return data  # 패딩이 없는 것으로 간주
        
        # 패딩이 올바른지 검증
        for i in range(pad_len):
            if data[-(i+1)] != pad_len:
                return data  # 패딩이 잘못됨
        
        return data[:-pad_len]
    except:
        return data

def generate_keys(password):
    """다양한 방법으로 키 생성"""
    keys = {}
    
    # 방법 1: 단순 SHA256
    keys['SHA256'] = hashlib.sha256(password.encode()).digest()
    
    # 방법 2: MD5 (32바이트를 위해 두 번)
    md5_hash = hashlib.md5(password.encode()).digest()
    keys['MD5x2'] = md5_hash + md5_hash
    
    # 방법 3: SHA256을 두 번
    sha1 = hashlib.sha256(password.encode()).digest()
    keys['SHA256x2'] = hashlib.sha256(sha1).digest()
    
    # 방법 4: 패스워드를 32바이트로 패딩
    padded = password.encode().ljust(32, b'\x00')[:32]
    keys['PADDED'] = padded
    
    # 방법 5: 패스워드 반복
    repeated = (password * 10).encode()[:32]
    keys['REPEATED'] = repeated
    
    return keys

def try_decrypt_ecb(ciphertext, key, method_name):
    """ECB 모드로 복호화 시도"""
    try:
        cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(ciphertext) + decryptor.finalize()
        
        # 패딩 제거 시도
        unpadded = remove_pkcs7_padding(decrypted)
        
        print(f"✓ ECB + {method_name}: 성공 (원본: {len(ciphertext)}, 복호화: {len(unpadded)} 바이트)")
        return unpadded
    except Exception as e:
        print(f"✗ ECB + {method_name}: 실패 ({str(e)})")
        return None

def try_decrypt_cbc(ciphertext, key, method_name):
    """CBC 모드로 복호화 시도 (IV는 처음 16바이트)"""
    try:
        if len(ciphertext) < 16:
            return None
            
        iv = ciphertext[:16]
        encrypted_data = ciphertext[16:]
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # 패딩 제거 시도
        unpadded = remove_pkcs7_padding(decrypted)
        
        print(f"✓ CBC + {method_name}: 성공 (원본: {len(ciphertext)}, 복호화: {len(unpadded)} 바이트)")
        return unpadded
    except Exception as e:
        print(f"✗ CBC + {method_name}: 실패 ({str(e)})")
        return None

def try_decrypt_cbc_zero_iv(ciphertext, key, method_name):
    """CBC 모드로 복호화 시도 (IV는 0으로 고정)"""
    try:
        iv = b'\x00' * 16  # 제로 IV
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(ciphertext) + decryptor.finalize()
        
        # 패딩 제거 시도
        unpadded = remove_pkcs7_padding(decrypted)
        
        print(f"✓ CBC(Zero IV) + {method_name}: 성공 (원본: {len(ciphertext)}, 복호화: {len(unpadded)} 바이트)")
        return unpadded
    except Exception as e:
        print(f"✗ CBC(Zero IV) + {method_name}: 실패 ({str(e)})")
        return None

def main():
    print("=== AES256 복호화 시도 ===")
    print(f"패스워드: {PASSWORD}")
    print(f"입력 파일: {FILE_IN}")
    print()
    
    # 파일 읽기
    try:
        with open(FILE_IN, 'rb') as f:
            ciphertext = f.read()
        print(f"파일 크기: {len(ciphertext)} 바이트")
        print()
    except FileNotFoundError:
        print(f"오류: {FILE_IN} 파일을 찾을 수 없습니다.")
        return
    
    # 다양한 키 생성
    keys = generate_keys(PASSWORD)
    
    print("생성된 키들:")
    for name, key in keys.items():
        print(f"  {name}: {key.hex()[:32]}...")
    print()
    
    successful_decryptions = []
    
    # 모든 키와 모드 조합 시도
    for method_name, key in keys.items():
        print(f"--- {method_name} 키로 시도 ---")
        
        # ECB 모드
        result = try_decrypt_ecb(ciphertext, key, method_name)
        if result is not None:
            successful_decryptions.append(('ECB_' + method_name, result))
        
        # CBC 모드 (IV = 첫 16바이트)
        result = try_decrypt_cbc(ciphertext, key, method_name)
        if result is not None:
            successful_decryptions.append(('CBC_' + method_name, result))
        
        # CBC 모드 (제로 IV)
        result = try_decrypt_cbc_zero_iv(ciphertext, key, method_name)
        if result is not None:
            successful_decryptions.append(('CBC_ZERO_' + method_name, result))
        
        print()
    
    # 결과 저장
    if successful_decryptions:
        print("=== 복호화 성공! ===")
        for i, (name, data) in enumerate(successful_decryptions):
            filename = f"{FILE_OUT.replace('.dat', '')}_{name}.dat"
            with open(filename, 'wb') as f:
                f.write(data)
            print(f"저장됨: {filename} ({len(data)} 바이트)")
            
            # 처음 몇 바이트를 16진수와 텍스트로 표시
            preview = data[:50]
            hex_preview = preview.hex()
            try:
                text_preview = preview.decode('utf-8', errors='ignore')
            except:
                text_preview = preview.decode('latin-1', errors='ignore')
            
            print(f"  미리보기 (Hex): {hex_preview}")
            print(f"  미리보기 (Text): {repr(text_preview)}")
            print()
    else:
        print("=== 복호화 실패 ===")
        print("모든 시도가 실패했습니다.")
        print("가능한 원인:")
        print("1. 잘못된 패스워드")
        print("2. 다른 암호화 알고리즘 사용")
        print("3. 추가적인 키 유도 과정 필요 (PBKDF2, scrypt 등)")
        print("4. 다른 암호화 모드 사용")

if __name__ == "__main__":
    main()