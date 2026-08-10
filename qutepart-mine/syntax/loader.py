"""This module is a set of functions, which load Parser from Kate XML files
"""

import copy
import sys
import xml.etree.ElementTree
import re
import logging

from qutepart.syntax.colortheme import ColorTheme
from qutepart.syntax import TextFormat

from qutepart import debug

def dprint(*args):
    debug.dprint(*args)

_logger = logging.getLogger('qutepart')

# import qutepart.syntax.cParser as _parserModule
# binaryParserAvailable = True

import qutepart.syntax.parser as _parserModule
binaryParserAvailable = False

# try:
#     import qutepart.syntax.cParser as _parserModule
#     binaryParserAvailable = True
# except ImportError:
#     _logger.warning('Failed to import quick parser in C. Using slow parser for syntax highlighting')
#     import qutepart.syntax.parser as _parserModule
#     binaryParserAvailable = False


_seqReplacer = re.compile('\\\\.')

_escapeSequences = \
{  '\\': '\\',
  'a': '\a',
  'b': '\b',
  'f': '\f',
  'n': '\n',
  'r': '\r',
  't': '\t',}


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def _processEscapeSequences(replaceText):
    """Replace symbols like \n \\, etc
    """
    def _replaceFunc(escapeMatchObject):
        char = escapeMatchObject.group(0)[1]
        if char in _escapeSequences:
            return _escapeSequences[char]

        return escapeMatchObject.group(0)  # no any replacements, return original value

    return _seqReplacer.sub(_replaceFunc, replaceText)


_DEFAULT_ATTRIBUTE_TO_STYLE_MAP = \
{
    'alert' : 'dsAlert',
    'base-n integer' : 'dsBaseN',
    'character' : 'dsChar',
    'string char': 'dsChar',
    'comment' : 'dsComment',
    'data type' : 'dsDataType',
    'decimal/value' : 'dsDecVal',
    'error' : 'dsError',
    'floating point' : 'dsFloat',
    'function' : 'dsFunction',
    'keyword' : 'dsKeyword',
    'normal' : 'dsNormal',
    'others' : 'dsOthers',
    'region marker' : 'dsRegionMarker',
    'string' : 'dsString'
}

_KNOWN_STYLES = set([  "dsNormal",
                       "dsKeyword",
                       "dsDataType",
                       "dsDecVal",
                       "dsBaseN",
                       "dsFloat",
                       "dsChar",
                       "dsString",
                       "dsComment",
                       "dsOthers",
                       "dsAlert",
                       "dsFunction",
                       "dsRegionMarker",
                       "dsError",
                       "CustomTmpForDebugging"])

_DEFAULT_DELIMINATOR = " \t.():!+,-<=>%&*/;?[]^{|}~\\"

def _parseBoolAttribute(value):
    if value.lower() in ('true', '1'):
        return True
    elif value.lower() in ('false', '0'):
        return False
    else:
        raise UserWarning("Invalid bool attribute value '%s'" % value)

def _safeGetRequiredAttribute(xmlElement, name, default):
    if name in xmlElement.attrib:
        return str(xmlElement.attrib[name])
    else:
        _logger.warning("Required attribute '%s' is not set for element '%s'", name, xmlElement.tag)
        return default


def _getContext(contextName, parser, formatConverterFunction, defaultValue):
    dprint('red', '_getContext', contextName, contextName in parser.contexts)
    if not contextName:
        return defaultValue
    if contextName in parser.contexts:
        return parser.contexts[contextName]
    elif contextName.startswith('##') and \
         parser.syntax.manager is not None:  # might be None, if loader is used by regenerate-definitions-db.py
        syntaxName = contextName[2:]
        dprint(f"{bcolors.WARNING}FAIL Syntax name{bcolors.ENDC}", contextName, syntaxName)
        syntax = parser.syntax.manager.getSyntax(formatConverterFunction, languageName = syntaxName)
        if(syntax == None):
            dprint(f"{bcolors.FAIL}FAIL1 Syntax name{bcolors.ENDC}", contextName, syntaxName)
            return parser.defaultContext
        parser = syntax.parser
        return parser.defaultContext
    elif (not contextName.startswith('##')) and \
         '##' in contextName and \
         contextName.count('##') == 1 and \
         parser.syntax.manager is not None:  # might be None, if loader is used by regenerate-definitions-db.py
        name, syntaxName = contextName.split('##')
        dprint(f"{bcolors.WARNING}FAIL Syntax name{bcolors.ENDC}", contextName, name, syntaxName)
        syntax = parser.syntax.manager.getSyntax(formatConverterFunction, languageName = syntaxName)
        if(syntax == None):
            dprint(f"{bcolors.FAIL}FAIL2 Syntax name{bcolors.ENDC}", contextName, name, syntaxName)
            return parser.defaultContext
        parser = syntax.parser
        return parser.contexts[name]
    else:
        _logger.warning('Invalid context name %s', repr(contextName))
        return parser.defaultContext


