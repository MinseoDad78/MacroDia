import os
import sys
import ctypes


class AdminProcess:

    def is_admin():
        """현재 프로세스가 관리자 권한으로 실행 중인지 확인"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def run_as_admin():
        """관리자 권한으로 현재 스크립트를 재실행"""
        if sys.platform != "win32":
            raise RuntimeError("이 코드는 Windows에서만 동작합니다.")

        script = os.path.abspath(sys.argv[0])  # 현재 스크립트 경로
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])  # 전달된 인자
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}" {params}', None, 1
            )
        except Exception as e:
            print(f"권한 상승 실패: {e}")
            sys.exit(1)

"""
if __name__ == "__main__":
    if not is_admin():
        print("관리자 권한이 필요합니다. 관리자 권한으로 재실행합니다.")
        run_as_admin()
        sys.exit(0)

    # 관리자 권한으로 실행된 후 수행할 작업
    print("관리자 권한으로 실행되었습니다.")
    input("계속하려면 Enter를 누르세요...")
"""