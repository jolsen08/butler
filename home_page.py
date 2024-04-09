import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
import csv
import ast
import json

st.set_page_config(page_title="Butler", page_icon='images/butler.png', layout="wide", initial_sidebar_state="collapsed", menu_items=None)

def csv_to_dict(file_path):
    data_dict = {}
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader, start=1):
            data_dict[f'row_{i}'] = row
    return data_dict

def replacer(string):
    replaced_string = string.replace(':', ' ').replace(',', ' ')
    return replaced_string


if 'authorized' not in st.session_state and 'login' not in st.session_state and 'signup' not in st.session_state:
    st.title("Welcome to Butler")
    st.write("Please Login or Sign Up")
    if st.button("Login"):
        st.session_state.login = True
        st.rerun()
    if st.button("Sign Up"):
        st.session_state.signup = True
        st.rerun()

elif 'login' in st.session_state and 'user_id' not in st.session_state:
    if st.session_state.login:
        col1, col2, col3 = st.columns(3)
        with col2:
            with st.form("Login Form"):
                
                username = st.text_input("Username")
                password = st.text_input("Password", type='password')
                if st.form_submit_button("Login"):
                    auth_df = pd.read_csv('authentication.csv')
                    if len(auth_df) == 0:
                        st.error("Username does not exist or Password does not match")
                    else:
                        matching_row = auth_df[auth_df['username'] == username].index
                        associated_password = auth_df.at[matching_row[0], 'password']
                        if password != associated_password:
                            st.error("Username does not exist or Password does not match")
                        else:
                            st.session_state.user_id = username
                            st.rerun()
    

elif 'signup' in st.session_state and 'new_username' not in st.session_state:
    col1, col2, col3 = st.columns(3)
    with col2:
        with st.form("Sign Up Form"):
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            username = st.text_input("Create a Username")
            password = st.text_input("Create a Password", type='password')
            password_confirm = st.text_input("Confirm Password", type='password')
            if st.form_submit_button("Next"):
                if password == password_confirm:
                    st.session_state.new_username = username
                    st.session_state.new_password = password
                    st.session_state.first_name = first_name
                    st.session_state.last_name = last_name
                
                    st.rerun()
                else:
                    st.error("Passwords do not match.")

elif 'new_username' in st.session_state and 'goal_1' not in st.session_state:
    with st.form("Questionnaire"):
        industry = st.text_input("What is your primary industry or area of work? (e.g., Marketing, Finance, Healthcare, Education)")
        org_size = st.selectbox("What is the size of your organization (number of employees)?", ['1-10','11-50','51-100','101-500','501+'])
        st.write("What are your top 3 business goals for the next year? (e.g., Increase brand awareness, improve customer satisfaction, boost sales)")
        goal_1 = st.text_input("Goal 1")
        goal_2 = st.text_input("Goal 2")
        goal_3 = st.text_input("Goal 3")
        kpis = st.checkbox("Do you track any key performance indicators (KPIs) related to your goals?")
        if st.form_submit_button("Next"):
            if kpis:
                st.session_state.kpis = True
                st.session_state.industry = industry
                st.session_state.org_size = org_size
                st.session_state.goal_1 = goal_1
                st.session_state.goal_2 = goal_2
                st.session_state.goal_3 = goal_3
                st.rerun()
            else:
                st.session_state.kpis = False
                st.session_state.industry = industry
                st.session_state.org_size = org_size
                st.session_state.goal_1 = goal_1
                st.session_state.goal_2 = goal_2
                st.session_state.goal_3 = goal_3
                st.rerun()