def _makeContextSwitcher(contextOperation, parser, formatConverterFunction):
    popsCount = 0
    contextToSwitch = None

    rest = contextOperation
    while rest.startswith('#pop'):
        popsCount += 1
        rest = rest[len('#pop'):]
    dprint(f"{bcolors.WARNING}POPPING %s{bcolors.ENDC}", popsCount)
    if rest == '#stay':
        if popsCount:
            _logger.warning("Invalid context operation '%s'", contextOperation)
    else:
        _logger.warning("Context_To_Switch A '%s'", rest)
        if rest.startswith('!'): # 2025_VERSION
            rest = rest[1:]
            _logger.warning("Context_To_Switch B '%s'", rest)
        contextToSwitch = _getContext(rest, parser, formatConverterFunction, None)

    if popsCount > 0 or contextToSwitch != None:
        return _parserModule.ContextSwitcher(popsCount, contextToSwitch, contextOperation)
    else:
        return None


################################################################################
##                               Rules
################################################################################

def _loadIncludeRules(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction):
    contextName = _safeGetRequiredAttribute(xmlElement, "context", None)
    
    # dprint('_loadIncludeRules', contextName, xmlElement)

    context = _getContext(contextName, parentContext.parser, formatConverterFunction, parentContext.parser.defaultContext)

    abstractRuleParams = _loadAbstractRuleParams(parentContext,
                                                 xmlElement,
                                                 attributeToFormatMap,
                                                 formatConverterFunction)
    return _parserModule.IncludeRules(abstractRuleParams, context)

def _simpleLoader(classObject):
    def _load(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction):
        abstractRuleParams = _loadAbstractRuleParams(parentContext,
                                                     xmlElement,
                                                     attributeToFormatMap,
                                                     formatConverterFunction)
        return classObject(abstractRuleParams)
    return _load

def _loadChildRules(context, xmlElement, attributeToFormatMap, formatConverterFunction):
    """Extract rules from Context or Rule xml element
    """
    rules = []
    #for ruleElement in xmlElement.getchildren(): #no longer work in python 3.9
    for ruleElement in xmlElement:
        if not ruleElement.tag in _ruleClassDict:
            raise ValueError("Not supported rule '%s'" % ruleElement.tag)
        rule = _ruleClassDict[ruleElement.tag](context, ruleElement, attributeToFormatMap, formatConverterFunction)
        rules.append(rule)
    return rules

def _loadAbstractRuleParams(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction):
    # attribute
    attribute = xmlElement.attrib.get("attribute", None)
    if attribute is not None:
        attribute = attribute.lower()  # not case sensitive
        try:
            format = attributeToFormatMap[attribute]
            textType = format.textType if format is not None else ' '
            if formatConverterFunction is not None and format is not None:
                format = formatConverterFunction(format)
        except KeyError:
            _logger.warning('Unknown rule attribute %s', attribute)
            format = parentContext.format
            textType = parentContext.textType
    else:
        format = None
        textType = None

    # context
    contextText = xmlElement.attrib.get("context", '#stay')
    context = _makeContextSwitcher(contextText, parentContext.parser, formatConverterFunction)

    lookAhead = _parseBoolAttribute(xmlElement.attrib.get("lookAhead", "false"))
    firstNonSpace = _parseBoolAttribute(xmlElement.attrib.get("firstNonSpace", "false"))
    dynamic = _parseBoolAttribute(xmlElement.attrib.get("dynamic", "false"))

    # TODO beginRegion
    # TODO endRegion

    column = xmlElement.attrib.get("column", None)
    if column is not None:
        column = int(column)
    else:
        column = -1

    return _parserModule.AbstractRuleParams(parentContext, format, textType, attribute, context, lookAhead, firstNonSpace, dynamic, column)

