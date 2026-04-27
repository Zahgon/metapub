""" metapub.clinvarfetcher: tools for interacting with ClinVar data """

# TODO: Add logging

from lxml import etree
from .clinvarvariant import ClinVarVariant, IdLocations
from .exceptions import MetaPubError, BaseXMLError
from .eutils_common import get_eutils_client
from .cache_utils import get_cache_path 
from .base import Borg, parse_elink_response
from .ncbi_errors import diagnose_ncbi_error, NCBIServiceError

class ClinVarFetcher(Borg):
    """ ClinVarFetcher (a Borg singleton object)

    Toolkit for retrieval of ClinVar information. 

    Set optional 'cachedir' parameter to absolute path of preferred directory 
    if desired; cachedir defaults to <current user directory> + /.cache

        clinvar = ClinVarFetcher()

        clinvar = ClinVarFetcher(cachedir='/path/to/cachedir')

    Usage
    -----

    Get ClinVar accession IDs for gene name (switch single_gene to True to filter out 
    results containing more genes than the specified gene being searched, default False).

        cv_ids = clinvar.ids_by_gene('FGFR3', single_gene=True)

    Get ClinVar accession in python dictionary format for given ID:

        cv_subm = clinvar.accession(65533)  # can also submit ID as string 

    Get list of pubmed IDs (pmids) for given ClinVar accession ID:

        pmids = clinvar.pmids_for_id(65533)  # can also submit ID as string

    Get list of pubmed IDs (pmids) for hgvs string:

        pmids = clinvar.pmids_for_hgvs('NM_017547.3:c.1289A>G')

    For more info, see the ClinVar eutils page:
    https://www.ncbi.nlm.nih.gov/clinvar/docs/maintenance_use/
    """

    _cache_filename = 'clinvarfetcher.db'

    def __init__(self, method='eutils', cachedir='default'):
        """Initialize ClinVarFetcher for clinical variant data retrieval.
        
        Args:
            method (str, optional): Service method to use. Currently only 'eutils'
                is supported. Defaults to 'eutils'.
            cachedir (str, optional): Directory for caching responses. Use 'default'
                for system cache directory. Defaults to 'default'.
        
        Raises:
            NotImplementedError: If an unsupported method is specified.
        
        Note:
            This is a Borg singleton - all instances share the same state.
            Provides access to NCBI's ClinVar database for clinical significance
            of genetic variants, gene-disease relationships, and variant literature.
        """
        self.method = method
        self._cache_path = None

        if method=='eutils':
            self._cache_path = get_cache_path(cachedir, self._cache_filename)
            self.qs = get_eutils_client(self._cache_path) 
            self.ids_by_gene = self._eutils_ids_by_gene
            self.get_accession = self._eutils_get_accession
            self.pmids_for_id = self._eutils_pmids_for_id
            self.ids_for_variant = self._eutils_ids_for_variant
            self.pmids_for_hgvs = self._eutils_pmids_for_hgvs
            self.variant = self._eutils_get_variant_summary
        else:
            raise NotImplementedError('coming soon: fetch from local clinvar via medgen-mysql.')

    def _eutils_get_accession(self, accession_id):
        """ returns python dict of info for given ClinVar accession ID.

        :param: accession_id (integer or string)
        :return: dictionary
        :raises: NCBIServiceError if ClinVar service is down
        """
        pass

    def _eutils_get_variant_summary(self, accession_id, id_from: IdLocations = 'entrez'):
        """ returns structured, flattened summary for a ClinVar variant given an accession ID.
        NOTE: By default, this is the Entrez UID that a variant has in E-utilities, NOT its ClinVar ID.

        To specify that you would like this accession_id to be parsed as a clinvar ID, specify 
        `id_from = 'clinvar'`

        :param: accession_id (integer or string)
        :param: id_from (string, either 'clinvar' or 'entrez')
        :return: ClinVarVariant
        :raises: MetaPubError if variation ID is invalid (empty XML document response)
        """
        pass

    def _eutils_ids_by_gene(self, gene, single_gene=False):
        """
        searches ClinVar for specified gene (HUGO); returns up to 500 matching results.

        :param: gene (string) - gene name in HUGO naming convention.
        :param: single_gene (bool) [default: False] - restrict results to single-gene accessions.
        :return: list of clinvar ids (strings)
        """
        pass

    def _eutils_pmids_for_id(self, clinvar_id):
        """
        example:
        https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=clinvar&db=pubmed&id=9

        :param: clinvar_id (integer or string)
        :return: list of pubmed IDs (strings)
        """
        pass

    def _eutils_ids_for_variant(self, hgvs_c):
        """ returns ClinVar IDs for given HGVS c. string

        :param: hgvs_c (string)
        :return: list of pubmed IDs (strings)
        """
        pass

    def _eutils_pmids_for_hgvs(self, hgvs_text):
        """ returns pubmed IDs for given HGVS c. string

        :param hgvs_text:
        :return: list of pubmed IDs
        """
        pass
