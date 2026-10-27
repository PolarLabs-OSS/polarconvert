from polarconvert import parse,serialize,convert
assert parse('{"a":2}', 'JSON')=={'a':2}
assert parse('a: 2\n','YAML')=={'a':2}
assert parse('name,age\nAlice,25\n','CSV')==[{'name':'Alice','age':'25'}]
assert parse('<root><a>x</a></root>','XML')=={'root':{'a':'x'}}
a=convert('[{"name":"Alice","age":25}]','JSON','CSV')
assert 'Alice' in a and 'name' in a
assert parse(convert('{"a":2}','JSON','YAML'),'YAML')=={'a':2}
assert '<root>' in serialize({'a':1},'XML')
try:parse('{bad}','JSON');raise AssertionError('Expected invalid')
except ValueError:pass
print('PASS: CSV JSON YAML XML parse convert validate')
