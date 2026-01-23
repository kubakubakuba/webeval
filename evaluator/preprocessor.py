import toml
import re
import sys
import random
import ast

RE = r'\"\{\{\$\s*(\w+)\s*\$\}\}\"'

safe_globals = {
	'__builtins__': {
		'range': range,
		'sorted': sorted,
		'list': list,
		'int': int,
		'len': len,
		'min': min,
		'max': max,
		'abs': abs,
	},
	'random': random
}

def validate_and_compile(source):
	try:
		tree = ast.parse(source, mode='eval')

	except SyntaxError:
		raise ValueError("Code must be a single valid expression. No semicolons, no statements.")

	for node in ast.walk(tree):
		#block access to  __class__, __bases__, etc
		if isinstance(node, ast.Attribute) and node.attr.startswith('_'):
			raise ValueError(f"Access to private attribute '{node.attr}' is forbidden.")
		
		if isinstance(node, ast.Name) and node.id in ('eval', 'exec', 'compile'):
			raise ValueError(f"Function '{node.id}' is forbidden.")

	return compile(tree, filename="<string>", mode="eval")

def preprocess(f):
	toml_content = f.read()
	toml_dict = toml.loads(toml_content)

	if 'preprocessor' in toml_dict:
		preprocessor_code = toml_dict.pop('preprocessor')
		context = {}
		for var_name, code_str in preprocessor_code.items():
			try:
				compiled_code = validate_and_compile(code_str)
				
				value = eval(compiled_code, safe_globals, context)
				context[var_name] = value
				
			except Exception as e:
				print(f"Security/Runtime error in variable '{var_name}': {e}")
				context[var_name] = f"ERROR_{var_name}"
	else:
		context = {}

	def replace_placeholder(match):
		var_name = match.group(1)
		if var_name in context:
			value = context[var_name]
			#dump the new toml string v=res
			return toml.dumps({'v': value}).strip().split('= ', 1)[1]
		else:
			print(f"Undefined variable '{var_name}' in placeholder")
			return f'"UNDEFINED_{var_name}"'

	toml_content_no_preprocessor = re.sub(r'\[preprocessor\][\s\S]*?(?=\n\[|$)', '', toml_content, count=1)
	processed_toml_content = re.sub(RE, replace_placeholder, toml_content_no_preprocessor)

	return processed_toml_content

if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("Usage: python preprocess.py input_file.toml")
		sys.exit(1)

	with open(sys.argv[1], 'r') as f:
		print(preprocess(f))