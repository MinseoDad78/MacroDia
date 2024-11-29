from services.SelectWindows import QApplication, DiabloManagerApp
import sys
from services.UACAdmin import AdminProcess



def main():
    """관리자 권한 확인 후 DiabloManagerApp 실행"""
    if not AdminProcess.is_admin():
        print("관리자 권한이 필요합니다. 관리자 권한으로 재실행합니다.")
        AdminProcess.run_as_admin()
        sys.exit(0)  # 현재 프로세스 종료 후 관리자 권한으로 재실행된 프로세스만 실행
    else:
        print("관리자 권한으로 실행 중입니다.")
        app = QApplication(sys.argv)  # PyQt5 애플리케이션 초기화
        manager_app = DiabloManagerApp()
        manager_app.show()
        sys.exit(app.exec_())  # PyQt5 이벤트 루프 실행

if __name__ == "__main__":
    main()
