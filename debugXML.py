import sys
import xml.etree.ElementTree

import re, regex

txt = '<oki></oki>'

txt3 = '<oki  />'

txt2 = '<>blbla</>'

# pattern = '<(?=\s*(?:[a-zA-Z_\$[:^ascii:]](?:[\w\$\-\.[:^ascii:]]*[\w\$[:^ascii:]])?:)?[a-zA-Z_\$[:^ascii:]](?:[\w\$\-\.[:^ascii:]]*[\w\$[:^ascii:]])?(?:(<(?:\s*/\*(?:[^\*]|\*+[^/\*])*\*+/)*)?(?:\s*/\*(?:[^\*]|\*+[^/\*])*\*+/)*\s*[\?,]|(?:/\*(?:[^\*]|\*+[^/\*])*\*+/)+(?![\s<>]|/[>/\*]|$|[a-zA-Z_\$[:^ascii:]](?:[\w\$\-\.[:^ascii:]]*[\w\$[:^ascii:]])?|\{)))" />'





pattern = '<\s*(?:[a-z][a-z\d]*:)?[a-z][a-z\d]*(?=[\s<>]|\/[>/\*]|$)'
# pattern = '<\s*(?:[a-z][a-z\d]*:)?[a-z][a-z\d]*(?=[\s<>]|/[>/\*]|$)'
	

	
pattern2 = '<\s*>'
	
pattern3 = '<\s*(?:(?:[a-zA-Z_\$[:^ascii:]](?:[\w\$\-\.[:^ascii:]]*[\w\$[:^ascii:]])?:)?[a-zA-Z_\$[:^ascii:]](?:[\w\$\-\.[:^ascii:]]*[\w\$[:^ascii:]])?|>)(?=[\s<>]|/[>/\*]|$)'
# pattern3 = r'<\s*(?:(?:[a-zA-Z_\$[:^ascii:]](?:[\w\$\-\.[:^ascii:]]*[\w\$[:^ascii:]])?:)?[a-zA-Z_\$[:^ascii:]](?:[\w\$\-\.[:^ascii:]]*[\w\$[:^ascii:]])?|>)'
	

pattern4 = '<\s*(?:(?:[a-zA-Z_\$[:^ascii:]](?:[\w\$\-\.[:^ascii:]]*[\w\$[:^ascii:]])?:)?[a-zA-Z_\$[:^ascii:]](?:[\w\$\-\.[:^ascii:]]*[\w\$[:^ascii:]])?|>)'
	
pattern5 = '<\s*(?:(?:[a-zA-Z_\$[:^ascii:]](?:[\w\$\-\.[:^ascii:]]*[\w\$[:^ascii:]])?:)?[a-zA-Z_\$[:^ascii:]](?:[\w\$\-\.[:^ascii:]]*[\w\$[:^ascii:]])?|>)'
	

# pattern6 = 

# pattern3 = re.compile(pattern3)
	
print('FIRST', re.search(pattern3, txt), re.findall(pattern3, txt))
	
print('SECOND', regex.match(pattern3, txt))
# print(re.search(pattern, txt))
# 
# print(re.findall(pattern, txt))
# 
# print(re.search(pattern, txt3))



# print(re.search(pattern3, txt3))

# print(re.search(pattern2, txt2))

exit()

def parseEntities(content):
	lines = content.split('\n')
	entities = {}
	for line in lines:
		line = line.strip()
		if line.startswith('<!ENTITY'):
			comment_index = line.find('<!--')
			if(comment_index and comment_index != -1):
				line = line[0:comment_index]
			
			first_db_quote_index = line.index('"')
			last_db_quote_index = line.rfind('"')
			value = line[first_db_quote_index+1:last_db_quote_index]
			key = line[len("<!ENTITY"):first_db_quote_index].strip()
			
			# Also alter the value with previous entities
			for key2, value2 in entities.items():
				value = value.replace('&' + key2 + ';', value2)
			
			entities[key] = value
			
			content = content.replace('&' + key + ';', value)
			print(key, value)
	return content

filePath = '/run/media/piccolo/SSD-DATA/1 - VERY IMPORTANT/CMT/qutepart/syntax/data/xml/javascript-react.xml'
with open(filePath, 'r', encoding='utf-8') as definitionFile:
	content = definitionFile.read()
	
	content = parseEntities(content)
	
	
	f2 = open(filePath + '.modded.xml', 'w')
	f2.write(content)
	f2.close()
	# print(content)
	
	try:
		# doc = xml.etree.ElementTree.parse(definitionFile)
		# root = doc.getroot()
		root = xml.etree.ElementTree.fromstring(content)
		
		
		
	except Exception as ex:
		print('When opening %s:' % filePath, file=sys.stderr)
		raise
		
		
	# print(dir(doc))
	
	# exit()
	
	


	highlightingElement = root.find('highlighting')
	print(highlightingElement)
	
	exit()
	
	for elem in doc.iter():
		print(elem.attrib)
		print(dir(elem))
		break
	exit()
	# highlightingElement = doc.doctype('test')
	print(dir(root))
	exit()
	print(doc.keys())
	print(dir(doc))
	print(doc.__doc__)
	# print(highlightingElement)
