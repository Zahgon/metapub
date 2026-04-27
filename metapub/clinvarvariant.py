"""metapub.clinvarvariant -- ClinVarVariant class instantiated by supplying ESummary XML string."""

import logging
from datetime import datetime
from typing import Optional, Literal
from dataclasses import dataclass

from lxml import etree

from .base import MetaPubObject
from .exceptions import MetaPubError, BaseXMLError

#TODO: Logging

# See: https://www.ncbi.nlm.nih.gov/clinvar/docs/clinsig/
# All possible clinical significance classes a variant may be classified as
# by a submitter.
# 
# NOTE: here we represent clinical significance classes in lowercase.
ClinSig = Literal[
    "pathogenic", "likely pathogenic", "uncertain significance",
    "likely benign", "benign", "conflicting interpretations",
    "drug response", "risk factor", "association",
    "protective", "other", "likely pathogenic, low penetrance",
    "pathogenic, low penetrance",
    "uncertain risk allele", "likely risk allele",
    "established risk allele", "affects", "conflicting data from submitters",
    "not provided", "vus-high", "vus-mid", "vus-low"
]
# Possible types of IDs a user may supply to initialize a variant.
IdLocations = Literal['clinvar', 'entrez']

@dataclass
class PathogenicSummary:
    counts: dict[ClinSig, int]
    total_submitters: int
    consensus: Optional[ClinSig]
    conflicting: bool
    review_status: Optional[str]

