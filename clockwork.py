import time
def clockwork(duration):
	def clock(method):
		def wrapper(*args,**kwargs):
			contingency = 0.001
			start = time.time()
			result = method(*args,**kwargs)
			while (time.time()-start) < (duration - contingency):
				pass
			return result
		return wrapper
	return clock

if __name__ == "__main__":
	@clockwork(3)
	def p(x):
		return x
	start = time.time()
	print(p(1))
	print("Duration: {}".format(time.time()-start))