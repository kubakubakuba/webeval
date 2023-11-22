import subprocess
from datetime import datetime
import re
from collections import defaultdict

class QtRVSim:
	def __init__(self, args="", submission_file=""):
		'''Initialize the evaluator with the submission file, arguments, and registers and memory ranges to compare.'''

		self.log = f"Evaluation started on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
		self.log += f"Arguments: {args}\n"
		self.log += f"Submission file: {submission_file}\n\n"
		self.log += f"Error log:"

		self.args = args
		self.submission_file = submission_file

		self.compare_registes = defaultdict(str) # list of registers to compare
		self.compare_memory_ranges = defaultdict(str) # list of memory ranges to compare

		self.do_compare_registers = False
		self.do_compare_memory_ranges = False

		self.cycles = -1
		self.result = -1
		self.cache_stats = defaultdict(int)
		self.scores = defaultdict(int)

		self.timeout_time = 10 #seconds

		self.regs = defaultdict(int)
		self.mem = defaultdict(int)

		self.verbose = False

		self.mem_output_file = "__mem_output__"
	
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

	def set_do_compare_memory_ranges(self, val=True):
		'''Set whether to compare memory ranges or not.'''
		self.do_compare_memory_ranges = val

	def set_compare_memory_ranges(self, mem):
		'''Set the memory ranges to compare. Pass an array of pairs (start, end) of memory ranges.'''
		self.compare_memory_ranges = mem

	def set_reference_regs(self, reg_dict):
		'''Pass a dict of values to compare against.'''
		self.compare_registes = reg_dict[0]

	def set_reference_memory(self, mem_values):
		'''Pass an array of pairs (address, value) to compare against.'''
		self.compare_memory = mem_values

	def rgx_get_cycles(self, log):
		'''Get the number of cycles from the stdout of qtrvsim.'''
		match = re.search(r"^cycles: (\d+)$", log, re.MULTILINE)
		if match is not None:
			self.cycles = int(match.group(1))
		else:
			self.cycles = -1

	def end_eval(self, score_metric="cycles"):
		self.log += f"\n\nEvaluation ended on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
		self.log += f"Result: {score}\n"

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
				self.regs[reg_key] = match.group(1)

	def set_verbose(self, val=True):
		'''Set whether to print the stdout and stderr of qtrvsim to the console.'''
		self.verbose = val

	def run(self):
		'''Run qtrvsim with the current configuration.'''
		#run qtrvsim with the given arguments, dump the output into the log string
		arguments = self.args.split()
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

			# if self.do_compare_memory_ranges: #TODO: implement
			# 	#compare memory ranges
			# 	self.rgx_get_memory_ranges(stdout_text)
			# 	for start, end in self.compare_memory_ranges:
			# 		for addr in range(start, end):
			# 			if self.mem[addr] != self.mem[addr]:
			# 				was_accepted = 1
			# 				break

		if killed:
			self.result = 2
		else:
			self.result = was_accepted

		#save score metrics, -> cycles and cache stats
		self.scores["cycles"] = self.cycles #scoring metric for cycles
		self.scores["cache"] = self.cache_stats["i-cache:improved-speed"] #scoring metric for cache