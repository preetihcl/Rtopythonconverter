import os
import subprocess
import textwrap
import openai
from flask import Flask, render_template, request, url_for, send_from_directory

app = Flask(__name__)


# Folder paths for uploaded and converted files
UPLOAD_FOLDER = "UPLOAD_FOLDER"
PYTHON_FOLDER = "PYTHON_FOLDER"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PYTHON_FOLDER, exist_ok=True)

# Helper function to clear a folder
def clear_folder(folder_path):
    if os.path.exists(folder_path):
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")

# Helper function to validate R code
def validate_r_code(r_code):
    """
    Validates R code by running it in a subprocess using the Rscript interpreter.
    Returns a tuple (is_valid, error_message).
    """
    try:
        # Normalize line endings to Unix style
        normalized_r_code = r_code.replace('\r\n', '\n').strip()

        # Save R code to a temporary file with UTF-8 encoding
        temp_r_file = "temp_code_validation.R"
        with open(temp_r_file, 'w', encoding='utf-8', newline='\n') as file:
            file.write(normalized_r_code)

        # Run the R script using Rscript command
        result = subprocess.run(
            ["Rscript", temp_r_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Check for errors in the execution
        if result.returncode != 0:
            return False, f"R script execution failed with error: {result.stderr.strip()}"
        
        return True, None
    except Exception as e:
        return False, f"An exception occurred during R script validation: {str(e)}"
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_r_file):
            os.remove(temp_r_file)

# Helper function to validate Python code
def validate_python_code(python_code):
    """
    Validates Python code by attempting to execute it.
    Returns a tuple (is_valid, error_message).
    """
    try:
        exec(python_code, {})
        return True, None
    except Exception as e:
        return False, str(e)

# Helper function to convert R code to Python
def convert_r_to_python(openai_key, r_code):
    """
    Converts R code to Python code using OpenAI API.
    """
    prompt = f"""
    You are a highly skilled programmer proficient in both R and Python. Your task is to convert the given R code into Python 3.x code that is functional and compliant with Python best practices.

    Instructions:
    1. Include all necessary library imports in the Python code.
    2. Ensure the Python code replicates the logic and functionality of the R code accurately.
    3. Output **only the Python code**—no explanations or comments.

    Here is the R code to convert:
    {r_code}
    """

    try:
        openai.api_key = openai_key
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",
            prompt=prompt,
            temperature=0,
            max_tokens=1500,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        raise Exception(f"Error during R to Python conversion: {e}")


@app.route('/', methods=['GET', 'POST'])
def RToPythonConverter():
    """
    Handles R to Python conversion, both from code snippets and file uploads.
    """
    if request.method == 'POST':
        openai_key = request.form.get('openai_key', '').strip()
        action = request.form.get('action')
        error_message = None
        python_code = ""
        download_link = None
        success_message = None

        # Validate OpenAI API Key
        if not openai_key:
            error_message = "The OpenAI API key is required for conversion. Please enter a valid key."
            return render_template(
                'RtoPythonConverter.html',
                error_message=error_message
            )

        # Handle R Code Snippet Conversion
        if action == 'convert':
            r_code = request.form.get('r_code', '').strip()
            if not r_code:
                error_message = "Please enter some R code to convert."
            else:
                # Validate the R code
                is_valid, validation_error = validate_r_code(r_code)
                if not is_valid:
                    error_message = f"R code validation failed: {validation_error}."
                else:
                    try:
                        python_code = convert_r_to_python(openai_key, r_code)
                        # Clean up indentation
                        python_code = textwrap.dedent(python_code)
                        # Validate the generated Python code
                        is_valid, validation_error = validate_python_code(python_code)
                        if not is_valid:
                            error_message = f"Generated python code validation failed: {validation_error}."
                        else:
                            success_message = "Converted and validated successfully!"
                    except Exception as e:
                        error_message = str(e)

            # Render response with either the Python code or error message
            return render_template(
                'RtoPythonConverter.html',
                r_code=r_code,
                python_code=python_code,
                error_message=error_message,
                success_message=success_message
            )

        # Handle R File Upload and Conversion
        elif action == 'upload_convert':
            uploaded_file = request.files.get('r_file')
            r_code = ""
            python_code = ""
            error_message = None
            success_message = None
            download_link = None

            if not uploaded_file or not (uploaded_file.filename.endswith('.R') or uploaded_file.filename.endswith('.r')):
                error_message = "The uploaded file must be a valid R file with the extension .R or .r."
            else:
                try:
                    # Clear the upload and Python folders
                    clear_folder(UPLOAD_FOLDER)
                    clear_folder(PYTHON_FOLDER)

                    # Save the uploaded R file
                    uploaded_file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
                    uploaded_file.save(uploaded_file_path)

                    # Read the R code from the file
                    with open(uploaded_file_path, 'r', encoding='utf-8') as file:
                        r_code = file.read()

                    # Validate the R code
                    is_valid, validation_error = validate_r_code(r_code)
                    if not is_valid:
                        error_message = f"R code validation failed: {validation_error}."
                    else:
                        # Convert R code to Python code
                        python_code = convert_r_to_python(openai_key, r_code)

                        # Clean up indentation
                        clean_python_code = textwrap.dedent(python_code)

                        # Validate the generated Python code
                        is_valid, validation_error = validate_python_code(clean_python_code)
                        if not is_valid:
                            error_message = f"Generated Python code validation failed: {validation_error}."
                        else:
                            # Save the converted Python code
                            python_file_name = os.path.splitext(uploaded_file.filename)[0] + ".py"
                            python_file_path = os.path.join(PYTHON_FOLDER, python_file_name)
                            with open(python_file_path, 'w', newline='\n', encoding='utf-8') as file:
                                file.write(clean_python_code)

                            # Provide download link and success message
                            download_link = url_for('download_file', filename=python_file_name)
                            success_message = "File converted and validated successfully! You can download the Python file."

                except Exception as e:
                    error_message = str(e)

            # Render the response based on the validation results
            return render_template(
                'RtoPythonConverter.html',
                r_code=r_code if error_message and not python_code else '',
                python_code=python_code if error_message and python_code else '',
                error_message=error_message,
                download_link=download_link,
                success_message=success_message
            )

    # Render initial page (GET request)
    return render_template('RtoPythonConverter.html')

@app.route('/download/<filename>')
def download_file(filename):
    """
    Allows downloading of the converted Python file.
    """
    return send_from_directory(PYTHON_FOLDER, filename, as_attachment=True)



if __name__ == '__main__':
    app.run(debug=True)