class ClinVarVariant(MetaPubObject):

    def __init__(self, xmlstr, *args, **kwargs):
        # Try new VCV format first, fall back to old format for backwards compatibility
        try:
            # Parse the full XML document first to determine format
            from lxml import etree
            dom = etree.fromstring(xmlstr)

            if dom.tag == 'ClinVarResult-Set':
                # New VCV format
                self._is_vcv_format = True
                super(ClinVarVariant, self).__init__(xmlstr, None, args, kwargs)  # Parse full document
                self.variation_archive = self.content.find('VariationArchive')
                if self.variation_archive is None:
                    # Check if this is an empty result set (invalid ID)
                    set_elem = self.content.find('set')
                    if set_elem is not None and len(set_elem) == 0:
                        raise BaseXMLError('Empty XML document')  # This will trigger the "Invalid ClinVar Variation ID" error
                    else:
                        raise BaseXMLError('No VariationArchive found in VCV format')
            else:
                # Old format
                self._is_vcv_format = False
                super(ClinVarVariant, self).__init__(xmlstr, 'VariationReport', args, kwargs)
                self.variation_archive = None
        except (etree.XMLSyntaxError, BaseXMLError) as e:
            # If XML parsing fails completely, let it bubble up
            raise BaseXMLError('Invalid XML document: %s' % str(e))

        if self.content is None:
            raise BaseXMLError('Empty XML document')

        if self._get('error'):
            raise MetaPubError('Supplied XML for ClinVarVariant contained explicit error: %s' % self._get('error'))

        # VariationReport basic details
        self.variation_id = self._get_variation_id()
        self.variation_name = self._get_variation_name()
        self.variation_type = self._get_variation_type()
        self.date_created = self._get_date_created()
        self.date_last_updated = self._get_date_last_updated()
        self.submitter_count = self._get_submitter_count()

        # Species Info
        self.species = self._get_species()
        self.taxonomy_id = self._get_taxonomy_id()

        # Gene List
        self.genes = self._get_gene_list()

        # Allele Info
        self.cytogenic_location = self._get_cytogenic_location()
        self.sequence_locations = self._get_sequence_locations()
        self.hgvs = self._get_hgvs_list()
        self.xrefs = self._get_xref_list()
        self.molecular_consequences = self._get_molecular_consequence_list()
        self.allele_frequencies = self._get_allele_frequency_list()

        # Clinical significance and classifications (new in VCV format)
        self.clinical_significance = self._get_clinical_significance()
        self.review_status = self._get_review_status()
        self.date_last_evaluated = self._get_date_last_evaluated()
        self.number_of_submissions = self._get_number_of_submissions()
        self.number_of_submitters = self._get_number_of_submitters()
        self.pathogenic_summary = self._get_pathogenic_summary()

        # VCV record metadata (new in VCV format)
        self.vcv_accession = self._get_vcv_accession()
        self.record_type = self._get_record_type()
        self.most_recent_submission = self._get_most_recent_submission()

        # Associated conditions/diseases (new in VCV format)
        self.associated_conditions = self._get_associated_conditions()

        # Enhanced molecular consequences (new in VCV format)
        self.molecular_consequences_detailed = self._get_molecular_consequences_detailed()

        # Enhanced sequence details (new in VCV format)
        self.sequence_details = self._get_sequence_details()

        # Enhanced gene information (new in VCV format)
        self.gene_dosage_info = self._get_gene_dosage_info()

        # Protein change summary (new in VCV format)
        self.protein_change = self._get_protein_change()

        # Clinical assertions (new in VCV format)
        self.clinical_assertions = self._get_clinical_assertions()

        # Enhanced citations (new in VCV format)
        self.citations = self._get_citations()

        # Observations


    def to_dict(self):
        """ returns a dictionary composed of all extractable properties of this concept. """
        pass

    ### HGVS string convenience properties

    def _get_hgvs_or_empty_list(self, hgvsdict):
        pass

    @property
    def hgvs_c(self):
        """ Returns a list of all coding HGVS strings from the Allelle data. """
        pass

    @property
    def hgvs_g(self):
        """ Returns a list of all genomic HGVS strings from the Allelle data. """
        pass

    @property
    def hgvs_p(self):
        """ Returns a list of all protein effect HGVS strings from the Allelle data. """
        pass

    ### VariationReport basic info

    def _get_variation_id(self):
        pass

    def _get_variation_name(self):
        pass

    def _get_variation_type(self):
        pass

    def _get_date_created(self):
        pass

    def _get_date_last_updated(self):
        pass

    def _get_submitter_count(self):
        pass

    def _get_species(self):
        pass

    def _get_taxonomy_id(self):
        pass

    #### GENE LIST

    def _get_gene_list(self):
        """ Returns a list of dictionaries representing each gene associated with this variant.

        Keys in gene dictionary vary by format but include: 'Symbol', 'FullName', 'GeneID', 'HGNC_ID', etc.
        """
        pass


    ### ALLELE INFORMATION

    def _get_allele_id(self):
        pass

    def _get_cytogenic_location(self):
        pass

    def _get_sequence_locations(self):
        pass

    def _get_hgvs_list(self):
        pass

    def _get_xref_list(self):
        pass

    def _get_molecular_consequence_list(self):
        pass

    def _get_allele_frequency_list(self):
        pass

    ### NEW VCV FORMAT ENHANCEMENTS ###

    def _get_clinical_significance(self) -> Optional[ClinSig]:
        """Get the clinical significance classification (e.g., 'pathogenic', 'benign')
        
        A list of all significance classes is available here: https://www.ncbi.nlm.nih.gov/clinvar/docs/clinsig/
        
        **Note**: in this version of Metapub, clinical significance is represented in lowercase.
        Older versions did NOT do this, so make sure to update your code if necessary!
        """
        pass

    def _get_review_status(self):
        """Get the review status (e.g., 'criteria provided, multiple submitters, no conflicts')"""
        pass

    def _get_date_last_evaluated(self):
        """Get the date when the clinical significance was last evaluated"""
        pass

    def _get_number_of_submissions(self):
        """Get the number of submissions for this variant"""
        pass

    def _get_number_of_submitters(self):
        """Get the number of submitters for this variant"""
        pass

    def _get_vcv_accession(self):
        """Get the VCV accession number (e.g., 'VCV000012397')"""
        pass

    def _get_record_type(self):
        """Get the record type (e.g., 'classified')"""
        pass

    def _get_most_recent_submission(self):
        """Get the date of the most recent submission"""
        pass

    def _get_associated_conditions(self):
        """Get list of associated conditions/diseases with their MedGen IDs"""
        pass

    def _get_molecular_consequences_detailed(self):
        """Get detailed molecular consequences with Sequence Ontology terms"""
        pass

    def _get_sequence_details(self):
        """Get enhanced sequence location details including VCF coordinates"""
        pass
    
    def _get_pathogenic_summary(self) -> Optional[PathogenicSummary]:
        """ Return the aggregation of per-submitter clinical germline significance classifications 
        into a readable summary.

        Returns a dataclass in the following format:
        {
          counts: {
            'pathogenic': 3,
            'likely pathogenic': 1,
            'uncertain significance': 0,
          }
          ...
          total_submitters: 4,
          consensus: 'pathogenic',
          conflicting': False,
          review_status: 'criteria provided, multiple submitters, no conflicts'
        }
        """
        pass

    def _get_gene_dosage_info(self):
        """Get gene dosage sensitivity information"""
        pass

    def _get_protein_change(self):
        """Get the simple protein change notation (e.g., 'R611Q')"""
        pass

    def _get_citations(self):
        """Get citation information from the clinical classifications"""
        pass

    def _get_clinical_assertions(self):
        """Get individual clinical assertions from submitters"""
        pass

    ### OBSERVATIONS


