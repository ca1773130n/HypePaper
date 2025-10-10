import ast
import re
import json
import argparse
import loguru
import fitz
import pandas as pd

import nest_asyncio

from sotapapers.utils.id_util import make_generated_id
nest_asyncio.apply()

from sotapapers.core.action import ActionType, ActionInput
from sotapapers.core.agent import Agent
from sotapapers.core.schemas import Paper, PaperContent, PaperMedia, PaperType, PaperSessionType, PaperAcceptStatus, PaperMetrics
from sotapapers.core.settings import Settings
from sotapapers.modules.arxiv_client import ArxivClient
from sotapapers.modules.web_scraper import WebScraper
from sotapapers.modules.llm.llama_cpp_client import LlamaCppClient
from sotapapers.utils.config import get_config_path
from sotapapers.utils.string_util import (
    fix_parentheses,
    find_first_successive_spaces,
    starts_with_number,
    split_text_at_years_with_dot,
    remove_non_numeric,
    replace_newlines_except_after_dot, 
    remove_garbage_lines,
    add_newlines_before_numbered_references,
    remove_unwanted_dashes,
    clean_json_string,
    tatr_table_to_csv
)

from sotapapers.utils.pdf_utils import get_full_text_from_pdf

from pathlib import Path
from collections import Counter

from gmft.auto import TATRDetectorConfig, AutoFormatConfig, AutoTableDetector, AutoTableFormatter
from gmft.pdf_bindings import PyPDFium2Document
from selenium.webdriver.common.by import By

