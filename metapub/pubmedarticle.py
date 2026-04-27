"""metapub.pubmedarticle -- PubMedArticle class instantiated by supplying ncbi XML string."""

import time
from datetime import datetime
from collections import OrderedDict

from .base import MetaPubObject
from .exceptions import MetaPubError
from .text_mining import re_numbers
from .pubmedauthor import PubMedAuthor

from . import cite


class PubMedArticle(MetaPubObject):
    """This PubMedArticle class receives an XML string as its required argument
    and parses it into its constituent parts, exposing them as attributes.

    Usage:
        paper = PubMedArticle(xml_string)

    To query services to return an article by pmid, use PubMedFetcher, which
    returns PubMedArticle objects.

    When xmlstr is parsed, the `pubmed_type` attribute will be set to one of 'article' or 'book',
    depending on whether PubmedBookArticle or PubmedArticle headings are found in the supplied
    xmlstr at instantiation.

    Since this class needs to work seamlessly in production whether it's a book
    or an article, the PubmedArticle attributes will always be available (set to None in many
    cases for PubmedBookArticle, e.g. volume, issue, journal), but PubmedBookArticle
    attributes will only be set when pubmed_type='book'.

    PubMedBook special handling of certain attributes:
        * abstract: a joined string from self.book_abstracts
        * title: comes from ArticleTitle

    Special attributes for PubmedBookArticle (pubmed_type='book'):
        * book_id (default: None) - string from IdType="bookaccession", e.g. "NBK1403"
        * book_title (default: None) - string with name of book (as differentiated from ArticleTitle)
        * book_publisher (default: None) - dict containing {'name': string, 'location': string}
        * book_sections (default: []) - dict with key->value pairs as section_name->SectionTitle
        * book_contribution_date (default: None) - python datetime date
        * book_date_revised (default: None) - python datetime date
        * book_history (default: [])  - dictionary with key->value pairs as PubStatus -> python datetime
        * book_language (default: None) - string (e.g. "eng")
        * book_editors (default: []) - list containing names from 'editors' AuthorList
        * book_abstracts (default: []) - dict with key->value pairs as Label->AbstractText.text)
        * book_medium (default: None) - string (e.g. "Internet")
        * book_synonyms (default: None) - list of disease synonyms (applicable to "gene" book)
        * book_publication_status (default: None) - string (e.g. "ppublish")
    """

    def __init__(self, xmlstr, *args, **kwargs):
        """Initialize PubMedArticle from NCBI XML data.
        
        Args:
            xmlstr (str): XML string from NCBI containing PubmedArticle or 
                PubmedBookArticle data.
            *args: Additional positional arguments passed to parent class.
            **kwargs: Additional keyword arguments passed to parent class.
        
        Note:
            The XML type is automatically detected to handle both regular articles
            and book chapters. The `pubmed_type` attribute will be set to 'article'
            or 'book' accordingly, and appropriate attributes will be populated.
        """
        self.pubmed_type = determine_pubmed_xml_type(xmlstr)

        if self.pubmed_type=='book':
            self._root = 'BookDocument'
            super(PubMedArticle, self).__init__(xmlstr, 'PubmedBookArticle', args, kwargs)
        elif self.pubmed_type=='article':
            self._root = 'MedlineCitation'
            super(PubMedArticle, self).__init__(xmlstr, 'PubmedArticle', args, kwargs)
        else:
            # assume we're here because of predownloaded Medline XML.
            self.pubmed_type = 'article'
            self._root = '.'
            super(PubMedArticle, self).__init__(xmlstr, None, args, kwargs)

        pmt = self.pubmed_type

        # shared between book and article types:
        self.pmid = self._get_pmid()
        self.url  = self._get_url()
        self.authors = self._get_authors() if pmt == 'article' else self._get_book_authors()
        self.author_list = self._get_author_list() if pmt == 'article' else self._get_book_author_list()
        self.title = self._get_title() if pmt == 'article' else self._get_book_articletitle()
        self.authors_str = self._get_authors_str()
        self.author1_last_fm = self._get_author1_last_fm()
        self.author1_lastfm = self._get_author1_lastfm()
        self.keywords = self._get_keywords()

        # 'article' only (not shared):
        self.pages = None if pmt == 'book' else self._get_pages()
        self.first_page = None if pmt == 'book' else self._get_first_page()
        self.last_page = None if pmt == 'book' else self._get_last_page()
        self.volume = None if pmt == 'book' else self._get_volume()
        self.issue = None if pmt == 'book' else self._get_issue()
        self.volume_issue = None if pmt == 'book' else self._get_volume_issue()
        self.doi = None if pmt == 'book' else self._get_doi()
        self.pii = None if pmt == 'book' else self._get_pii()
        self.pmc = None if pmt == 'book' else self._get_pmc()
        self.issn = None if pmt == 'book' else self._get_issn()

        # MeSH headings ('article' only)
        self.mesh = self._get_mesh_headings()

        # Chemical associations ('article' only)
        self.chemicals = self._get_chemicals()

        # Grant information (?? 'article' only ??)
        self.grants = self._get_grantlist()

        # Publication Types (?? 'article' only ??)
        self.publication_types = self._get_publication_types()

        # 'book' only:
        self.book_accession_id = None if pmt == 'article' else self._get_bookaccession_id()
        self.book_title = None if pmt == 'article' else self._get_book_title()
        self.book_publisher = None if pmt == 'article' else self._get_book_publisher()
        self.book_language = None if pmt == 'article' else self._get_book_language()
        self.book_editors = None if pmt == 'article' else self._get_book_editors()
        self.book_abstracts = None if pmt == 'article' else self._get_book_abstracts()
        self.book_sections = None if pmt == 'article' else self._get_book_sections()
        self.book_copyright = None if pmt == 'article' else self._get_book_copyright()
        self.book_medium = None if pmt == 'article' else self._get_book_medium()
        self.book_synonyms = None if pmt == 'article' else self._get_book_synonyms()
        self.book_publication_status = None if pmt == 'article' else self._get_book_publication_status()
        self.book_history = None if pmt == 'article' else self._get_book_history()
        self.book_contribution_date = None if pmt == 'article' else self._get_book_contribution_date()
        self.book_date_revised = None if pmt == 'article' else self._get_book_contribution_date()

        # the shared oddballs, must be done last.
        self.abstract = self._get_abstract() if pmt == 'article' else self._get_book_abstract()
        self.journal = self.book_title if pmt == 'book' else self._get_journal()
        self.year = self._get_book_year() if pmt == 'book' else self._get_year()

        self.history = self._get_article_history()

    def to_dict(self):
        """Convert PubMedArticle to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary containing all article attributes except
                internal XML content and processing attributes.
        
        Note:
            Excludes 'content', 'xml', and '_root' attributes from the output
            to provide a clean data representation suitable for serialization.
        """
        pass

    @property
    def citation(self):
        """ Returns a formatted citation string built from this article's author(s), title,
        journal, year, volume, pages, and doi.

        Article Example:

        McNally EM, et al. Genetic mutations and mechanisms in dilated cardiomyopathy. Journal of Clinical Investigation. 2013; 123:19-26. doi: 10.1172/JCI62862.

        Book Example (GeneReviews):

        Tranebjarg L, et al. Jervell and Lange-Nielsen syndrome. 2002 Jul 29 (Updated 2014 Nov 20). In: Pagon RA, et al., editors. GeneReviews (Internet). Seattle (WA): University of Washington, Seattle; 1993-2015. Available from: https://www.ncbi.nlm.nih.gov/books/NBK1405/.
        """
        pass

    @property
    def citation_html(self):
        """ Returns a formatted citation string built from this article's author(s), title,
        journal, year, volume, and pages.

        Article Example:

        McNally EM, <i>et al</i>. Genetic mutations and mechanisms in dilated cardiomyopathy. <i>Journal of Clinical Investigation</i>. 2013; <b>123</b>:19-26. doi: 10.1172/JCI62862.

        GeneReviews Example:
        Tranebjarg L, <i>et al</i>. <i>Jervell and Lange-Nielsen syndrome</i>. 2002 Jul 29 (Updated 2014 Nov 20). In: Pagon RA, <i>et al</i>., editors. GeneReviews (Internet). Seattle (WA): University of Washington, Seattle; 1993-2015. Available from: https://www.ncbi.nlm.nih.gov/books/NBK1405/.
        """
        pass

    @property
    def citation_bibtex(self):
        pass
    
    @property
    def pubdate(self):
        """Normalized publication date as datetime object.
        
        Returns the best available publication date from PubMed XML in order of preference:
        1. Article PubDate (Year/Month/Day or MedlineDate)
        2. Book contribution date  
        3. History dates (pubmed, entrez, etc.)
        
        Returns:
            datetime or None: Publication date as datetime object, or None if no date found
            
        Example:
            article = fetch.article_by_pmid('12345')
            if article.pubdate:
                print(f"Published: {article.pubdate.strftime('%Y-%m-%d')}")
        """
        pass

    def _construct_datetime(self, d):
        pass
    
    def _parse_medlinedate(self, medline_text):
        """Parse MedlineDate strings like '2007 Spring', '1999-2000', '2007 Mar-Apr'"""
        pass

    def _get_bookaccession_id(self):
        pass

    def _get_book_title(self):
        pass

    def _get_book_articletitle(self):
        pass

    def _get_book_authors(self):
        pass

    def _get_book_author_list(self):
        pass

    def _get_book_publisher(self):
        pass

    def _get_book_publisher_location(self):
        pass

    def _get_book_language(self):
        pass

    def _get_book_editors(self):
        pass

    def _get_book_abstracts(self):
        pass

    def _get_book_sections(self):
        pass

    def _get_book_abstract(self):
        pass

    def _get_book_copyright(self):
        pass

    def _get_book_medium(self):
        pass

    def _get_book_contribution_date(self):
        pass

    def _get_book_date_revised(self):
        pass

    def _get_book_synonyms(self):
        pass

    def _get_book_history(self):
        pass

    def _get_book_publication_status(self):
        pass

    def _get_book_year(self):
        pass

    def _get_pmid(self):
        pass

    def _get_url(self):
        pass

    def _get_abstract(self):
        pass

    def _get_authors(self):
        # N.B. Citations may have 0 authors. e.g., pmid:7550356
        pass

    def _get_author_list(self):
        pass

    def _get_authors_str(self):
        pass

    def _get_author1_last_fm(self):
        """ return first author's name, in format Last INITS (space between surname and initials)"""
        pass

    def _get_author1_lastfm(self):
        """return first author's name, in format LastINITS (no space between surname and initials)"""
        pass

    def _get_keywords(self):
        pass

    def _get_journal(self):
        pass

    def _get_pages(self):
        pass

    def _get_first_page(self):
        pass

    def _get_last_page(self):
        pass

    def _get_title(self):
        pass

    def _get_volume(self):
        pass

    def _get_issue(self):
        pass

    def _get_volume_issue(self):
        pass

    def _get_article_history(self):
        pass

    def _get_year(self):
        pass

    def _get_doi(self):
        pass

    def _get_pii(self):
        pass

    def _get_pmc(self):
        pass

    def _get_issn(self):
        pass

    def _get_mesh_headings(self):
        pass

    def _get_chemicals(self):
        pass

    def _get_publication_types(self):
        pass

    def _get_grantlist(self):
        pass

    def __str__(self):
        # [article example] 
        # Asensio C, PÃ©rez-DÃ­az JC. A new family of low molecular weight antibiotics from enterobacteria. Biochem Biophys Res Commun. 1976 Mar 8;69(1):7-14. 
        if self.pubmed_type == 'article':
            return '<PubMedArticle {pmid}> {authors_str}. {title}. {journal}. {year}. {volume_issue}:{pages}'.format(**self.to_dict())
        else:
            return '<PubMedBook {pmid}> {title}. {authors_str}. {book_title}. {year}'.format(**self.to_dict())


############################################################################
## Utilities

def _xml_au_to_last_fm(au):
    "Medline XML specific conversion of author name to lastname-firstinitial format."
    pass


def square_voliss_data_for_pma(pma):
    """ Takes a PubMedArticle object, returns same object with corrected volume/issue
    information (if needed)
    """
    if pma.volume != None and pma.issue is None:
        # try to get a number out of the parts that came after the first number.
        volparts = re_numbers.findall(pma.volume)
        if len(volparts) > 1:
            pma.volume = volparts[0]
            # take a guess. best we can do. this often works (e.g. Brain journal)
            pma.issue = volparts[1]
    if pma.issue and pma.volume:
        if pma.issue.find('Pt') > -1:
            pma.issue = re_numbers.findall(pma.issue)[0]
    return pma

def determine_pubmed_xml_type(xmlstr):
    """ Returns string "type" of pubmed article XML based on presence of expected strings.

    Possible returns:
        'article'
        'book'
        'unknown'

    :param xmlstr: xml in any data type (str, bytes, unicode...)
    :return typestring: (str)
    :rtype: str
    """
    pass

