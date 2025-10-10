import sys
import regex
import re
import unicodedata
import json
import re
import string
import csv
import io
import loguru

from typing import Optional, Dict, Any
from charset_normalizer import detect
from pathlib import PosixPath

def has_successive_spaces(text):
    return bool(re.search(r'\s{2,}', text))

def find_first_successive_spaces(text):
    match = re.search(r'\s{4,}', text)
    return match.start() if match else -1

def starts_with_number(text):
    pattern = r'^\d+'
    match = re.match(pattern, text)
    return bool(match)

def fix_parentheses(input_string):
    open_count = 0
    result = []

    for char in input_string:
        if char == '(':
            open_count += 1
            result.append(char)
        elif char == ')':
            if open_count > 0:
                open_count -= 1
                result.append(char)
        else:
            result.append(char)

    result.append(')' * open_count)
    fixed = ''.join(result)
    return fixed

def remove_non_numeric(text):
    return re.sub(r'[^0-9]', '', text)

def remove_unwanted_dashes(text):
    return re.sub(r'-\s+', '', text)

def find_references_start(text):
    patterns = [
        r'^\s*(References|Bibliography|Works Cited|Literature Cited)\s*$',
        r'^\s*REFERENCES\s*$',
        r'^\s*References\s*\n',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.end()
    return None

def replace_newlines_except_after_dot(text, replacement):
    temp_text = text.replace('.\n', 'NEWLINE_AFTER_DOT')
    temp_text = temp_text.replace('\n', replacement)
    text = temp_text.replace('NEWLINE_AFTER_DOT', '.\n')
    return text

def add_newlines_before_numbered_references(text):
    pattern = r'^\d+\.\s'
    modified_text = re.sub(pattern, '.\n', text)
    return modified_text

def extract_page_numbers(text):
    pattern = r'\n[0-9]*\n'
    matches = re.findall(pattern, text)
    return [match.strip() for match in matches]

def remove_garbage_lines(text):
    pattern = r'^\s*[0-9]*\s*(Published as a conference paper.*)\s*\n'
    return re.sub(pattern, '\n\n', text, flags=re.MULTILINE)

def get_author_first_pattern():
    name_prefix_pattern = r"""
        (?:
            ([A-Z]|van der|van de|van den|van|von|de)
        )
    """ 
    
    name_remaining_pattern = r"""
        (?:
            \.|[a-z\,\'\-]*|((?=\p{L})(?!\s))
        )
    """
    
    author_name_pattern = rf'''
        (?: 
            {name_prefix_pattern}
            {name_remaining_pattern}
            (?:
                {name_prefix_pattern}?
                {name_remaining_pattern}
            )?
            \s
            (
                {name_prefix_pattern}
                {name_remaining_pattern}
            )
        )
    '''
    
    author_pattern = rf'''
        {author_name_pattern}|"et al"
    '''

    # Define a regex pattern to match separators between authors
    separator_pattern = r'''
        (?:                                     # Non-capturing group for separators
            ,\s*                                # Comma separator
            |                                   # or
            ,\s*and\s+                          # ', and ' separator
            |                                   # or
            \s+and\s+                           # ' and ' separator
            |                                   # or
            \s+&\s+                             # ' & ' separator
        )
    '''
    
    title_pattern = r'[0-9a-zA-Z\s\-\:\;\?\'\"]+'

    # Combine the patterns to match the start of a citation
    pattern = rf'''
        ^{author_pattern}                        # First author
        (?:                                     # Non-capturing group for additional authors
            {separator_pattern}
            {author_pattern}
        )*
        (?:
            \s
            (\()?\d{4}[a-z]?(\))?                      # Year in parentheses, possibly with a letter, followed by a period
        )?
        \.
        \s+
        {title_pattern}
        (?:
            \s
            \d{4}[a-z]?
        )
        \.
    '''
    return regex.compile(author_pattern, regex.MULTILINE | regex.VERBOSE | regex.UNICODE), regex.compile(pattern, regex.MULTILINE | regex.VERBOSE | regex.UNICODE) 
    #return regex.compile(author_pattern, regex.VERBOSE | regex.UNICODE), regex.compile(pattern, regex.VERBOSE | regex.UNICODE) 

def split_text_at_years_with_dot(text):
    pattern = r'''
        ^
        (?:                                    # Non-capturing group for authors
            (?:\p{L}+\s+)*                     # Possible prefixes in last name
            \p{L}+                             # Last name
            ,?\s+                              # Optional comma, followed by whitespace
            (?:\p{L}\.\s*)+                    # One or more initials
        )
        (?:                                    # Additional authors
            (?:,\s*|,\s*and\s+|,\s*&\s+| and\s+| &\s+|\s+and\s+|\s+&\s+)   # Separators
            (?:\p{L}+\s+)*                     # Possible prefixes in last name
            \p{L}+                             # Last name
            ,?\s+                              # Optional comma, followed by whitespace
            (?:\p{L}\.\s*)+                    # One or more initials
        )*
        \s*                                    # Optional whitespace
        \(?\d{4}[a-z]?\)?\.                      # Year in parentheses, possibly with a letter, followed by a period
    '''
   
    regex_pattern = regex.compile(pattern, regex.MULTILINE | regex.VERBOSE | regex.UNICODE)
    matches = list(regex_pattern.finditer(text))
   
    author_first = False 
    if len(matches) == 0:
        print(f'no matches found for pattern: {pattern}')
        author_first = True
       
        author_pattern, regex_pattern = get_author_first_pattern()
        matches = list(regex_pattern.finditer(text))

    # If no matches are found, return the whole text as one citation
    if len(matches) == 0:
        print(f'no matches found for pattern: {pattern}')
        return []

    # Add the end position of the text to facilitate slicing
    match_positions = [(match.start(), match.end()) for match in matches]

    last_citation_start = match_positions[-1][0]
    last_citation_end = match_positions[-1][1]
    last_newline_match = re.search(r'\.\n[0-9A-Z]+', text[last_citation_end:])
    last_newline_index = last_citation_end + last_newline_match.start() if last_newline_match else len(text)
    
    if last_newline_index < len(text):
        references_text = text[:last_newline_index+1]
    else:
        references_text = text
       
    print(f'last part: {text[last_citation_start:last_newline_index]}') 
    print(f'references_text after slicing({last_citation_end}/{last_newline_index}/{len(text)}): {references_text}')

    matches = list(regex_pattern.finditer(references_text))
    if len(matches) == 0:
        print(f'no matches found for pattern: {pattern} in references_text after slicing')
        return []

    # Extract citations based on the positions of the matches
    match_positions = [(match.start(), match.end()) for match in matches]
    citations = []
    cur_citation = ''

    if author_first:
        author_after_dot_pattern = regex.compile(rf'\.{author_pattern}', regex.MULTILINE | regex.VERBOSE | regex.UNICODE)
        dot_matches = list(author_after_dot_pattern.finditer(references_text))
        if dot_matches is not None:
            for dot_match in dot_matches:
                dot_matches_start = dot_match.start()
                dot_matches_end = dot_match.end()
                dot_matches_text = references_text[dot_matches_start:dot_matches_end]
                references_text = references_text[:dot_matches_start+1] + '\n' + references_text[dot_matches_start+1:]
                print(f'text having pattern recognized after dot: {dot_matches_text}')
   
    last_matched = False
    year_pattern = regex.compile(r'\s\(?[1-2](0|9)\d{2}[a-z]?\)?\.', regex.MULTILINE | regex.VERBOSE | regex.UNICODE)
    garbage_pattern = regex.compile(r'[0-9]+\.[0-9]+|[0-9]+-[0-9]+', regex.MULTILINE | regex.VERBOSE | regex.UNICODE)

    for line in references_text.split('\n'):
        citation = line.lstrip('0123456789').replace('- ', '')
        matches = list(regex_pattern.finditer(citation))

        if len(matches) > 0:
            match_start = matches[0].start()
            match_end = matches[0].end()
            print(f'matched: {citation[match_start:match_end]}')
            
            author_matches = list(author_pattern.finditer(citation))
            author_match_end = author_matches[0].end() if len(author_matches) > 0 else 0
            
            garbage_match = garbage_pattern.search(citation)
            if garbage_match is not None:
                print(f'garbage_match: {garbage_match}')
                garbage_matches_start = garbage_match.start()
                garbage_matches_end = garbage_match.end()
                garbage_matches_text = citation[garbage_matches_start:garbage_matches_end]
                citation = citation[:garbage_matches_start] + citation[garbage_matches_end+1:]

            year_match = year_pattern.search(cur_citation)
            if year_match is not None and len(cur_citation) > 0:
                year_matches_start = year_match.start()
                year_matches_end = year_match.end()
                if cur_citation[year_matches_start-1] != '.' or cur_citation[year_matches_start-1] != ',':
                    temp_citation = list(cur_citation)
                    temp_citation[year_matches_start-1] = ','
                    cur_citation = ''.join(temp_citation)
                
                last_matched = True

                    
                # truncate if it contains appendix text
                if len(cur_citation) > year_matches_end+1:
                    cur_citation = cur_citation[:year_matches_end+1]

                if 'arXiv preprint' in cur_citation:
                    arxiv_match_start = cur_citation.find('arXiv preprint')
                    arxiv_match_end = cur_citation[arxiv_match_start:].find(',')
                    cur_citation = cur_citation[:arxiv_match_start] + cur_citation[arxiv_match_start+arxiv_match_end+1:]

                print(f'citation [{len(citations)}]: {cur_citation}')
                citations.append(cur_citation)
                cur_citation = citation
                continue
            else:
                last_matched = False
        else:
            last_matched = False

        if len(cur_citation) > 0 and cur_citation[-1] == '.':
            cur_citation += ' '
        cur_citation += citation

    '''
    if not last_matched and len(cur_citation) > 0:
        year_match = year_pattern.search(cur_citation)
        print(f'year_match: {year_match}, cur_citation: {cur_citation}')
        if year_match and len(cur_citation) > 0:
            year_matches_end = year_match.end()
            if len(cur_citation) > year_matches_end:
                cur_citation = cur_citation[:year_matches_end+1]
        citations.append(cur_citation)
    '''
        
    final_citations = []
    # double check
    for citation in citations:
        matches = list(regex_pattern.finditer(citation))
        if len(matches) == 0:
            print(f'no matches found for pattern: {regex_pattern} in citation: {citation}')
            continue
        print(f'citation [{len(final_citations)}]: {citation}')
        final_citations.append(citation)
    return final_citations 

def is_natural_language_line(line):
    import spacy
    nlp = spacy.load('en_core_web_sm')

    line = line.strip()
    if not line:
        return False
    doc = nlp(line)
    first_token = doc[0]

    if first_token.is_lower or first_token.pos_ in ['PRON', 'DET', 'ADV', 'VERB', 'ADJ', 'SCONJ', 'CCONJ', 'NUM']:
        return True

    if any(sent for sent in doc.sents if any(token.dep_ == 'nsubj' for token in sent) and any(token.pos_ == 'VERB' for token in sent)):
        return True
    return False

def remove_unicode_chars(s: str) -> str:
    # Normalize to NFKD and filter out non-ASCII characters
    normalized = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in normalized if ord(c) < 128)

