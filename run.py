import subprocess


# Executa o FastAPI
subprocess.Popen(["uvicorn", "api:app", "--reload"])


# Executa o Streamlit
subprocess.run(["streamlit", "run", "app.py"])
