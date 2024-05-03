import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
import csv
import ast
import json
import html
import time

st.set_page_config(page_title="Butler", page_icon='images/butler.png', layout="wide", initial_sidebar_state="collapsed", menu_items=None)

def csv_to_dict(file_path):
    data_dict = {}
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        row_count = sum(1 for row in reader)  # Count total rows
        csvfile.seek(0)  # Reset file pointer to beginning
        reader = csv.DictReader(csvfile)  # Re-initialize reader
        if row_count > 50:
            # Read only the first 100 rows
            for i, row in enumerate(reader, start=1):
                if i > 50:
                    break
                data_dict[f'row_{i}'] = row
        else:
            # Read all rows if there are 100 or fewer
            for i, row in enumerate(reader, start=1):
                data_dict[f'row_{i}'] = row
    return data_dict

def nav_page(page_name, timeout_secs=2):
    nav_script = """
        <script type="text/javascript">
            function attempt_nav_page(page_name, start_time, timeout_secs) {
                var links = window.parent.document.getElementsByTagName("a");
                for (var i = 0; i < links.length; i++) {
                    if (links[i].href.toLowerCase().endsWith("/" + page_name.toLowerCase())) {
                        links[i].click();
                        return;
                    }
                }
                var elasped = new Date() - start_time;
                if (elasped < timeout_secs * 1000) {
                    setTimeout(attempt_nav_page, 100, page_name, start_time, timeout_secs);
                } else {
                    alert("Unable to navigate to page '" + page_name + "' after " + timeout_secs + " second(s).");
                }
            }
            window.addEventListener("load", function() {
                attempt_nav_page("%s", new Date(), %d);
            });
        </script>
    """ % (page_name, timeout_secs)
    html(nav_script)



def replacer(string):
    replaced_string = string.replace(':', ' ').replace(',', ' ')
    return replaced_string

