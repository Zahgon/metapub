__author__ = 'nthmost'
__doc__ = '''metapub.PubMedFetcher -- tools to deal with NCBI's E-utilities interface to PubMed'''

from lxml import etree
import requests
import logging

from .eutils_common import get_eutils_client
from .eutils_compat import EutilsRequestError
from .cache_utils import get_cache_path
from .pubmedarticle import PubMedArticle
from .pubmedcentral import get_pmid_for_otherid
from .pubmed_clinicalqueries import *
from .utils import kpick, parameterize, lowercase_keys, remove_chars
from .text_mining import re_pmid, is_ncbi_bookID, re_matching_quotes
from .exceptions import MetaPubError, InvalidPMID, InvalidBookID
from .base import Borg
from .config import DEFAULT_EMAIL, API_KEY
from .ncbi_errors import diagnose_ncbi_error, NCBIServiceError, handle_ncbi_request_error

log = logging.getLogger('metapub.pubmedfetcher')

def get_uids_from_esearch_result(xmlstr):
    """Extract unique identifiers from an ESearch XML result.
    
    Args:
        xmlstr (str): XML string returned from NCBI ESearch query.
        
    Returns:
        List[str]: List of PMID strings extracted from the XML.
        
    Raises:
        NCBIServiceError: If XML parsing fails due to NCBI service issues.
    """
    pass

def parse_related_pmids_result(xmlstr):
    """Parse XML results from ELink query for related PMIDs.
    
    Args:
        xmlstr (str): XML string returned from NCBI ELink query.
        
    Returns:
        Dict[str, List[str]]: Dictionary mapping relationship types to lists of PMIDs.
            Common keys include 'pubmed', 'reviews', 'cited', etc.
            
    Raises:
        NCBIServiceError: If XML parsing fails due to NCBI service issues.
    """
    try:
        outd = {}
        # Handle XML with encoding declarations properly
        if xmlstr.strip().startswith('<?xml'):
            dom = etree.fromstring(xmlstr.encode('utf-8'))
        else:
            dom = etree.fromstring(xmlstr)
        for linkset in dom.findall('LinkSet/LinkSetDb'):
            heading = linkset.find('LinkName').text.split('_')[-1]
            outd[heading] = []
            for Id in linkset.findall('Link/Id'):
                outd[heading].append(Id.text)
        return outd
    except Exception as e:
        # Handle XML parsing errors that might indicate service issues
        diagnosis = diagnose_ncbi_error(e)
        if diagnosis['is_service_issue']:
            raise NCBIServiceError(
                f"Error parsing related articles: {diagnosis['user_message']}", 
                diagnosis['error_type'], 
                diagnosis['suggested_actions']
            ) from e
        else:
            raise

