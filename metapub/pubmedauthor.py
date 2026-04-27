"""metapub.pubmedauthor -- PubMedAuthor class instantiated a ncbi Author XML Element"""

from .base import MetaPubObject
from .exceptions import MetaPubError


class PubMedAuthor(MetaPubObject):
    """This PubMedAuthor class receives a xml element as required argument
    and parses it into its parts, exposing them as attributes.

    Usage:
        author = PubMedAuthor(xml_elem)

    To retrieve the standard represenation of a author name, use the __str__ method.

    (About unicode: metapub uses unicode_literals in both py3 and py2, so the str() function
    returns unicode, unless called by a py2k "str()" statement in which unicode_literals is off.)
    """

    def __init__(self, xmlelem, *args, **kwargs):

        self.last_name = None
        self.fore_name = None
        self.initials = None
        self.collective_name = None
        self.affiliations = []

        if xmlelem is None:
            return

        self.content = xmlelem
        self._parse_xml()

    def to_dict(self):
        pass

    def _parse_xml(self):
        pass

    def __str__(self):
        if self.last_name and self.initials:
            return self.last_name + ' ' + self.initials
        elif self.collective_name:
            return self.collective_name
        elif self.last_name:
            return self.last_name
        else:
            return 'Unnamed Author'

