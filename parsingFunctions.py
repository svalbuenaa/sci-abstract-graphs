# Imports
import xml.etree.ElementTree as ET
import re
import pandas as pd

# Find a PMID in a directory with XML files for PMIDs
def findPMIDInXML(XML_dir: str, XML_file: list,  PMID: str):
    for el in XML_file:
        tree = ET.parse(XML_dir+el)
        root = tree.getroot()

        for node in root:
            if node.tag == 'PubmedArticle':
                if node.find("./MedlineCitation/PMID").text.strip() == PMID:
                    print(PMID + el)
            elif node.tag == 'PubmedBookArticle':
                if node.find("./BookDocument/PMID").text.strip() == PMID:
                    print(PMID + el)
            else:
                print("No PubmedArticle or PubmedBookArticle tag for PMID: " + PMID)


# Parse the XML files in a directory to extract articles' information
def parseXML(XML_dir: str, XML_file: list, XML_parsed: list, XML_nor_parsed: list, current_parsing_XML: str, DF_output: str):
    number_files = len(XML_file)
    for el in XML_file:
        current_parsing_XML = el
        
        # For each 100K papers, save intermediate file and print state 
        if int(current_parsing_XML[:-4]) % 100000 == 0:
            if int(current_parsing_XML[:-4]) != 0:
                df = pd.DataFrame(XML_nor_parsed)
                df.to_csv(DF_output)
            
            print("Currently parsing article: "+str(current_parsing_XML[:-4])+"/"+str(number_files*200))

        try:
            tree = ET.parse(XML_dir+el)
            root = tree.getroot()
    
            for node in root:
                article_data = {}
                not_parsed_XML_files = []
                if node.tag == 'PubmedArticle':
                    # Type of entry
                    article_data['Type'] = 'Article'
    
                    # PMID
                    pmid_node = node.find('./MedlineCitation/PMID')
                    article_data['PMID'] = pmid_node.text.strip() if pmid_node is not None else None
    
                    # DOI
                    # For the DOI there are 2 nodes (PubmedArticle/PubmedData/ArticleIdList/ArticleId[@IdType ="doi"]) and
                    # (PubmedArticle/MedlineCitation/Article/ELocationID[@EIdType ="doi"]]). The first is better
                    doi_node = node.find('./PubmedData/ArticleIdList/ArticleId[@IdType = "doi"]')
                    article_data['DOI'] = doi_node.text.strip() if doi_node is not None else None
    
                    # Journal
                    journal_node = node.find('./MedlineCitation/Article/Journal/Title')
                    article_data['Journal'] = journal_node.text.strip() if journal_node is not None else None
    
                    # Title
                    title_node = node.find('./MedlineCitation/Article/ArticleTitle')
                    article_data['Title'] = title_node.text.strip() if title_node is not None else None
    
                    # Abstract
                    abstract_node = node.find('./MedlineCitation/Article/Abstract')
                    if abstract_node is not None:
                        abstract_text = ''
                        for elem in abstract_node.iter():
                            if elem.text:
                                abstract_text += elem.text.strip() + ' '
                        article_data['Abstract'] = abstract_text.strip()
                    else:
                        article_data['Abstract'] = None
    
                    # Authors list
                    authors = []
                    for author in node.findall('./MedlineCitation/Article/AuthorList/Author'):
                        author_info = {}
                        forename_node = author.find('./ForeName')
                        lastname_node = author.find('./LastName')
                        if forename_node is not None and forename_node.text and lastname_node is not None and lastname_node.text:
                            author_info['Name'] = forename_node.text.strip() + ' ' + lastname_node.text.strip()
                        else:
                            continue
    
                        affiliations = []
                        for affiliation in author.findall('./AffiliationInfo/Affiliation'):
                            affiliations.append(affiliation.text.strip())
    
                        author_info['Affiliation'] = affiliations
                        authors.append(author_info)
                    article_data['Authors'] = authors
    
                    # MeshHeadings
                    mesh_headings = []
                    for mesh_heading in node.findall('./MedlineCitation/MeshHeadingList/MeshHeading'):
                        descriptor_name = mesh_heading.find('./DescriptorName').text.strip()
                        mesh_headings.append(descriptor_name)
                    article_data['MeshHeadings'] = ', '.join(mesh_headings) if mesh_headings else None
    
                    # Chemicals
                    chemicals = []
                    for chemical in node.findall('./MedlineCitation/ChemicalList/Chemical'):
                        chemical_name = chemical.find('./NameOfSubstance').text.strip()
                        chemicals.append(chemical_name)
                    article_data['Chemicals'] = chemicals if chemicals else None
    
                    # Publication types
                    publication_types = []
                    for publication_type in node.findall('./MedlineCitation/Article/PublicationTypeList/PublicationType'):
                        publication_types.append(publication_type.text.strip())
                    article_data['PublicationTypes'] = publication_types if publication_types else None
    
                    # Publication date
                    pub_date_node = node.find('./MedlineCitation/Article/Journal/JournalIssue/PubDate/Year')
                    if pub_date_node is not None:
                        article_data['PublicationDate'] = pub_date_node.text.strip()
                    else:
                        article_data['PublicationDate'] = None
    
                    # Language
                    language_node = node.find('./MedlineCitation/Article/Language')
                    article_data['Language'] = language_node.text.strip() if language_node is not None else None
    
                    # Keywords
                    keywords = []
                    for keyword in node.findall('./MedlineCitation/KeywordList/Keyword'):
                        if keyword.text:
                            keywords.append(keyword.text.strip())
                    article_data['Keywords'] = keywords if keywords else None
            
        
                elif node.tag == 'PubmedBookArticle':
                    # Type of entry
                    article_data['Type'] = 'Book Article'
    
                    # PMID
                    pmid_node = node.find('./BookDocument/PMID')
                    article_data['PMID'] = pmid_node.text.strip() if pmid_node is not None else None
    
                    # Book Accession
                    book_accession_node = node.find('./BookDocument/ArticleIdList/ArticleId[@IdType = "bookaccession"]')
                    article_data["Book Accession"] = book_accession_node if book_accession_node is not None else None
                    
                    # Book Publisher Name
                    publisher_node = node.find('./BookDocument/Book/Publisher/PublisherName')
                    article_data['Publisher'] = publisher_node.text.strip() if publisher_node is not None else None
    
                    # Book title
                    book_title_node = node.find('./BookDocument/Book/BookTitle')
                    article_data['BookTitle'] = book_title_node.text.strip() if book_title_node is not None else None
        
                    # Title
                    title_node = node.find('./BookDocument/ArticleTitle')
                    if title_node != None and title_node.find("./i") != None:
                        article_data["Title"] = ''.join(text.strip() for text in title_node.itertext() if text.strip())
                    elif title_node != None and title_node.find("./i") == None:
                        article_data['Title'] = title_node.text.strip()
                    else:
                        article_data['Title'] = None
    
                    # Abstract
                    abstract_node = node.find('./BookDocument/Abstract')
                    if abstract_node is not None:
                        article_data['Abstract'] = ''.join(
                            text.strip() if child.tag != 'i' else re.sub("\n", "", " "+text.strip()+" ")
                            for child in abstract_node.iter() if child.tag != "CopyrightInformation"
                            for text in ([child.text] if child.text else []) + ([child.tail] if child.tail else [])
                        )
                    else:
                        article_data['Abstract'] = None
    
                    # Authors list
                    authors = []
                    for author in node.findall('./BookDocument/AuthorList[@Type="authors"]/Author'):
                        author_info = {}
                        forename_node = author.find('./ForeName')
                        lastname_node = author.find('./LastName')
                        if forename_node is not None and lastname_node is not None:
                            author_info['Name'] = forename_node.text.strip() + ' ' + lastname_node.text.strip()
                        else:
                            continue
    
                        affiliations = []
                        for affiliation in author.findall('./AffiliationInfo/Affiliation'):
                            affiliations.append(affiliation.text.strip())
    
                        author_info['Affiliation'] = affiliations
                        authors.append(author_info)
                    article_data['Authors'] = authors
    
                    # Publication date
                    pub_date_node = node.find('./BookDocument/Book/PubDate/Year')
                    if pub_date_node is not None:
                        article_data['PublicationDate'] = pub_date_node.text.strip()
                    else:
                        article_data['PublicationDate'] = None
    
                    # Language
                    language_node = node.find('./BookDocument/Language')
                    article_data['Language'] = language_node.text.strip() if language_node is not None else None
    
                    # Keywords
                    keywords = []
                    for keyword in node.findall('./BookDocument/KeywordList/Keyword'):
                        if keyword.text:
                            keywords.append(keyword.text.strip())
                    article_data['Keywords'] = ', '.join(keywords) if keywords else None
    
                else:
                    continue
    
        
                XML_parsed.append(article_data)

        except:
            print(el+" not parsed")
            not_parsed_XML_files.append(el)
            continue

        if current_parsing_XML == XML_file[-1]:
            print("Last XML file parsed")