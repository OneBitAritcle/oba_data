import sys
import airflow
import os

print("--- Python Executable ---")
print(sys.executable)
print("\n" + "="*40 + "\n")

print("--- sys.path (Python Library Search Order) ---")
# 경로 목록을 하나씩 출력
for i, path in enumerate(sys.path):
    print(f"{i}: {path}")
print("\n" + "="*40 + "\n")

print("--- Airflow library is actually loaded from ---")
print(os.path.dirname(airflow.__file__))
print("\n" + "="*40 + "\n")

print("--- PYTHONPATH Environment Variable ---")
pythonpath = os.environ.get('PYTHONPATH')
if pythonpath:
    print("WARNING: PYTHONPATH is set!")
    print(pythonpath)
else:
    print("PYTHONPATH is not set. (Good)")