def _loadDetectChar(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction):
    abstractRuleParams = _loadAbstractRuleParams(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction)

    char = _safeGetRequiredAttribute(xmlElement, "char", None)
    if char is not None:
        char = _processEscapeSequences(char)

    index = 0
    if abstractRuleParams.dynamic:
        try:
            index = int(char)
        except ValueError:
            _logger.warning('Invalid DetectChar char %s', char)
            index = 0
        char = None
        if index <= 0:
            _logger.warning('Too little DetectChar index %d', index)
            index = 0

    return _parserModule.DetectChar(abstractRuleParams, str(char), index)

def _loadDetect2Chars(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction):
    char = _safeGetRequiredAttribute(xmlElement, 'char', None)
    char1 = _safeGetRequiredAttribute(xmlElement, 'char1', None)
    if char is None or char1 is None:
        string = None
    else:
        string = _processEscapeSequences(char) + _processEscapeSequences(char1)

    abstractRuleParams = _loadAbstractRuleParams(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction)
    return _parserModule.Detect2Chars(abstractRuleParams, string)

def _loadAnyChar(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction):
    string = _safeGetRequiredAttribute(xmlElement, 'String', '')
    abstractRuleParams = _loadAbstractRuleParams(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction)
    return _parserModule.AnyChar(abstractRuleParams, string)

def _loadStringDetect(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction):
    string = _safeGetRequiredAttribute(xmlElement, 'String', None)

    abstractRuleParams = _loadAbstractRuleParams(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction)
    return _parserModule.StringDetect(abstractRuleParams,
                                      string)

def _loadWordDetect(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction):
    word = _safeGetRequiredAttribute(xmlElement, "String", "")
    insensitive = _parseBoolAttribute(xmlElement.attrib.get("insensitive", "false"))

    abstractRuleParams = _loadAbstractRuleParams(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction)

    return _parserModule.WordDetect(abstractRuleParams, word, insensitive)

def _loadKeyword(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction):
    string = _safeGetRequiredAttribute(xmlElement, 'String', None)
    try:
        words = parentContext.parser.lists[string]
    except KeyError:
        _logger.warning("List '%s' not found", string)

        words = list()

    insensitive = _parseBoolAttribute(xmlElement.attrib.get("insensitive", "false"))

    abstractRuleParams = _loadAbstractRuleParams(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction)
    return _parserModule.keyword(abstractRuleParams, words, insensitive)

def _loadRegExpr(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction):
    def _processCraracterCodes(text):
        """QRegExp use \0ddd notation for character codes, where d in octal digit
        i.e. \0377 is character with code 255 in the unicode table
        Convert such notation to unicode text
        """
        text = str(text)
        def replFunc(matchObj):
            matchText = matchObj.group(0)
            charCode = eval('0o' + matchText[2:])
            return chr(charCode)
        return re.sub(r"\\0\d\d\d", replFunc, text)

    insensitive = _parseBoolAttribute(xmlElement.attrib.get('insensitive', 'false'))
    string = _safeGetRequiredAttribute(xmlElement, 'String', None)

    if string is not None:
        string = _processCraracterCodes(string)

        wordStart = string.strip('(').startswith('\\b')
        lineStart = string.strip('(').startswith('^')
    else:
        wordStart = False
        lineStart = False

    abstractRuleParams = _loadAbstractRuleParams(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction)
    return _parserModule.RegExpr(abstractRuleParams,
                                 string, insensitive, wordStart, lineStart)

def _loadAbstractNumberRule(rule, parentContext, xmlElement):
    abstractRuleParams = _loadAbstractRuleParams(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction)
    return _parserModule.NumberRule(abstractRuleParams, childRules)

def _loadInt(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction):
    childRules = _loadChildRules(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction)
    abstractRuleParams = _loadAbstractRuleParams(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction)
    return _parserModule.Int(abstractRuleParams, childRules)

def _loadFloat(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction):
    childRules = _loadChildRules(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction)
    abstractRuleParams = _loadAbstractRuleParams(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction)
    return _parserModule.Float(abstractRuleParams, childRules)

def _loadRangeDetect(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction):
    char = _safeGetRequiredAttribute(xmlElement, "char", 'char is not set')
    char1 = _safeGetRequiredAttribute(xmlElement, "char1", 'char1 is not set')

    abstractRuleParams = _loadAbstractRuleParams(parentContext, xmlElement, attributeToFormatMap, formatConverterFunction)
    return _parserModule.RangeDetect(abstractRuleParams, char, char1)


