import os
import winreg
import subprocess
import zipfile
import shutil
import webbrowser

def get_edge_version():
    """Edge 브라우저 버전을 확인하는 함수"""
    
    print("="*60)
    print("Microsoft Edge 버전 확인")
    print("="*60 + "\n")
    
    # 방법 1: 레지스트리에서 확인 (HKEY_CURRENT_USER)
    try:
        print("📋 레지스트리 확인 중...")
        key_path = r"SOFTWARE\Microsoft\Edge\BLBeacon"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        version, _ = winreg.QueryValueEx(key, "version")
        winreg.CloseKey(key)
        
        if version:
            print(f"✅ 성공! Edge 버전: {version}\n")
            return version
    except Exception as e:
        print(f"   ⚠️  HKEY_CURRENT_USER 실패")
    
    # 방법 2: 레지스트리에서 확인 (HKEY_LOCAL_MACHINE)
    try:
        print("📋 로컬머신 레지스트리 확인 중...")
        key_path = r"SOFTWARE\Microsoft\Edge\BLBeacon"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
        version, _ = winreg.QueryValueEx(key, "version")
        winreg.CloseKey(key)
        
        if version:
            print(f"✅ 성공! Edge 버전: {version}\n")
            return version
    except Exception as e:
        print(f"   ⚠️  HKEY_LOCAL_MACHINE 실패")
    
    # 방법 3: 실행 파일에서 직접 확인
    try:
        print("📋 Edge 실행 파일 확인 중...")
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        
        for edge_path in edge_paths:
            if os.path.exists(edge_path):
                print(f"   파일 발견: {edge_path}")
                cmd = f'powershell "(Get-Item \'{edge_path}\').VersionInfo.FileVersion"'
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                version = result.stdout.strip()
                
                if version:
                    print(f"✅ 성공! Edge 버전: {version}\n")
                    return version
    except Exception as e:
        print(f"   ⚠️  실행 파일 확인 실패")
    
    print("❌ Edge 버전을 확인할 수 없습니다.\n")
    return None


def find_downloaded_zip(downloads_folder, edge_version):
    """다운로드 폴더에서 EdgeDriver zip 파일 찾기"""
    
    # 다운로드 폴더의 모든 zip 파일 확인
    if os.path.exists(downloads_folder):
        for filename in os.listdir(downloads_folder):
            if filename.lower().endswith('.zip') and 'edgedriver' in filename.lower():
                full_path = os.path.join(downloads_folder, filename)
                return full_path
    
    return None


def extract_edgedriver(zip_path, target_dir):
    """EdgeDriver 압축 해제"""
    
    print(f"\n📦 압축 해제 중...")
    print(f"   Zip 파일: {zip_path}")
    print(f"   대상 폴더: {target_dir}\n")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # zip 파일 내용 확인
            file_list = zip_ref.namelist()
            print(f"   압축 파일 내용: {file_list}\n")
            
            # msedgedriver.exe 찾기
            driver_in_zip = None
            for file in file_list:
                if file.endswith('msedgedriver.exe'):
                    driver_in_zip = file
                    break
            
            if driver_in_zip:
                # 압축 해제
                zip_ref.extract(driver_in_zip, target_dir)
                
                # 하위 폴더에 있을 경우 최상위로 이동
                extracted_path = os.path.join(target_dir, driver_in_zip)
                final_path = os.path.join(target_dir, "msedgedriver.exe")
                
                if extracted_path != final_path:
                    if os.path.exists(final_path):
                        os.remove(final_path)
                    shutil.move(extracted_path, final_path)
                    
                    # 빈 폴더 정리
                    extracted_dir = os.path.dirname(extracted_path)
                    if extracted_dir != target_dir and os.path.exists(extracted_dir):
                        try:
                            shutil.rmtree(extracted_dir)
                        except:
                            pass
                
                print(f"✅ 압축 해제 완료: {final_path}\n")
                return final_path
            else:
                print("❌ zip 파일에서 msedgedriver.exe를 찾을 수 없습니다.\n")
                return None
        
    except zipfile.BadZipFile:
        print(f"❌ 손상된 zip 파일입니다: {zip_path}\n")
        return None
    except Exception as e:
        print(f"❌ 압축 해제 실패: {e}\n")
        return None