elif 'kpis' in st.session_state and 'kpi_goals' not in st.session_state:
    if st.session_state.kpis:
        with st.form("Questionnaire Continued"):
            kpi_goals = st.text_input("Please list 2-3 of your most important KPIs")
            data_sources = st.text_input("What data sources do you typically use to track your business performance? (e.g., CRM system, website analytics, social media data)")
            comfort_level = st.selectbox("How comfortable are you with data analysis and visualization tools?", ['Beginner','Intermediate','Advanced'])
            insights = st.text_input("What types of insights would be most valuable to you from your personal data? (e.g., Identify customer trends, track marketing campaign performance, analyze sales patterns)")
            update_interval = st.selectbox("How often would you like to receive updates and reports based on your data?", ['Daily','Weekly','Monthly','Quarterly'])
            preferred_format = st.selectbox("What is your preferred format for receiving data insights?",['Interactive Dashboard','Visual Reports','Text Summaries'])
            challenges = st.text_input("Do you have any specific challenges or questions you'd like your personal data analyst to answer?")
            if st.form_submit_button("Next"):
                st.session_state.kpi_goals = kpi_goals
                st.session_state.data_sources = data_sources
                st.session_state.comfort_level = comfort_level
                st.session_state.insights = insights
                st.session_state.update_interval = update_interval
                st.session_state.preferred_format = preferred_format
                st.session_state.challenges = challenges
                st.rerun()
    else:
        with st.form("Questionnaire Continued"):
            data_sources = st.text_input("What data sources do you typically use to track your business performance? (e.g., CRM system, website analytics, social media data)")
            comfort_level = st.selectbox("How comfortable are you with data analysis and visualization tools?", ['Beginner','Intermediate','Advanced'])
            insights = st.text_input("What types of insights would be most valuable to you from your personal data? (e.g., Identify customer trends, track marketing campaign performance, analyze sales patterns)")
            update_interval = st.selectbox("How often would you like to receive updates and reports based on your data?", ['Daily','Weekly','Monthly','Quarterly'])
            preferred_format = st.selectbox("What is your preferred format for receiving data insights?",['Interactive Dashboard','Visual Reports','Text Summaries'])
            challenges = st.text_input("Do you have any specific challenges or questions you'd like your personal data analyst to answer?")
            if st.form_submit_button("Next"):
                st.session_state.kpi_goals = 'None'
                st.session_state.data_sources = data_sources
                st.session_state.comfort_level = comfort_level
                st.session_state.insights = insights
                st.session_state.update_interval = update_interval
                st.session_state.preferred_format = preferred_format
                st.session_state.challenges = challenges
                st.rerun()

elif 'kpi_goals' in st.session_state and 'default' not in st.session_state:
    with st.form("Questionnaire Continued (last time)"):
        typical_workday = st.text_input("Describe your typical workday. What kind of data do you encounter most frequently?")
        magic_button = st.text_input("Imagine you have a magic button that instantly analyzes your data and provides a key business insight. What question would you ask it?")
        overwhelmed = st.text_input("How often do you feel overwhelmed by the amount of data available to you?")
        business_decision = st.text_input("In the past, have you made a business decision based on data analysis? If so, can you briefly describe the situation and outcome? If not, please leave this question blank.")
        frustrates = st.text_input("What frustrates you the most about the way you currently analyze your personal data?")
        if st.form_submit_button("Submit Smart Form"):
            with open('authentication.csv', 'a') as file:
                file.write(f'\n{st.session_state.new_username},{st.session_state.first_name},{st.session_state.last_name},{st.session_state.new_password},{replacer(st.session_state.industry)},{replacer(st.session_state.org_size)},{replacer(st.session_state.goal_1)},{replacer(st.session_state.goal_2)},{replacer(st.session_state.goal_3)},{st.session_state.kpis},{replacer(st.session_state.kpi_goals)},{replacer(st.session_state.data_sources)},{replacer(st.session_state.comfort_level)},{replacer(st.session_state.insights)},{replacer(st.session_state.update_interval)},{replacer(st.session_state.preferred_format)},{replacer(st.session_state.challenges)},{replacer(typical_workday)},{replacer(magic_button)},{replacer(overwhelmed)},{replacer(business_decision)},{replacer(frustrates)},{None}')
            for x in st.session_state:
                del st.session_state[x]
            st.session_state.default = True
            st.rerun()