_ruleClassDict = \
{
    'DetectChar': _loadDetectChar,
    'Detect2Chars': _loadDetect2Chars,
    'AnyChar': _loadAnyChar,
    'StringDetect': _loadStringDetect,
    'WordDetect': _loadWordDetect,
    'RegExpr': _loadRegExpr,
    'keyword': _loadKeyword,
    'Int': _loadInt,
    'Float': _loadFloat,
    'HlCOct': _simpleLoader(_parserModule.HlCOct),
    'HlCHex': _simpleLoader(_parserModule.HlCHex),
    'HlCStringChar': _simpleLoader(_parserModule.HlCStringChar),
    'HlCChar': _simpleLoader(_parserModule.HlCChar),
    'RangeDetect': _loadRangeDetect,
    'LineContinue': _simpleLoader(_parserModule.LineContinue),
    'IncludeRules': _loadIncludeRules,
    'DetectSpaces': _simpleLoader(_parserModule.DetectSpaces),
    'DetectIdentifier': _simpleLoader(_parserModule.DetectIdentifier)
}

################################################################################
##                               Context
################################################################################


def _loadContexts(highlightingElement, parser, attributeToFormatMap, formatConverterFunction):
    dprint("LOAD CONTEXTS")
    contextsElement = highlightingElement.find('contexts')

    xmlElementList = contextsElement.findall('context')
    contextList = []
    for xmlElement in xmlElementList:
        name = _safeGetRequiredAttribute(xmlElement,
                                         'name',
                                         'Error: context name is not set!!!')
        context = _parserModule.Context(parser, name)
        contextList.append(context)

    defaultContext = None # contextList[0]

    contextDict = {}
    for context in contextList:
        if((context.name == 'Normal' or context.name == 'Base') and defaultContext == None): defaultContext = context
        # dprint('CONTEXTRIA', context)
        contextDict[context.name] = context

    if(defaultContext == None): defaultContext = contextList[0]
    
    parser.setContexts(contextDict, defaultContext)

    # parse contexts stage 2: load contexts
    for xmlElement, context in zip(xmlElementList, contextList):
        # if(not hasattr(context, 'attribute')): continue
        # dprint("Load Context pre", xmlElement, context)
        
        _loadContext(context, xmlElement, attributeToFormatMap, formatConverterFunction)
        debug.dprint('red', 'syntax', parser.syntax.name, context.name, context.rules)
        exit()


def _loadContext(context, xmlElement, attributeToFormatMap, formatConverterFunction):
    """Construct context from XML element
    Contexts are at first constructed, and only then loaded, because when loading context,
    _makeContextSwitcher must have references to all defined contexts
    """
    attribute = _safeGetRequiredAttribute(xmlElement, 'attribute', '<not set>').lower()
    # dprint(context.name, "ATTRIBUTE", attribute)
    if attribute != '<not set>':  # there are no attributes for internal contexts, used by rules. See perl.xml
        try:
            format = attributeToFormatMap[attribute]
        except KeyError:
            _logger.warning('Unknown context attribute %s', attribute)
            format = TextFormat()
    else:
        format = None

    textType = format.textType if format is not None else ' '
    if formatConverterFunction is not None and format is not None:
        format = formatConverterFunction(format)

    lineEndContextText = xmlElement.attrib.get('lineEndContext', '#stay')
    lineEndContext = _makeContextSwitcher(lineEndContextText,  context.parser, formatConverterFunction)
    lineBeginContextText = xmlElement.attrib.get('lineEndContext', '#stay')
    lineBeginContext = _makeContextSwitcher(lineBeginContextText, context.parser, formatConverterFunction)

    # if _parseBoolAttribute(xmlElement.attrib.get('fallthrough', 'false')):
    fallthroughContextText = _safeGetRequiredAttribute(xmlElement, 'fallthroughContext', '#stay') # 2025_VERSION, Sometimes fallthrough is just not here
    if(fallthroughContextText != '#stay'):
        fallthroughContext = _makeContextSwitcher(fallthroughContextText, context.parser, formatConverterFunction)
    else:
        fallthroughContext = None

    dynamic = _parseBoolAttribute(xmlElement.attrib.get('dynamic', 'false'))
    
    print("fallthroughContext", fallthroughContextText, fallthroughContext)

    context.setValues(attribute, format, lineEndContext, lineBeginContext, fallthroughContext, dynamic, textType)

    # load rules
    rules = _loadChildRules(context, xmlElement, attributeToFormatMap, formatConverterFunction)
    context.setRules(rules)