class PubMedFetcher(Borg):
    '''PubMedFetcher (a Borg singleton object backed by an optional SQLite cache)

    An interaction layer for querying via specified method to return PubMedArticle objects.

    Currently available methods: eutils

    Basic Usage:

        fetch = PubMedFetcher()

    To specify a service method (more coming soon):

        fetch = PubMedFetcher('eutils')

    To return an article by querying the service with a known PMID or NCBI Book ID:

        paper = fetch.article_by_pmid('123456')
        book = fetch.article_by_pmid('NBK1234')

    Similar methods exist for returning papers by DOI and PM Central id:

        paper = fetch.article_by_doi('10.1038/ng.379')
        paper = fetch.article_by_pmcid('PMC3458974')

    Finally, you can search for PMIDs via citation details by using the pmids_for_citation
    method, for which you usually only need 3 out of 5 details to triangulate on a good result.

        pmids = fetch.pmids_for_citation(journal='Science', year='2008', volume='4',
                first_page='7', author_name='Grant')
    '''

    _cache_filename = 'pubmedfetcher.db'

    def __init__(self, method='eutils', **kwargs):
        """Initialize PubMedFetcher with specified service method.
        
        Args:
            method (str, optional): Service method to use. Currently only 'eutils' 
                is supported. Defaults to 'eutils'.
            **kwargs: Additional keyword arguments.
                cachedir (str, optional): Custom directory for caching responses.
                    If not provided, uses default cache directory.
        
        Raises:
            NotImplementedError: If an unsupported method is specified.
        
        Note:
            This is a Borg singleton - all instances share the same state.
        """
        self.method = method
        cachedir = kwargs.get("cachedir")

        if method=='eutils':
            self._cache_path = get_cache_path(cachedir, self._cache_filename)
            self.qs = get_eutils_client(self._cache_path)
            self.article_by_pmid = self._eutils_article_by_pmid
            self.article_by_pmcid = self._eutils_article_by_pmcid
            self.article_by_doi = self._eutils_article_by_doi
            self.pmids_for_query = self._eutils_pmids_for_query
        else:
            raise NotImplementedError('Planned future options: "mysql", "cache-only"')

    def _eutils_article_by_pmid(self, pmid):
        pass

    def _eutils_article_by_pmcid(self, pmcid):
        # if user submitted a bare number, prepend "PMC" to make sure it is submitted correctly
        # the conversion API at pubmedcentral.
        pass

    def _eutils_article_by_doi(self, doi):
        pass

    def _eutils_pmids_for_query(self, query='', since=None, until=None, retstart=0, retmax=250,
                pmc_only=False, **kwargs):
        '''returns list of pmids for given freeform query string plus keyword arguments.

        Freeform queries encased in quotes will be considered "exact match" queries.

        All Pubmed Advanced Query tokens (e.g. "TI" for title) are supported, plus many
        "soft" keywords that will, when parsed, map to the correct token for you. For example,
        you can supply journal name with any of the following keywords:

            "journal" == "jtitle" == "journal_title" == "TA"

        Keyword arguments are case-INsensitive since they are lowercased upon arrival.

        Example of series of queries to accomplish "pagination" of data:

        first_250 = fetch.pmids_for_query('some query')
        second_250 = fetch.pmids_for_query('some query', retstart=500, retmax=250)

        :param: query (string) default ''
        :param: since (string) default None  # Y/m/d format expected. Y alone or Y/m allowed.
        :param: until (string) default None  # Y/m/d format expected. Y alone or Y/m allowed.
        :param: retstart (int) default 0
        :param: retmax (int) default 250
        :param: pmc_only (bool) default False  # constructs query to only search Pubmed Central.
        '''
        pass

    def pmids_for_clinical_query(self, query, category, optimization='broad',
            since=None, until=None, retstart=0, retmax=250, pmc_only=False, **kwargs):
        '''Takes a query and a category (required, see below) and returns a list
        of pubmed IDs returned by NCBI for that query.

        See also PubMedFetcher.pmids_for_query for other parameters.

            available categories:

                therapy
                diagnosis
                etiology
                prognosis
                prediction

           available optimizations:
                broad   (default)
                narrow

        :param: query (string)
        :param: category (string)
        :param: optimization (string) [default: broad]
        :return: list of pubmed IDs
        '''
        pass

    def pmids_for_medical_genetics_query(self, query, category='all', since=None, until=None,
                    retstart=0, retmax=250, pmc_only=False, **kwargs):
        '''Takes a query and category (see below) and returns a list of pubmed IDs.
        IDs returned by NCBI for that query.

        See also PubMedFetcher.pmids_for_query for other parameters.

            available categories:

                all     (default)
                diagnosis
                differential_diagnosis
                clinical_description
                management
                genetic_counseling
                genetic_testing

        :param: query (string)
        :param: category (string) [default: all]
        :return: list of pubmed IDs
        '''
        pass

    def pmids_for_citation(self, **kwargs):
        '''returns list of pmids for given citation. requires at least 3/5 of these keyword arguments:
            jtitle or journal (journal title)
            year or date
            volume
            spage or first_page (starting page / first page)
            aulast (first author's last name) or author1_first_lastfm (as produced by PubMedArticle class)

        Strings submitted for journal/jtitle will be run through metapub.utils.remove_chars to deal with HTML-
        encoded characters and to remove punctuation.
        '''
        # output format in return:
        # journal_title|year|volume|first_page|author_name|your_key|
        base_uri = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/ecitmatch.cgi?db=pubmed&retmode=xml&bdata={journal_title}|{year}|{volume}|{first_page}|{author_name}|{api_key}|'

        kwargs = lowercase_keys(kwargs)
        journal_title = remove_chars(kpick(kwargs, options=['jtitle', 'journal', 'journal_title'], default=''), urldecode=True)
        author_name = _reduce_author_string(kpick(kwargs,
                        options=['aulast', 'author1_last_fm', 'author', 'authors'], default=''))
        first_page = kpick(kwargs, options=['spage', 'first_page'], default='')
        year = kpick(kwargs, options=['year', 'date', 'pdat'], default='')
        volume = kpick(kwargs, options=['volume'], default='')

        inp_dict = { 'journal_title': parameterize(journal_title, '+'),
                     'year': str(year),
                     'volume': str(volume),
                     'first_page': str(first_page),
                     'author_name': parameterize(author_name, '+'),
                     'api_key': API_KEY or ''
                   }

        # clean up any "n/a" values.  eutils doesn't understand them.
        for k in inp_dict:
            if inp_dict[k].lower() == 'n/a':
                inp_dict[k] = ''

        req = base_uri.format(**inp_dict)
        log.debug('pmids_for_citation: querying with %s', req)

        content = requests.get(req, timeout=30).text
        pmids = []
        for item in content.split('\n'):
            if item.strip():
                pmid = item.split('|')[-1]
                pmids.append(pmid.strip())
        return pmids

    def related_pmids(self, pmid):
        '''For supplied pmid, return related ids of related pubmed articles,
        organized into a dictionary keyed by type of relation.  The keys include:

            * pubmed    (all related links)
            * citedin   (papers that cited this paper)
            * five      (the "five" that pubmed displays as the top related results)
            * reviews   (review papers that cite this paper)
            * combined  (?)

        query example:
        https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?retmode=xml&dbfrom=pubmed&id=14873513&cmd=neighbor
        
        :raises: NCBIServiceError if NCBI ELink service is down
        '''
        pass

    def pmid_for_bookID(self, book_id):
        '''For supplied NCBI Book ID, use the pubmed advanced query API to find its PMID.

        Not all NCBI Books have PMIDs.  If there is no associated PMID, this returns None.

        :param book_id: (str) e.g. "NBK2020"
        :return: (str) or None -- PMID if found, None otherwise.
        '''
        book_id = book_id.strip()
        if not is_ncbi_bookID(book_id):
            raise InvalidBookID('{} is not an NCBI Book ID'.format(book_id))
        res = self.pmids_for_query(book_id)
        if len(res) > 0:
            return res[0].strip()
        return None