elif 'user_id' in st.session_state:
    files_df = pd.read_csv("files.csv")
    files_df = files_df[files_df['username'] == st.session_state.user_id]
    if len(files_df) == 0:
        needs_files = True
    else:
        needs_files = False
    max_digit = 0
    files = os.listdir('files')
    for filename in files:
        digit = int(filename)
        if digit > max_digit:
            max_digit = digit
    df = pd.read_csv('authentication.csv')
    matching_row = df[df['username'] == st.session_state.user_id].index
    first_name = df.at[matching_row[0], 'first_name']
    st.title(f"Welcome, {first_name}")
    if needs_files:
        with st.form("File Uploader", clear_on_submit=True):
            file = st.file_uploader("Upload some Data!", type=['csv','xlsx'], accept_multiple_files=True, label_visibility="visible")

            if st.form_submit_button("Submit Data"):
                digit = max_digit + 1
                for uploaded_file in file:
                    if uploaded_file.type == 'application/vnd.ms-excel' or uploaded_file.type == 'text/csv':
                        with open(f'files/{digit}', 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                    with open('files.csv', 'a') as file:
                        file.write(f"\n{st.session_state.user_id},{digit}")
                    
                    digit += 1
                    
                st.success("Files Submitted Successfully!")
                st.rerun()
    else:
        GOOGLE_API_KEY = 'AIzaSyCGOmo2Z9gUCL3_d6WZ_Pa4qDgtdyKtaDo'
        genai.configure(api_key=GOOGLE_API_KEY)

        model = genai.GenerativeModel('gemini-pro')

        df = pd.read_csv('authentication.csv')
        matching_row = df[df['username'] == st.session_state.user_id].index
        first_name = df.at[matching_row[0], 'first_name']
        industry = df.at[matching_row[0], 'industry']
        org_size = df.at[matching_row[0], 'org_size']
        goal_1 = df.at[matching_row[0], 'goal_1']
        goal_2 = df.at[matching_row[0], 'goal_2']
        goal_3 = df.at[matching_row[0], 'goal_3']
        kpis = df.at[matching_row[0], 'kpis']
        kpi_goals = df.at[matching_row[0], 'kpi_goals']
        data_sources = df.at[matching_row[0], 'data_sources']
        comfort_level = df.at[matching_row[0], 'comfort_level']
        insights = df.at[matching_row[0], 'insights']
        update_interval = df.at[matching_row[0], 'update_interval']
        preferred_format = df.at[matching_row[0], 'preferred_format']
        challenges = df.at[matching_row[0], 'challenges']
        typical_workday = df.at[matching_row[0], 'typical_workday']
        magic_button = df.at[matching_row[0], 'magic_button']
        overwhelmed = df.at[matching_row[0], 'overwhelmed']
        business_decision = df.at[matching_row[0], 'business_decision']
        frustrates = df.at[matching_row[0], 'frustrates']



        test_prompt = f'''
        Your name is Butler. You are a personal data analyst for {first_name}. You are assigned to view his data and provide feedback as a data analyst.

        The person you are assisting was provided with a questionnaire. Here are the questions and results from this survey:
        What is your primary industry or area of work? (e.g., Marketing, Finance, Healthcare, Education): {industry}
        What is the size of your organization (number of employees)?: {org_size}
        What are your top 3 business goals for the next year? (e.g., Increase brand awareness, improve customer satisfaction, boost sales): {goal_1}, {goal_2}, {goal_3}
        Do you track any key performance indicators (KPIs) related to your goals?: {kpis}
        Please list 2-3 of the most important KPIs: {kpi_goals}
        What data sources do you typically use to track your business performance? (e.g., CRM system, website analytics, social media data): {data_sources}
        How comfortable are you with data analysis and visualization tools? (Beginner, Intermediate, Advanced): {comfort_level}
        What types of insights would be most valuable to you from your personal data? (e.g., Identify customer trends, track marketing campaign performance, analyze sales patterns): {insights}
        How often would you like to receive updates and reports based on your data? (Daily, Weekly, Monthly): {update_interval}
        What is your preferred format for receiving data insights? (Interactive dashboard, Visual reports, Text summaries): {preferred_format}
        Do you have any specific challenges or questions you'd like your personal data analyst to answer?: {challenges}
        Describe your typical workday. What kind of data do you encounter most frequently? (Open ended to understand data touchpoints): {typical_workday}
        Imagine you have a magic button that instantly analyzes your data and provides a key business insight. What question would you ask it?: {magic_button}
        How often do you feel overwhelmed by the amount of data available to you?: {overwhelmed}
        In the past, have you made a business decision based on data analysis? If so, can you briefly describe the situation and outcome?: {business_decision}
        What frustrates you the most about the way you currently analyze your personal data?: {frustrates}


        

        I'm giving you a matrix that represents the view of a webpage. Square 1 is the top left corner. Square 2 is the top middle square. Square 3 is the top right corner.
        Square 4 is the middle left square. Square 5 is the center square. Square 6 is the right middle square. Square 7 is the bottom left corner. Square 8 is the bottom middle square. Lastly, square 9 is the bottom right corner.


        Based on the responses from this individual, create a view based on their industry and what you think would be most helpful for them in terms of an analytical dashboard. Here are the following components you can put in each square:
        - line chart
        - bar chart
        - text
        - area chart
        - scatter chart
        - map
        - image
        - dataframe

        You can use the same element multiple times and you can use one or more elements not at all. Whatever is best for this user.


        Your response should follow the following format with exactness (nothing more, nothing less):
        [visual element],[visual element],[visual element]...

        and so on through 9 squares.
        '''
        df = pd.read_csv('authentication.csv')
        filtered_row = df[df['username'] == st.session_state.user_id].iloc[0]
        view = str(filtered_row['view'])

        # if st.button("Generate a New View"):
        #     response = model.generate_content(test_prompt)

        #     feedback = response.text
        #     feedback = feedback.replace('\n', '')

        #     # st.write(response.text)

        #     result_list = feedback.split(", ")
        
        #     condition = df['username'] == st.session_state.user_id
        #     input_list = str(result_list).replace('"','')
        #     input_list = input_list.replace(",","-")
        #     df.loc[condition, 'view'] = str(input_list)
        #     df.to_csv('authentication.csv', index=False)
        #     st.rerun()

        if view == '' or view == 'nan' or view is None:
            response = model.generate_content(test_prompt)

            feedback = response.text
            feedback = feedback.replace('\n', '')

            # st.write(response.text)

            result_list = feedback.split(", ")
            result_list = str(result_list).replace('"','').replace(",","-").replace("[",'').replace("]",'').replace("'",'')

            input_list_json = json.dumps(result_list)
        
            condition = df['username'] == st.session_state.user_id
            df.loc[condition, 'view'] = result_list
            df.to_csv('authentication.csv', index=False)
            st.rerun()
        
        else:
            df = pd.read_csv('authentication.csv')
            condition = df['username'] == st.session_state.user_id
            input_list = df.loc[condition, 'view'].iloc[0]  # Assuming there's only one matching row
            result_list = input_list.split("-")

            col1, col2, col3 = st.columns(3)
            for index, x in enumerate(result_list):
                if index <=2:
                    if index == 0:
                        with col1:
                            st.write(x)
                    elif index == 1:
                        with col2:
                            st.write(x)
                    elif index == 2:
                        with col3:
                            st.write(x)
                elif index <= 5:
                    if index == 3:
                        st.write('---')
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(x)
                    elif index == 4:
                        with col2:
                            st.write(x)
                    elif index == 5:
                        with col3:
                            st.write(x)
                else:
                    if index == 6:
                        st.write('---')
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(x)
                    elif index == 7:
                        with col2:
                            st.write(x)
                    elif index == 8:
                        with col3:
                            st.write(x)





        

        
        
            



                        




