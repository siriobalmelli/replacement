# prototype merge function
def merge_dict(in_to, *out_of):
	for b in objects:
		def scalar(thing=None):
			return thing == None or isinstance(thing, str) or not hasattr(thing, "__len__")

		# expose a uniform way of inserting into 'a'
		# ... depend on exceptions in case these don't pan out against b's datatype
		# (putting the "duck" and "cower" firmly into duck-typing).
		if hasattr(in_to, "update"):
			def push(k, v=None):
				'''push_dict()
				Check (and if kosher, push) k:v into 'in_to' - 'in_to' being a dictionary
				'''
				# new keys inserted as-is
				if k not in in_to:
					in_to[k] = v
					return
				# duplicate values ignored
				if in_to[k] == v:
					return
				# otherwise, merge recursively
				# NOTE that 2 conflicting scalars will become a list
				merge(in_to[k], v)

		else:
			# 'in_to' must be "insertable-into-able"
			if not hasattr(in_to, "append"):
				in_to = [ in_to ]
			def push(k, v=None):
				'''push_list()
				Push into 'in_to' as in_to list.
				'''
				if v:
					k = {k: v}
				in_to.append(k)

		# dictionary (key: value) types have an "items" function
		if hasattr(b, "items"):
			for k, v in b.items():
				push(k, v)
		# other iterable types are, well, iterable :P
		elif hasattr(b, "__iter__"):
			for val in b:
				push(val)
		# scalar?
		elif scalar(b):
			push(b)
		# garbage!
		else:
			raise Exception("cannot merge type '{0}'".format(type(b)))