class PaperReader(Agent):
    def __init__(self, settings: Settings, logger: loguru.logger):
        self.settings = settings
        self.log = logger
        self.arxiv_client = ArxivClient(settings, logger)
        
        llm_system_prompt = settings.config.paper_reader.llm.system_prompt
        self.llm_client = LlamaCppClient(settings, logger, llm_system_prompt)
        
    def set_file_path(self, file_path: Path):
        self.file_path = file_path
        self.pdf_doc = PyPDFium2Document(file_path.absolute())
        self.full_text = get_full_text_from_pdf(file_path)
        self.llm_client.attach_file(file_path)

    def extract_section(self, full_text, start_patterns, end_patterns):
        """
        Extracts a section of text between start and end patterns.

        Args:
            full_text (str): The entire text of the document.
            start_patterns (list): A list of possible start keywords for the section.
            end_patterns (list): A list of possible keywords that mark the end of the section.

        Returns:
            str: The extracted section text, or None if not found.
        """
        # Create robust regex patterns
        # This joins all possible start/end words with '|' (OR operator)
        # re.IGNORECASE makes the search case-insensitive
        start_regex = r'|'.join(start_patterns)
        end_regex = r'|'.join(end_patterns)

        try:
            # Find the start of the section
            # We search for the start pattern followed by a newline to be more specific
            start_match = re.search(f'({start_regex})' + r'\n', full_text, re.IGNORECASE)
            if not start_match:
                print(f"Could not find start of section with keywords: {start_patterns}")
                return None

            # The text we'll search for the end pattern starts after the beginning of the start_match
            text_after_start = full_text[start_match.end():]

            # Find the first occurrence of an end pattern after the start of our section
            end_match = re.search(end_regex, text_after_start, re.IGNORECASE)

            if not end_match:
                print(f"Found a start but could not find the end of the section with keywords: {end_patterns}")
                # If no end is found, maybe it's the last section? This part can be improved.
                return text_after_start.strip() 

            # The section is the text between the start and the end
            section_text = text_after_start[:end_match.start()]
            
            return section_text.strip()

        except Exception as e:
            return f"An error occurred during regex search: {e}"

    def extract_abstract(self):
        abstract_start = ["Abstract", "A B S T R A C T"]
        abstract_end = ["Introduction", "1. Introduction", "I. Introduction", "Keywords:", "Index Terms"]
        abstract = self.extract_section(self.full_text, abstract_start, abstract_end)
        if abstract is None:
            return None
        
        abstract = abstract.replace('\n', ' ')
        abstract = abstract.replace('  ', ' ')
        abstract = abstract.strip()
        abstract = remove_unwanted_dashes(abstract)
        return abstract

    def extract_tasks(self):
        prompt = '\n'.join(self.settings.config.paper_reader.llm.prompts.extract_specific_problem)
        thoughts, response = self.llm_client.run(prompt)
        return response.strip('\n[]').replace(', ', ',').split(',')

    def extract_methods(self):
        prompt = '\n'.join(self.settings.config.paper_reader.llm.prompts.extract_methods)
        thoughts, response = self.llm_client.run(prompt)
        return response.strip('\n[]').replace(', ', ',').split(',')

    def extract_datasets_and_metrics(self):
        all_tables, all_dataset_names, all_table_csv_texts = self.extract_tables()
        metrics_prompt = self.settings.config.paper_reader.llm.prompts.extract_metrics
        metrics_prompt = '\n'.join(metrics_prompt)
        
        comparisons_prompt = self.settings.config.paper_reader.llm.prompts.extract_comparisons
        comparisons_prompt = '\n'.join(comparisons_prompt)
        metrics = set()
        comparisons_list = []

        for table_csv_text in all_table_csv_texts:
            prompt = f"{metrics_prompt}\n\n{table_csv_text}"
            thoughts, response = self.llm_client.run(prompt)

            # get string enclosed in ```json and ```
            print(f'metrics response: {response}')
            if response.find('```json') != -1:
                match_result = re.search(r'```json(.*)```', response, re.DOTALL)
                if match_result is None:
                    continue
                response = re.search(r'```json(.*)```', response, re.DOTALL).group(1)

            try:
                cleaned_response = clean_json_string(response)
                if cleaned_response is None:
                    self.log.error(f"Failed to clean JSON for metrics: {response}")
                    continue
                metrics_list = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                self.log.error(f"Failed to decode JSON for metrics: {e}. Response: {response}")
                metrics_list = []

            for metric in metrics_list:
                if isinstance(metric, str):
                    metrics.add(metric)

            prompt = f"{comparisons_prompt}\n\n{table_csv_text}"
            thoughts, response = self.llm_client.run(prompt)
            print(f'comparisons response: {response}')

            # get string enclosed in ```json and ```
            if response.find('```json') != -1:
                match_result = re.search(r'```json(.*)```', response, re.DOTALL)
                if match_result is None:
                    continue
                response = match_result.group(1)
            try:
                cleaned_response = clean_json_string(response)
                if cleaned_response is None:
                    self.log.error(f"Failed to clean JSON for comparisons: {response}")
                    continue
                comparisons = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                self.log.error(f"Failed to decode JSON for comparisons: {e}. Response: {response}")
                comparisons = []

            for comparison in comparisons:
                print(comparison)
                comparisons_list.append(comparison)
        return all_dataset_names, list(metrics), comparisons_list

    def extract_limitations(self):
        limitations_start = ["Limitations", "Limitations of this study", "Limitations and Future Work"]
        limitations_end = ["Conclusion", "Conclusions", "Acknowledgements", "References", "Appendix", "References"]
        limitations = self.extract_section(self.full_text, limitations_start, limitations_end)
        if limitations is None:
            return None
        
        limitations = limitations.replace('\n', ' ')
        limitations = limitations.replace('  ', ' ')
        limitations = limitations.strip()
        return limitations
    
    def extract_references(self, verbose: bool = False) -> list[Paper]:
        #references_section = self._find_references_section(self.full_text)
        references_section = self._extract_references_without_headers_footers(self.file_path)
        
        if verbose:
            self.log.debug(f'original references section: {references_section}')
       
        if references_section and len(references_section) > 0:
            '''
            references_content = re.sub(r'.*\n', '', references_section, 1)
            if references_content.startswith('\n'):
                references_content = references_content[1:]
            '''
            references_content = references_section
            start_chunk_matches = re.search(r'^\[\d|(?<=\d)\.(?=\s)', references_content)
            if start_chunk_matches is None:
                references_content = replace_newlines_except_after_dot(references_content, ' ')
                references_content = remove_garbage_lines(references_content)
                self.log.debug(f'references_content after replacing newlines: {references_content}')
                self.log.debug('reference section without index numbers detected. splitting at years with dot ..')
                references_content = split_text_at_years_with_dot(references_content)
            else:
                if references_content.startswith('['):
                    references_content = references_content.replace('[', '\n[')
                    references_content = self._clean_parsed_text(references_content)
                elif references_content.startswith('('):
                    references_content = references_content.replace('(', '\n(')
                    references_content = self._clean_parsed_text(references_content)
                else:
                    references_content = add_newlines_before_numbered_references(references_content)
                    self.log.debug(f'references_content after adding newlines before numbered references: {references_content}')
                    references_content = self._parse_number_indexed_references_text(references_content)

            if len(references_content) == 0:
                self.log.debug('no references content detected')
                return []
               
            if verbose:
                self.log.debug(f'references content after cleaning: {references_content}')

            references_content = '\n'.join(references_content)
            papers = self._parse_references(references_content)

            for i, paper in enumerate(papers):
                print(f"Paper {i+1}:")
                print(f"  Title: {paper.title}")
                print(f"  Authors: {paper.authors}")
                print(f"  Type: {paper.paper_type}")
                print(f"  Year: {paper.year}")
                print(f"  Venue: {paper.venue}")
                print(f"  Pages: {paper.pages}")
                print()

            self.reference_papers = papers
        else:
            print("No references section found.")
            self.reference_papers = []
        return self.reference_papers

    def extract_references_arxiv(self, paper: Paper):
        url = paper.media.arxiv_url
        self.log.debug(f'arxiv url: {url}')
        if url is None:
            return []
       
        web_scraper = WebScraper(self.settings, self.log)
        web_scraper.fetch_url(url)
       
        references_id = 'col-references'
        if not web_scraper._wait_for_element_located(By.ID, references_id, 5):
            return []
        
        references_list_element = web_scraper.find_element_by_id(references_id)

        if references_list_element is None:
            return []
        
        references_list_elements = references_list_element.find_all('bib-paper')
        if len(references_list_elements) == 0:
            return []
       
        reference_texts = [] 
        for element in references_list_elements:
            ref_text = element.find('a').text
            reference_texts.append(ref_text)
            
        references_content = '\n'.join(reference_texts)
        papers = self._parse_references(references_content)

        for i, paper in enumerate(papers):
            print(f"Paper {i+1}:")
            print(f"  Title: {paper.title}")
            print(f"  Authors: {paper.authors}")
            print(f"  Type: {paper.paper_type}")
            print(f"  Year: {paper.year}")
            print(f"  Venue: {paper.venue}")
            print(f"  Pages: {paper.pages}")
            print()

        self.reference_papers = papers 
   
    def extract_tables(self):
        table_detector_config = TATRDetectorConfig()
        table_detector_config.detector_base_threshold = 0.75
        self.table_detector = AutoTableDetector(table_detector_config)

        config_hdr = AutoFormatConfig()
        config_hdr.verbosity = 3
        config_hdr.enable_multi_header = True
        config_hdr.semantic_spanning_cells = True
        self.table_formatter: AutoTableFormatter = AutoTableFormatter(config=config_hdr)
 
        all_tables = []
        all_table_csv_texts = []
        all_dataset_names = []

        pdf_path = self.file_path.absolute().with_suffix('')
       
        table_index = 0
        for page in self.pdf_doc:
            tables = self.table_detector.extract(page)
            for table in tables:
                extracted_table = self.table_formatter.extract(table)
                captions = extracted_table.captions()
                
                table_csv_path = f'{pdf_path}.table{table_index:02d}.csv'
                print(f'writing table to {table_csv_path}')

                df = extracted_table.df()
                df.to_csv(table_csv_path)
                # get csv text from dataframe
                table_csv_text = ""
                for index, row in df.iterrows():
                    table_csv_text += ','.join(row.values.astype(str)) + '\n'

                all_table_csv_texts.append(table_csv_text)

                dataset_names = self.extract_datasets(captions)
                all_dataset_names.extend(dataset_names)
                all_tables.append(extracted_table)

                table_index += 1

        return all_tables, all_dataset_names, all_table_csv_texts
   
    def summarize_sentence(self, sentence: str, max_words: int):
        prompt = '\n'.join(self.settings.config.paper_reader.llm.prompts.summarize_sentence)
        prompt = prompt.replace('{max_words}', str(max_words))
        prompt += f'\n\n{sentence}'
        thoughts, response = self.llm_client.run(prompt)
        return response.strip()
    
    def summarize_paragraph(self, paragraph: str, max_sentences: int):
        prompt = '\n'.join(self.settings.config.paper_reader.llm.prompts.summarize_paragraph)
        prompt = prompt.replace('{max_sentences}', str(max_sentences))
        prompt += f'\n\n{paragraph}'
        thoughts, response = self.llm_client.run(prompt)
        return response.strip()

    def extract_datasets(self, captions: str):
        prompt = '\n'.join(self.settings.config.paper_reader.llm.prompts.extract_datasets)
        prompt += f'\n\n{captions}'
        thoughts, response = self.llm_client.run(prompt)
        return response.strip('\n[]').replace(', ', ',').split(',')
  
    def _parse_citation(self, references_lines):
        papers = []
        for ref in references_lines:
            paper = self._parse_bibliographic_info(ref.strip())
            if paper:
                papers.append(paper)
        return papers
    
    def _parse_references(self, ref):
        return self._parse_bibliographic_info(ref)

    def _parse_number_indexed_references_text(self, text):
        def new_line_index(text) -> bool:
            pattern = r'[0-9]+\.\s'
            matches = re.search(pattern, text) 
            if matches is not None:
                return matches.start(), matches.end()
            return -1, -1

        lines = text.split('\n')
        cleaned_refs = []
        current_ref = ''
        for line in lines:
            if new_line_index(line)[0] == 0:
                cleaned_refs.append(current_ref)
                current_ref = ''
            current_ref += line.strip()
        
        # Final cleaning
        final_refs = []
        for ref in cleaned_refs:
            index_start, index_end = new_line_index(ref)
            if len(ref) > 0 and index_start == 0:
                final_refs.append(ref[index_end:].strip())

        return self._clean_parsed_reference_text(final_refs)
        
    def _clean_parsed_text(self, text):
        lines = text.split('\n')
        
        cleaned_refs = []
        current_ref = ""
        right_column = ""

        def is_new_line(text) -> bool:
            if len(text) == 0:
                return False
            if text[0] == '[':
                return True
            pattern = r'^(?<=\d)\.\s'
            match = re.search(pattern, text)
            if match:
                return True
            return False
        
        for line in lines:
            if len(line) == 0:
                continue
            
            if len(line) < 2:
                if line[0] == '\n':
                    cleaned_refs.append(current_ref)
                continue
            
            spaces_first_occur_index = find_first_successive_spaces(line)

            if is_new_line(line):
                # If we have a previous reference, add it to the list
                if len(current_ref) > 0:
                    cleaned_refs.append(current_ref)

                if spaces_first_occur_index == 0:
                    lstripped = line.lstrip()
                    if starts_with_number(lstripped):
                        stripped = lstripped.lstrip('0123456789')
                        if len(stripped) > 0:
                            right_column += " " + stripped.strip()
                elif spaces_first_occur_index > 0:
                    right_column += " " + line[spaces_first_occur_index:].strip()
                    current_ref = line[:spaces_first_occur_index].strip()
                else:
                    current_ref = line.strip()
            elif spaces_first_occur_index >= 0:
                if spaces_first_occur_index == 0:
                    lstripped = line.lstrip()
                    if starts_with_number(lstripped):
                        stripped = lstripped.lstrip('0123456789')
                        if len(stripped) > 0:
                            right_column += " " + stripped.strip()
                    else:
                        right_column += " " + lstripped
                elif spaces_first_occur_index > 0:
                    right_column += " " + line[spaces_first_occur_index:].strip()
                current_ref += " " + line[:spaces_first_occur_index].strip()
            else:
                current_ref += " " + line.strip()

        last_part = current_ref + " " + right_column

        last_part = last_part.replace('\n', ' ')
        last_part = last_part.replace('[', '\n[')
        last_part_lines = last_part.split('\n')
        for line in last_part_lines:
            if not is_new_line(line):
                continue
            cleaned_refs.append(line.replace('- ', '').strip())
         
        # Final cleaning
        return self._clean_parsed_reference_text(cleaned_refs)

    def _clean_parsed_reference_text(self, refs):
        # Final cleaning
        final_refs = []
        for ref in refs:
            ref = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', ref)
            ref = re.sub(r'\s+', ' ', ref).strip()
            final_refs.append(ref)
        return final_refs
         
    def _parse_bibliographic_info(self, ref):
        # make references into a file
        file_path = self.file_path.absolute().as_posix() + '.citations.txt'
        with open(file_path, 'w') as f:
            f.write(ref)

        # run AnyStyle
        parse_references_result = self.perform_action(ActionType.EXECUTE_SHELL_COMMAND, ActionInput(f'anystyle parse "{file_path}"'))
        json_text = parse_references_result.message
        if len(json_text) == 0:
            self.log.error(f'failed to parse references for paper [{self.file_path.name}]: {json_text}')
            return []
        
        info = json.loads(json_text)

        papers = []
        for citation in info:
            paper = self._parse_bibliographic_info_single(citation)
            if paper is not None:
                papers.append(paper)
        return papers

    def _parse_bibliographic_info_single(self, citation):
        title = ''
        authors = []
        year = -1
        note = ''
        venue = ''
        paper_type = None
        pages = None
        
        for key, value in citation.items():
            if key == 'citation-number':
                pass
            elif key == 'author':
                for author in value:
                    author_name = None
                    if 'given' in author:
                        author_name = author['given']
                    if 'family' in author:
                        if author_name is not None:
                            author_name += ' '
                        else:
                            author_name = ''
                        author_name += author['family']
                    if author_name is None:
                        if 'literal' in author:
                            author_name = author['literal']
                        elif 'others' in author:
                            author_name = author['others']
                        else:
                            author_name = ''
                    if isinstance(author_name, str):
                        authors.append(author_name)
            elif key == 'title':
                title = fix_parentheses(value[0].replace('- ', ''))
            elif key == 'container-title':
                venue = fix_parentheses(value[0].replace('- ', ''))
            elif key == 'type':
                if value is not None and value != 'null':
                    paper_type = value
            elif key == 'date':
                date_str = None
                if isinstance(value, list):
                    if len(value) > 0:
                        date_str = value[0]
                else:
                    date_str = value

                if date_str is not None and len(date_str) > 0:
                    date_str = remove_non_numeric(date_str)
                    if '-' in date_str:
                        year_str = date_str.split('-')[0]
                    elif '.' in date_str:
                        year_str = date_str.split('.')[0]
                    elif ',' in date_str:
                        year_str = date_str.split(',')[0]
                    else:
                        year_str = date_str
                    #year_str = year_str[:4]
                    numbers = re.findall(r'\d+', year_str)
                    if len(numbers) > 0:
                        year = int(numbers[0][:4])
                    else:
                        print(f'failed to get year from: {date_str}')
            elif key == 'pages':
                pages = value
            elif key == 'note':
                note = value

        if year == -1 and len(authors) == 0:
            return None

        paper_content = PaperContent(
            abstract=None,
            references=None,
            cited_by=None,
            bibtex=None,
            primary_task=None,
            secondary_task=None,
            tertiary_task=None,
            primary_method=None,
            secondary_method=None,
            tertiary_method=None,
            datasets_used=None,
            metrics_used=None,
            comparisons=None,
            limitations=None
        )
        
        paper_media = PaperMedia(
            pdf_url=None,
            youtube_url=None,
            github_url=None,
            project_page_url=None,
            arxiv_url=None
        )
    
        github_star_count = 0
        github_star_avg_hype = 0
        github_star_weekly_hype = 0
        github_star_monthly_hype = 0
        github_star_tracking_start_date = None
        github_star_tracking_latest_footprint = None
        citations_total = None
        
        paper_metrics = PaperMetrics(
            github_star_count=github_star_count,
            github_star_avg_hype=github_star_avg_hype,
            github_star_weekly_hype=github_star_weekly_hype,
            github_star_monthly_hype=github_star_monthly_hype,
            github_star_tracking_start_date=github_star_tracking_start_date,
            github_star_tracking_latest_footprint=github_star_tracking_latest_footprint,
            citations_total=citations_total
        )

        arxiv_id = None
        if paper_type is not None:
            conf_keywords = ['Conf.', 'Conference', 'Workshop', 'Workshops', 'Symposium', 'Symposia', 'Symposiums', 'Conference on', 'Workshop on', 'Symposium on', 'Conference of', 'Workshop of', 'Symposium of']
            if paper_type == 'paper-conference' or any(conf_keyword in venue for conf_keyword in conf_keywords):
                paper_type = PaperType.CONFERENCE_PAPER
            elif paper_type == 'article-journal':
                is_arxiv = False
                for note_str in note:
                    if 'arxiv' not in note_str.lower():
                        continue
                    paper_type = PaperType.ARXIV_PAPER
                    arxiv_id = note_str.split(':')[1].split('v')[0]
                    is_arxiv = True
                    break
                if not is_arxiv:
                    paper_type = PaperType.JOURNAL_PAPER
            elif paper_type == 'book':
                paper_type = PaperType.BOOK
            elif paper_type == 'chapter':
                paper_type = PaperType.BOOK_CHAPTER
            elif paper_type == 'report':
                paper_type = PaperType.REPORT
            else:
                paper_type = PaperType.UNKNOWN
                
        paper_session_type = PaperSessionType.UNKNOWN
        paper_accept_status = PaperAcceptStatus.UNKNOWN
        
        if title == '':
            return None

        if year == -1:
            return None
        
        if len(authors) == 0:
            return None
        
        # strip if [] exists in title
        if '[' in title:
            start_index = title.find('[')
            title = title[:start_index]
        
        if isinstance(note, list):
            note = ' '.join(note)
 
        paper = Paper(
            id=make_generated_id(title, year),
            arxiv_id=arxiv_id,
            title=title,
            authors=authors,
            year=year,
            venue=venue,
            pages=pages,
            paper_type=paper_type,
            session_type=paper_session_type,
            accept_status=paper_accept_status,
            note=note,
            content=paper_content,
            media=paper_media,
            metrics=paper_metrics
        )
        return paper

    def _find_references_section(self, text):
        headers = ["References", "Bibliography", "Works Cited", "Literature Cited"]
        
        for header in headers:
            pattern = rf"(?i){re.escape(header)}.*?(?=\n\n\w+|\Z)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                references_text = match.group().strip()
                print(f'references_text: {references_text}')
                references_text = re.split(r'\n[0-9]+\n', references_text)[0]
                return references_text
        return None 
   
    def _extract_references_without_headers_footers(self, file_path):
        # Open the PDF
        doc = fitz.open(file_path)
        references_text = ""
        found_references = False
        page_texts = []

        # Collect text from each page to identify potential headers/footers
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text("text")
            page_texts.append(text.splitlines())

        # Find recurring lines across pages (likely headers/footers)
        all_lines = [line for page in page_texts for line in page]
        line_counts = Counter(all_lines)
        # Consider lines as headers/footers if they appear on more than half of the pages
        common_lines = {line for line, count in line_counts.items() if count > doc.page_count / 2}

        # Loop through each page again to extract the References section, excluding common lines
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text_lines = page.get_text("text").splitlines()
            text = "\n".join(line for line in text_lines if line not in common_lines)

            # Check if the text contains the start of the References section
            if not found_references:
                # Match "References" (or adjust for other keywords if needed)
                if re.search(r'References', text):
                    found_references = True
                    # Start collecting text after finding "References"
                    remaining_text = text.split("References", 1)
                    if len(remaining_text) > 1:
                        references_text += remaining_text[1].strip()
            else:
                # Continue collecting text in subsequent pages
                references_text += "\n" + text

        doc.close()
        return references_text
    
    def extract_references_from_pdf(self, file_path):
        # Open the PDF
        doc = fitz.open(file_path)
        references_text = ""
        found_references = False

        # Loop through each page to search for the References section
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()

            # Check if the text contains the start of the References section
            if not found_references:
                # Match "References" (or adjust for other keywords if needed)
                if re.search(r'References', text, re.IGNORECASE):
                    found_references = True
                    # Start collecting text after finding "References"
                    references_text += text.split("References", 1)[1].strip()
            else:
                # Continue collecting text in subsequent pages
                references_text += "\n" + text

        # Optional: Stop collecting if another section header is detected
        references_text = re.split(r'[A-Z][a-z]+', references_text)[0]

        doc.close()
        return references_text
    
    def _get_text_from_response(self, response):
        text = ''
        for text_chunk in response.response_gen:
            text += text_chunk
        return text

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf-path', type=str, required=True)
    parser.add_argument('--config-path', type=str, default=get_config_path().absolute())
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    settings = Settings(args.config_path)
    logger = loguru.logger

    paper_reader = PaperReader(settings, logger)
    paper_reader.set_file_path(pdf_path)
    
    abstract = paper_reader.extract_abstract()
    tasks = paper_reader.extract_tasks()
    methods = paper_reader.extract_methods()
    all_dataset_names, metrics, comparisons = paper_reader.extract_datasets_and_metrics()
    references = paper_reader.extract_references(verbose=False)
    limitations = paper_reader.summarize_paragraph(paper_reader.extract_limitations(), settings.get('paper_reader').llm.max_summary_sentences_normal)

    print(f'abstract: {abstract}')
    print(f'tasks: {tasks}')
    print(f'methods: {methods}')
    print(f'datasets: {all_dataset_names}')
    print(f'metrics: {metrics}')
    print(f'comparisons: {comparisons}')
    print(f'limitations: {limitations}')