def compare_strings_with_tolerance(s1: str, s2: str, max_diff: int = 2) -> bool:
    s1 = remove_unicode_chars(s1).lower()
    s2 = remove_unicode_chars(s2).lower()
    
    if len(s1) != len(s2):
        return False
    diff_count = sum(1 for a, b in zip(s1, s2) if a != b)
    return diff_count <= max_diff

if __name__ == '__main__':
    text = sys.argv[1]
    
    author_pattern, regex_pattern = get_author_first_pattern()

    matches = list(regex_pattern.finditer(text))
    if len(matches) == 0:
        print(f'no matches found for pattern: {regex_pattern}')
        sys.exit(1)
        
    match_positions = [(match.start(), match.end()) for match in matches]

    last_citation_start = match_positions[-1][0]
    last_citation_end = match_positions[-1][1]
    last_newline_match = re.search(r'\.\n', text[last_citation_end:])
    last_newline_index = last_citation_end + last_newline_match.start() if last_newline_match else len(text)
    print(f'last_newline_index: {last_newline_index}, len(text): {len(text)}')
    if last_newline_index < len(text):
        references_text = text[:last_newline_index+1]
    else:
        references_text = text

    author_after_dot_pattern = regex.compile(rf'\.{author_pattern}', regex.MULTILINE | regex.VERBOSE | regex.UNICODE)
    dot_matches = list(author_after_dot_pattern.finditer(references_text))
    if dot_matches is not None and len(dot_matches) > 0:
        dot_matches_start = dot_matches[0].start()
        references_text = references_text[:dot_matches_start+1] + '\n' + references_text[dot_matches_start+1:]
    print(references_text)
 
    
    citations = []
    cur_citation = ''
   
    last_matched = False
    year_pattern = regex.compile(r'\s\d{4}[a-z]?\.', regex.VERBOSE | regex.UNICODE)
    
    for line in references_text.split('\n'):
        citation = line.lstrip('0123456789').replace('- ', '')
        matches = list(regex_pattern.finditer(citation))
        print(f'matches: {matches}')
        if len(matches) > 0:
            match_end = matches[-1].end()
            author_matches = list(author_pattern.finditer(citation))
            author_match_end = author_matches[-1].end() if len(author_matches) > 0 else 0
            print(f'match_end: {match_end}, author_match_end: {author_match_end}')
            #print(f'match_end: {match_end}, len(citation): {len(citation)}')
            #buffer = citation
            year_match = year_pattern.search(cur_citation)
            print(f'year_match: {year_match}, cur_citation: {cur_citation}')
            if year_match and len(cur_citation) > 0:
                year_matches_end = year_match.end()
                last_matched = True
                
                citations.append(cur_citation)
                print(f'citation [{len(citations)}]: {cur_citation}')
                cur_citation = citation
                #cur_citation = buffer
                #buffer = ''
                continue
        else:
            last_matched = False

        cur_citation += citation

    if not last_matched and len(cur_citation) > 0:
        # truncate if it contains appendix text
        year_match = year_pattern.search(cur_citation)
        print(f'year_match: {year_match}, cur_citation: {cur_citation}')
        if year_match and len(cur_citation) > 0:
            year_matches_end = year_match.end()
            if len(cur_citation) > year_matches_end:
                cur_citation = cur_citation[:year_matches_end]
        citations.append(cur_citation) 
    print(last_matched, citations)
    #parsed = split_text_at_years_with_dot(text)
    #print(parsed)

