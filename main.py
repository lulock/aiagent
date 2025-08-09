import os
from dotenv import load_dotenv
import sys

from google import genai
from google.genai import types
from functions.get_files_info import schema_get_files_info, schema_get_file_content, schema_run_python_file, schema_write_file, call_function

def main():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")

    client = genai.Client(api_key=api_key)

    system_prompt = system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
"""
    model_name = 'gemini-2.0-flash-001'

    available_functions = types.Tool(
        function_declarations=[
            schema_get_files_info,
            schema_get_file_content,
            schema_run_python_file,
            schema_write_file
        ]
    )

    #print("Hello from aiagent!")
    if len(sys.argv) < 2:
        print("error! no query passed")
        exit(1)
    else:
        prompt = sys.argv[1]
        try:
            verbose = sys.argv[2] == '--verbose'
        except:
            verbose = False
        messages = [types.Content(
            role='user',
            parts=[types.Part.from_text(text=prompt)]
        )]
        for i in range(20):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=messages,
                    config=types.GenerateContentConfig(
                        tools=[available_functions],
                        system_instruction=system_prompt
                    ),
                )
            except Exception as e:
                print(f'Error: {str(e)}')
                break
            
            for candidate in response.candidates:
                messages.append(candidate.content)

            if response.function_calls and len(response.function_calls) > 0:
                for function_call_part in response.function_calls:
                    try:
                        result = call_function(function_call_part)
                    except Exception as e:
                        messages.append(
                            types.Content(
                                role='tool',
                                parts=[types.Part(types.FunctionResponse(
                                    name=function_call_part.name,
                                    response={'error': str(e)}
                                ))]
                            )
                        )
                    if len(result.parts) > 0:
                        messages.append(types.Content(
                            role='tool',
                            parts=result.parts
                        ))
                        if verbose:
                            print(f"-> {result.parts[0].function_response.response}")
                    else:
                        raise Exception('Error: no function call results')
            else:
                print(response.text)
                break

        if len(sys.argv) > 2 and sys.argv[2] == '--verbose':
            print(f'User prompt: {prompt}')
            print(f'Prompt tokens: {response.usage_metadata.prompt_token_count}')
            print(f'Response tokens: {response.usage_metadata.candidates_token_count}')


if __name__ == "__main__":
    main()
