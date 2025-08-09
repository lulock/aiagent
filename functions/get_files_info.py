import os
import subprocess
from config import *

from google.genai import types
schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)

schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="Prints contents of files in the specified directory along with their sizes, constrained to the working directory and limited to 10000 characters.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the file to get content from, relative to the working directory.",
            ),
        },
    ),
)

schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Executes specified file with optional additional arguments, constrained to the working directory. Prints both STDERR and STDOUT, or exit code if unsuccessful.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={ 
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the file to get content from, relative to the working directory.",
            ),
            "args": types.Schema(
                type=types.Type.STRING,
                description="The additional arguments to append to the function call, if provided.",
            ),
        },
    ),
)

schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Writes specified contents to specified file, listing characters written upon success.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The file_path to write to, relative to the working directory.",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="The content to write to file."
            ),
        },
    ),
)

def get_files_info(working_directory, directory="."):
    full_path = os.path.join(working_directory, directory)

    # check if the file is outside the working directory
    if not os.path.abspath(full_path).startswith(os.path.abspath(working_directory)):
        return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'

    if not os.path.isdir(os.path.abspath(full_path)):
        return f'Error: "{directory}" is not a directory'

    dirs = os.listdir(os.path.abspath(full_path))
    res_string = ''

    for dir in dirs:
        path = '/'.join([os.path.abspath(full_path), dir])
        res_string += f'- {dir}: file_size={os.path.getsize(path)}, is_dir={not os.path.isfile(path)}\n'

    return res_string

def get_file_content(working_directory, file_path):
    # check if the file is outside the working directory
    try: 
        full_path = os.path.abspath(os.path.join(working_directory, file_path))
        full_wd_path = os.path.abspath(working_directory)
        if not full_path.startswith(full_wd_path):
            return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'

        if not os.path.isfile(full_path):
            return f'Error: File not found or is not a regular file: "{file_path}"'

        with open(full_path, "r") as f:
            file_content_string = f.read(MAX_CHARS + 1)
            if len(file_content_string) > MAX_CHARS:
                return file_content_string[:MAX_CHARS] + f'[...File "{file_path}" truncated at 10000 characters]'

            return file_content_string
    except Exception as e:
        return f'Error: {e}'

def write_file(working_directory, file_path, content):
    # check if the file is outside the working directory
    try: 
        full_path = os.path.abspath(os.path.join(working_directory, file_path))
        full_wd_path = os.path.abspath(working_directory)
        if not full_path.startswith(full_wd_path):
            return f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'

        if not os.path.isfile(full_path):
            # if the file path does not exist then create it!
            dirname = os.path.dirname(full_path)
            os.makedirs(dirname, exist_ok=True)
            #return f'Error: File not found or is not a regular file: "{file_path}"'

        with open(full_path, "w") as f:
            f.write(content)

        return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'
    except Exception as e:
        return f'Error: {e}'

def run_python_file(working_directory, file_path, args=[]):
    # check if the file is outside the working directory
    try: 
        full_path = os.path.abspath(os.path.join(working_directory, file_path))
        full_wd_path = os.path.abspath(working_directory)
        if not full_path.startswith(full_wd_path):
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

        if not os.path.isfile(full_path):
            return f'Error: File "{file_path}" not found.'
        if file_path[-3:] != ".py":
            return f'Error: "{file_path}" is not a Python file.'

        print(full_wd_path)
        print(full_path)
        print(file_path)

        result = subprocess.run(['uv', 'run', f'{file_path}'] + args, capture_output=True, text=True, timeout=30, cwd=full_wd_path)

        resulting_string = f'STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\n'
        if result.returncode != 0:
            resulting_string += f'Process exited with code {result.returncode}'

        if result is None:
            return f'No output produced'
        else:
            return resulting_string

    except Exception as e:
        return f"Error: executing Python file: {e}"

call_fn = {
    "run_python_file": run_python_file,
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "write_file": write_file,
}

def call_function(function_call_part, verbose=False):
    if verbose:
        print(f"Calling function: {function_call_part.name}({function_call_part.args})")
    else:
        print(f" - Calling function: {function_call_part.name}")

    if function_call_part.name in call_fn:
        result = call_fn[function_call_part.name](working_directory = "./calculator", **function_call_part.args)
    else:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_call_part.name,
                    response={"error": f"Unknown function: {function_call_part.name}"},
                )
            ],
        )

    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_call_part.name,
                response={"result": result},
            )
        ],
    )