for filename in os.listdir('files'):
    if filename.endswith('.csv'):
        
        # Construct the full file path
        file_path = f'files/{filename}'
        df = pd.read_csv(file_path)
        
        for column in df.columns:
            if not column.endswith('_month') and not column.endswith('_year'):
                try:
            # Check if column values follow common date patterns
                    if df[column].str.match(r'\d{4}-\d{2}-\d{2}').all() or \
                    df[column].str.match(r'[A-Za-z]{3}\s\d{1,2},\s\d{4}').all() or \
                    df[column].str.match(r'\d{1,2}/\d{1,2}/\d{4}').all():
                        
                        df[column] = pd.to_datetime(df[column])
                        
                        df[f"{column}_month"] = df[column].dt.month
                        df[f"{column}_year"] = df[column].dt.year
                        
                        df.drop(columns=[column], inplace=True)  # Drop the original date column
                    
                except:
                    continue
        
        df.to_csv(f'files/{filename}', index=False)


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
    file_list = []
    for filename in os.listdir('files'):
        if filename.startswith(st.session_state.user_id):
            file_list.append(filename)

    if len(file_list) == 0:
        needs_files = True
    else:
        needs_files = False

    df = pd.read_csv('authentication.csv')
    matching_row = df[df['username'] == st.session_state.user_id].index
    first_name = df.at[matching_row[0], 'first_name']
    st.title(f"Welcome, {first_name}")
    loading_box = st.empty()
    progress_box = st.empty()
    if needs_files:
        with st.form("File Uploader", clear_on_submit=True):
            file = st.file_uploader("Upload some Data!", type=['csv','xlsx'], accept_multiple_files=True, label_visibility="visible")

            if st.form_submit_button("Submit Data"):
                # digit = max_digit + 1
                for uploaded_file in file:
                    if uploaded_file.type == 'application/vnd.ms-excel' or uploaded_file.type == 'text/csv':
                        with open(f'files/{st.session_state.user_id}_{uploaded_file.name}', 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                    
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


        I'm giving you a matrix that represents the view of a webpage (the top left corner will have a pre-built component). Square 1 is the top middle square. Square 2 is the top right square. Square 3 is the bottom left corner.
        Square 4 is the bottom middle square. Square 5 is the bottom right square.


        Based on the responses from this individual, create a view based on their industry and what you think would be most helpful for them in terms of an analytical dashboard. Here are the following components you can put in each square:
        - line chart
        - bar chart
        - text
        - area chart
        - scatter chart
        - dataframe

        You can use the same element multiple times and you can use one or more elements not at all. Whatever is best for this user.

        Your response should follow the following format with exactness (nothing more, nothing less):
        [visual element],[visual element],[visual element]...

        and so on through 5 squares. Make sure there is a comma in between each visual element name!
        '''


        df = pd.read_csv('authentication.csv')
        filtered_row = df[df['username'] == st.session_state.user_id].iloc[0]
        view = str(filtered_row['view'])

        if st.button("Generate a New View"):
            temp_df = pd.read_csv('visualizations.csv')
            for index, row in temp_df.iterrows():
                if row['user_id'] == st.session_state.user_id:
                    temp_df.drop(temp_df.index, inplace=True)
            
            temp_df.to_csv('visualizations.csv', index=False)

            response = model.generate_content(test_prompt)

            feedback = response.text
            feedback = feedback.replace('\n', '')

            # st.write(response.text)

            result_list = feedback.split(", ")
            result_list.insert(0, 'user_questions')
            result_list = str(result_list).replace('"','').replace(",","-").replace("[",'').replace("]",'').replace("'",'')
            

            input_list_json = json.dumps(result_list)
        
            condition = df['username'] == st.session_state.user_id
            df.loc[condition, 'view'] = result_list
            df.to_csv('authentication.csv', index=False)
            st.rerun()

        if view == '' or view == 'nan' or view is None:
            response = model.generate_content(test_prompt)

            feedback = response.text
            feedback = feedback.replace('\n', '')

            # st.write(response.text)

            result_list = feedback.split(", ")
            result_list.insert(0, 'user_questions')
            result_list = str(result_list).replace('"','').replace(",","-").replace("[",'').replace("]",'').replace("'",'')
            

            input_list_json = json.dumps(result_list)
        
            condition = df['username'] == st.session_state.user_id
            df.loc[condition, 'view'] = result_list
            df.to_csv('authentication.csv', index=False)
            visuals = ['line chart','bar chart','area chart', 'scatter chart']
            st.rerun()
        
        else:
            df = pd.read_csv('authentication.csv')
            condition = df['username'] == st.session_state.user_id
            input_list = df.loc[condition, 'view'].iloc[0]
            result_list = input_list.split("-")
            visuals = ['line chart','bar chart','area chart', 'scatter chart']

            col1, col2, col3 = st.columns(3)

            visuals_df = pd.read_csv('visualizations.csv')
            # vis_data = pd.read_csv('visualizations.csv')
            # vis_data = vis_data[vis_data['user_id'] == st.session_state.user_id]
            for filename in os.listdir('files'):
                if filename.startswith(st.session_state.user_id):
                    data_file = filename
                    # st.write(data_file)
            

            data = csv_to_dict(f'files/{data_file}')
            visuals_df = visuals_df[visuals_df['user_id'] == st.session_state.user_id]
            
            visuals_list = []
            for index, row in visuals_df.iterrows():
                visuals_list.append(row['column_1'])
                visuals_list.append(row['column_2'])
                visuals_list.append(row['group_by'])
                visuals_list.append(row['order_by'])
            
            if 'count_indicator' not in st.session_state:
                st.session_state.vis_count = 0

            st.session_state.count_indicator = True

            visual_count_list = []
            for item in result_list:
                if item in visuals:
                    visual_count_list.append('a')

            visual_count_number = len(visual_count_list)

            if 'load_statement' not in st.session_state:
                st.session_state.load_statement = 'Getting things set up...'
            if 'load_amount' not in st.session_state:
                st.session_state.load_amount = 0.01

     
            loading_box.warning(st.session_state.load_statement)
            progress_box.progress(st.session_state.load_amount)
            for index, x in enumerate(result_list):
                if index <=2:
                    if index == 0:
                        if st.session_state.load_statement == 'Getting things set up...':
                            st.session_state.load_statement = 'Setting up chat window...'
                        loading_box.warning(st.session_state.load_statement)
                        with col1:
                            with st.form("Q/A", clear_on_submit=True):
                                input_question = st.text_input("Ask Gemini a question about your data!")
                                if st.form_submit_button("Submit"):
                                    test_prompt = f'''
Your name is Butler. You are a personal data analyst for a person. You are assigned to view his/her data and provide feedback as a data analyst.

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

        
        This is the data that was provided: {data}


Based on the data, answer the following question briefly (a few sentences or less): {input_question}
'''
                                    response = model.generate_content(test_prompt)
                                    feedback = response.text
                                    st.write(feedback)
                        
                    elif index == 1:
                        if st.session_state.load_amount < .03:
                            st.session_state.load_amount = .03
                        progress_box.progress(st.session_state.load_amount)
                        if st.session_state.load_statement == 'Setting up chat window...':
                            st.session_state.load_statement = 'Setting up dashboard elements...'
                        loading_box.warning(st.session_state.load_statement)
                        with col2:
                            if x.strip().lower() in visuals:
                                loading_box.warning('Creating visualizations...')
                                column_values = visuals_df['vis_number'].astype(str).tolist()
                          
                                if st.session_state.user_id in visuals_df['user_id'].tolist():
                                    st.subheader(f"{visuals_list[1]} by {visuals_list[0]}")
                                    df = pd.read_csv(f'files/{data_file}')
                                    if visuals_list[2].lower() != 'none':
                                        df = df.groupby(visuals_list[2]).apply(lambda x: x.sort_values(visuals_list[3])).reset_index(drop=True)
                                    elif visuals_list[3].lower() != 'none':
                                        df = df.sort_values(by=visuals_list[3])
                
                         
                                    if x.strip().lower() == 'line chart':
                                        st.line_chart(data=df, x=visuals_list[0], y=visuals_list[1])
                                    elif x.strip().lower() == 'bar chart':
                                        st.bar_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#228B22')
                                    elif x.strip().lower() == 'area chart':
                                        st.area_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#ff8c00')
                                    elif x.strip().lower() == 'scatter chart':
                                        st.scatter_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#8B0000')
                                    
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)

                                else:
                                    st.session_state.vis_count += 1
                                    new_prompt = f'''
        Your name is Butler. You are a personal data analyst for a person. You are assigned to view his/her data and provide feedback as a data analyst.

        
        This is the data that was provided: {data}

        Based on this data, I want you to provide 2 column names and 2 additional column names to use for "group by" and "order by" functionality for pandas dataframes. These 4 elements of your output should be for the most useful {x}. Your output should include only 4 column names, separated by a single comma (no spaces). The last 2 column names are the following: the first being what the user should group the df by and the second being the what the user should order the df by. These can be the same or different columns as the first two of your output. 
        The first two column names should also be compatible with the data that would be required to create a proper {x}. You may need to analyze the data provided and designate each column as numerical, categorical, or date values so that you can provide the best columns as input for the {x}. The first column name will be used for the x axis, the second will be the y axis (I'll be using streamlit built-in functions for generating a {x} and it will require an x column and y column as parameters). Also, refrain from using any type of ID or unique name (such as customer names) as a column name.
        If you think the df does not need to be grouped or ordered by a certain column, say "None" for the last two elements of your output. 

        Make sure you are maintaining correct spelling of each column name as it is shown in the data (it needs to be the full column name). Ensure that it is the complete and correct column name, otherwise it won't work with the data.

        Once again, your output should only include column names from the data! Nothing else. (don't use contract start dates)
        It should follow the same format:
        column_name,column_name,column_name,column_name
                                '''
                                    response = model.generate_content(new_prompt)
                                    feedback = response.text.strip()
                                    column_list = feedback.split(',')
                                    df = pd.read_csv('visualizations.csv')
                                    new_row = {'user_id': st.session_state.user_id, 'column_1': column_list[0].lstrip(), 'column_2': column_list[1].lstrip(), 'group_by': column_list[2].lstrip(), 'order_by': column_list[3].lstrip(), 'vis_number': st.session_state.vis_count}
                                    df = df.append(new_row, ignore_index=True)
                                    df.to_csv('visualizations.csv', index=False)
                                    user_df = pd.read_csv('visualizations.csv')
                                    user_df = user_df[user_df['user_id'] == st.session_state.user_id]
                                    if len(user_df) == visual_count_number:
                                        st.rerun()
               
                            elif x.strip().lower() == 'text':
                                loading_box.warning('Generating insights from Gemini...')
                                text_input = f'''
You are a personal data analyst who is an expert in the {industry} industry. 


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


Here is the data you are to analyze: {data}

In a few sentences or less (in bullet point format), give me a summary of what you see or any trends or patterns you are noticing that could be helpful for a busines owner or data steward.
'''
                                response = model.generate_content(text_input)
                                st.subheader("Gemini's Insights")
                                st.write(response.text)
                      
                            elif x.strip().lower() == 'dataframe' or x == 'data frame':
                                
                                st.subheader("Your Data")
                                df = pd.read_csv(f"files/{data_file}")
                                st.dataframe(df)
                        if st.session_state.load_amount < .24:
                            st.session_state.load_amount = .24
                        progress_box.progress(st.session_state.load_amount)
                            # st.write(x)
                    elif index == 2:
                        with col3:
                            variable = True
                            if variable:
                            # if x in visuals:
                                loading_box.warning('Creating visualizations...')
                                column_values = visuals_df['vis_number'].astype(str).tolist()
                                if st.session_state.user_id in visuals_df['user_id'].tolist():
                                    # st.subheader(f"{visuals_list[1]} by {visuals_list[0]}")
                                    df = pd.read_csv(f'files/{data_file}')
                                    if visuals_list[2].strip().lower() != 'none' and visuals_list[2] != None and visuals_list[2] in df.columns:
                                        df = df.groupby(visuals_list[2]).apply(lambda x: x.sort_values(visuals_list[3])).reset_index(drop=True)
                                    elif visuals_list[3].lower() != 'none' and visuals_list[3] in df.columns:
                                        df = df.sort_values(by=visuals_list[3])

                                    if x == 'line chart':
                                        st.line_chart(data=df, x=visuals_list[0], y=visuals_list[1])
                                    elif x == 'bar chart':
                                        st.bar_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#228B22')
                                    elif x == 'area chart':
                                        st.area_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#ff8c00')
                                    elif x == 'scatter chart':
                                        st.scatter_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#8B0000')
                                    
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)

                                else:
                                    st.session_state.vis_count += 1
                                    new_prompt = f'''
        Your name is Butler. You are a personal data analyst for a person. You are assigned to view his/her data and provide feedback as a data analyst.

        
        This is the data that was provided: {data}

        Based on this data, I want you to provide 2 column names and 2 additional column names to use for "group by" and "order by" functionality for pandas dataframes. These 4 elements of your output should be for the most useful {x}. Your output should include only 4 column names, separated by a single comma (no spaces). The last 2 column names are the following: the first being what the user should group the df by and the second being the what the user should order the df by. These can be the same or different columns as the first two of your output. 
        The first two column names should also be compatible with the data that would be required to create a proper {x}. You may need to analyze the data provided and designate each column as numerical, categorical, or date values so that you can provide the best columns as input for the {x}. The first column name will be used for the x axis, the second will be the y axis (I'll be using streamlit built-in functions for generating a {x} and it will require an x column and y column as parameters). Also, refrain from using any type of ID or unique name (such as customer names) as a column name.
        If you think the df does not need to be grouped or ordered by a certain column, say "None" for the last two elements of your output. 

        Make sure you are maintaining correct spelling of each column name as it is shown in the data (it needs to be the full column name). Ensure that it is the complete and correct column name, otherwise it won't work with the data.

        Once again, your output should only include column names from the data! Nothing else. (don't use contract start dates)
        It should follow the same format:
        column_name,column_name,column_name,column_name
                                '''
                                    response = model.generate_content(new_prompt)
                                    feedback = response.text.strip()
                                    column_list = feedback.split(',')
                                    df = pd.read_csv('visualizations.csv')
                                    new_row = {'user_id': st.session_state.user_id, 'column_1': column_list[0].lstrip(), 'column_2': column_list[1].lstrip(), 'group_by': column_list[2].lstrip(), 'order_by': column_list[3].lstrip(), 'vis_number': st.session_state.vis_count}
                                    df = df.append(new_row, ignore_index=True)
                                    df.to_csv('visualizations.csv', index=False)
                                    user_df = pd.read_csv('visualizations.csv')
                                    user_df = user_df[user_df['user_id'] == st.session_state.user_id]
                                    if len(user_df) == visual_count_number:
                                        st.rerun()
                            elif x == 'text':
                                loading_box.warning("Generating insights from Gemini...")
                                text_input = f'''
You are a personal data analyst who is an expert in the {industry} industry. 


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


Here is the data you are to analyze: {data}

In a few sentences or less (in bullet point format), give me a summary of what you see or any trends or patterns you are noticing that could be helpful for a busines owner or data steward.
'''
                                response = model.generate_content(text_input)
                                st.subheader("Gemini's Insights")
                                st.write(response.text)
                            elif x == 'dataframe' or x == 'data frame':
                                st.subheader("Your Data")
                                df = pd.read_csv(f"files/{data_file}")
                                st.dataframe(df)
                    if st.session_state.load_amount < .43:
                        st.session_state.load_amount = .43    
                    progress_box.progress(st.session_state.load_amount)  
                            # st.write(x)
                elif index <= 5:
                    if index == 3:
                        st.write('---')
                        col1, col2, col3 = st.columns(3)
                        with col1:
                           
                            if x in visuals:
                 
                                loading_box.warning('Creating visualizations...')
   
                                column_values = visuals_df['vis_number'].astype(str).tolist()
                                if st.session_state.user_id in visuals_df['user_id'].tolist():
                                    st.subheader(f"{visuals_list[1]} by {visuals_list[0]}")
                                    df = pd.read_csv(f'files/{data_file}')
                                    if visuals_list[2].lower() != 'none':
                                        df = df.groupby(visuals_list[2]).apply(lambda x: x.sort_values(visuals_list[3])).reset_index(drop=True)
                                    elif visuals_list[3].lower() != 'none':
                                        df = df.sort_values(by=visuals_list[3])

                                    if x == 'line chart':
                                        st.line_chart(data=df, x=visuals_list[0], y=visuals_list[1])
                                    elif x == 'bar chart':
                                        st.bar_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#228B22')
                                    elif x == 'area chart':
                                        st.area_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#ff8c00')
                                    elif x == 'scatter chart':
                                        st.scatter_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#8B0000')
                                    
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)

                                else:
                                    st.session_state.vis_count += 1
                                    new_prompt = f'''
        Your name is Butler. You are a personal data analyst for a person. You are assigned to view his/her data and provide feedback as a data analyst.

        
        This is the data that was provided: {data}

        Based on this data, I want you to provide 2 column names and 2 additional column names to use for "group by" and "order by" functionality for pandas dataframes. These 4 elements of your output should be for the most useful {x}. Your output should include only 4 column names, separated by a single comma (no spaces). The last 2 column names are the following: the first being what the user should group the df by and the second being the what the user should order the df by. These can be the same or different columns as the first two of your output. 
        The first two column names should also be compatible with the data that would be required to create a proper {x}. You may need to analyze the data provided and designate each column as numerical, categorical, or date values so that you can provide the best columns as input for the {x}. The first column name will be used for the x axis, the second will be the y axis (I'll be using streamlit built-in functions for generating a {x} and it will require an x column and y column as parameters). Also, refrain from using any type of ID or unique name (such as customer names) as a column name.
        If you think the df does not need to be grouped or ordered by a certain column, say "None" for the last two elements of your output. 

        Make sure you are maintaining correct spelling of each column name as it is shown in the data (it needs to be the full column name). Ensure that it is the complete and correct column name, otherwise it won't work with the data.

        Once again, your output should only include column names from the data! Nothing else. (don't use contract start dates)
        It should follow the same format:
        column_name,column_name,column_name,column_name
                                '''
                                    response = model.generate_content(new_prompt)
                                    feedback = response.text.strip()
                                    column_list = feedback.split(',')
                                    df = pd.read_csv('visualizations.csv')
                                    new_row = {'user_id': st.session_state.user_id, 'column_1': column_list[0].lstrip(), 'column_2': column_list[1].lstrip(), 'group_by': column_list[2].lstrip(), 'order_by': column_list[3].lstrip(), 'vis_number': st.session_state.vis_count}
                                    df = df.append(new_row, ignore_index=True)
                                    df.to_csv('visualizations.csv', index=False)
                                    user_df = pd.read_csv('visualizations.csv')
                                    user_df = user_df[user_df['user_id'] == st.session_state.user_id]
                                    if len(user_df) == visual_count_number:
                                        st.rerun()
                            elif x == 'text':
                                loading_box.warning("Generating insights from Gemini...")
                                text_input = f'''
You are a personal data analyst who is an expert in the {industry} industry. 


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


Here is the data you are to analyze: {data}

In a few sentences or less (in bullet point format), give me a summary of what you see or any trends or patterns you are noticing that could be helpful for a busines owner or data steward.
'''
                                response = model.generate_content(text_input)
                                st.subheader("Gemini's Insights")
                                st.write(response.text)
                            elif x == 'dataframe' or x == 'data frame':
                                st.subheader("Your Data")
                                df = pd.read_csv(f"files/{data_file}")
                                st.dataframe(df)
                        if st.session_state.load_amount < .62:
                            st.session_state.load_amount = .62
                        progress_box.progress(st.session_state.load_amount)
                            # st.write(x)
                    elif index == 4:
                        with col2:
                            if x in visuals:
                                loading_box.warning('Creating visualizations...')
                                column_values = visuals_df['vis_number'].astype(str).tolist()
                                if st.session_state.user_id in visuals_df['user_id'].tolist():
                                    st.subheader(f"{visuals_list[1]} by {visuals_list[0]}")
                                    df = pd.read_csv(f'files/{data_file}')
                                    if visuals_list[2].lower() != 'none':
                                        df = df.groupby(visuals_list[2]).apply(lambda x: x.sort_values(visuals_list[3])).reset_index(drop=True)
                                    elif visuals_list[3].lower() != 'none':
                                        df = df.sort_values(by=visuals_list[3])
                
                                    if x == 'line chart':
                                        st.line_chart(data=df, x=visuals_list[0], y=visuals_list[1])
                                    elif x == 'bar chart':
                                        st.bar_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#228B22')
                                    elif x == 'area chart':
                                        st.area_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#ff8c00')
                                    elif x == 'scatter chart':
                                        st.scatter_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#8B0000')
                                    
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)

                                else:
                                    st.session_state.vis_count += 1
                                    new_prompt = f'''
        Your name is Butler. You are a personal data analyst for a person. You are assigned to view his/her data and provide feedback as a data analyst.

        
        This is the data that was provided: {data}

        Based on this data, I want you to provide 2 column names and 2 additional column names to use for "group by" and "order by" functionality for pandas dataframes. These 4 elements of your output should be for the most useful {x}. Your output should include only 4 column names, separated by a single comma (no spaces). The last 2 column names are the following: the first being what the user should group the df by and the second being the what the user should order the df by. These can be the same or different columns as the first two of your output. 
        The first two column names should also be compatible with the data that would be required to create a proper {x}. You may need to analyze the data provided and designate each column as numerical, categorical, or date values so that you can provide the best columns as input for the {x}. The first column name will be used for the x axis, the second will be the y axis (I'll be using streamlit built-in functions for generating a {x} and it will require an x column and y column as parameters). Also, refrain from using any type of ID or unique name (such as customer names) as a column name.
        If you think the df does not need to be grouped or ordered by a certain column, say "None" for the last two elements of your output. 

        Make sure you are maintaining correct spelling of each column name as it is shown in the data (it needs to be the full column name). Ensure that it is the complete and correct column name, otherwise it won't work with the data.

        Once again, your output should only include column names from the data! Nothing else. (don't use contract start dates)
        It should follow the same format:
        column_name,column_name,column_name,column_name
                                '''
                                    response = model.generate_content(new_prompt)
                                    feedback = response.text.strip()
                                    column_list = feedback.split(',')
                                    df = pd.read_csv('visualizations.csv')
                                    new_row = {'user_id': st.session_state.user_id, 'column_1': column_list[0].lstrip(), 'column_2': column_list[1].lstrip(), 'group_by': column_list[2].lstrip(), 'order_by': column_list[3].lstrip(), 'vis_number': st.session_state.vis_count}
                                    df = df.append(new_row, ignore_index=True)
                                    df.to_csv('visualizations.csv', index=False)
                                    user_df = pd.read_csv('visualizations.csv')
                                    user_df = user_df[user_df['user_id'] == st.session_state.user_id]
                                    if len(user_df) == visual_count_number:
                                        st.rerun()

                            elif x == 'text':
                
                                loading_box.warning("Generating insights from Gemini...")
                                text_input = f'''
You are a personal data analyst who is an expert in the {industry} industry. 


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


Here is the data you are to analyze: {data}

In a few sentences or less (in bullet point format), give me a summary of what you see or any trends or patterns you are noticing that could be helpful for a busines owner or data steward.
'''
                                response = model.generate_content(text_input)
                                st.subheader("Gemini's Insights")
                                st.write(response.text)
                
                            elif x == 'dataframe' or x == 'data frame':
                                st.subheader("Your Data")
                                df = pd.read_csv(f"files/{data_file}")
                                st.dataframe(df)
                        if st.session_state.load_amount < .81:
                            st.session_state.load_amount = .81
                        progress_box.progress(st.session_state.load_amount)
                    elif index == 5:
                        with col3:
                            if x in visuals:
                             
                                loading_box.warning('Creating visualizations...')
                                column_values = visuals_df['vis_number'].astype(str).tolist()
                                if st.session_state.user_id in visuals_df['user_id'].tolist():

                                    st.subheader(f"{visuals_list[1]} by {visuals_list[0]}")
                                    st.subheader('Conversion Rate by Industry')
                                    df = pd.read_csv(f'files/{data_file}')
                                    if visuals_list[2].lower() != 'none':
                                        df = df.groupby(visuals_list[2]).apply(lambda x: x.sort_values(visuals_list[3])).reset_index(drop=True)
                                    elif visuals_list[3].lower() != 'none':
                                        df = df.sort_values(by=visuals_list[3])
            
                                    if x == 'line chart':
                                        st.line_chart(data=df, x=visuals_list[0], y=visuals_list[1])
                                    elif x == 'bar chart':
                                        st.bar_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#228B22')
                                    elif x == 'area chart':
                                        st.area_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#ff8c00')
                                    elif x == 'scatter chart':
                                        st.scatter_chart(data=df, x=visuals_list[0], y=visuals_list[1], color='#8B0000')
                                    
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)
                                    visuals_list.pop(0)

                                else:
                                    df = pd.read_csv('files/dan_Marketing Agency Data Set - Sheet1.csv')
                                    st.subheader('Conversion Rate by Industry')
                                    st.line_chart(data=df, x='Industry', y='Conversion Rate')
                                    st.session_state.vis_count += 1
                                    new_prompt = f'''
        Your name is Butler. You are a personal data analyst for a person. You are assigned to view his/her data and provide feedback as a data analyst.

        
        This is the data that was provided: {data}

        Based on this data, I want you to provide 2 column names and 2 additional column names to use for "group by" and "order by" functionality for pandas dataframes. These 4 elements of your output should be for the most useful {x}. Your output should include only 4 column names, separated by a single comma (no spaces). The last 2 column names are the following: the first being what the user should group the df by and the second being the what the user should order the df by. These can be the same or different columns as the first two of your output. 
        The first two column names should also be compatible with the data that would be required to create a proper {x}. You may need to analyze the data provided and designate each column as numerical, categorical, or date values so that you can provide the best columns as input for the {x}. The first column name will be used for the x axis, the second will be the y axis (I'll be using streamlit built-in functions for generating a {x} and it will require an x column and y column as parameters). Also, refrain from using any type of ID or unique name (such as customer names) as a column name.
        If you think the df does not need to be grouped or ordered by a certain column, say "None" for the last two elements of your output. 

        Make sure you are maintaining correct spelling of each column name as it is shown in the data (it needs to be the full column name). Ensure that it is the complete and correct column name, otherwise it won't work with the data.

        Once again, your output should only include column names from the data! Nothing else. (don't use contract start dates)
        It should follow the same format:
        column_name,column_name,column_name,column_name
                                '''
                                    response = model.generate_content(new_prompt)
                                    feedback = response.text.strip()
                                    column_list = feedback.split(',')
                                    df = pd.read_csv('visualizations.csv')
                                    new_row = {'user_id': st.session_state.user_id, 'column_1': column_list[0].lstrip(), 'column_2': column_list[1].lstrip(), 'group_by': column_list[2].lstrip(), 'order_by': column_list[3].lstrip(), 'vis_number': st.session_state.vis_count}
                                    df = df.append(new_row, ignore_index=True)
                                    df.to_csv('visualizations.csv', index=False)
                                    user_df = pd.read_csv('visualizations.csv')
                                    user_df = user_df[user_df['user_id'] == st.session_state.user_id]
                                    if len(user_df) == visual_count_number:
                                        st.rerun()
                            elif x == 'text':
                                st.subheader('Conversion Rate by Industry')
                                st.line_chart(data=df, x='Industry', y='Conversion Rate')
                                loading_box.warning("Generating insights from Gemini...")
                                text_input = f'''
You are a personal data analyst who is an expert in the {industry} industry. 


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


Here is the data you are to analyze: {data}

In a few sentences or less (in bullet point format), give me a summary of what you see or any trends or patterns you are noticing that could be helpful for a busines owner or data steward.
'''
                                response = model.generate_content(text_input)
                                st.subheader("Gemini's Insights")
                                st.write(response.text)
                            elif x == 'dataframe' or x == 'data frame':
                                st.subheader("Your Data")
                                df = pd.read_csv(f"files/{data_file}")
                                st.dataframe(df)
                        progress_box.empty()
                        loading_box.success("Your Dashboard is Ready!")
                        time.sleep(1.5)
                        del st.session_state.load_amount
                        del st.session_state.load_statement
                        loading_box.empty()
                            
                            # st.write(x)
#                 else:
#                     if index == 6:
#                         st.write('---')
#                         col1, col2, col3 = st.columns(3)
#                         with col1:
#                             if x in visuals:
                             
                            
#                                 column_values = visuals_df['vis_number'].astype(str).tolist()
#                                 if st.session_state.user_id in visuals_df['user_id'].tolist():
#                                     st.subheader(f"{visuals_list[1]} by {visuals_list[0]}")
#                                     df = pd.read_csv(f'files/{data_file}')
#                                     if visuals_list[2].lower() != 'none':
#                                         df = df.groupby(visuals_list[2]).apply(lambda x: x.sort_values(visuals_list[3])).reset_index(drop=True)
#                                     elif visuals_list[3].lower() != 'none':
#                                         df = df.sort_values(by=visuals_list[3])
                

#                                     if x == 'line chart':
#                                         st.line_chart(data=df, x=visuals_list[0], y=visuals_list[1])
#                                     elif x == 'bar chart':
#                                         st.bar_chart(data=df, x=visuals_list[0], y=visuals_list[1])
#                                     elif x == 'area chart':
#                                         st.area_chart(data=df, x=visuals_list[0], y=visuals_list[1])
#                                     elif x == 'scatter chart':
#                                         st.scatter_chart(data=df, x=visuals_list[0], y=visuals_list[1])
                                    
#                                     visuals_list.pop(0)
#                                     visuals_list.pop(0)
#                                     visuals_list.pop(0)
#                                     visuals_list.pop(0)


#                                 else:
#                                     st.session_state.vis_count += 1
#                                     new_prompt = f'''
#         Your name is Butler. You are a personal data analyst for a person. You are assigned to view his/her data and provide feedback as a data analyst.

#         The person you are assisting was provided with a questionnaire. Here are the questions and results from this survey:
#         What is your primary industry or area of work? (e.g., Marketing, Finance, Healthcare, Education): {industry}
#         What is the size of your organization (number of employees)?: {org_size}
#         What are your top 3 business goals for the next year? (e.g., Increase brand awareness, improve customer satisfaction, boost sales): {goal_1}, {goal_2}, {goal_3}
#         Do you track any key performance indicators (KPIs) related to your goals?: {kpis}
#         Please list 2-3 of the most important KPIs: {kpi_goals}
#         What data sources do you typically use to track your business performance? (e.g., CRM system, website analytics, social media data): {data_sources}
#         How comfortable are you with data analysis and visualization tools? (Beginner, Intermediate, Advanced): {comfort_level}
#         What types of insights would be most valuable to you from your personal data? (e.g., Identify customer trends, track marketing campaign performance, analyze sales patterns): {insights}
#         How often would you like to receive updates and reports based on your data? (Daily, Weekly, Monthly): {update_interval}
#         What is your preferred format for receiving data insights? (Interactive dashboard, Visual reports, Text summaries): {preferred_format}
#         Do you have any specific challenges or questions you'd like your personal data analyst to answer?: {challenges}
#         Describe your typical workday. What kind of data do you encounter most frequently? (Open ended to understand data touchpoints): {typical_workday}
#         Imagine you have a magic button that instantly analyzes your data and provides a key business insight. What question would you ask it?: {magic_button}
#         How often do you feel overwhelmed by the amount of data available to you?: {overwhelmed}
#         In the past, have you made a business decision based on data analysis? If so, can you briefly describe the situation and outcome?: {business_decision}
#         What frustrates you the most about the way you currently analyze your personal data?: {frustrates}

        
#         This is the data that was provided: {data}


#         Based on this data, I want you to provide column names and columns to use for "group by" and "order by" functionality for pandas dataframes. These 4 elements of your output should be for the most useful {x}. Your output should include only two column names, separated by a single comma (no spaces). Then, in the same format, two more column names (the first being what the user should group the df by and the second being the what the user should order the df by). These can be the same or different columns as the first two of your output. 
#         The first two column names should also be compatible with the data that would be required to create a proper {x}. You may need to analyze the data provided and designate each column as numerical or categorical or some other form so that you can provide the best columns as input for the {x}. The first column name will be used for the x axis, the second will be the y axis (I'll be using streamlit built-in functions for generating a {x} and it will require an x column and y column as parameters). Also, refrain from using any type of ID or unique name (be smart enough to find categorical columns) as a column name.
#         If you think the df does not need to be grouped or ordered by a certain column, say "None" for the last two elements of your output. 

#         I will be using the following code to organize the df, so make sure your third and fourth columns (the group by and order by columns) would allow this functionality:
#         if [group_by column].lower() != 'none':
#             df = df.groupby([group_by column]).apply(lambda x: x.sort_values([order_by column]).reset_index(drop=True)
#         elif [order_by column].lower() != 'none':
#             df = df.sort_values(by=[order_by column])

#         Make sure you are maintaining correct spelling of each column name as it is shown in the data (it needs to be the full column name).

#         Once again, your output should only include column names from the data! Nothing else.
#         It should follow the same format:
#         column_name,column_name,column_name,column_name
#                                 '''
#                                     response = model.generate_content(new_prompt)
#                                     feedback = response.text.strip()
#                                     column_list = feedback.split(',')
#                                     df = pd.read_csv('visualizations.csv')
#                                     new_row = {'user_id': st.session_state.user_id, 'column_1': column_list[0].lstrip(), 'column_2': column_list[1].lstrip(), 'group_by': column_list[2].lstrip(), 'order_by': column_list[3].lstrip(), 'vis_number': st.session_state.vis_count}
#                                     df = df.append(new_row, ignore_index=True)
#                                     df.to_csv('visualizations.csv', index=False)
#                                     user_df = pd.read_csv('visualizations.csv')
#                                     user_df = user_df[user_df['user_id'] == st.session_state.user_id]
#                                     if len(user_df) == visual_count_number:
#                                         st.rerun()
#                             elif x == 'text':
#                                 text_input = f'''
# You are a personal data analyst who is an expert in the {industry} industry. 


# The person you are assisting was provided with a questionnaire. Here are the questions and results from this survey:
#         What is your primary industry or area of work? (e.g., Marketing, Finance, Healthcare, Education): {industry}
#         What is the size of your organization (number of employees)?: {org_size}
#         What are your top 3 business goals for the next year? (e.g., Increase brand awareness, improve customer satisfaction, boost sales): {goal_1}, {goal_2}, {goal_3}
#         Do you track any key performance indicators (KPIs) related to your goals?: {kpis}
#         Please list 2-3 of the most important KPIs: {kpi_goals}
#         What data sources do you typically use to track your business performance? (e.g., CRM system, website analytics, social media data): {data_sources}
#         How comfortable are you with data analysis and visualization tools? (Beginner, Intermediate, Advanced): {comfort_level}
#         What types of insights would be most valuable to you from your personal data? (e.g., Identify customer trends, track marketing campaign performance, analyze sales patterns): {insights}
#         How often would you like to receive updates and reports based on your data? (Daily, Weekly, Monthly): {update_interval}
#         What is your preferred format for receiving data insights? (Interactive dashboard, Visual reports, Text summaries): {preferred_format}
#         Do you have any specific challenges or questions you'd like your personal data analyst to answer?: {challenges}
#         Describe your typical workday. What kind of data do you encounter most frequently? (Open ended to understand data touchpoints): {typical_workday}
#         Imagine you have a magic button that instantly analyzes your data and provides a key business insight. What question would you ask it?: {magic_button}
#         How often do you feel overwhelmed by the amount of data available to you?: {overwhelmed}
#         In the past, have you made a business decision based on data analysis? If so, can you briefly describe the situation and outcome?: {business_decision}
#         What frustrates you the most about the way you currently analyze your personal data?: {frustrates}


# Here is the data you are to analyze: {data}

# In a few sentences, give me a summary of what you see or any trends or patterns you are noticing that could be helpful for a busines owner or data steward.
# '''
#                                 response = model.generate_content(text_input)
#                                 st.subheader("Gemini's Insights")
#                                 st.write(response.text)
#                             elif x == 'dataframe' or x == 'data frame':
#                                 st.subheader("Your Data")
#                                 df = pd.read_csv(f"files/{data_file}")
#                                 st.dataframe(df)
                            
#                             # st.write(x)
#                     elif index == 7:
#                         with col2:
#                             if x in visuals:
                               
                         
#                                 column_values = visuals_df['vis_number'].astype(str).tolist()
#                                 if st.session_state.user_id in visuals_df['user_id'].tolist():
#                                     st.subheader(f"{visuals_list[1]} by {visuals_list[0]}")
#                                     df = pd.read_csv(f'files/{data_file}')
#                                     if visuals_list[2].lower() != 'none':
#                                         df = df.groupby(visuals_list[2]).apply(lambda x: x.sort_values(visuals_list[3])).reset_index(drop=True)
#                                     elif visuals_list[3].lower() != 'none':
#                                         df = df.sort_values(by=visuals_list[3])
                

#                                     if x == 'line chart':
#                                         st.line_chart(data=df, x=visuals_list[0], y=visuals_list[1])
#                                     elif x == 'bar chart':
#                                         st.bar_chart(data=df, x=visuals_list[0], y=visuals_list[1])
#                                     elif x == 'area chart':
#                                         st.area_chart(data=df, x=visuals_list[0], y=visuals_list[1])
#                                     elif x == 'scatter chart':
#                                         st.scatter_chart(data=df, x=visuals_list[0], y=visuals_list[1])
                                    
#                                     visuals_list.pop(0)
#                                     visuals_list.pop(0)
#                                     visuals_list.pop(0)
#                                     visuals_list.pop(0)

#                                 else:
#                                     st.session_state.vis_count += 1
#                                     new_prompt = f'''
#         Your name is Butler. You are a personal data analyst for a person. You are assigned to view his/her data and provide feedback as a data analyst.

#         The person you are assisting was provided with a questionnaire. Here are the questions and results from this survey:
#         What is your primary industry or area of work? (e.g., Marketing, Finance, Healthcare, Education): {industry}
#         What is the size of your organization (number of employees)?: {org_size}
#         What are your top 3 business goals for the next year? (e.g., Increase brand awareness, improve customer satisfaction, boost sales): {goal_1}, {goal_2}, {goal_3}
#         Do you track any key performance indicators (KPIs) related to your goals?: {kpis}
#         Please list 2-3 of the most important KPIs: {kpi_goals}
#         What data sources do you typically use to track your business performance? (e.g., CRM system, website analytics, social media data): {data_sources}
#         How comfortable are you with data analysis and visualization tools? (Beginner, Intermediate, Advanced): {comfort_level}
#         What types of insights would be most valuable to you from your personal data? (e.g., Identify customer trends, track marketing campaign performance, analyze sales patterns): {insights}
#         How often would you like to receive updates and reports based on your data? (Daily, Weekly, Monthly): {update_interval}
#         What is your preferred format for receiving data insights? (Interactive dashboard, Visual reports, Text summaries): {preferred_format}
#         Do you have any specific challenges or questions you'd like your personal data analyst to answer?: {challenges}
#         Describe your typical workday. What kind of data do you encounter most frequently? (Open ended to understand data touchpoints): {typical_workday}
#         Imagine you have a magic button that instantly analyzes your data and provides a key business insight. What question would you ask it?: {magic_button}
#         How often do you feel overwhelmed by the amount of data available to you?: {overwhelmed}
#         In the past, have you made a business decision based on data analysis? If so, can you briefly describe the situation and outcome?: {business_decision}
#         What frustrates you the most about the way you currently analyze your personal data?: {frustrates}

        
#         This is the data that was provided: {data}


#         Based on this data, I want you to provide column names and columns to use for "group by" and "order by" functionality for pandas dataframes. These 4 elements of your output should be for the most useful {x}. Your output should include only two column names, separated by a single comma (no spaces). Then, in the same format, two more column names (the first being what the user should group the df by and the second being the what the user should order the df by). These can be the same or different columns as the first two of your output. 
#         The first two column names should also be compatible with the data that would be required to create a proper {x}. You may need to analyze the data provided and designate each column as numerical or categorical or some other form so that you can provide the best columns as input for the {x}. The first column name will be used for the x axis, the second will be the y axis (I'll be using streamlit built-in functions for generating a {x} and it will require an x column and y column as parameters). Also, refrain from using any type of ID or unique name (be smart enough to find categorical columns) as a column name.
#         If you think the df does not need to be grouped or ordered by a certain column, say "None" for the last two elements of your output. 

#         I will be using the following code to organize the df, so make sure your third and fourth columns (the group by and order by columns) would allow this functionality:
#         if [group_by column].lower() != 'none':
#             df = df.groupby([group_by column]).apply(lambda x: x.sort_values([order_by column]).reset_index(drop=True)
#         elif [order_by column].lower() != 'none':
#             df = df.sort_values(by=[order_by column])

#         Make sure you are maintaining correct spelling of each column name as it is shown in the data (it needs to be the full column name).

#         Once again, your output should only include column names from the data! Nothing else.
#         It should follow the same format:
#         column_name,column_name,column_name,column_name
#                                 '''
#                                     response = model.generate_content(new_prompt)
#                                     feedback = response.text.strip()
#                                     column_list = feedback.split(',')
#                                     df = pd.read_csv('visualizations.csv')
#                                     new_row = {'user_id': st.session_state.user_id, 'column_1': column_list[0].lstrip(), 'column_2': column_list[1].lstrip(), 'group_by': column_list[2].lstrip(), 'order_by': column_list[3].lstrip(), 'vis_number': st.session_state.vis_count}
#                                     df = df.append(new_row, ignore_index=True)
#                                     df.to_csv('visualizations.csv', index=False)
#                                     user_df = pd.read_csv('visualizations.csv')
#                                     user_df = user_df[user_df['user_id'] == st.session_state.user_id]
#                                     if len(user_df) == visual_count_number:
#                                         st.rerun()
#                             elif x == 'text':
#                                 text_input = f'''
# You are a personal data analyst who is an expert in the {industry} industry. 


# The person you are assisting was provided with a questionnaire. Here are the questions and results from this survey:
#         What is your primary industry or area of work? (e.g., Marketing, Finance, Healthcare, Education): {industry}
#         What is the size of your organization (number of employees)?: {org_size}
#         What are your top 3 business goals for the next year? (e.g., Increase brand awareness, improve customer satisfaction, boost sales): {goal_1}, {goal_2}, {goal_3}
#         Do you track any key performance indicators (KPIs) related to your goals?: {kpis}
#         Please list 2-3 of the most important KPIs: {kpi_goals}
#         What data sources do you typically use to track your business performance? (e.g., CRM system, website analytics, social media data): {data_sources}
#         How comfortable are you with data analysis and visualization tools? (Beginner, Intermediate, Advanced): {comfort_level}
#         What types of insights would be most valuable to you from your personal data? (e.g., Identify customer trends, track marketing campaign performance, analyze sales patterns): {insights}
#         How often would you like to receive updates and reports based on your data? (Daily, Weekly, Monthly): {update_interval}
#         What is your preferred format for receiving data insights? (Interactive dashboard, Visual reports, Text summaries): {preferred_format}
#         Do you have any specific challenges or questions you'd like your personal data analyst to answer?: {challenges}
#         Describe your typical workday. What kind of data do you encounter most frequently? (Open ended to understand data touchpoints): {typical_workday}
#         Imagine you have a magic button that instantly analyzes your data and provides a key business insight. What question would you ask it?: {magic_button}
#         How often do you feel overwhelmed by the amount of data available to you?: {overwhelmed}
#         In the past, have you made a business decision based on data analysis? If so, can you briefly describe the situation and outcome?: {business_decision}
#         What frustrates you the most about the way you currently analyze your personal data?: {frustrates}


# Here is the data you are to analyze: {data}

# In a few sentences, give me a summary of what you see or any trends or patterns you are noticing that could be helpful for a busines owner or data steward.
# '''
#                                 response = model.generate_content(text_input)
#                                 st.subheader("Gemini's Insights")
#                                 st.write(response.text)
#                             elif x == 'dataframe' or x == 'data frame':
#                                 st.subheader("Your Data")
#                                 df = pd.read_csv(f"files/{data_file}")
#                                 st.dataframe(df)
                                
#                             # st.write(x)
#                     elif index == 8:
#                         with col3:
#                             if x in visuals:
                        
#                                 column_values = visuals_df['vis_number'].astype(str).tolist()
#                                 if st.session_state.user_id in visuals_df['user_id'].tolist():
#                                     st.subheader(f"{visuals_list[1]} by {visuals_list[0]}")
#                                     df = pd.read_csv(f'files/{data_file}')
#                                     if visuals_list[2].lower() != 'none':
#                                         df = df.groupby(visuals_list[2]).apply(lambda x: x.sort_values(visuals_list[3])).reset_index(drop=True)
#                                     elif visuals_list[3].lower() != 'none':
#                                         df = df.sort_values(by=visuals_list[3])
                

#                                     if x == 'line chart':
#                                         st.line_chart(data=df, x=visuals_list[0], y=visuals_list[1])
#                                     elif x == 'bar chart':
#                                         st.bar_chart(data=df, x=visuals_list[0], y=visuals_list[1])
#                                     elif x == 'area chart':
#                                         st.area_chart(data=df, x=visuals_list[0], y=visuals_list[1])
#                                     elif x == 'scatter chart':
#                                         st.scatter_chart(data=df, x=visuals_list[0], y=visuals_list[1])
                                    
#                                     visuals_list.pop(0)
#                                     visuals_list.pop(0)
#                                     visuals_list.pop(0)
#                                     visuals_list.pop(0)

#                                 else:
#                                     st.session_state.vis_count += 1
#                                     new_prompt = f'''
#         Your name is Butler. You are a personal data analyst for a person. You are assigned to view his/her data and provide feedback as a data analyst.

#         The person you are assisting was provided with a questionnaire. Here are the questions and results from this survey:
#         What is your primary industry or area of work? (e.g., Marketing, Finance, Healthcare, Education): {industry}
#         What is the size of your organization (number of employees)?: {org_size}
#         What are your top 3 business goals for the next year? (e.g., Increase brand awareness, improve customer satisfaction, boost sales): {goal_1}, {goal_2}, {goal_3}
#         Do you track any key performance indicators (KPIs) related to your goals?: {kpis}
#         Please list 2-3 of the most important KPIs: {kpi_goals}
#         What data sources do you typically use to track your business performance? (e.g., CRM system, website analytics, social media data): {data_sources}
#         How comfortable are you with data analysis and visualization tools? (Beginner, Intermediate, Advanced): {comfort_level}
#         What types of insights would be most valuable to you from your personal data? (e.g., Identify customer trends, track marketing campaign performance, analyze sales patterns): {insights}
#         How often would you like to receive updates and reports based on your data? (Daily, Weekly, Monthly): {update_interval}
#         What is your preferred format for receiving data insights? (Interactive dashboard, Visual reports, Text summaries): {preferred_format}
#         Do you have any specific challenges or questions you'd like your personal data analyst to answer?: {challenges}
#         Describe your typical workday. What kind of data do you encounter most frequently? (Open ended to understand data touchpoints): {typical_workday}
#         Imagine you have a magic button that instantly analyzes your data and provides a key business insight. What question would you ask it?: {magic_button}
#         How often do you feel overwhelmed by the amount of data available to you?: {overwhelmed}
#         In the past, have you made a business decision based on data analysis? If so, can you briefly describe the situation and outcome?: {business_decision}
#         What frustrates you the most about the way you currently analyze your personal data?: {frustrates}

        
#         This is the data that was provided: {data}


#         Based on this data, I want you to provide column names and columns to use for "group by" and "order by" functionality for pandas dataframes. These 4 elements of your output should be for the most useful {x}. Your output should include only two column names, separated by a single comma (no spaces). Then, in the same format, two more column names (the first being what the user should group the df by and the second being the what the user should order the df by). These can be the same or different columns as the first two of your output. 
#         The first two column names should also be compatible with the data that would be required to create a proper {x}. You may need to analyze the data provided and designate each column as numerical or categorical or some other form so that you can provide the best columns as input for the {x}. The first column name will be used for the x axis, the second will be the y axis (I'll be using streamlit built-in functions for generating a {x} and it will require an x column and y column as parameters). Also, refrain from using any type of ID or unique name (be smart enough to find categorical columns) as a column name.
#         If you think the df does not need to be grouped or ordered by a certain column, say "None" for the last two elements of your output. 

#         I will be using the following code to organize the df, so make sure your third and fourth columns (the group by and order by columns) would allow this functionality:
#         if [group_by column].lower() != 'none':
#             df = df.groupby([group_by column]).apply(lambda x: x.sort_values([order_by column]).reset_index(drop=True)
#         elif [order_by column].lower() != 'none':
#             df = df.sort_values(by=[order_by column])

#         Make sure you are maintaining correct spelling of each column name as it is shown in the data (it needs to be the full column name).

#         Once again, your output should only include column names from the data! Nothing else.
#         It should follow the same format:
#         column_name,column_name,column_name,column_name
#                                 '''
#                                     response = model.generate_content(new_prompt)
#                                     feedback = response.text.strip()
#                                     column_list = feedback.split(',')
#                                     df = pd.read_csv('visualizations.csv')
#                                     new_row = {'user_id': st.session_state.user_id, 'column_1': column_list[0].lstrip(), 'column_2': column_list[1].lstrip(), 'group_by': column_list[2].lstrip(), 'order_by': column_list[3].lstrip(), 'vis_number': st.session_state.vis_count}
#                                     df = df.append(new_row, ignore_index=True)
#                                     df.to_csv('visualizations.csv', index=False)

#                                     user_df = pd.read_csv('visualizations.csv')
#                                     user_df = user_df[user_df['user_id'] == st.session_state.user_id]

#                                     if len(user_df) == visual_count_number:
#                                         st.rerun()
#                             elif x == 'text':
#                                 text_input = f'''
# You are a personal data analyst who is an expert in the {industry} industry. 


# The person you are assisting was provided with a questionnaire. Here are the questions and results from this survey:
#         What is your primary industry or area of work? (e.g., Marketing, Finance, Healthcare, Education): {industry}
#         What is the size of your organization (number of employees)?: {org_size}
#         What are your top 3 business goals for the next year? (e.g., Increase brand awareness, improve customer satisfaction, boost sales): {goal_1}, {goal_2}, {goal_3}
#         Do you track any key performance indicators (KPIs) related to your goals?: {kpis}
#         Please list 2-3 of the most important KPIs: {kpi_goals}
#         What data sources do you typically use to track your business performance? (e.g., CRM system, website analytics, social media data): {data_sources}
#         How comfortable are you with data analysis and visualization tools? (Beginner, Intermediate, Advanced): {comfort_level}
#         What types of insights would be most valuable to you from your personal data? (e.g., Identify customer trends, track marketing campaign performance, analyze sales patterns): {insights}
#         How often would you like to receive updates and reports based on your data? (Daily, Weekly, Monthly): {update_interval}
#         What is your preferred format for receiving data insights? (Interactive dashboard, Visual reports, Text summaries): {preferred_format}
#         Do you have any specific challenges or questions you'd like your personal data analyst to answer?: {challenges}
#         Describe your typical workday. What kind of data do you encounter most frequently? (Open ended to understand data touchpoints): {typical_workday}
#         Imagine you have a magic button that instantly analyzes your data and provides a key business insight. What question would you ask it?: {magic_button}
#         How often do you feel overwhelmed by the amount of data available to you?: {overwhelmed}
#         In the past, have you made a business decision based on data analysis? If so, can you briefly describe the situation and outcome?: {business_decision}
#         What frustrates you the most about the way you currently analyze your personal data?: {frustrates}


# Here is the data you are to analyze: {data}

# In a few sentences, give me a summary of what you see or any trends or patterns you are noticing that could be helpful for a busines owner or data steward.
# '''
#                                 response = model.generate_content(text_input)
#                                 st.subheader("Gemini's Insights")
#                                 st.write(response.text)
#                             elif x == 'dataframe' or x == 'data frame':
#                                 st.subheader("Your Data")
#                                 df = pd.read_csv(f"files/{data_file}")
#                                 st.dataframe(df)
#                             # st.write(x)





        

        
        
            



                        




