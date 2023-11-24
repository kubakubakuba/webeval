import subprocess
from datetime import datetime
import re
from collections import defaultdict

class QtRVSim:
	def __init__(self, args="", submission_file=""):
		'''Initialize the evaluator with the submission file, arguments, and registers and memory to compare.'''

		self.log = f"Evaluation started on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
		self.log += f"Arguments: {args}\n"
		#self.log += f"Submission file: {submission_file}\n\n"
		self.log += f"Error log:"

		self.args = args
		self.mem_arg = ""
		self.dump_mem_arg = ""
		self.submission_file = submission_file

		self.compare_registes = defaultdict(str) # list of registers to compare
		self.reference_memory = defaultdict(str) # list of memory to compare
		self.starting_memory_addr = 0

		self.reference_ending_memory_addr = 0
		self.reference_ending_memory_length = 0

		self.do_compare_registers = False
		self.do_compare_memory = False
		self.do_set_starting_memory = False

		self.cycles = -1
		self.result = -1
		self.cache_stats = defaultdict(int)
		self.scores = defaultdict(int)

		self.timeout_time = 10 #seconds

		self.regs = defaultdict(int)
		self.mem = defaultdict(int)

		self.verbose = False

		self.mem_output_file = "__ending_mem__"
		self.starting_memory_file = '__starting_mem__'

		self.register_names = [
			"zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2",
			"s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5",
			"a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7",
			"s8", "s9", "s10","s11", "t3", "t4", "t5", "t6"
		]
	
	def get_result(self):
		'''Return the result of the evaluation.'''
		return self.result
	
	def get_cycles(self):
		'''Return the cycles of the evaluation.'''
		return self.cycles
	
	def get_scores(self):
		'''Return the scores of the evaluation.'''
		return self.scores
	
	def get_log(self):
		'''Return the log of the evaluation.'''
		return self.log
	
	def set_args(self, args):
		'''Set the arguments to pass to qtrvsim.'''
		self.args = args

	def set_submission_file(self, submission_file):
		'''Set the submission file to evaluate.'''
		self.submission_file = submission_file

	def set_do_compare_registers(self, val=True):
		'''Set whether to compare registers or not.'''
		self.do_compare_registers = val

	def set_do_compare_memory(self, val=True):
		'''Set whether to compare memory or not.'''
		self.do_compare_memory = val
		if not val:
			self.mem_arg = ""
			self.dump_mem_arg = ""

	def set_reference_ending_regs(self, reg_dict):
		'''Pass a dict of values to compare against.'''
		self.compare_registes = reg_dict

	def set_starting_memory(self, mem):
		'''Set the starting memory. Pass an array of pairs (address, value).'''
		start_address = min(mem.keys())
		end_address = max(mem.keys()) + 4

		self.starting_memory_addr = start_address

		with open(self.starting_memory_file, 'w') as file:
			for address in range(start_address, end_address, 4):
				# Write the value if the address is in the dictionary, otherwise write 0
				value = mem.get(address, 0)
				file.write(f"{value}\n")

		self.mem_arg = f" --load-range {self.starting_memory_addr},{self.starting_memory_file}"

	def set_reference_ending_memory(self, mem):
		'''Pass an array of pairs (address, value) to compare against.'''
		self.reference_ending_memory_addr = min(mem.keys())
		self.reference_ending_memory_length = max(mem.keys()) + 4
		#add a flag to dump memory to a file
		self.reference_ending_memory_length = self.reference_ending_memory_length - self.reference_ending_memory_addr

		self.dump_mem_arg = f" --dump-range {hex(self.reference_ending_memory_addr)},{self.reference_ending_memory_length},{self.mem_output_file}"

		self.reference_memory = mem

	def rgx_get_cycles(self, log):
		'''Get the number of cycles from the stdout of qtrvsim.'''
		match = re.search(r"^cycles: (\d+)$", log, re.MULTILINE)
		if match is not None:
			self.cycles = int(match.group(1))
		else:
			self.cycles = -1

	def read_mem_output_file(self):
		'''Read the memory file and set the self.mem dictionary.'''
		self.mem = defaultdict(int) #clear the memory
		base_address = self.reference_ending_memory_addr

		with open(self.mem_output_file, 'r') as file:
			for line in file:
				mem_val = line.strip()
				self.mem[base_address] = int(mem_val, 16)
				base_address += 4

	def clear_files(self):
		'''Clear the memory and starting memory files.'''
		with open(self.mem_output_file, 'w') as f:
			f.write("")
		with open(self.starting_memory_file, 'w') as f:
			f.write("")

	def end_eval(self, score_metric="cycles"):
		self.log += f"\n\nEvaluation ended on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
		score = self.scores[score_metric] if self.result == 0 else -1
		self.log += f"Result: {score}\n"
		self.clear_files()

	def reset(self):
		self.do_compare_memory = False
		self.do_compare_registers = False
		self.starting_memory_addr = 0
		self.reference_ending_memory_addr = 0
		self.reference_ending_memory_length = 0
		self.mem = defaultdict(int)
		self.regs = defaultdict(int)
		self.compare_registes = defaultdict(int)
		self.reference_memory = defaultdict(int)

	def rgx_get_cache_stats(self, log):
		'''Get the cache stats from the stdout of qtrvsim. Set them to the self.cache_stats dictionary.'''

		patterns = {
			r"^i-cache:reads: (\d+)$": ("i-cache:reads", int),
			r"^i-cache:hit: (\d+)$": ("i-cache:hit", int),
			r"^i-cache:miss: (\d+)$": ("i-cache:miss", int),
			r"^i-cache:hit-rate: (\d+\.\d+)$": ("i-cache:hit-rate", float),
			r"^i-cache:stalled-cycles: (\d+)$": ("i-cache:stalled-cycles", int),
			r"^i-cache:improved-speed: (\d+\.\d+)$": ("i-cache:improved-speed", float),
			r"^d-cache:reads: (\d+)$": ("d-cache:reads", int),
			r"^d-cache:hit: (\d+)$": ("d-cache:hit", int),
			r"^d-cache:miss: (\d+)$": ("d-cache:miss", int),
			r"^d-cache:hit-rate: (\d+\.\d+)$": ("d-cache:hit-rate", float),
			r"^d-cache:stalled-cycles: (\d+)$": ("d-cache:stalled-cycles", int),
			r"^d-cache:improved-speed: (\d+\.\d+)$": ("d-cache:improved-speed", float),
		}

		for pattern, (stat_key, value_type) in patterns.items():
			match = re.search(pattern, log, re.MULTILINE)
			if match:
				self.cache_stats[stat_key] = value_type(match.group(1))
		
	def rgx_get_registers(self, log):
		'''Get the registers from the stdout of qtrvsim. Set them to the self.regs dictionary.'''
		self.regs = defaultdict(int) #clear the registers

		# Patterns for registers
		patterns = {
			r"PC:(0x[0-9a-fA-F]+)": "PC",
			**{rf"R{i}:(0x[0-9a-fA-F]+)": f"R{i}" for i in range(32)},
			r"mvendorid: (0x[0-9a-fA-F]+)": "mvendorid",
			r"marchid: (0x[0-9a-fA-F]+)": "marchid",
			r"mimpid: (0x[0-9a-fA-F]+)": "mimpid",
			r"mhardid: (0x[0-9a-fA-F]+)": "mhardid",
			r"mstatus: (0x[0-9a-fA-F]+)": "mstatus",
		}

		for pattern, reg_key in patterns.items():
			match = re.search(pattern, log, re.MULTILINE)
			if match:
				self.regs[reg_key] = int(match.group(1), 16)
		
		for i in range(32):
			if f"R{i}" in self.regs:
				self.regs[self.register_names[i]] = self.regs.pop(f"R{i}") #replace Ri values with the register names

	def set_verbose(self, val=True):
		'''Set whether to print the stdout and stderr of qtrvsim to the console.'''
		self.verbose = val

	def log_test_name(self, test_name):
		'''Log the name of the test.'''
		failed = self.result != 0

		if failed:
			self.log += f"\nRunning: {test_name} - FAILED\n"
		else:
			self.log += f"\nRunning: {test_name} - PASSED\n"

	def run(self):
		'''Run qtrvsim with the current configuration.'''
		#run qtrvsim with the given arguments, dump the output into the log string
		arguments = self.args + self.mem_arg + self.dump_mem_arg
		print(self.args)
		print(self.mem_arg)
		print(self.dump_mem_arg)
		arguments = arguments.split()
		command = ["qtrvsim_cli"] + arguments + ["--asm", self.submission_file]

		killed = False

		try:
			process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			stdout, stderr = process.communicate(timeout=self.timeout_time)

		except subprocess.TimeoutExpired:
			process.kill()
			stdout, stderr = None, None
			killed = True
			self.log += f"\nKilled after {self.timeout_time} seconds."

		stdout_text =  "" if killed else stdout.decode('utf-8')
		stderr_text = f'Killed after {self.timeout_time} seconds.' if killed else stderr.decode('utf-8')

		if self.verbose:
			print(stdout_text)
			print(stderr_text)

		was_accepted = 0 #TODO: check if the output is correct

		if not killed:
			self.rgx_get_cycles(stdout_text)
			self.rgx_get_cache_stats(stdout_text)

			if self.do_compare_registers:
				self.rgx_get_registers(stdout_text)
				#compare registers
				for reg, value in self.compare_registes.items():
					if self.regs[reg] != value:
						was_accepted = 1
						self.log += f"\nregister {reg} does not match, expected {value}, got {self.regs[reg]}"

			if self.do_compare_memory:
				self.read_mem_output_file()
				for addr, value in self.reference_memory.items():
					if self.mem[addr] != value:
						was_accepted = 1
						self.log += f"\nmemory at {hex(addr)} does not match, expected {value}, got {self.mem[addr]}"

		if killed:
			self.result = 2
		else:
			self.result = was_accepted

		#save score metrics, -> cycles and cache stats
		self.scores["cycles"] = self.cycles #scoring metric for cycles
		self.scores["cache"] = self.cache_stats["i-cache:improved-speed"] #scoring metric for cache