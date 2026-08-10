"""Bracket highlighter.
Calculates list of QTextEdit.ExtraSelection
"""

import time
import re

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QTextEdit


class _TimeoutException(UserWarning):
    """Operation timeout happened
    """
    pass


class BracketHighlighter:
    """Bracket highliter.
    Calculates list of QTextEdit.ExtraSelection

    Currently, this class might be just a set of functions.
    Probably, it will contain instance specific selection colors later
    """
    _MAX_SEARCH_TIME_SEC = 0.02

    _START_BRACKETS = '({['
    _END_BRACKETS = ')}]'
    _ALL_BRACKETS = _START_BRACKETS + _END_BRACKETS
    _OPOSITE_BRACKET = dict( (bracket, oposite)
                    for (bracket, oposite) in zip(_START_BRACKETS + _END_BRACKETS, _END_BRACKETS + _START_BRACKETS))

    # Regex pour parser les tags JSX/HTML
    _TAG_NAME_PATTERN = re.compile(r'^<(/?)([a-zA-Z][a-zA-Z0-9_.-]*)')

    currentMatchedBrackets = None  # instance variable. None or ((block, columnIndex), (block, columnIndex))

    def _iterateDocumentCharsForward(self, block, startColumnIndex):
        """Traverse document forward. Yield (block, columnIndex, char)
        Raise _TimeoutException if time is over
        """
        # Chars in the start line
        endTime = time.time() + self._MAX_SEARCH_TIME_SEC
        for columnIndex, char in list(enumerate(block.text()))[startColumnIndex:]:
            yield block, columnIndex, char
        block = block.next()

        # Next lines
        while block.isValid():
            for columnIndex, char in enumerate(block.text()):
                yield block, columnIndex, char

            if time.time() > endTime:
                raise _TimeoutException('Time is over')

            block = block.next()

    def _iterateDocumentCharsBackward(self, block, startColumnIndex):
        """Traverse document forward. Yield (block, columnIndex, char)
        Raise _TimeoutException if time is over
        """
        # Chars in the start line
        endTime = time.time() + self._MAX_SEARCH_TIME_SEC
        for columnIndex, char in reversed(list(enumerate(block.text()[:startColumnIndex]))):
            yield block, columnIndex, char
        block = block.previous()

        # Next lines
        while block.isValid():
            for columnIndex, char in reversed(list(enumerate(block.text()))):
                yield block, columnIndex, char

            if time.time() > endTime:
                raise _TimeoutException('Time is over')

            block = block.previous()

    def _findMatchingBracket(self, bracket, qpart, block, columnIndex):
        """Find matching bracket for the bracket.
        Return (block, columnIndex) or (None, None)
        Raise _TimeoutException, if time is over
        """
        if bracket in self._START_BRACKETS:
            charsGenerator = self._iterateDocumentCharsForward(block, columnIndex + 1)
        else:
            charsGenerator = self._iterateDocumentCharsBackward(block, columnIndex)

        depth = 1
        oposite = self._OPOSITE_BRACKET[bracket]
        for block, columnIndex, char in charsGenerator:
            if qpart.isCode(block, columnIndex):
                if char == oposite:
                    depth -= 1
                    if depth == 0:
                        return block, columnIndex
                elif char == bracket:
                    depth += 1
        else:
            return None, None

    def _parseTagAtPosition(self, block, columnIndex):
        """Parse tag name at given position.
        Returns (tagName, isClosingTag, tagStartCol, tagEndCol) or None if not a valid tag.
        tagStartCol is position of '<', tagEndCol is position after tag name.
        """
        text = block.text()

        # Gérer les cas limites
        if not text or columnIndex < 0 or columnIndex >= len(text):
            return None

        # Trouver le début du tag (chercher '<' en arrière)
        tagStartCol = columnIndex
        while tagStartCol > 0 and text[tagStartCol] != '<':
            tagStartCol -= 1

        if tagStartCol < 0 or text[tagStartCol] != '<':
            return None

        # Extraire le texte à partir de '<'
        tagText = text[tagStartCol:]
        match = self._TAG_NAME_PATTERN.match(tagText)

        if not match:
            return None

        isClosingTag = match.group(1) == '/'
        tagName = match.group(2)
        tagEndCol = tagStartCol + match.end()

        return (tagName, isClosingTag, tagStartCol, tagEndCol)

    def _isInsideTag(self, block, columnIndex):
        """Check if cursor is inside a tag (between < and >).
        Returns True if inside a tag, False otherwise.
        """
        text = block.text()

        # Gérer les cas limites
        if not text or columnIndex < 0 or columnIndex >= len(text):
            return False

        # Chercher '<' en arrière et '>' en avant
        foundOpenBracket = False
        for i in range(columnIndex, -1, -1):
            if text[i] == '>':
                return False  # On a trouvé '>' avant '<', donc pas dans un tag
            if text[i] == '<':
                foundOpenBracket = True
                break

        return foundOpenBracket

    def _isSelfClosingTag(self, block, tagStartCol):
        """Check if tag is self-closing (ends with />).
        Search forward from tagStartCol to find '>' and check if preceded by '/'.
        Returns (isSelfClosing, endBlock, endCol) or (False, None, None) if not found.
        """
        text = block.text()

        # Gérer les cas limites
        if not text or tagStartCol < 0:
            return False, None, None

        endTime = time.time() + self._MAX_SEARCH_TIME_SEC

        # Chercher dans le bloc courant
        for i in range(tagStartCol, len(text)):
            if text[i] == '>':
                return (i > 0 and text[i-1] == '/'), block, i

        # Chercher dans les blocs suivants
        nextBlock = block.next()
        while nextBlock.isValid():
            text = nextBlock.text()
            for i in range(len(text)):
                if text[i] == '>':
                    return (i > 0 and text[i-1] == '/'), nextBlock, i

            if time.time() > endTime:
                return False, None, None
            nextBlock = nextBlock.next()

        return False, None, None

    def _isTagComplete(self, block, tagStartCol):
        """Check if tag has a closing '>' before another '<' starts.
        Returns True if complete, False if still being typed.
        """
        text = block.text()

        if not text or tagStartCol < 0:
            return False

        endTime = time.time() + self._MAX_SEARCH_TIME_SEC

        # Chercher '>' ou '<' dans le bloc courant (à partir de tagStartCol + 1 pour ignorer le '<' initial)
        for i in range(tagStartCol + 1, len(text)):
            if text[i] == '>':
                return True
            if text[i] == '<':
                # Un nouveau tag commence avant que celui-ci soit fermé
                return False

        # Chercher dans les blocs suivants (tags multi-lignes)
        nextBlock = block.next()
        while nextBlock.isValid():
            text = nextBlock.text()
            for i in range(len(text)):
                if text[i] == '>':
                    return True
                if text[i] == '<':
                    return False

            if time.time() > endTime:
                return False
            nextBlock = nextBlock.next()

        return False

    def _findMatchingTag(self, tagName, isClosingTag, qpart, block, tagStartCol, tagEndCol):
        """Find matching tag for the given tag.
        Return ((startBlock, startCol), (endBlock, endCol)) for the matching tag name,
        or (None, None) if not found.
        Raise _TimeoutException if time is over.
        """
        endTime = time.time() + self._MAX_SEARCH_TIME_SEC
        depth = 1

        if isClosingTag:
            # Chercher en arrière pour trouver le tag ouvrant
            currentBlock = block
            searchStart = tagStartCol - 1

            while currentBlock.isValid():
                text = currentBlock.text()

                # Parcourir le texte en arrière
                i = searchStart if currentBlock == block else len(text) - 1
                while i >= 0:
                    if text[i] == '>' and qpart.isCode(currentBlock, i):
                        # Trouver le début de ce tag
                        tagInfo = self._findTagStartBackward(currentBlock, i)
                        if tagInfo:
                            foundTagName, foundIsClosing, foundStartCol, foundEndCol, foundBlock = tagInfo
                            if foundTagName.lower() == tagName.lower():
                                if foundIsClosing:
                                    depth += 1
                                else:
                                    # Vérifier si c'est un tag auto-fermant
                                    isSelfClosing, _, _ = self._isSelfClosingTag(foundBlock, foundStartCol)
                                    if not isSelfClosing:
                                        depth -= 1
                                        if depth == 0:
                                            return ((foundBlock, foundStartCol), (foundBlock, foundEndCol - 1))
                            # Continuer la recherche depuis le bloc et position où on a trouvé le tag
                            if foundBlock != currentBlock:
                                currentBlock = foundBlock
                                text = currentBlock.text()
                            i = foundStartCol - 1
                            continue
                    i -= 1

                if time.time() > endTime:
                    raise _TimeoutException('Time is over')

                currentBlock = currentBlock.previous()
                searchStart = len(currentBlock.text()) - 1 if currentBlock.isValid() else -1
        else:
            # Chercher en avant pour trouver le tag fermant
            # D'abord vérifier si c'est un tag auto-fermant
            isSelfClosing, _, _ = self._isSelfClosingTag(block, tagStartCol)
            if isSelfClosing:
                return (None, None)

            currentBlock = block
            searchStart = tagEndCol

            while currentBlock.isValid():
                text = currentBlock.text()

                # Parcourir le texte en avant
                i = searchStart if currentBlock == block else 0
                while i < len(text):
                    if text[i] == '<' and qpart.isCode(currentBlock, i):
                        tagInfo = self._parseTagAtPosition(currentBlock, i)
                        if tagInfo:
                            foundTagName, foundIsClosing, foundStartCol, foundEndCol = tagInfo
                            if foundTagName.lower() == tagName.lower():
                                if foundIsClosing:
                                    depth -= 1
                                    if depth == 0:
                                        return ((currentBlock, foundStartCol), (currentBlock, foundEndCol - 1))
                                else:
                                    # Vérifier si c'est un tag auto-fermant
                                    isSelfClosing, _, _ = self._isSelfClosingTag(currentBlock, foundStartCol)
                                    if not isSelfClosing:
                                        depth += 1
                            i = foundEndCol
                            continue
                    i += 1

                if time.time() > endTime:
                    raise _TimeoutException('Time is over')

                currentBlock = currentBlock.next()
                searchStart = 0

        return (None, None)

    def _findTagStartBackward(self, block, closingBracketCol):
        """Find the start of a tag given the position of '>'.
        Returns (tagName, isClosingTag, tagStartCol, tagEndCol, foundBlock) or None.
        Handles nested tags in attributes like: <Button endContent={<Icon />}>
        Also handles multi-line tags.
        """
        endTime = time.time() + self._MAX_SEARCH_TIME_SEC

        currentBlock = block
        text = currentBlock.text()

        # Gérer les cas limites
        if not text or closingBracketCol < 0:
            return None

        # Chercher '<' en arrière, mais ignorer les tags complets imbriqués
        # On compte les '>' et '<' pour trouver le bon '<'
        i = closingBracketCol - 1
        nestedTagDepth = 0  # Compte les '>' non appariés

        while currentBlock.isValid():
            while i >= 0:
                if text[i] == '>':
                    # Un autre '>' trouvé, on entre dans un tag imbriqué
                    nestedTagDepth += 1
                elif text[i] == '<':
                    if nestedTagDepth > 0:
                        # Ce '<' ferme un tag imbriqué, on continue
                        nestedTagDepth -= 1
                    else:
                        # C'est le '<' qu'on cherche
                        result = self._parseTagAtPosition(currentBlock, i)
                        if result:
                            tagName, isClosingTag, tagStartCol, tagEndCol = result
                            # Retourner aussi le bloc où on a trouvé le tag
                            return (tagName, isClosingTag, tagStartCol, tagEndCol, currentBlock)
                        return None
                i -= 1

            if time.time() > endTime:
                return None

            # Passer au bloc précédent
            currentBlock = currentBlock.previous()
            if currentBlock.isValid():
                text = currentBlock.text()
                i = len(text) - 1

        return None

    _LARGE_TAG_LINE_THRESHOLD = 15  # Nombre de lignes à partir duquel on colore tout le contenu

    def _highlightTag(self, qpart, block, columnIndex):
        """Highlight JSX/HTML tag and matching tag.
        Return tuple of QTextEdit.ExtraSelection's or None if not a tag.
        If the tag spans more than _LARGE_TAG_LINE_THRESHOLD lines, highlight all content.
        """
        tagInfo = self._parseTagAtPosition(block, columnIndex)
        if not tagInfo:
            return None

        tagName, isClosingTag, tagStartCol, tagEndCol = tagInfo

        # Ne pas highlighter si le tag est incomplet (en cours de frappe)
        if not self._isTagComplete(block, tagStartCol):
            return None

        try:
            matchResult = self._findMatchingTag(tagName, isClosingTag, qpart, block, tagStartCol, tagEndCol)
        except _TimeoutException:
            return []

        matchedStartPos, matchedEndPos = matchResult

        if matchedStartPos is not None:
            matchedBlock, matchedStartCol = matchedStartPos
            _, matchedEndCol = matchedEndPos

            self.currentMatchedBrackets = ((block, tagStartCol), (matchedBlock, matchedStartCol))

            # Calculer le nombre de lignes entre les deux tags
            lineCount = abs(block.blockNumber() - matchedBlock.blockNumber()) + 1

            if lineCount > self._LARGE_TAG_LINE_THRESHOLD:
                # Tag large : colorer tout le contenu entre les deux tags
                if isClosingTag:
                    # On est sur le tag fermant, le tag ouvrant est matchedBlock
                    startBlock, startCol = matchedBlock, matchedStartCol
                    endBlock, endCol = block, tagEndCol
                else:
                    # On est sur le tag ouvrant, le tag fermant est matchedBlock
                    startBlock, startCol = block, tagStartCol
                    endBlock, endCol = matchedBlock, matchedEndCol + 1

                # Trouver la fin du tag ouvrant (le premier '>' après startCol)
                openTagEnd = self._findTagEnd(startBlock, startCol)

                selections = [self._makeContentSelection(startBlock, startCol, endBlock, endCol, openTagEnd)]
            else:
                # Tag normal : colorer juste les balises
                selections = [self._makeTagSelection(block, tagStartCol, tagEndCol, True)]
                selections.append(self._makeTagSelection(matchedBlock, matchedStartCol, matchedEndCol + 1, True))

            return selections
        else:
            self.currentMatchedBrackets = None
            # Vérifier si c'est une balise auto-fermante
            isSelfClosing, endBlock, endCol = self._isSelfClosingTag(block, tagStartCol)
            if isSelfClosing:
                # Balise auto-fermante : colorer avec le fond vert léger
                return [self._makeSelfClosingTagSelection(block, tagStartCol, endBlock, endCol)]
            else:
                # Tag non fermé (pas de match trouvé) : colorer en rouge
                return [self._makeTagSelection(block, tagStartCol, tagEndCol, False)]

    def _findTagEnd(self, block, tagStartCol):
        """Find the position of '>' that closes the opening tag.
        Returns (block, col) or None.
        """
        currentBlock = block
        text = currentBlock.text()
        i = tagStartCol

        while currentBlock.isValid():
            while i < len(text):
                if text[i] == '>':
                    return (currentBlock, i)
                i += 1
            currentBlock = currentBlock.next()
            if currentBlock.isValid():
                text = currentBlock.text()
                i = 0

        return None

    def _makeContentSelection(self, startBlock, startCol, endBlock, endCol, openTagEnd):
        """Make a selection that covers all content between opening and closing tags.
        Uses a lighter background color for the content.
        """
        from PyQt5.QtGui import QColor

        selection = QTextEdit.ExtraSelection()

        # Utiliser une couleur verte plus légère/transparente pour le contenu
        bgColor = QColor(0, 255, 0, 40)  # Vert avec alpha faible
        selection.format.setBackground(bgColor)

        # Sélectionner du début du tag ouvrant jusqu'à la fin du tag fermant
        selection.cursor = QTextCursor(startBlock)
        selection.cursor.setPosition(startBlock.position() + startCol)
        selection.cursor.setPosition(endBlock.position() + endCol, QTextCursor.KeepAnchor)

        return selection

    def _makeSelfClosingTagSelection(self, startBlock, startCol, endBlock, endCol):
        """Make a selection for self-closing tags (like <input />).
        Uses a lighter green background color for the entire tag.
        """
        from PyQt5.QtGui import QColor

        selection = QTextEdit.ExtraSelection()

        # Utiliser la même couleur verte légère que pour les grands tags
        bgColor = QColor(0, 255, 0, 40)  # Vert avec alpha faible
        selection.format.setBackground(bgColor)

        # Sélectionner du '<' jusqu'au '>' inclus
        selection.cursor = QTextCursor(startBlock)
        selection.cursor.setPosition(startBlock.position() + startCol)
        selection.cursor.setPosition(endBlock.position() + endCol + 1, QTextCursor.KeepAnchor)

        return selection

    def _makeTagSelection(self, block, startCol, endCol, matched):
        """Make matched or unmatched QTextEdit.ExtraSelection for a tag.
        """
        selection = QTextEdit.ExtraSelection()

        if matched:
            bgColor = Qt.green
        else:
            bgColor = Qt.red

        selection.format.setBackground(bgColor)
        selection.cursor = QTextCursor(block)
        selection.cursor.setPosition(block.position() + startCol)
        selection.cursor.setPosition(block.position() + endCol, QTextCursor.KeepAnchor)

        return selection

    def _makeMatchSelection(self, block, columnIndex, matched):
        """Make matched or unmatched QTextEdit.ExtraSelection
        """
        selection = QTextEdit.ExtraSelection()

        if matched:
            bgColor = Qt.green
        else:
            bgColor = Qt.red

        selection.format.setBackground(bgColor)
        selection.cursor = QTextCursor(block)
        selection.cursor.setPosition(block.position() + columnIndex)
        selection.cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)

        return selection

    def _highlightBracket(self, bracket, qpart, block, columnIndex):
        """Highlight bracket and matching bracket
        Return tuple of QTextEdit.ExtraSelection's
        """
        try:
            matchedBlock, matchedColumnIndex = self._findMatchingBracket(bracket, qpart, block, columnIndex)
        except _TimeoutException:  # not found, time is over
            return[] # highlight nothing

        if matchedBlock is not None:
            self.currentMatchedBrackets = ((block, columnIndex), (matchedBlock, matchedColumnIndex))
            return [self._makeMatchSelection(block, columnIndex, True),
                    self._makeMatchSelection(matchedBlock, matchedColumnIndex, True)]
        else:
            self.currentMatchedBrackets = None
            return [self._makeMatchSelection(block, columnIndex, False)]

    def extraSelections(self, qpart, block, columnIndex):
        """List of QTextEdit.ExtraSelection's, which highlight brackets and JSX/HTML tags
        """
        blockText = block.text()

        # D'abord vérifier les brackets classiques
        if columnIndex < len(blockText) and \
             blockText[columnIndex] in self._ALL_BRACKETS and \
             qpart.isCode(block, columnIndex):
            return self._highlightBracket(blockText[columnIndex], qpart, block, columnIndex)
        elif columnIndex > 0 and \
           blockText[columnIndex - 1] in self._ALL_BRACKETS and \
           qpart.isCode(block, columnIndex - 1):
            return self._highlightBracket(blockText[columnIndex - 1], qpart, block, columnIndex - 1)

        # Ensuite vérifier les tags JSX/HTML
        if self._isInsideTag(block, columnIndex) and qpart.isCode(block, columnIndex):
            tagSelections = self._highlightTag(qpart, block, columnIndex)
            if tagSelections is not None:
                return tagSelections

        # Vérifier aussi si le curseur est juste après un tag (position - 1)
        if columnIndex > 0 and self._isInsideTag(block, columnIndex - 1) and qpart.isCode(block, columnIndex - 1):
            tagSelections = self._highlightTag(qpart, block, columnIndex - 1)
            if tagSelections is not None:
                return tagSelections

        self.currentMatchedBrackets = None
        return []