################################################################################
##                               Syntax
################################################################################
def _textTypeForDefStyleName(attribute, defStyleName):
    """ ' ' for code
        'c' for comments
        'b' for block comments
        'h' for here documents
    """
    if 'here' in attribute.lower() and defStyleName == 'dsOthers':
        return 'h'  # ruby
    elif 'block' in attribute.lower() and defStyleName == 'dsComment':
        return 'b'
    elif defStyleName in ('dsString', 'dsRegionMarker', 'dsChar', 'dsOthers'):
        return 's'
    elif defStyleName == 'dsComment':
        return 'c'
    else:
        return ' '

def _makeFormat(defaultTheme, defaultStyleName, textType, item=None):
    format = copy.copy(defaultTheme.format[defaultStyleName])

    format.textType = textType

    if item is not None:
        caseInsensitiveAttributes = {}
        for key, value in item.attrib.items():
            caseInsensitiveAttributes[key.lower()] = value.lower()

        if 'color' in caseInsensitiveAttributes:
            format.color = caseInsensitiveAttributes['color']
        if 'selColor' in caseInsensitiveAttributes:
            format.selectionColor = caseInsensitiveAttributes['selColor']
        if 'italic' in caseInsensitiveAttributes:
            format.italic = _parseBoolAttribute(caseInsensitiveAttributes['italic'])
        if 'bold' in caseInsensitiveAttributes:
            format.bold = _parseBoolAttribute(caseInsensitiveAttributes['bold'])
        if 'underline' in caseInsensitiveAttributes:
            format.underline = _parseBoolAttribute(caseInsensitiveAttributes['underline'])
        if 'strikeout' in caseInsensitiveAttributes:
            format.strikeOut = _parseBoolAttribute(caseInsensitiveAttributes['strikeout'])
        if 'spellChecking' in caseInsensitiveAttributes:
            format.spellChecking = _parseBoolAttribute(caseInsensitiveAttributes['spellChecking'])

    return format

def _loadAttributeToFormatMap(highlightingElement):
    defaultTheme = ColorTheme(TextFormat)
    attributeToFormatMap = {}

    itemDatasElement = highlightingElement.find('itemDatas')
    if itemDatasElement is not None:
        for item in itemDatasElement.findall('itemData'):
            attribute = item.get('name').lower()
            defaultStyleName = item.get('defStyleNum')

            if not defaultStyleName in defaultTheme.format:
                _logger.warning("Unknown default style '%s'", defaultStyleName)
                defaultStyleName = 'dsNormal'

            format = _makeFormat(defaultTheme,
                                 defaultStyleName,
                                 _textTypeForDefStyleName(attribute, defaultStyleName),
                                 item)

            attributeToFormatMap[attribute] = format

    # HACK not documented, but 'normal' attribute is used by some parsers without declaration
    if not 'normal' in attributeToFormatMap:
        attributeToFormatMap['normal'] = _makeFormat(defaultTheme, 'dsNormal',
                                                     _textTypeForDefStyleName('normal', 'dsNormal'))
    if not 'string' in attributeToFormatMap:
        attributeToFormatMap['string'] = _makeFormat(defaultTheme, 'dsString',
                                                     _textTypeForDefStyleName('string', 'dsString'))

    return attributeToFormatMap

def _loadLists(root, highlightingElement, syntax):
    lists = {}  # list name: list
    for listElement in highlightingElement.findall('list'):
        # Sometimes item.text is none. Broken xml files
        items = [str(item.text.strip()) \
                    for item in listElement.findall('item') \
                        if item.text is not None]
        name = _safeGetRequiredAttribute(listElement, 'name', 'Error: list name is not set!!!')
        lists[name] = items
        # 2025_VERSION
        for include in listElement.findall('include'):
            include_text = include.text
            include_text_parts = include_text.split('##')
            language = include_text_parts[1]
            include_list_name = include_text_parts[0]
            external_syntax = syntax.manager.getSyntax(None, languageName = language)
            external_lists = external_syntax.parser.lists
            
            lists[include_list_name] = external_lists[include_list_name]
            
            dprint('included_list', lists[include_list_name])
            # language_context = _getContext(include_text, parser, formatConverterFunction, defaultValue):


    return lists

