# Copyright 2017 Mycroft AI, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class Fragment(object):
    """(Abstract) empty sentence fragment"""

    def __init__(self, tree):
        self._tree = tree

    def expand(self):
        """Expanded version of the fragment."""
        # Creates one empty sentence
        return [[]]

    def __str__(self):
        return self._tree.__str__()

    def __repr__(self):
        return self._tree.__repr__()


class Word(Fragment):
    """Single word in the sentence tree."""

    def expand(self):
        # Creates one sentence that contains exactly that word
        return [[self._tree]]


class Sentence(Fragment):
    """A Sentence made of several concatenations/words."""

    def expand(self):
        # Creates a combination of all sub-sentences
        old_expanded = [[]]
        for sub in self._tree:
            sub_expanded = sub.expand()
            new_expanded = []
            while len(old_expanded) > 0:
                sentence = old_expanded.pop()
                for new in sub_expanded:
                    new_expanded.append(sentence + new)
            old_expanded = new_expanded
        return old_expanded


class Options(Fragment):
    """A Combination of possible sub-sentences."""

    def expand(self):
        # Returns all of its options as seperated sub-sentences
        options = []
        for option in self._tree:
            options.extend(option.expand())
        return options


class SentenceTreeParser(object):
    """
    Generate sentence token trees from a list of tokens
    ['1', '(', '2', '|', '3, ')'] -> [['1', '2'], ['1', '3']]
    """

    def __init__(self, tokens):
        self.tokens = tokens

    def _parse(self):
        """
        Generate sentence token trees
        ['1', '(', '2', '|', '3, ')'] -> ['1', ['2', '3']]
        """
        self._current_position = 0
        return self._parse_expr()

    def _parse_expr(self):
        """
        Generate sentence token trees from the current position to
        the next closing parentheses / end of the list and return it
        ['1', '(', '2', '|', '3, ')'] -> ['1', [['2'], ['3']]]
        ['2', '|', '3'] -> [['2'], ['3']]
        """
        # List of all generated sentences
        sentence_list = []
        # Currently active sentence
        cur_sentence = []
        sentence_list.append(Sentence(cur_sentence))
        # Determine which form the current expression has
        while(self._current_position < len(self.tokens)):
            cur = self.tokens[self._current_position]
            self._current_position += 1
            if cur == '(':
                # Parse the subexpression
                subexpr = self._parse_expr()
                # add it to the sentence
                cur_sentence.append(subexpr)
            elif cur == '|':
                # Begin parsing a new sentence
                cur_sentence = []
                sentence_list.append(Sentence(cur_sentence))
            elif cur == ')':
                # End parsing the current subexpression
                break
            # TODO anything special about {sth}?
            else:
                cur_sentence.append(Word(cur))
        return Options(sentence_list)

    def _expand_tree(self, tree):
        """
        Expand a list of sub sentences to all combinated sentences.
        ['1', ['2', '3']] -> [['1', '2'], ['1', '3']]
        """
        return tree.expand()

    def expand_parentheses(self):
        tree = self._parse()
        return self._expand_tree(tree)