import streamlit as st
from datetime import datetime, timedelta
from fpdf import FPDF  # To generate PDFs
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Function to send email with Yes/No buttons
def send_email_via_sendgrid(to_email, subject, company_name, issue_date, calculated_date):
    try:
        app_url = "https://your-streamlit-app-url.com"  # Replace with your Streamlit app URL

        # Construct email message with Yes/No buttons
        message = f"""
        <html>
        <body>
        <p>Greetings {company_name} Team,</p>

        <p>It has come to our notice that your license issue date is {issue_date.strftime('%d/%m/%Y')} and the deadline was {calculated_date.strftime('%d/%m/%Y')}. We regret to inform you that there is a chance of a late registration penalty of AED 10,000 imposed on the license.</p>

        <p>We are informing you in advance to avoid any surprises if it happens. Once imposed, you will receive a message and email for the approval of your registration and the penalty.</p>

        <p>Would you like to proceed with the registration despite the possibility of a penalty?</p>

        <p>Please click one of the options below:</p>
        <a href="{app_url}?response=yes&company={company_name}" style="padding:10px 20px;background-color:green;color:white;text-decoration:none;">Yes</a>
        <a href="{app_url}?response=no&company={company_name}" style="padding:10px 20px;background-color:red;color:white;text-decoration:none;">No</a>

        <p>Thanks.</p>
        </body>
        </html>
        """

        # Send the email using SendGrid
        sg = SendGridAPIClient('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')  # Replace with your SendGrid API key
        email = Mail(
            from_email='megha@finanshels.com',  # Replace with your verified SendGrid email
            to_emails=to_email,
            subject=subject,
            html_content=message)
        
        response = sg.send(email)
        st.success(f"Email successfully sent to {to_email}")
    
    except Exception as e:
        st.error(f"Error sending email: {e}")

# Function to convert text documents into PDF and store in a folder
def convert_to_pdf(documents, output_filename="merged_documents.pdf"):
    # Create folder if it doesn't exist
    output_folder = "generated_pdfs"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Define the full output path for the PDF
    output_path = os.path.join(output_folder, output_filename)

    # Create the PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for doc in documents:
        # Adding text content from documents
        pdf.multi_cell(200, 10, txt=doc)
        pdf.ln()

    # Save the PDF to the specified path
    pdf.output(output_path)
    st.success(f"Documents have been merged and saved as {output_path}")
    
    # Provide a download link
    with open(output_path, "rb") as file:
        st.download_button(
            label="Download the generated PDF",
            data=file,
            file_name=output_filename,
            mime="application/pdf"
        )

# Part 1: Deal Signed and Document Flow
st.title("Document Registration Flow")

# Input company details and email at the start
company_name = st.text_input("Enter the Company Name")
company_email = st.text_input("Enter the Company's Email Address")

if not company_email:
    st.error("Please enter the company's email address to proceed.")