def _makeKeywordsLowerCase(listDict):
    # Make all keywords lowercase, if syntax is not case sensitive
    for keywordList in listDict.values():
        for index, keyword in enumerate(keywordList):
            keywordList[index] = keyword.lower()

def _loadSyntaxDescription(root, syntax):
    syntax.name = _safeGetRequiredAttribute(root, 'name', 'Error: .parser name is not set!!!')
    syntax.section = _safeGetRequiredAttribute(root, 'section', 'Error: Section is not set!!!')
    syntax.extensions = [_f for _f in _safeGetRequiredAttribute(root, 'extensions', '').split(';') if _f]
    syntax.firstLineGlobs = [_f for _f in root.attrib.get('firstLineGlobs', '').split(';') if _f]
    syntax.mimetype = [_f for _f in root.attrib.get('mimetype', '').split(';') if _f]
    syntax.version = root.attrib.get('version', None)
    syntax.kateversion = root.attrib.get('kateversion', None)
    syntax.priority = int(root.attrib.get('priority', '0'))
    syntax.author = root.attrib.get('author', None)
    syntax.license = root.attrib.get('license', None)
    syntax.hidden = _parseBoolAttribute(root.attrib.get('hidden', 'false'))

    # not documented
    syntax.indenter = root.attrib.get('indenter', None)


# 2025_VERSION
def parseEntities(content):
	return content;
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
			
			content = content.replace('&' + key + ';', value)
			dprint(key, value)
	return content

def loadSyntax(syntax, filePath, formatConverterFunction = None):

    # dprint("LOAD SYNTAX", filePath)
    _logger.debug("Loading syntax %s", filePath)
    with open(filePath, 'r', encoding='utf-8') as definitionFile:
        try:
            root = xml.etree.ElementTree.parse(definitionFile).getroot()
            
            # 2025_VERSION
            # content = definitionFile.read()
            # content = parseEntities(content)
            # root = xml.etree.ElementTree.fromstring(content)
        except Exception as ex:
            dprint('When opening %s:' % filePath, file=sys.stderr)
            raise

    highlightingElement = root.find('highlighting')

    _loadSyntaxDescription(root, syntax)

    deliminatorSet = set(_DEFAULT_DELIMINATOR)

    # parse lists
    lists = _loadLists(root, highlightingElement, syntax)
    debug.dprint('red', 'loadLists_ended')

    # parse itemData
    keywordsCaseSensitive = True

    generalElement = root.find('general')
    if generalElement is not None:
        keywordsElement = generalElement.find('keywords')

        if keywordsElement is not None:
            keywordsCaseSensitive = _parseBoolAttribute(keywordsElement.get('casesensitive', "true"))

            if not keywordsCaseSensitive:
                _makeKeywordsLowerCase(lists)

            if 'weakDeliminator' in keywordsElement.attrib:
                weakSet = keywordsElement.attrib['weakDeliminator']
                deliminatorSet.difference_update(weakSet)

            if 'additionalDeliminator' in keywordsElement.attrib:
                additionalSet = keywordsElement.attrib['additionalDeliminator']
                deliminatorSet.update(additionalSet)

        indentationElement = generalElement.find('indentation')

        if indentationElement is not None and \
           'mode' in indentationElement.attrib:
            syntax.indenter = indentationElement.attrib['mode']

        # dprint("LOAD SYNTAX pre comments", filePath)   
        commentElements = generalElement.find('comments')
        if commentElements != None:
                commentElement = commentElements.find('comment')

                if commentElement is not None:
                    syntax.comment = commentElement.attrib['start']
            

    deliminatorSetAsString = ''.join(list(deliminatorSet))
    debugOutputEnabled = _logger.isEnabledFor(logging.DEBUG)  # for cParser
    parser = _parserModule.Parser(syntax, deliminatorSetAsString, lists, keywordsCaseSensitive, debugOutputEnabled)
    syntax._setParser(parser)
    attributeToFormatMap = _loadAttributeToFormatMap(highlightingElement)
    # dprint('pre-loadcontexg')
    # parse contexts
    _loadContexts(highlightingElement, syntax.parser, attributeToFormatMap, formatConverterFunction)
    # dprint('post-loadcontexg', filePath)

    return syntax
