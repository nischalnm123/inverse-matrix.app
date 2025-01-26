import streamlit as st
import numpy as np
import firebase_admin
from firebase_admin import credentials, auth
import pandas as pd
from io import BytesIO

# Initialize Firebase Admin SDK (only if not already initialized)
if not firebase_admin._apps:
    cred = credentials.Certificate("./key.json")
    firebase_admin.initialize_app(cred)

def register_user(email, password, display_name):
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name
        )
        return True, f"User {user.display_name} registered successfully!"
    except Exception as e:
        return False, str(e)

def authenticate_user(email, password):
    try:
        user = auth.get_user_by_email(email)
        return True, f"Welcome back, {user.display_name}!"
    except Exception as e:
        return False, "Invalid email or user does not exist."

def calculate_inverse(matrix):
    try:
        matrix_np = np.array(matrix, dtype=float)
        inverse_np = np.linalg.inv(matrix_np)
        return inverse_np, None
    except np.linalg.LinAlgError:
        return None, "Matrix is not invertible!"
    except ValueError:
        return None, "Invalid input! Please enter numeric values."

def generate_report(input_matrix, output_matrix):
    report_data = {
        "Input Matrix": [" ".join(map(str, row)) for row in input_matrix],
        "Output (Inverse Matrix)": [" ".join(map(lambda x: f"{x:.2f}", row)) for row in output_matrix]
    }
    report_df = pd.DataFrame(report_data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        report_df.to_excel(writer, index=False, sheet_name='Matrix Report')
    output.seek(0)  # Reset the pointer to the beginning of the file
    return output

# Streamlit UI
def main():
    st.set_page_config(page_title="Matrix Inverse Calculator", layout="wide", page_icon="🧮")

    st.title("🧮 Matrix Inverse Calculator")

    # Session-based authentication state
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
        st.session_state.user_message = ""

    # Login/Registration Section
    st.sidebar.title("User Authentication")
    if not st.session_state.is_authenticated:
        auth_option = st.sidebar.radio("Choose an option", options=["Login", "Register"])

        if auth_option == "Register":
            st.sidebar.subheader("Register")
            reg_email = st.sidebar.text_input("Email", placeholder="Enter your email")
            reg_password = st.sidebar.text_input("Password", placeholder="Enter your password", type="password")
            reg_display_name = st.sidebar.text_input("Display Name", placeholder="Enter your name")
            if st.sidebar.button("Register"):
                success, message = register_user(reg_email, reg_password, reg_display_name)
                if success:
                    st.sidebar.success(message)
                else:
                    st.sidebar.error(message)

        elif auth_option == "Login":
            st.sidebar.subheader("Login")
            email = st.sidebar.text_input("Email", placeholder="Enter your email")
            password = st.sidebar.text_input("Password", placeholder="Enter your password", type="password")
            if st.sidebar.button("Login"):
                is_authenticated, message = authenticate_user(email, password)
                st.session_state.is_authenticated = is_authenticated
                st.session_state.user_message = message
                if is_authenticated:
                    st.sidebar.success(message)
                else:
                    st.sidebar.error(message)

    if st.session_state.is_authenticated:
        st.sidebar.success(st.session_state.user_message)

        # Main Functionality after Login
        st.header("Matrix Inverse Calculation")

        # Step 1: Matrix Size Input
        size = st.selectbox("Select Matrix Size", options=[2, 3, 4], index=0)

        # Step 2: Matrix Input with Persistent State
        matrix_key = f"matrix_{size}"  # Unique key for the matrix size

        # Initialize matrix in session state if not already
        if matrix_key not in st.session_state:
            st.session_state[matrix_key] = [[0.0] * size for _ in range(size)]

        matrix_input = st.session_state[matrix_key]  # Reference session state matrix

        st.write(f"Enter values for a {size}x{size} matrix:")

        for i in range(size):
            cols = st.columns(size)
            for j in range(size):
                # Display existing value from session state
                matrix_value = matrix_input[i][j]
                # Update session state when the user changes a value
                new_value = cols[j].text_input(
                    f"Row {i+1}, Col {j+1}",
                    value=str(matrix_value),
                    key=f"cell_{size}{i}{j}",
                )
                try:
                    matrix_input[i][j] = float(new_value)
                except ValueError:
                    pass  # Ignore invalid inputs temporarily

        # Submit Button
        if st.button("Calculate Inverse"):
            inverse_matrix, error = calculate_inverse(matrix_input)
            if error:
                st.error(error)
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Input Matrix:")
                    st.write(np.array(matrix_input))

                with col2:
                    st.write("Inverse Matrix:")
                    st.write(inverse_matrix)

                # Generate Report
                report_file = generate_report(matrix_input, inverse_matrix)
                st.download_button(
                    label="Download Report",
                    data=report_file,
                    file_name="Matrix_Inverse_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    main()