def main():
    print("\n" + "="*60)
    print("EdgeDriver 설치 프로그램")
    print("="*60 + "\n")
    
    # 1. Edge 버전 확인
    edge_version = get_edge_version()
    
    if not edge_version:
        print("❌ Edge 버전을 확인할 수 없어 종료합니다.\n")
        input("엔터 키를 눌러 종료...")
        return
    
    print(f"🎯 확인된 Edge 버전: {edge_version}\n")
    
    # 2. 올바른 다운로드 URL 생성
    download_url = f"https://msedgedriver.microsoft.com/{edge_version}/edgedriver_win64.zip"
    
    print("="*60)
    print("다운로드 안내")
    print("="*60 + "\n")
    print("📥 다운로드 URL:")
    print(f"   {download_url}\n")
    
    # 3. 브라우저로 다운로드 페이지 열기
    print("🌐 브라우저로 다운로드 페이지를 여는 중...\n")
    try:
        webbrowser.open(download_url)
        print("✅ 브라우저가 열렸습니다.")
        print("   파일이 자동으로 다운로드됩니다.\n")
    except:
        print("⚠️  브라우저를 자동으로 열 수 없습니다.")
        print("   위 URL을 복사하여 브라우저에 붙여넣으세요.\n")
    
    # 4. 사용자 입력 대기
    print("="*60)
    print("다운로드 완료 후 계속하기")
    print("="*60 + "\n")
    print("📌 다운로드가 완료되면 아무 키나 눌러주세요...")
    input()
    
    # 5. 다운로드 폴더에서 zip 파일 찾기
    print("\n🔍 다운로드된 파일을 찾는 중...\n")
    
    # 일반적인 다운로드 폴더 경로
    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    
    zip_path = find_downloaded_zip(downloads_folder, edge_version)
    
    if not zip_path:
        print("❌ 다운로드 폴더에서 EdgeDriver zip 파일을 찾을 수 없습니다.\n")
        print(f"📁 확인한 경로: {downloads_folder}\n")
        
        # 수동 경로 입력
        print("📌 zip 파일의 전체 경로를 입력하거나 엔터를 눌러 종료:")
        manual_path = input("경로: ").strip().strip('"')
        
        if manual_path and os.path.exists(manual_path):
            zip_path = manual_path
        else:
            print("\n❌ 유효한 경로가 아닙니다. 종료합니다.\n")
            input("엔터 키를 눌러 종료...")
            return
    
    print(f"✅ 파일 발견: {zip_path}\n")
    
    # 6. 설치 경로 선택
    print("="*60)
    print("설치 경로 선택")
    print("="*60 + "\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"1. 현재 스크립트 폴더 (권장)")
    print(f"   {script_dir}")
    print(f"2. 다운로드 폴더")
    print(f"   {downloads_folder}")
    print("3. 사용자 지정 경로")
    
    choice = input("\n선택 (1, 2 또는 3): ").strip()
    
    if choice == "2":
        target_dir = downloads_folder
    elif choice == "3":
        custom_path = input("설치 경로 입력: ").strip().strip('"')
        if not os.path.exists(custom_path):
            print(f"\n❌ 경로가 존재하지 않습니다: {custom_path}")
            input("엔터 키를 눌러 종료...")
            return
        target_dir = custom_path
    else:
        target_dir = script_dir
    
    print(f"\n📁 설치 경로: {target_dir}\n")
    
    # 7. 압축 해제
    driver_path = extract_edgedriver(zip_path, target_dir)
    
    # 8. 결과 출력
    print("="*60)
    if driver_path and os.path.exists(driver_path):
        print("✅ 설치 완료!")
        print("="*60 + "\n")
        print(f"📍 EdgeDriver 위치:")
        print(f"   {driver_path}\n")
        
        # 다운로드한 zip 파일 삭제 여부 확인
        if os.path.dirname(zip_path) == downloads_folder:
            delete_zip = input("다운로드한 zip 파일을 삭제하시겠습니까? (y/n): ").lower()
            if delete_zip == 'y':
                try:
                    os.remove(zip_path)
                    print(f"✅ 삭제 완료: {zip_path}\n")
                except Exception as e:
                    print(f"⚠️  삭제 실패: {e}\n")
        
        print("💡 다음 단계:")
        print("   Battle.net 토큰 추출 스크립트에서 다음과 같이 사용:")
        print(f'\n   EDGE_DRIVER_PATH = r"{driver_path}"\n')
    else:
        print("❌ 설치 실패")
        print("="*60 + "\n")
    
    print("="*60 + "\n")
    input("엔터 키를 눌러 종료...")


if __name__ == "__main__":
    main()