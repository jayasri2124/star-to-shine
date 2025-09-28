
Star to Shine - Recruitment Chatbot 

Files created:
- app.py : Main Streamlit chatbot app
- requirements.txt : Python packages required

How to run locally:
1. Create a virtual environment and activate it thorugh the below commands

    python -m venv venv
    On Windows: venv\\Scripts\\activate
   

2. Install requirements(streamlit,pandas)

   pip install -r /mnt/data/requirements.txt

3. Run the Streamlit app:
   streamlit run /mnt/data/app.py

The app will open in your browser (usually at http://localhost:8501). The app stores applicants in a local SQLite database file 'star_to_shine.db' in the same directory.


this chatbot contains both the admin view, user view:
Admin view:
- Use the sidebar to switch to Admin mode to see/save/export applicants as CSV.
Deployed on Streamlit Cloud 


