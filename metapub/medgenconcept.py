"""metapub.medgenconcept -- MedGenConcept class instantiated by supplying ESummary XML string."""

import logging
from lxml import etree

from .base import MetaPubObject
from .exceptions import MetaPubError

logger = logging.getLogger()


class MedGenConcept(MetaPubObject):

    def __init__(self, xmlstr, *args, **kwargs):
        super(MedGenConcept, self).__init__(xmlstr, 'DocumentSummarySet/DocumentSummary', args, kwargs)

        if self._get('error'):
            raise MetaPubError('Supplied XML for MedGenConcept contained explicit error: %s' % self._get('error'))

        # sometimes, ConceptMeta is an XML document embedded within the XML response. Boo-urns. 
        try:
            self.meta = etree.fromstring('<ConceptMeta>'+self.content.find('ConceptMeta').text+'</ConceptMeta>')
        except TypeError:
            self.meta = self.content.find('ConceptMeta')
        
        self.modes_of_inheritance = self._get_modes_of_inheritance()
        self.OMIM = self._get_OMIM()        # is a list, since sometimes there are more than one.
        self.names = self._get_names()
        self.CUI = self._get_CUI()
        self.title = self._get_title()
        self.definition = self._get_definition()
        self.semantic_id = self._get_semantic_id()
        self.semantic_type = self._get_semantic_type()
        self.associated_genes = self._get_associated_genes()
        self.cytogenic = self._get_cytogenic()
        self.chromosome = self._get_chromosome()
        self.definitions = self._get_definitions()
        self.uid = self._get_medgen_uid()

    def to_dict(self):
        """ returns a dictionary composed of all extractable properties of this concept. """
        pass

    @property
    def synonyms(self):
        """Returns a list of the 'name' values from self.names."""
        pass

    @property
    def medgen_uid(self):
        """Synonym for "uid". Sometimes when juggling concepts from multiple places, this helps."""
        pass

    def _get_CUI(self):
        pass
    
    def _get_title(self):
        pass
        
    def _get_definition(self):
        pass
    
    def _get_semantic_id(self):
        pass
    
    def _get_semantic_type(self):
        pass
        
    def _get_medgen_uid(self):
        pass
    
    def _get_modes_of_inheritance(self):
        """ returns a list of all known ModesOfInheritance, in format:
        [ { 'CUI': 'CNxxxx', 'name': 'some name', 'medgen_uid': 'xxxxxx', 'tui': 'A000 }, ...  ]
        """
        pass
             
    def _get_associated_genes(self):
        """ returns a list of AssociatedGenes, in format:
        [ { 'gene_id': 'xxx', 'chromosome': 'X', 'cytogen_loc': 'X9234235', 'hgnc': 'GENE' }, ]
        
        if not available, returns None. 
        """
        pass

    def _get_names(self):
        """ Returns a list of this concept's equivalent Names in various dictionaries,
        in format:
        
        {'SDUI': '300555', 'SCUI': 'xxx', 'CODE': '300555', 'SAB': 'OMIM' 'TTY': 'PT',
         'type': 'syn', 'name': 'DENT DISEASE 2'}
        """
        pass

    def _get_OMIM(self):
        """ Returns this concept's OMIM ids (list of strings), when available, else returns []. """
        pass
        
    def _get_chromosome(self):
        """returns this concept's affected chromosome, if applicable/available"""
        pass

    def _get_cytogenic(self):
        """returns this concept's cytogenic property, if applicable/available"""
        pass

    def _get_definitions(self):
        """returns this concept's definitions as LIST of strings."""
        pass

    # TODO
    # ClinicalFeatures / ClinicalFeature
    # <ClinicalFeatures><ClinicalFeature uid="9232" CUI="C0019322" TUI="T190" SDUI="HP:0001537"><Name>Umbilical hernia</Name><SemanticType>Anatomical Abnormality</SemanticType></ClinicalFeature><ClinicalFeature uid="87607" CUI="C0349588" TUI="T033" SDUI="HP:0004322"><Name>Short stature</Name><SemanticType>Finding</SemanticType></ClinicalFeature><ClinicalFeature uid="333360" CUI="C1839606" TUI="T033" SDUI="HP:0003126"><Name>Low-molecular-weight proteinuria</Name><SemanticType>Finding</SemanticType></ClinicalFeature><ClinicalFeature uid="383844" CUI="C1856145" TUI="T033" SDUI="HP:0100543"><Name>Cognitive impairment</Name><SemanticType>Finding</SemanticType></ClinicalFeature><ClinicalFeature uid="349145" CUI="C1859342" TUI="T033" SDUI="HP:0000114"><Name>Proximal tubulopathy</Name><SemanticType>Finding</SemanticType></ClinicalFeature><ClinicalFeature uid="504348" CUI="CN000117" TUI="T033" SDUI="HP:0000121"><Name>Nephrocalcinosis</Name><SemanticType>Finding</SemanticType><Definition>Nephrocalcinosis is the deposition of calcium salts in renal parenchyma.</Definition></ClinicalFeature><ClinicalFeature uid="504774" CUI="CN001157" TUI="T033" SDUI="HP:0001263"><Name>Global developmental delay</Name><SemanticType>Finding</SemanticType><Definition>A delay in the achievement of motor or mental milestones in the domains of development of a child, including motor skills, speech and language, cognitive skills, and social and emotional skills. This term should only be used to describe children younger than five years of age.</Definition></ClinicalFeature><ClinicalFeature uid="505127" CUI="CN001948" TUI="T033" SDUI="HP:0002150"><Name>Hypercalciuria</Name><SemanticType>Finding</SemanticType></ClinicalFeature><ClinicalFeature uid="505493" CUI="CN002923" TUI="T033" SDUI="HP:0003236"><Name>Elevated serum creatine phosphokinase</Name><SemanticType>Finding</SemanticType><Definition>An elevation of the level of the enzyme creatine kinase (also known as creatine phosphokinase, CPK; EC 2.7.3.2) in the blood. CPK levels can be elevated in a number of clinical disorders such as myocardial infarction, rhabdomyolysis, and muscular dystrophy.</Definition></ClinicalFeature><ClinicalFeature uid="425142" CUI="CN003029" TUI="T033" SDUI="HP:0003355"><Name>Aminoaciduria</Name><SemanticType>Finding</SemanticType><Definition>An increased concentration of an amino acid in the urine.</Definition></ClinicalFeature><ClinicalFeature uid="776439" CUI="CN183891" TUI="T033" SDUI="HP:0012622"><Name>Chronic kidney disease</Name><SemanticType>Finding</SemanticType><Definition>Functional anomaly of the kidney persisting for at least three months.</Definition></ClinicalFeature></ClinicalFeatures><PhenotypicAbnormalities><Category CUI="CN000115" name="Abnormality of the genitourinary system"><ClinicalFeature uid="504348" CUI="CN000117" TUI="T033" SDUI="HP:0000121"><SemanticType>Finding</SemanticType><Name>Nephrocalcinosis</Name><Definition>Nephrocalcinosis is the deposition of calcium salts in renal parenchyma.</Definition></ClinicalFeature><ClinicalFeature uid="425142" CUI="CN003029" TUI="T033" SDUI="HP:0003355"><SemanticType>Finding</SemanticType><Name>Aminoaciduria</Name><Definition>An increased concentration of an amino acid in the urine.</Definition></ClinicalFeature><ClinicalFeature uid="776439" CUI="CN183891" TUI="T033" SDUI="HP:0012622"><SemanticType>Finding</SemanticType><Name>Chronic kidney disease</Name><Definition>Functional anomaly of the kidney persisting for at least three months.</Definition></ClinicalFeature></Category><Category CUI="CN000664" name="Abnormality of the nervous system"><ClinicalFeature uid="504774" CUI="CN001157" TUI="T033" SDUI="HP:0001263"><SemanticType>Finding</SemanticType><Name>Global developmental delay</Name><Definition>A delay in the achievement of motor or mental milestones in the domains of development of a child, including motor skills, speech and language, cognitive skills, and social and emotional skills. This term should only be used to describe children younger than five years of age.</Definition></ClinicalFeature></Category><Category CUI="CN001754" name="Abnormality of metabolism/homeostasis"><ClinicalFeature uid="505493" CUI="CN002923" TUI="T033" SDUI="HP:0003236"><SemanticType>Finding</SemanticType><Name>Elevated serum creatine phosphokinase</Name><Definition>An elevation of the level of the enzyme creatine kinase (also known as creatine phosphokinase, CPK; EC 2.7.3.2) in the blood. CPK levels can be elevated in a number of clinical disorders such as myocardial infarction, rhabdomyolysis, and muscular dystrophy.</Definition></ClinicalFeature><ClinicalFeature uid="425142" CUI="CN003029" TUI="T033" SDUI="HP:0003355"><SemanticType>Finding</SemanticType><Name>Aminoaciduria</Name><Definition>An increased concentration of an amino acid in the urine.</Definition></ClinicalFeature>
    
    # TODO
    # PhenotypicAbnormalities 
    # <PhenotypicAbnormalities><Category CUI="CN000115" name="Abnormality of the genitourinary system"><ClinicalFeature uid="504348" CUI="CN000117" TUI="T033" SDUI="HP:0000121"><SemanticType>Finding</SemanticType><Name>Nephrocalcinosis</Name><Definition>Nephrocalcinosis is the deposition of calcium salts in renal parenchyma.</Definition></ClinicalFeature><ClinicalFeature uid="425142" CUI="CN003029" TUI="T033" SDUI="HP:0003355"><SemanticType>Finding</SemanticType><Name>Aminoaciduria</Name><Definition>An increased concentration of an amino acid in the urine.</Definition></ClinicalFeature><ClinicalFeature uid="776439" CUI="CN183891" TUI="T033" SDUI="HP:0012622"><SemanticType>Finding</SemanticType><Name>Chronic kidney disease</Name><Definition>Functional anomaly of the kidney persisting for at least three months.</Definition></ClinicalFeature></Category><Category CUI="CN000664" name="Abnormality of the nervous system"><ClinicalFeature uid="504774" CUI="CN001157" TUI="T033" SDUI="HP:0001263"><SemanticType>Finding</SemanticType><Name>Global developmental delay</Name><Definition>A delay in the achievement of motor or mental milestones in the domains of development of a child, including motor skills, speech and language, cognitive skills, and social and emotional skills. This term should only be used to describe children younger than five years of age.</Definition></ClinicalFeature></Category><Category CUI="CN001754" name="Abnormality of metabolism/homeostasis"><ClinicalFeature uid="505493" CUI="CN002923" TUI="T033" SDUI="HP:0003236"><SemanticType>Finding</SemanticType><Name>Elevated serum creatine phosphokinase</Name><Definition>An elevation of the level of the enzyme creatine kinase (also known as creatine phosphokinase, CPK; EC 2.7.3.2) in the blood. CPK levels can be elevated in a number of clinical disorders such as myocardial infarction, rhabdomyolysis, and muscular dystrophy.</Definition></ClinicalFeature><ClinicalFeature uid="425142" CUI="CN003029" TUI="T033" SDUI="HP:0003355"><SemanticType>Finding</SemanticType><Name>Aminoaciduria</Name><Definition>An increased concentration of an amino acid in the urine.</Definition></ClinicalFeature></Category></PhenotypicAbnormalities>
        
    # TODO
    # <RelatedDisorders></RelatedDisorders>
    
    # TODO
    # <SNOMEDCT></SNOMEDCT>
    
    # known others not planned for inclusion:
    # <PharmacologicResponse></PharmacologicResponse>
    