else:
    # Upload documents section
    uploaded_files = st.file_uploader("Upload your documents", accept_multiple_files=True)

    if uploaded_files:
        st.write("Documents uploaded:")
        documents_content = []  # List to store file contents

        for uploaded_file in uploaded_files:
            st.write(f"- {uploaded_file.name}")

            # Try to process the file content safely
            try:
                # If the file is a text file, we decode it as UTF-8
                if uploaded_file.type.startswith("text"):
                    content = uploaded_file.read().decode("utf-8")
                    documents_content.append(content)
                else:
                    # If the file is binary (e.g., pdf, image, etc.), handle it as binary
                    documents_content.append(f"Binary file: {uploaded_file.name} (cannot be previewed as text)")
            except Exception as e:
                st.error(f"Error reading {uploaded_file.name}: {e}")

        # Ask if all documents are uploaded
        all_uploaded = st.radio("Have all required documents been uploaded?", ("Yes", "No"))

        if all_uploaded == "No":
            st.warning("Please upload the remaining documents.")
        elif all_uploaded == "Yes":
            # Continue to due date check after confirming all documents are uploaded
            # Date input widget
            date_input_str = st.text_input("Enter the Trade License Issue Date (DD-MM-YYYY or DD/MM/YYYY)", "")

            # If a date is manually typed, try to parse it
            if date_input_str:
                date_input_str = date_input_str.replace("/", "-")
                try:
                    input_date = datetime.strptime(date_input_str, "%d-%m-%Y").date()
                except ValueError:
                    st.error("Please enter a valid date in DD-MM-YYYY or DD/MM/YYYY format.")

            # Define the threshold date for 90-day rule
            threshold_date = datetime(2024, 3, 1).date()

            # Function to get deadline based on the month and day (ignoring the year)
            def get_deadline_based_on_rules(input_date):
                month_day = (input_date.month, input_date.day)
                if (1, 1) <= month_day <= (2, 29):
                    return "31 May 2024"
                elif (3, 1) <= month_day <= (4, 30):
                    return "30 Jun 2024"
                elif (5, 1) <= month_day <= (5, 31):
                    return "31 Jul 2024"
                elif (6, 1) <= month_day <= (6, 30):
                    return "31 Aug 2024"
                elif (7, 1) <= month_day <= (7, 31):
                    return "30 Sep 2024"
                elif (8, 1) <= month_day <= (9, 30):
                    return "31 Oct 2024"
                elif (10, 1) <= month_day <= (11, 30):
                    return "30 Nov 2024"
                elif (12, 1) <= month_day <= (12, 31):
                    return "31 Dec 2024"
                return None

            # If both date and company name are provided
            if date_input_str and company_name:
                try:
                    if input_date > threshold_date:
                        calculated_date = input_date + timedelta(days=90)
                    else:
                        deadline = get_deadline_based_on_rules(input_date)
                        if deadline:
                            calculated_date = datetime.strptime(deadline, "%d %b %Y").date()

                    current_date = datetime.today().date()

                    # Check if the calculated deadline is past the current date
                    if calculated_date < current_date:
                        st.markdown('<div class="box">The registration is past due date.</div>', unsafe_allow_html=True)

                        if st.button("Send Email"):
                            # Generate the appropriate message
                            send_email_via_sendgrid(company_email, "FTA Registration Deadline Notification", company_name, input_date, calculated_date)

                    else:
                        st.markdown('<div class="box">The registration is not past due date. Proceeding to convert documents to PDF.</div>', unsafe_allow_html=True)
                        
                        if st.button("Convert to PDF"):
                            # Convert uploaded documents into a single PDF and save it in the "generated_pdfs" folder
                            convert_to_pdf(documents_content, "merged_documents.pdf")

                except Exception as e:
                    st.error(f"An error occurred: {e}")

                # New FTA Customer Account Creation Section
                st.subheader("Customer Account Creation in FTA")

                # Step 1: Check if the account is already created
                account_created = st.radio("Is the customer account already created in FTA?", ("Yes", "No"))

                if account_created == "No":
                    st.write("Tax manually triggers an email to confirm with the customer for proceeding with account creation which requires Email OTP.")

                    # Ask if customer replied within a fixed interval
                    customer_replied = st.radio("Did the customer reply within the fixed interval?", ("Yes", "No"))

                    if customer_replied == "Yes":
                        st.write("Tax manually creates FTA account for the customer which requires Email OTP authentication.")
                    else:
                        st.warning("Please wait for the customer to reply or resend the email.")
                else:
                    # Step 2: Existing account check
                    account_type = st.radio("Is the existing account with Email or UAE Pass?", ("Email", "UAE Pass"))

                    if account_type == "UAE Pass":
                        st.write("Tax manually logs into the FTA portal using UAE Pass and gets the Pass code verified by the customer.")
                    else:
                        st.write("Tax logs into the existing account using Email.")

    else:
        st.write("No documents uploaded yet.")

# Part 2: Handle Yes/No Response from Email
st.title("Document Registration Response")

# Get the response from the URL query parameters
query_params = st.experimental_get_query_params()
response = query_params.get("response", [None])[0]  # Fetch 'response' query parameter
company_name = query_params.get("company", [None])[0]  # Fetch 'company' query parameter

if response:
    if response == "yes":
        st.success(f"The company {company_name} has chosen to proceed with the registration.")
        # Proceed with additional registration steps if needed
        # ...
    elif response == "no":
        st.warning(f"The company {company_name} has chosen not to proceed with the registration.")
else:
    st.info("Waiting for response from the client...")