def _reduce_author_string(author_string):
    # try splitting by commas
    authors = author_string.split(',')
    if len(authors)<2:
        # try splitting by semicolons
        authors = author_string.split(';')

    author1 = authors[0]
    # presume last name is at the end of the string
    return author1.split(' ')[-1]


"""
Search Field Descriptions and Tags

from https://www.ncbi.nlm.nih.gov/books/NBK3827/

Affiliation [AD]
Article Identifier [AID]
All Fields [ALL]
Author [AU]
Author Identifier [AUID]
Book [book]
Comment Corrections
Corporate Author [CN]
Create Date [CRDT]
Completion Date [DCOM]
EC/RN Number [RN]
Editor [ED]
Entrez Date [EDAT]
Filter [FILTER]
First Author Name [1AU]
Full Author Name [FAU]
Full Investigator Name [FIR]
Grant Number [GR]   Investigator [IR]
ISBN [ISBN]
Issue [IP]
Journal [TA]
Language [LA]
Last Author [LASTAU]
Location ID [LID]
MeSH Date [MHDA]
MeSH Major Topic [MAJR]
MeSH Subheadings [SH]
MeSH Terms [MH]
Modification Date [LR]
NLM Unique ID [JID]
Other Term [OT]
Owner
Pagination [PG]
Personal Name as Subject [PS]   Pharmacological Action [PA]
Place of Publication [PL]
PMID [PMID]
Publisher [PUBN]
Publication Date [DP]
Publication Type [PT]
Secondary Source ID [SI]
Subset [SB]
Supplementary Concept[NM]
Text Words [TW]
Title [TI]
Title/Abstract [TIAB]
Transliterated Title [TT]
UID [PMID]
Version
Volume [VI]
"""