def clean_json_string(json_str: str, logger: loguru.logger=None) -> Optional[str]:
    """Clean a JSON string to make it parseable by json.loads()."""
    if logger is None:
        logger = loguru.logger

    try:
        # Step 1: Normalize encoding
        encoding_info = detect(json_str.encode())
        if encoding_info['encoding'] != 'utf-8':
            logger.info("Detected non-UTF-8 encoding: %s. Normalizing to UTF-8.", encoding_info['encoding'])
            json_str = json_str.encode(encoding_info['encoding'] or 'utf-8', errors='ignore').decode('utf-8', errors='ignore')

        # Step 2: Remove non-printable characters (except valid JSON control chars)
        valid_chars = set(string.printable) - set('\b\f')  # Allow \n, \r, \t
        json_str = ''.join(c for c in json_str if c in valid_chars)
        logger.debug("Removed non-printable characters.")

        # Step 3: Strip markdown or code fences
        json_str = re.sub(r'^```json\s*|\s*```$', '', json_str, flags=re.MULTILINE)
        json_str = re.sub(r'^```.*?\n|\n```$', '', json_str, flags=re.MULTILINE)
        logger.debug("Stripped markdown code fences.")

        # Step 4: Remove comments (// or /* */)
        json_str = re.sub(r'//.*?\n|/\*.*?\*/', '', json_str, flags=re.DOTALL)
        logger.debug("Removed comments.")

        # Step 5: Fix common JSON errors
        # Remove trailing commas in objects/arrays
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        # Replace single quotes with double quotes
        json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)
        # Escape unescaped quotes
        json_str = re.sub(r'(?<!\\)(\")', r'\\\1', json_str)
        logger.debug("Fixed trailing commas and quotes.")

        # Step 6: Strip leading/trailing whitespace
        json_str = json_str.strip()
        logger.debug("Stripped whitespace.")

        # strip backslashes
        json_str = re.sub(r'\\', '', json_str)

        # Step 7: Validate JSON
        json.loads(json_str)
        logger.info("JSON string is valid after cleaning.")
        return json_str

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON after cleaning: {json_str} - {e}")
        try:
            # Try demjson as a fallback for relaxed JSON
            import demjson3 as demjson
            demjson.decode(json_str)
            logger.info("JSON parsed successfully with demjson.")
            return json_str
        except ImportError:
            logger.warning("demjson3 not installed. Install with 'conda install demjson3' for relaxed JSON parsing.")
        except demjson.JSONDecodeError as de:
            logger.error(f"demjson failed to parse JSON: {de}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error cleaning JSON: {json_str} - {e}")
        return None

def parse_json(json_str: str) -> Optional[Dict[Any, Any]]:
    """Clean and parse a JSON string into a dictionary."""
    cleaned_json = clean_json_string(json_str)
    if cleaned_json is None:
        return None

    try:
        return json.loads(cleaned_json)
    except json.JSONDecodeError as e:
        print("Failed to parse cleaned JSON: %s", e)
        return None

def tatr_table_to_csv(table) -> str:
    """Converts TATRFormattedTable to CSV string"""
    data_dict = table.to_dict()
    output = io.StringIO()
    
    # Get headers from dictionary keys
    headers = list(data_dict.keys())
    
    # Create CSV writer
    writer = csv.writer(output)
    writer.writerow(headers)  # Write header row
    
    # Write data rows by transposing column values
    for row in data_dict.values():
        if isinstance(row, PosixPath):
            print(f'skipping row: {row}')
            continue
        # check row is iterable object
        if not hasattr(row, '__iter__'):
            print(f'skipping row: {row}')
            continue
        
        writer.writerow(row)
    return output.getvalue()

def table_captions_to_csv(captions: str) -> str:
    """Converts table captions to CSV string"""
    return captions