import toml
import re
import sys
import random

RE = r'\"\{\{\$\s*(\w+)\s*\$\}\}\"'

safe_globals = {'random': random}

def preprocess(f):
	toml_content = f.read()

	toml_dict = toml.loads(toml_content)

	if 'preprocessor' in toml_dict:
		preprocessor_code = toml_dict.pop('preprocessor')
		context = {}
		for var_name, code_str in preprocessor_code.items():
			try:
				exec(f"{var_name} = {code_str}", safe_globals, context)
			except Exception as e:
				print(f"Error in preprocessor code for variable '{var_name}': {e}")
				sys.exit(1)
	else:
		context = {}

	def replace_placeholder(match):
		var_name = match.group(1)
		
		if var_name in context:
			value = context[var_name]
			return toml.dumps({'value': value}).strip().split('= ', 1)[1]
		
		else:
			print(f"Undefined variable '{var_name}' in placeholder")
			sys.exit(1)

	toml_content_no_preprocessor = re.sub(r'\[preprocessor\][\s\S]*?(?=\n\[|$)', '', toml_content, count=1)

	processed_toml_content = re.sub(RE, replace_placeholder, toml_content_no_preprocessor)

	return processed_toml_content

if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("Usage: python preprocess.py input_file.toml")
		sys.exit(1)

	with open(sys.argv[1], 'r') as f:
		print(preprocess(f))