'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE eSearchResult PUBLIC "-//NLM//DTD esearch 20060628//EN" "https://eutils.ncbi.nlm.nih.gov/eutils/dtd/20060628/esearch.dtd">
<eSearchResult><Count>1</Count><RetMax>1</RetMax><RetStart>0</RetStart><QueryKey>1</QueryKey><WebEnv>NCID_1_129952677_165.112.9.37_9001_1426564126_1266564592_0MetA0_S_MegaStore_F_1</WebEnv><IdList>
<Id>25023161</Id>
</IdList><TranslationSet><Translation>     <From>Journal of Neural Transmission[TA]</From>     <To>"J Neural Transm"[Journal] OR "J Neural Transm"[Journal] OR "J Neural Transm Suppl"[Journal] OR "J Neural Transm Park Dis Dement Sect"[Journal] OR "J Neural Transm Gen Sect"[Journal]</To>    </Translation></TranslationSet><TranslationStack>   <TermSet>    <Term>2014[DP]</Term>    <Field>DP</Field>    <Count>1171381</Count>    <Explode>N</Explode>   </TermSet>   <TermSet>    <Term>"J Neural Transm"[Journal]</Term>    <Field>Journal</Field>    <Count>1177</Count>    <Explode>N</Explode>   </TermSet>   <TermSet>    <Term>"J Neural Transm"[Journal]</Term>    <Field>Journal</Field>    <Count>3005</Count>    <Explode>N</Explode>   </TermSet>   <OP>OR</OP>   <TermSet>    <Term>"J Neural Transm Suppl"[Journal]</Term>    <Field>Journal</Field>    <Count>1409</Count>    <Explode>N</Explode>   </TermSet>   <OP>OR</OP>   <TermSet>    <Term>"J Neural Transm Park Dis Dement Sect"[Journal]</Term>    <Field>Journal</Field>    <Count>226</Count>    <Explode>N</Explode>   </TermSet>   <OP>OR</OP>   <TermSet>    <Term>"J Neural Transm Gen Sect"[Journal]</Term>    <Field>Journal</Field>    <Count>526</Count>    <Explode>N</Explode>   </TermSet>   <OP>OR</OP>   <OP>GROUP</OP>   <OP>AND</OP>   <TermSet>    <Term>121[VI]</Term>    <Field>VI</Field>    <Count>44530</Count>    <Explode>N</Explode>   </TermSet>   <OP>AND</OP>   <TermSet>    <Term>Freitag[1AU]</Term>    <Field>1AU</Field>    <Count>496</Count>    <Explode>N</Explode>   </TermSet>   <OP>AND</OP>  </TranslationStack><QueryTranslation>2014[DP] AND ("J Neural Transm"[Journal] OR "J Neural Transm"[Journal] OR "J Neural Transm Suppl"[Journal] OR "J Neural Transm Park Dis Dement Sect"[Journal] OR "J Neural Transm Gen Sect"[Journal]) AND 121[VI] AND Freitag[1AU]</QueryTranslation></eSearchResult>'''
