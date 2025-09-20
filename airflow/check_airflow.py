import inspect
from airflow.models.dag import DAG
import airflow

try:
    # 1. 현재 사용되는 airflow 라이브러리의 버전 출력
    print(f"Airflow version being used: {airflow.__version__}")
    print("-" * 30)

    # 2. DAG 클래스가 어디에서 로드되었는지 실제 파일 경로를 출력
    print("DAG class is loaded from file:")
    print(inspect.getfile(DAG))
    print("-" * 30)

    # 3. DAG 클래스의 __init__ 메서드가 어떤 인자들을 받는지 출력
    #    여기에 'timezone'이 있는지 확인하는 것이 핵심입니다.
    print("Arguments for DAG.__init__ method:")
    args = inspect.getfullargspec(DAG.__init__)
    print(args)
    print("-" * 30)

    if 'timezone' in args.kwonlyargs or 'timezone' in args.args:
        print("✅ SUCCESS: 'timezone' argument found.")
    else:
        print("❌ FAILURE: 'timezone' argument NOT found.")

except Exception as e:
    print(f"An error occurred: {e}")